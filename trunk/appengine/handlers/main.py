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

from google.appengine.ext import db
from models import JobOpening, JobFeedUrl, ToolExperienceBucket, ProgrammingLanguageTool
class UrlSubmission(webapp.RequestHandler):

  def convert_joblist(self, joblist, feed_url_object):
	
    # Convert simple Job() objects into the database entities
    converted_jobs = []
    unique_languages = {}
    for job in joblist:
		x = JobOpening(location=db.GeoPt(job.geo[0], job.geo[1]), feed=feed_url_object)
		x.update_location()
		
		x.job_id = job.job_id
		x.title = job.title
		x.expiration = job.expiration
		x.expired = datetime.now().date() >= job.expiration

		required_programming_languages = job.skills[parse_jobs.SKILL_REQUIRED][parse_jobs.SKILL_CATEGORY_PROGRAMMING_LANGUAGES]
		
		# For each unique programming language, create a list of JobOpening entities that reference it.
		for lang_experience in required_programming_languages:
			lang_joblist = unique_languages.setdefault(lang_experience.name, [])
			lang_joblist.append(x)
		
		converted_jobs.append( x )

    return converted_jobs, unique_languages


  def get(self):

	link_url = self.request.get('submission_url')
	contact_email = self.request.get('contact_email')
	
	validate_only = self.request.get('validate_only')
	
	from urlparse import urlsplit
	parsed_url = urlsplit(link_url)
	link_hostname = parsed_url.hostname
	
	
	submission_result = "OK!"
	
	
	joblist = []
	if link_hostname:
		
		q = JobFeedUrl.all()
		q.filter("link =", link_url)
		if q.get():
			submission_result = "Duplicate URL"
			
		else:

			try:
				joblist = parse_jobs.fetchJobList(link_url)
				
				feed_url_object = JobFeedUrl(link=db.Link(link_url))
				if contact_email:
				    feed_url_object.contact = db.Email(contact_email)
				feed_url_object.put()
				
				converted_jobs, unique_languages = self.convert_joblist(joblist, feed_url_object)
				
				prog_lang_entities = []
				for unique_language, jobs in unique_languages.items():
					lang_entity = ProgrammingLanguageTool(name=unique_language, canonical=unique_language.lower())
					prog_lang_entities.append(lang_entity)
				
				prog_lang_entity_keys = db.put( prog_lang_entities )
				
				# After we obtain keys for each of the new programming language entities,
				# we need to assign those language entities to the jobs.
				
				
				job_entity_keys = db.put( converted_jobs )
				
			except IOError, e:
				submission_result = "Failed; Couldn't fetch URL"
	else:
	    submission_result = "Failed; Bad URL"
	
	
	
#    import validate
#    error = validate.doValidation(link_url)
	
	validation_only_option = bool(validate_only)
#    if error:
#        submission_result = str(error)
	
	template_file = '../templates/submission_result.html'
	self.response.out.write(template.render(
	    os.path.join(os.path.dirname(__file__), template_file),
	    {
			  'current_user': users.get_current_user(),
			  'submission_result': submission_result,
#			  'validation_only_option': validation_only_option,
			  'link_hostname': link_hostname,
			  'job_count': len(joblist),
			  'link_url': link_url
		}
	))


# =============================================================================
class FriendlyFeedRepresentation:
	def __init__(self, job_feed_object):
		self.link = "<a href=\"" + str(job_feed_object.link) + "\">" + str(job_feed_object.link) + "</a>"
		self.since = str( job_feed_object.since.date() )
		
# =============================================================================
class FeedList(webapp.RequestHandler):

	def get(self):

		q = JobFeedUrl.all()
#		q.filter("sleeping =", True)
		q.order("since")
		feed_list = q.fetch(20)	# TODO - paginate results

		template_file = '../templates/feedlist.html'
		self.response.out.write(template.render(
			os.path.join(os.path.dirname(__file__), template_file),
				{
					'current_user': users.get_current_user(),
					'feed_list': map(FriendlyFeedRepresentation, feed_list)
				}
			)
		)

# =============================================================================

def main():
  application = webapp.WSGIApplication([
	      ('/', make_static_handler('../templates/index.html')),
	      ('/speedtest', make_static_handler('../templates/speedtest.html')),
	      ('/register', make_static_handler('../templates/registration.html')),
	      ('/urlsubmission', UrlSubmission),
	      ('/feedlist', FeedList)
      ],
      debug=('Development' in os.environ['SERVER_SOFTWARE']))
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
