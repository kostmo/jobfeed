#!/usr/bin/python2.5
#
# Copyright 2010 Karl Ostmo
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Main frontend/UI handlers."""

__author__ = 'kostmo@gmail.com (Karl Ostmo)'

import os
import os.path
import wsgiref.handlers

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db

import logging
from datetime import datetime

import feedparser
import models
from auxilliary import getHighestBinWithAtMost, getHighestBucketWithAtMost, getBucketsAtOrAbove, recoverExperienceEntity
from auxilliary import recoverOrgKey
# =============================================================================

template.register_template_library(
    'django.contrib.humanize.templatetags.humanize')
template.register_template_library('templatelib')

# =============================================================================
SKILL_CATEGORY_ENTITY_MAPPING = {
    feedparser.SKILL_CATEGORY_APIS: models.Api,
    feedparser.SKILL_CATEGORY_EQUIPMENT: models.Equip,
    feedparser.SKILL_CATEGORY_DUTIES: models.Duty,
    feedparser.SKILL_CATEGORY_APPLICATIONS: models.App,
    feedparser.SKILL_CATEGORY_PROGRAMMING_LANGUAGES: models.Lang
}

SKILL_CATEGORY_MODEL_NAME_MAPPING = {}
for category, model in SKILL_CATEGORY_ENTITY_MAPPING.items():
    SKILL_CATEGORY_MODEL_NAME_MAPPING[model.__name__] = category

SKILL_CATEGORY_SHORT_TO_FULL_NAME = {}
SKILL_CATEGORY_SUMMARIES_DICT = {}
for i, shortname in enumerate(feedparser.SKILL_CATEGORIES):
    SKILL_CATEGORY_SHORT_TO_FULL_NAME[shortname] = feedparser.SKILL_CATEGORY_NAMES[i]
    SKILL_CATEGORY_SUMMARIES_DICT[shortname] = feedparser.SKILL_CATEGORY_SUMMARIES[i]

# =============================================================================
def make_static_handler(template_file):
    """Creates a webapp.RequestHandler type that renders the given template
    to the response stream."""
    class StaticHandler(webapp.RequestHandler):
        def get(self):
            self.response.out.write(template.render(
                os.path.join(os.path.dirname(__file__), template_file),
                {'current_user': users.get_current_user()}))

    return StaticHandler

# =============================================================================
def make_static_xml_handler(template_file):
    """Creates a webapp.RequestHandler type that renders the given template
    to the response stream."""
    class StaticXmlHandler(webapp.RequestHandler):
        def get(self):
            self.response.headers['Content-Type'] = "application/xml"
#      self.response.headers['Content-Type'] = "text/xml"
            self.response.out.write(template.render(
                os.path.join(os.path.dirname(__file__), template_file),
                {'current_user': users.get_current_user()}))

    return StaticXmlHandler

# =============================================================================
# As per http://code.google.com/appengine/docs/python/datastore/keysandentitygroups.html#Kinds_Names_and_IDs
def normalizeAndSanitizeKey(original):
    unsanitized_name = original.lower()
    disallowed_prefix_suffix = "__" # two underscores
    if unsanitized_name.endswith(disallowed_prefix_suffix) and disallowed_prefix_suffix.startswith(disallowed_prefix_suffix):
        return "x" + unsanitized_name
    return unsanitized_name

# =============================================================================
class SkillConversionHelper:
    def __init__(self):
        pass

# =============================================================================
class FeedUrlSubmission(webapp.RequestHandler):
    '''This routine extracts job entities from the XML feed. There are entities
    that the job makes reference to; these are extracted into separate lists
    and committed to the datstore first.'''

    def convert_job(self, job, parent_entity):
        x = models.Job(parent=parent_entity, location=db.GeoPt(job.geo[0], job.geo[1]))
        x.update_location()

        if job.link:
            x.link = db.Link(job.link)

        x.job_id = job.job_id
        x.title = job.title
        x.description = job.description
        x.expiration = job.expiration
        x.expired = datetime.now().date() >= job.expiration
        x.sample = job.sample
        return x

    # --------------------------------------------------------------------------
    def post(self):

        link_url = self.request.get('submission_url')
        contact_email = self.request.get('contact_email')
        crawl_interval_days = 7*max(1, int(self.request.get('crawl_interval_weeks')))

        validate_only = self.request.get('validate_only')   # TODO Not used

        from urlparse import urlsplit
        parsed_url = urlsplit(link_url)
        link_hostname = parsed_url.hostname


        submission_result = "OK!"


        joblist = []
        all_jobs = []
        if link_hostname:

            q = models.Feed.all()
            q.filter("link =", link_url)
            if q.get():
                submission_result = "Duplicate URL"
            else:
                try:

                    from urllib import urlopen
                    org_hierarchy = feedparser.fetchJobList( urlopen(link_url) )

                    feed_url_object = models.Feed(link=db.Link(link_url))
                    feed_url_object.interval = crawl_interval_days
                    if contact_email:
                        feed_url_object.contact = db.Email(contact_email)
                    # We hold off on committing the feed url in case there are any problems


                    # These entities use parent/child key relationships.
                    organization_entities = []
                    site_entities = []
                    department_entities = []

                    experience_bucketed_skills_entities = []
                    basic_skills_entities_by_category = {}
                    used_skill_names_by_category = {}
                    used_permanence_entity_refs = {}
                    used_seniority_entity_refs = {}

                    for organization, sites_dict in org_hierarchy.items():

                        organization_keyname = normalizeAndSanitizeKey(organization.domain)
                        organization_entity = models.Org.get_or_insert( organization_keyname, name=organization.name, lower=organization.name.lower(), domain=organization.domain)

                        for site, departments_dict in sites_dict.items():

                            site_keyname = normalizeAndSanitizeKey(site.name)
                            site_entity_key = db.Key.from_path('Org', organization_keyname, 'Site', site_keyname)
                            site_entity = models.Site.get(site_entity_key)
                            if not site_entity:
                                site_entity = models.Site(parent=organization_entity, key_name=site_keyname)
                                site_entity.name = site.name
                                site_entity.address = site.address
                                site_entity.geo = db.GeoPt(site.geo[0], site.geo[1])
                                db.put(site_entity)


                            for department, joblist in departments_dict.items():

                                job_parent = None
                                if department:
                                    department_keyname = normalizeAndSanitizeKey(department.name)
                                    department_entity_key = db.Key.from_path('Org', organization_keyname, 'Site', site_keyname, 'Dept', department_keyname)
                                    department_entity = models.Dept.get(department_entity_key)
                                    if not department_entity:
                                        department_entity = models.Dept(parent=site_entity, key_name=department_keyname)
                                        department_entity.name = department.name
                                        db.put(department_entity)
                                    job_parent = department_entity
                                else:
                                    job_parent = site_entity

                                for raw_job in joblist:
                                    all_jobs.append( raw_job )

                                    # Convert simple Job() objects into model entities
                                    raw_job.converted_job_entity = self.convert_job(raw_job, job_parent)
                                    if not (raw_job.permanence is None):
                                        raw_job.converted_job_entity.permanence_level = used_permanence_entity_refs.setdefault(raw_job.permanence, models.PermanenceLevel(key_name=str(raw_job.permanence), name=feedparser.PERMANENCE_OPTIONS[raw_job.permanence], rank=raw_job.permanence))
                                    if not (raw_job.seniority is None):
                                        raw_job.converted_job_entity.seniority_level = used_seniority_entity_refs.setdefault(raw_job.seniority, models.SeniorityLevel(key_name=str(raw_job.seniority), name=feedparser.SENIORITY_OPTIONS[raw_job.seniority], rank=raw_job.seniority))

                                    if raw_job.degree_level:
                                        normalized_degree_level_name = raw_job.degree_level.lower()
                                        if normalized_degree_level_name in feedparser.DEGREE_LEVEL_YEARS_DICT:
                                            degree_level_years = feedparser.DEGREE_LEVEL_YEARS_DICT[raw_job.degree_level.lower()]
                                            degree_level_entity = models.DegreeLevel.get_or_insert(normalized_degree_level_name, name=raw_job.degree_level, rank=degree_level_years)
                                            # TODO: Deal with synonyms/alternate spellings
                                            raw_job.converted_job_entity.degree_level = degree_level_entity

                                    for skill_category, skill_list in raw_job.skills.items():
                                        # Retrieve the skillname dict for this category. This dict is persistent across jobs.
                                        skill_buckets_unique_by_name = used_skill_names_by_category.setdefault(skill_category, {})

                                        for raw_skill in skill_list:
                                            normalized_skillname = normalizeAndSanitizeKey(raw_skill.name)
                                            skill_experience_entities = None
                                            if normalized_skillname in skill_buckets_unique_by_name:
                                                skill_experience_entities = skill_buckets_unique_by_name[normalized_skillname]
                                            else:
                                                # This is the first time this skill name was encountered. Create and assign the model entity instance.

                                                basic_skill_entity = SKILL_CATEGORY_ENTITY_MAPPING[skill_category](key_name=normalized_skillname, name=raw_skill.name, lower=raw_skill.name.lower())

                                                # queue to be "put()"
                                                basic_skills_entities_by_category.setdefault(skill_category, []).append( basic_skill_entity )

                                                skill_experience_entities = [models.Exp(parent=basic_skill_entity, key_name=str(years), years=years) for years in models.EXPERIENCE_YEARS_BUCKETS]
                                                experience_bucketed_skills_entities.extend( skill_experience_entities )  # queue to be "put()"

                                                skill_buckets_unique_by_name[normalized_skillname] = skill_experience_entities

                                            # Whether or not the current skill's name has already been encountered, we
                                            # must link the cannonical bucket entity reference to the raw job's skill list.
                                            raw_skill.bucket_entities = getBucketsAtOrAbove(skill_experience_entities, raw_skill.years)

                    # put() each type into the datastore in separate groups
                    # Here it's okay if the entity already exists; it will just get overwritten by sharing the same key_name.
                    for skill_category_name, skill_entity_list in basic_skills_entities_by_category.items():
                        db.put( skill_entity_list )

                    # We can put() the buckets all in one batch, since they use a supertype shared by each skill category and are homogeneous
                    # Here, since we've also specified the key_name and parent, duplicates will also be overwritten.
                    db.put( experience_bucketed_skills_entities )

                    db.put( used_permanence_entity_refs.values() )
                    db.put( used_seniority_entity_refs.values() )


                    # Consolidate the "keywords" as new entities.
                    unified_keyword_dict = {}
                    for raw_job in all_jobs:
                        raw_job.unified_keywords = []
                        for keyword in raw_job.keywords:
                            normalized_keyword = normalizeAndSanitizeKey(keyword)
                            keyword_entity = unified_keyword_dict.setdefault(normalized_keyword, models.Sub(key_name=normalized_keyword, name=keyword, lower=keyword.lower()))
                            raw_job.unified_keywords.append( keyword_entity )

                    db.put( unified_keyword_dict.values() )

                    for raw_job in all_jobs:
                        raw_job.converted_job_entity.kw = [u.key() for u in set(raw_job.unified_keywords)]


                    # The final thing to do before put()-ing the jobs into the datastore is adding the skill buckets to the correct list.
                    for raw_job in all_jobs:
                        for skill_category, skill_list in raw_job.skills.items():
                            for raw_skill in skill_list:

                                bucket_list = None
                                if raw_skill.required:
                                    bucket_list = raw_job.converted_job_entity.required
                                else:
                                    bucket_list = raw_job.converted_job_entity.preferred

                                bucket_list.extend( [x.key() for x in raw_skill.bucket_entities] )

                    # We put() the feed URL in the datastore as late as possible in case there
                    # were any problems with data in the feed
                    feed_url_object.put()
                    job_entities = []
                    for raw_job in all_jobs:
                        raw_job.converted_job_entity.feed = feed_url_object
                        job_entities.append( raw_job.converted_job_entity )

                    db.put( job_entities )

                except IOError, e:
                    submission_result = "Failed; Couldn't fetch URL"
        else:
            submission_result = "Failed; Bad URL"


        validation_only_option = bool(validate_only)


        # TODO - use sharded counter
        job_counter_entity = models.SimpleCounter.get_or_insert("job_count")
        job_counter_entity.count += len(joblist)
        job_counter_entity.put()

        template_file = '../templates/registration_result.html'
        self.response.out.write(template.render(
            os.path.join(os.path.dirname(__file__), template_file),
            {
                'current_user': users.get_current_user(),
                'submission_result': submission_result,
                'link_hostname': link_hostname,
                'job_count': len(all_jobs),
                'link_url': link_url
            }
        ))

# =============================================================================
class FriendlyFeedRepresentation:
    def __init__(self, job_feed_object):
#        self.link = "<a href=\"" + str(job_feed_object.link) + "\">" + str(job_feed_object.link) + "</a>"
        self.link = job_feed_object.link
        self.since = str( job_feed_object.since.date() )


MAX_ITEMS_PER_PAGE = 20
# =============================================================================
class SkillsListHandler(webapp.RequestHandler):

    def get(self):

        skills_list = []
        skill_category_name = self.request.get('skill_category')
        last_in_pagination = self.request.get('last')
        category_description = None
        category_fullname = None
        next_page = ""
        if skill_category_name in SKILL_CATEGORY_ENTITY_MAPPING:
            skill_entity_model = SKILL_CATEGORY_ENTITY_MAPPING[skill_category_name]

            q = skill_entity_model.all()
            if last_in_pagination:
                q.filter("lower >", last_in_pagination)
            q.order("lower")
            skills_list = q.fetch( MAX_ITEMS_PER_PAGE + 1 )

            if len(skills_list) > MAX_ITEMS_PER_PAGE:

                next_page = "<a href='" + self.request.path + "?" + "skill_category" + "=" + skill_category_name + "&last=" + skills_list[MAX_ITEMS_PER_PAGE].lower + "'>Next " + str(MAX_ITEMS_PER_PAGE) + " >></a>"

            category_fullname = SKILL_CATEGORY_SHORT_TO_FULL_NAME[skill_category_name]
            category_description = SKILL_CATEGORY_SUMMARIES_DICT[skill_category_name]

        template_file = '../templates/skillslist.html'
        self.response.out.write(template.render(
            os.path.join(os.path.dirname(__file__), template_file),
                {
                    'current_user': users.get_current_user(),
                    'category_description': category_description,
                    'category_fullname': category_fullname,
                    'skills_list': skills_list[:MAX_ITEMS_PER_PAGE],
                    'next_page': next_page
                }
            )
        )

# =============================================================================
class KeywordsListHandler(webapp.RequestHandler):

	def get(self):

		skills_list = []
		last_in_pagination = self.request.get('last')
		next_page = ""

		q = models.Sub.all()
		if last_in_pagination:
			q.filter("lower >", last_in_pagination)
		q.order("lower")
		skills_list = q.fetch( MAX_ITEMS_PER_PAGE + 1 )

		if len(skills_list) > MAX_ITEMS_PER_PAGE:
			next_page = "<a href='" + self.request.path + "?last=" + skills_list[MAX_ITEMS_PER_PAGE].lower + "'>Next " + str(MAX_ITEMS_PER_PAGE) + " >></a>"

		template_file = '../templates/keywordslist.html'
		self.response.out.write(template.render(
			os.path.join(os.path.dirname(__file__), template_file),
				{
					'current_user': users.get_current_user(),
					'skills_list': skills_list[:MAX_ITEMS_PER_PAGE],
					'next_page': next_page
				}
			)
		)

# =============================================================================
class MakeBookmarkHandler(webapp.RequestHandler):

	def get(self):
		message = "Did nothing."

		job_key_string = self.request.get('job_key')
		if job_key_string and users.get_current_user():
			job_key = db.Key(job_key_string)
			db.put(models.Bkmk(job=job_key))
			message = "Added bookmark"

		self.response.out.write(template.render(
			os.path.join(os.path.dirname(__file__), '../templates/redirect.html'),
			{
				'message': message,
			}))

# =============================================================================
class BookmarksListHandler(webapp.RequestHandler):

	def get(self):

		bookmark_list = []
		last_in_pagination = self.request.get('last')
		next_page = ""

		q = models.Bkmk.all()
		if last_in_pagination:
			q.filter("since >", last_in_pagination)
		q.order("since")
		q.filter("user =", users.get_current_user())
		bookmark_list = q.fetch( MAX_ITEMS_PER_PAGE + 1 )

		if len(bookmark_list) > MAX_ITEMS_PER_PAGE:
			next_page = "<a href='" + self.request.path + "?last=" + bookmark_list[MAX_ITEMS_PER_PAGE].since + "'>Next " + str(MAX_ITEMS_PER_PAGE) + " >></a>"

		template_file = '../templates/bookmarklist.html'
		self.response.out.write(template.render(
			os.path.join(os.path.dirname(__file__), template_file),
				{
					'current_user': users.get_current_user(),
					'bookmark_list': bookmark_list[:MAX_ITEMS_PER_PAGE],
					'next_page': next_page
				}
			)
		)

# =============================================================================
class OrganizationListHandler(webapp.RequestHandler):

	def get(self):

		organization_list = []
		last_in_pagination = self.request.get('last')
		next_page = ""

		q = models.Org.all()
		if last_in_pagination:
			q.filter("lower >", last_in_pagination)
		q.order("lower")
		organization_list = q.fetch( MAX_ITEMS_PER_PAGE + 1 )

		if len(organization_list) > MAX_ITEMS_PER_PAGE:
			next_page = "<a href='" + self.request.path + "?last=" + organization_list[MAX_ITEMS_PER_PAGE].lower + "'>Next " + str(MAX_ITEMS_PER_PAGE) + " >></a>"

		template_file = '../templates/organizationlist.html'
		self.response.out.write(template.render(
			os.path.join(os.path.dirname(__file__), template_file),
				{
					'current_user': users.get_current_user(),
					'organization_list': organization_list[:MAX_ITEMS_PER_PAGE],
					'next_page': next_page
				}
			)
		)



# =============================================================================
class OrgJobsListHandler(webapp.RequestHandler):

    def get(self):
        org_key = None
        org_key_string = self.request.get('org_key')
        if org_key_string:
            org_key = db.Key(org_key_string)
            logging.info("I was passed the org key!")
        if not org_key:
            job_key_string = self.request.get('job_key')
            if job_key_string:
#                org_key = db.Key(job_key_string).parent().parent().parent()    # Go up through department, site, organization.
                org_key = recoverOrgKey( db.Key(job_key_string) )


        org_entity = db.get(org_key)

        jobs_list = []
        last_in_pagination = self.request.get('last')
        next_page = ""

        q = models.Job.all()
        q.order("__key__")
        if last_in_pagination:
            q.filter("__key__ >", db.Key(last_in_pagination))
        q.ancestor(org_key)
        jobs_list = q.fetch( MAX_ITEMS_PER_PAGE + 1 ) # TODO - paginate results

        if len(jobs_list) > MAX_ITEMS_PER_PAGE:
            next_page = "<a href='" + self.request.path + "?org_key=" + str(org_key) + "&last=" + str(jobs_list[MAX_ITEMS_PER_PAGE].key()) + "'>Next " + str(MAX_ITEMS_PER_PAGE) + " &gt;&gt;</a>"

        template_file = '../templates/orgjobslist.html'
        self.response.out.write(template.render(
            os.path.join(os.path.dirname(__file__), template_file),
                {
                    'current_user': users.get_current_user(),
                    'jobs_list': jobs_list[:MAX_ITEMS_PER_PAGE],
					'org_domain': org_entity.domain,
					'org_name': org_entity.name,
                    'next_page': next_page
                }
            )
        )

# =============================================================================
class PostingExampleHandler(webapp.RequestHandler):

	def get(self):

		q = models.Job.all()
		q.filter("job_id =", int(self.request.get('id')))
		q.filter("sample =", True )

		template_file = '../templates/posting.html'
		self.response.out.write(template.render(
			os.path.join(os.path.dirname(__file__), template_file),
				{
					'job': q.get()
				}
			)
		)

# =============================================================================
class FeedList(webapp.RequestHandler):

    def get(self):

        q = models.Feed.all()
        q.order("since")
        feed_list = q.fetch(20) # TODO - paginate results


        transformed_feed_list = map(FriendlyFeedRepresentation, feed_list)

        template_file = '../templates/feedlist.html'
        if self.request.get('format') == "xml":
            template_file = '../templates/feedlist.xml'
            self.response.headers['Content-Type'] = "application/xml"


        self.response.out.write(template.render(
            os.path.join(os.path.dirname(__file__), template_file),
                {
                    'current_user': users.get_current_user(),
                    'feed_list': transformed_feed_list
                }
            )
        )

# =============================================================================
class SkillCategoryObject:
    def __init__(self, key, title):
        self.key = key
        self.title = title

# =============================================================================
class SkillsTestHandler(webapp.RequestHandler):

    def get(self):

        categories = [SkillCategoryObject(feedparser.SKILL_CATEGORIES[i], feedparser.SKILL_CATEGORY_NAMES[i]) for i in range(len(feedparser.SKILL_CATEGORY_NAMES))]

        template_file = '../templates/skillstest.html'
        self.response.out.write(template.render(
            os.path.join(os.path.dirname(__file__), template_file),
                {
                    'current_user': users.get_current_user(),
                    'categories': categories
                }
            )
        )

# =============================================================================
class SkillsList:
    def __init__(self, skills_list, category, label):
        self.skills_list = skills_list
        self.category = category
        self.label = label

# =============================================================================
class SaveProfileHandler(webapp.RequestHandler):

    def post(self):

        message = ""
        load_key = self.request.get('load_key')
        if load_key and self.request.get('deleting') == "true":

            # Verify that the user has permission to delete this entity.
            if db.get(load_key).user == users.get_current_user():
                db.delete(load_key);
                message = "Deleted."
        else:

            formval = self.request.get('skill_keys')
            joined_keyword_keys = self.request.get('keyword_keys')
            if formval or joined_keyword_keys:
                logging.info("skill keys: " + formval)
                saved_name = self.request.get('saved_name')
                logging.info("saved name: " + saved_name)

                # Check whether we are overwriting an existing name
                q = models.SavedSearch.all()
                q.filter("title =", saved_name)

                entity = q.get()
                if not entity:
                    entity = models.SavedSearch()

                keywords_keys_list = joined_keyword_keys.split(",")
                logging.info("keywords keys list: " + str(keywords_keys_list))


                from auxilliary import parseStringifiedExperienceDict
                experience_keys_list = parseStringifiedExperienceDict(formval)

                entity.title = saved_name
                entity.qualifications = experience_keys_list
                entity.kw = map(db.Key, filter(bool, keywords_keys_list))
                entity.put()

                message = "Saved."


        self.response.out.write(template.render(
		os.path.join(os.path.dirname(__file__), '../templates/redirect.html'),
		{
		    'message': message,
		}))

# =============================================================================
# XXX DEPRECATED
class SaveSearchHandler(webapp.RequestHandler):

    def post(self):

        formval = self.request.get('skill_keys')
        if formval:
            logging.info("skill keys: " + formval)
            saved_name = self.request.get('saved_name')
            logging.info("saved name: " + saved_name)

            stringified_skill_keys_list = formval.split(";")
            skill_keys_list = []
            for binned_skill_lump in stringified_skill_keys_list:

                parent_keystring, years = binned_skill_lump.split(":")
                appropriate_bin = getHighestBinWithAtMost(models.EXPERIENCE_YEARS_BUCKETS, int(years))

                k = recoverExperienceEntity(parent_keystring, appropriate_bin)
                skill_keys_list.append(k)

            entity = models.SavedSearch(title=saved_name, qualifications=skill_keys_list)
            entity.put()


        renderProfilePage(self)


# =============================================================================
def quoteString(val):
    return "\"" + str(val) + "\""

# =============================================================================
def getSkillsDictFromKeys(experience_keys):
    skills_years_dict = {}

    qualifications_entities = db.get(experience_keys)
    for entity in qualifications_entities:
        skills_years_dict[str(entity.key().parent())] = entity.years

    return skills_years_dict

# =============================================================================
def getSkillsDict(self):
    skills_years_dict = {}

    load_key = self.request.get('load_key')

    if load_key:
        if self.request.get('deleting') == "true":
            db.delete(load_key);
        else:
            qualifications_keys = models.SavedSearch.get(load_key).qualifications
            skills_years_dict = getSkillsDictFromKeys(qualifications_keys)

    return skills_years_dict

# =============================================================================
def getSkillsJson(self):

    from django.utils import simplejson
    return simplejson.dumps(getSkillsDict(self))

# =============================================================================
# XXX DEPRECATED
def renderProfilePage(self):

    loaded_skills = getSkillsJson(self)

    q = models.SavedSearch.all()
    q.filter("user =", users.get_current_user())
    q.order("-saved")
    saved_searches = q.fetch(50)

    skills_lists = []
    for i, category in enumerate(feedparser.SKILL_CATEGORIES):
        model = SKILL_CATEGORY_ENTITY_MAPPING[category]
        q = model.all()
        q.order("name")
        skills_lists.append( SkillsList( q.fetch(1000), category, feedparser.SKILL_CATEGORY_NAMES[i] ) )

    self.response.out.write(template.render(
        os.path.join(os.path.dirname(__file__), '../templates/profile.html'),
        {
            'current_user': users.get_current_user(),
            'skills_lists': skills_lists,
            'saved_searches': saved_searches,
            'loaded_skills': loaded_skills,
            'years_bins': models.EXPERIENCE_YEARS_BUCKETS
        }))

# =============================================================================
def buildAjaxExperienceDict(loaded_skills_dict):
    loaded_skills = {}
    loaded_skills["searchable_skill_keys"] = loaded_skills_dict


    named_skill_entities = db.get(loaded_skills_dict.keys())

    readable = {}
    for entity in named_skill_entities:
        categorized_skill_list = readable.setdefault(SKILL_CATEGORY_SHORT_TO_FULL_NAME[SKILL_CATEGORY_MODEL_NAME_MAPPING[entity.key().kind()]], [])
        categorized_skill_list.append( [entity.name, loaded_skills_dict[str(entity.key())], str(entity.key())] )

    loaded_skills["categorized_skills"] = readable


    return loaded_skills

# =============================================================================
def extractMinimumBuckets(qualifications_keys):
    mins = []
    extracted = {}
    for qual_key in qualifications_keys:
        lst = extracted.setdefault(qual_key.parent(), [])
        lst.append(qual_key)

    for value in extracted.values():
        mins.append( min(value, key=lambda x: int(x.name())) )

    return mins

# =============================================================================
JOB_DESCRIPTION_CHARACTER_LIMIT = 100
class JobDataHandler(webapp.RequestHandler):

    def get(self):

        # TODO
        job_posting_key = self.request.get('job_posting_key')
        if job_posting_key:

            # TODO: Also do "preferred"!!
            job_entity = models.Job.get(job_posting_key)
            qualifications_keys = job_entity.required

            # For display, we're only interested in minium required experience.
            qualifications_keys = extractMinimumBuckets(qualifications_keys)


            loaded_skills_dict = getSkillsDictFromKeys(qualifications_keys)

            loaded_skills = buildAjaxExperienceDict(loaded_skills_dict)


            keyword_entities = db.get(job_entity.kw)
            loaded_skills["keyword_list"] = [x.name for x in keyword_entities]

            optional_ellipsis = ""
            if len(job_entity.description) > JOB_DESCRIPTION_CHARACTER_LIMIT:
                optional_ellipsis = "&hellip;"

            loaded_skills["description"] = job_entity.description[:JOB_DESCRIPTION_CHARACTER_LIMIT] + optional_ellipsis

        from django.utils import simplejson
        self.response.out.write(simplejson.dumps(loaded_skills))


# =============================================================================
class ProfileDataHandler(webapp.RequestHandler):

    def get(self):

        loaded_skills_dict = {}

        load_key = self.request.get('load_key')

        if load_key:

            search_entity = models.SavedSearch.get(load_key)

            qualifications_keys = search_entity.qualifications
            loaded_skills_dict = getSkillsDictFromKeys(qualifications_keys)


            loaded_skills_dict = getSkillsDict(self)
            loaded_skills = buildAjaxExperienceDict(loaded_skills_dict)


            loaded_skills["experience_keys"] = map(str, qualifications_keys)


            keyword_entities = db.get(search_entity.kw)
            loaded_skills["keyword_list"] = [[x.name, str(x.key())] for x in keyword_entities]



            from django.utils import simplejson
            self.response.out.write(simplejson.dumps(loaded_skills))

# =============================================================================
class SearchProfileHandler(webapp.RequestHandler):

    def get(self):
        renderProfilePage(self)

# =============================================================================
class SkillsAutoCompleteHandler(webapp.RequestHandler):

    def get(self):

        prefix = self.request.get('query')
        query_string = prefix.lower()

        category = self.request.get('type')
        model = SKILL_CATEGORY_ENTITY_MAPPING[category]

        q = model.all()
        q.filter("lower >=", query_string)
        q.filter("lower <", query_string + u"\ufffd")

        for result in q.fetch(20):
            self.response.out.write(result.name + "\t" + str(result.key()) + "\n")

# =============================================================================
class KeywordAutoCompleteHandler(webapp.RequestHandler):

    def get(self):

        prefix = self.request.get('query')
        query_string = prefix.lower()

        q = models.Sub.all()
        q.filter("lower >=", query_string)
        q.filter("lower <", query_string + u"\ufffd")

        for result in q.fetch(20):
            self.response.out.write(result.name + "\t" + str(result.key()) + "\n")

# =============================================================================
class OrganizationAutoCompleteHandler(webapp.RequestHandler):

    def get(self):

        prefix = self.request.get('query')
        query_string = prefix.lower()

        q = models.Org.all()
        q.filter("lower >=", query_string)
        q.filter("lower <", query_string + u"\ufffd")

        for result in q.fetch(20):
            self.response.out.write(result.name + "\t" + str(result.key()) + "\n")

# =============================================================================
class RandomizedFeedHandler(webapp.RequestHandler):

    def get(self):

        from testfeed import generateFeed
        doc = generateFeed()

        self.response.headers['Content-Type'] = "application/xml"
        doc.writexml( self.response.out, addindent="\t", newl="\n" )

# =============================================================================
class MainHandler(webapp.RequestHandler):

    def get(self):

        q = models.SavedSearch.all()
        q.filter("user =", users.get_current_user())
        q.order("-saved")
        saved_searches = q.fetch(50)


        q = models.DegreeLevel.all()
        q.order("rank")
        degree_levels = q.fetch(10)

        q = models.SeniorityLevel.all()
        q.order("rank")
        seniority_levels = q.fetch(10)

        q = models.PermanenceLevel.all()
        q.order("rank")
        permanence_levels = q.fetch(10)

        class SkillType:
            pass

        skills_types = []
        for i, category in enumerate(feedparser.SKILL_CATEGORIES):
            t = SkillType()
            t.key = category
            t.label = feedparser.SKILL_CATEGORY_NAMES[i]
            skills_types.append(t)

        self.response.out.write(template.render(
            os.path.join(os.path.dirname(__file__), '../templates/index.html'),
            {
                'current_user': users.get_current_user(),
                'saved_searches': saved_searches,
            	'years_bins': models.EXPERIENCE_YEARS_BUCKETS,
                'skill_types': skills_types,
                'skill_type_summaries': feedparser.SKILL_CATEGORY_SUMMARIES,
                'degree_levels': degree_levels,
                'seniority_levels': seniority_levels,
                'permanence_levels': permanence_levels,
            }
        ))

# =============================================================================
def main():
    application = webapp.WSGIApplication([
            ('/', MainHandler),
            ('/speedtest', make_static_handler('../templates/speedtest.html')),
            ('/register', make_static_handler('../templates/registration.html')),
            ('/urlsubmission', FeedUrlSubmission),
            ('/feeds', FeedList),
            ('/organizations', OrganizationListHandler),	# TODO
            ('/skills', SkillsListHandler),
            ('/orgjobs', OrgJobsListHandler),
            ('/keywords', KeywordsListHandler),
            ('/skillstest', SkillsTestHandler),
            ('/profile', SearchProfileHandler),
            ('/profiledata', ProfileDataHandler),
            ('/jobdata', JobDataHandler),
            ('/save', SaveSearchHandler),
            ('/randomized_feed.xml', RandomizedFeedHandler),

            ('/save_profile', SaveProfileHandler),

            ('/jobs/posting', PostingExampleHandler),

            ('/bookmarks', BookmarksListHandler),
            ('/add_bookmark', MakeBookmarkHandler),

            ('/skills_autocomplete', SkillsAutoCompleteHandler),
            ('/keyword_autocomplete', KeywordAutoCompleteHandler),
            ('/organization_autocomplete', OrganizationAutoCompleteHandler),
        ],
        debug=('Development' in os.environ['SERVER_SOFTWARE']))
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
