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


import models

# =============================================================================

template.register_template_library(
    'django.contrib.humanize.templatetags.humanize')
template.register_template_library('templatelib')

# =============================================================================
class MainHandler(webapp.RequestHandler):

  
  def GetSchemaKinds(self):
    """Returns the list of kinds for this app."""

    from google.appengine.ext.db import stats

    class KindStatError(Exception):
      """Unable to find kind stats for an all-kinds download."""


    global_stat = stats.GlobalStat.all().get()
    if not global_stat:
      raise KindStatError()
    timestamp = global_stat.timestamp
    kind_stat = stats.KindStat.all().filter("timestamp =", timestamp).fetch(1000)
#    kind_stat = stats.KindStat.all().fetch(1000)	# Experimental
    kind_list = [stat.kind_name for stat in kind_stat
                 if stat.kind_name and not stat.kind_name.startswith('__')]
    kind_set = set(kind_list)
    return list(kind_set)



  def get(self):

		import models
#		all_kinds = self.GetSchemaKinds()
		all_kinds = [kind_class.kind() for kind_class in models.MODEL_LIST]

		present_kinds = []
		'''
		for kind_name in all_kinds:
			if hasattr(models, kind_name):
				kind_class = getattr(models, kind_name)
				first_entity = kind_class.all(keys_only=True).get()
				if first_entity:
					present_kinds.append(kind_name)
		'''
		
		for kind_class in models.MODEL_LIST:
			first_entity = kind_class.all(keys_only=True).get()
			if first_entity:
				present_kinds.append(kind_name)

		self.response.out.write(template.render(
            os.path.join(os.path.dirname(__file__), '../templates/maintenance.html'),
            {
                'greeting': "Hiyo!",
				'kinds': all_kinds,
				'present_kinds': present_kinds
            }
        ))
		
# =============================================================================
class MassDeletionHandler(webapp.RequestHandler):
    
    def post(self):

        kind_string = self.request.get('kind')

        import bulkupdate, models

        result = None
        if hasattr(models, kind_string):
            kind_class = getattr(models, kind_string)
            job = bulkupdate.BulkDelete(kind_class.all(keys_only=True))
            job.start()
            result = "Deleting all <b>" + kind_string + "</b> entities..."
        else:
            result = "Module does not have the class \"" + kind_string + "\""

        self.response.out.write(template.render(
            os.path.join(os.path.dirname(__file__), '../templates/maintenance_result.html'),
            {

                'result': result,
            }
        ))

# =============================================================================
def main():
    application = webapp.WSGIApplication([
            ('/_ah/maintenance/', MainHandler),
            ('/_ah/maintenance/delete', MassDeletionHandler),
        ],
        debug=('Development' in os.environ['SERVER_SOFTWARE']))
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
