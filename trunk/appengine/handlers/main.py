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

import logging
from datetime import datetime

import parse_jobs
import models



template.register_template_library(
    'django.contrib.humanize.templatetags.humanize')
template.register_template_library('templatelib')


def make_static_handler(template_file):
    """Creates a webapp.RequestHandler type that renders the given template
    to the response stream."""
    class StaticHandler(webapp.RequestHandler):
        def get(self):
            self.response.out.write(template.render(
                os.path.join(os.path.dirname(__file__), template_file),
                {'current_user': users.get_current_user()}))

    return StaticHandler

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
def langToKey(original):
    unsanitized_name = original.lower()
    disallowed_prefix_suffix = "__" # two underscores
    if unsanitized_name.endswith(disallowed_prefix_suffix) and disallowed_prefix_suffix.startswith(disallowed_prefix_suffix):
        return "x" + unsanitized_name
    return unsanitized_name


SKILL_CATEGORY_ENTITY_MAPPING = {
    parse_jobs.SKILL_CATEGORY_APIS: models.ApiSkill,
    parse_jobs.SKILL_CATEGORY_EQUIPMENT: models.EquipmentSkill,
    parse_jobs.SKILL_CATEGORY_ACTIVITIES: models.ActivitySkill,
    parse_jobs.SKILL_CATEGORY_APPLICATIONS: models.ApplicationSkill,
    parse_jobs.SKILL_CATEGORY_PROGRAMMING_LANGUAGES: models.ProgrammingLanguageSkill
}

SKILL_CATEGORY_MODEL_NAME_MAPPING = {}
for category, model in SKILL_CATEGORY_ENTITY_MAPPING.items():
    SKILL_CATEGORY_MODEL_NAME_MAPPING[model.__name__] = category

SKILL_CATEGORY_SHORT_TO_FULL_NAME = {}
for i, shortname in enumerate(parse_jobs.SKILL_CATEGORIES):
    SKILL_CATEGORY_SHORT_TO_FULL_NAME[shortname] = parse_jobs.SKILL_CATEGORY_NAMES[i]

# =============================================================================
class SkillConversionHelper:
    def __init__(self):
        pass


# =============================================================================
# skill_experience_entities is guaranteed to have at least one item
def getHighestBinWithAtMost(bins, years):
    
    last_bucket = bins[0]
    for bin in bins:
        if bin > years:
            return last_bucket
        last_bucket =bin
    return last_bucket

# =============================================================================
# skill_experience_entities is guaranteed to have at least one item
def getHighestBucketWithAtMost(skill_experience_entities, years):
    
    last_bucket = skill_experience_entities[0]
    for bucket in skill_experience_entities:
        if bucket.years > years:
            return last_bucket
        last_bucket = bucket
    return last_bucket

# =============================================================================
from google.appengine.ext import db
class UrlSubmission(webapp.RequestHandler):

    def convert_job(self, job):
        x = models.JobOpening(location=db.GeoPt(job.geo[0], job.geo[1]))
        x.update_location()

        x.contract = job.contract
        x.job_id = job.job_id
        x.title = job.title
        x.expiration = job.expiration
        x.expired = datetime.now().date() >= job.expiration
        return x


    def post(self):

        link_url = self.request.get('submission_url')
        contact_email = self.request.get('contact_email')
        crawl_interval_days = 7*max(1, int(self.request.get('crawl_interval_weeks')))

        validate_only = self.request.get('validate_only')   # XXX Not used

        from urlparse import urlsplit
        parsed_url = urlsplit(link_url)
        link_hostname = parsed_url.hostname


        submission_result = "OK!"


        joblist = []
        if link_hostname:

            q = models.JobFeedUrl.all()
            q.filter("link =", link_url)
            if q.get():
                submission_result = "Duplicate URL"
            else:
                try:
                    joblist = parse_jobs.fetchJobList(link_url)

                    feed_url_object = models.JobFeedUrl(link=db.Link(link_url))
                    feed_url_object.interval = crawl_interval_days
                    if contact_email:
                        feed_url_object.contact = db.Email(contact_email)
                    # We hold off on committing the feed url in case there are any problems    
                
                    


                    experience_bucketed_skills_entities = []
                    basic_skills_entities_by_category = {}
                    used_skill_names_by_category = {}
                    for raw_job in joblist:
                        
                        # Convert simple Job() objects into model entities
                        raw_job.converted_job_entity = self.convert_job(raw_job)
                        
                        
                        for skill_category, skill_list in raw_job.skills.items():
                            # Retrieve the skillname dict for this category. This dict is persistent across jobs.
                            skill_buckets_unique_by_name = used_skill_names_by_category.setdefault(skill_category, {})
                            
                            for raw_skill in skill_list:
                                normalized_skillname = langToKey(raw_skill.name)
                                skill_experience_entities = None
                                if normalized_skillname in skill_buckets_unique_by_name:
                                    skill_experience_entities = skill_buckets_unique_by_name[normalized_skillname]
                                else:
                                    # This is the first time this skill name was encountered. Create and assign the model entity instance.

                                    basic_skill_entity = SKILL_CATEGORY_ENTITY_MAPPING[skill_category](key_name=normalized_skillname, name=raw_skill.name)
                                    
                                    # queue to be "put()"
                                    basic_skills_entities_by_category.setdefault(skill_category, []).append( basic_skill_entity )
                                    
#                                    skill_experience_entities = [models.SkillExperience(skill=basic_skill_entity, years=years) for years in models.EXPERIENCE_YEARS_BUCKETS]
                                    skill_experience_entities = [models.SkillExperience(parent=basic_skill_entity, key_name=str(years), years=years) for years in models.EXPERIENCE_YEARS_BUCKETS]
                                    experience_bucketed_skills_entities.extend( skill_experience_entities )  # queue to be "put()"
                                    
                                    skill_buckets_unique_by_name[normalized_skillname] = skill_experience_entities
                                    
                                # Whether or not the current skill's name has already been encountered, we
                                # must link the cannonical bucket entity reference to the raw job's skill list.
                                raw_skill.bucket_entity = getHighestBucketWithAtMost(skill_experience_entities, raw_skill.years)
                                    
                    # put() each type into the datastore in separate groups
                    # Here it's okay if the entity already exists; it will just get overwritten by sharing the same key_name.
                    for skill_category_name, skill_entity_list in basic_skills_entities_by_category.items():
                        db.put( skill_entity_list )

                    # We can put() the buckets all in one batch, since they use a supertype shared by each skill category and are homogeneous
                    # Here, since we've also specified the key_name and parent, duplicates will also be overwritten.
                    db.put( experience_bucketed_skills_entities )

                    # The final thing to do before put()-ing the jobs into the datastore is adding the skill buckets to the correct list.
                    for raw_job in joblist:
                        for skill_category, skill_list in raw_job.skills.items():
                            for raw_skill in skill_list:
                                
                                bucket_list = None
                                if raw_skill.required:
                                    bucket_list = raw_job.converted_job_entity.required
                                else:
                                    bucket_list = raw_job.converted_job_entity.preferred
                                bucket_list.append( raw_skill.bucket_entity.key() )

                    # We put() the feed URL in the datastore as late as possible in case there
                    # were any problems with data in the feed
                    feed_url_object.put()
                    job_entities = []
                    for raw_job in joblist:
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
                'job_count': len(joblist),
                'link_url': link_url
            }
        ))

# =============================================================================
class FriendlyFeedRepresentation:
    def __init__(self, job_feed_object):
#        self.link = "<a href=\"" + str(job_feed_object.link) + "\">" + str(job_feed_object.link) + "</a>"
        self.link = job_feed_object.link
        self.since = str( job_feed_object.since.date() )

# =============================================================================
class SkillsListHandler(webapp.RequestHandler):

    def get(self):

        skills_list = []
        skill_category_name = self.request.get('skill_category')

        if skill_category_name in SKILL_CATEGORY_ENTITY_MAPPING:
            skill_entity_model = SKILL_CATEGORY_ENTITY_MAPPING[skill_category_name]
        
            q = skill_entity_model.all()
            q.order("name")
            skills_list = q.fetch(50) # TODO - paginate results

        template_file = '../templates/skillslist.html'
        self.response.out.write(template.render(
            os.path.join(os.path.dirname(__file__), template_file),
                {
                    'current_user': users.get_current_user(),
                    'skills_list': skills_list
                }
            )
        )

# =============================================================================
class FeedList(webapp.RequestHandler):

    def get(self):

        q = models.JobFeedUrl.all()
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

        categories = [SkillCategoryObject(parse_jobs.SKILL_CATEGORIES[i], parse_jobs.SKILL_CATEGORY_NAMES[i]) for i in range(len(parse_jobs.SKILL_CATEGORY_NAMES))]

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
class SaveSearchHandler(webapp.RequestHandler):
    
    def post(self):
        
        formval = self.request.get('skill_keys')
        if formval:
            logging.info("skill keys: " + formval)
            saved_name = self.request.get('saved_name')
            logging.info("saved name: " + saved_name)
#            skill_keys_list = formval.split(",")
#            logging.info("skill keys list: " + str(skill_keys_list))
#            skill_keys_list = map(db.Key, skill_keys_list)

            stringified_skill_keys_list = formval.split(";")
            skill_keys_list = []
            for binned_skill_lump in stringified_skill_keys_list:
                
                parent_keystring, years = binned_skill_lump.split(":")
                appropriate_bin = getHighestBinWithAtMost(models.EXPERIENCE_YEARS_BUCKETS, int(years))
                
                parent_key_object = db.Key(parent_keystring)
                k = db.Key.from_path(parent_key_object.kind(), parent_key_object.name(), 'SkillExperience', str(appropriate_bin))
                skill_keys_list.append(k)

            entity = models.SavedSearch(title=saved_name, qualifications=skill_keys_list)
            entity.put()


        renderProfilePage(self)

# =============================================================================
def quoteString(val):
    return "\"" + str(val) + "\""

# =============================================================================
def getSkillsDict(self):
    skills_years_dict = {}

    load_key = self.request.get('load_key')
    
    if load_key:
        if self.request.get('deleting') == "true":
            db.delete(load_key);
        else:
            qualifications_keys = models.SavedSearch.get(load_key).qualifications
            qualifications_entities = db.get(qualifications_keys)
            
            for entity in qualifications_entities:
                skills_years_dict[str(entity.key().parent())] = entity.years

    return skills_years_dict

# =============================================================================
def getSkillsJson(self):

    import json
    return json.dumps(getSkillsDict(self))
    
# =============================================================================
def renderProfilePage(self):

    loaded_skills = getSkillsJson(self)

    q = models.SavedSearch.all()
    q.filter("user =", users.get_current_user())
    q.order("-saved")
    saved_searches = q.fetch(50)
    
    skills_lists = []
    for i, category in enumerate(parse_jobs.SKILL_CATEGORIES):
        model = SKILL_CATEGORY_ENTITY_MAPPING[category]
        q = model.all()
        q.order("name")
        skills_lists.append( SkillsList( q.fetch(1000), category, parse_jobs.SKILL_CATEGORY_NAMES[i] ) )
    
    self.response.out.write(template.render(
        os.path.join(os.path.dirname(__file__), '../templates/searchprofile.html'),
        {
            'current_user': users.get_current_user(),
            'skills_lists': skills_lists,
            'saved_searches': saved_searches,
            'loaded_skills': loaded_skills,
            'years_bins': models.EXPERIENCE_YEARS_BUCKETS
        }))

# =============================================================================
class ProfileDataHandler(webapp.RequestHandler):
    
    def get(self):

        loaded_skills = {}
        
        loaded_skills_dict = getSkillsDict(self)
        loaded_skills["searchable_skill_keys"] = loaded_skills_dict
        
        
        named_skill_entities = db.get(loaded_skills_dict.keys())
        
        readable = {}
        for entity in named_skill_entities:
            categorized_skill_list = readable.setdefault(SKILL_CATEGORY_SHORT_TO_FULL_NAME[SKILL_CATEGORY_MODEL_NAME_MAPPING[entity.key().kind()]], [])
            categorized_skill_list.append( [entity.name, loaded_skills_dict[str(entity.key())]] )
        
        loaded_skills["readable_skills"] = readable
        
        import json
        self.response.out.write(json.dumps(loaded_skills))
        
# =============================================================================
class SearchProfileHandler(webapp.RequestHandler):
    
    def get(self):
        renderProfilePage(self)

# =============================================================================
class MainHandler(webapp.RequestHandler):
    
    def get(self):
        
        q = models.SavedSearch.all()
        q.filter("user =", users.get_current_user())
        q.order("-saved")
        saved_searches = q.fetch(50)
        
        self.response.out.write(template.render(
            os.path.join(os.path.dirname(__file__), '../templates/index.html'),
            {
                'current_user': users.get_current_user(),
                'saved_searches': saved_searches
            }
        ))

# =============================================================================
def main():
    application = webapp.WSGIApplication([
            ('/', MainHandler),
            ('/speedtest', make_static_handler('../templates/speedtest.html')),
            ('/register', make_static_handler('../templates/registration.html')),
            ('/urlsubmission', UrlSubmission),
            ('/feeds', FeedList),
            ('/skillslist', SkillsListHandler),
            ('/skillstest', SkillsTestHandler),
            ('/profile', SearchProfileHandler),
            ('/profiledata', ProfileDataHandler),
            ('/save', SaveSearchHandler),
        ],
        debug=('Development' in os.environ['SERVER_SOFTWARE']))
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
