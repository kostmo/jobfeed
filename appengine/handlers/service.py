#!/usr/bin/python2.5
#
# Copyright 2009 Roman Nurik
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

"""Service /s/* request handlers."""

__author__ = 'api.roman.public@gmail.com (Roman Nurik)'

import os
import sys
import wsgiref.handlers

from django.utils import simplejson

from google.appengine.ext import db
from google.appengine.ext import webapp

from geo import geotypes

import models
import logging


def _merge_dicts(*args):
    """Merges dictionaries right to left. Has side effects for each argument."""
    return reduce(lambda d, s: d.update(s) or d, args)


class SearchService(webapp.RequestHandler):
    """Handler for job search requests."""
    def get(self):
        def _simple_error(message, code=400):
            self.error(code)
            self.response.out.write(simplejson.dumps({
              'status': 'error',
              'error': { 'message': message },
              'results': []
            }))
            return None


        self.response.headers['Content-Type'] = 'application/json'
        query_type = self.request.get('type')

        if not query_type in ['proximity', 'bounds']:
            return _simple_error('type parameter must be '
                                 'one of "proximity", "bounds".',
                                 code=400)

        if query_type == 'proximity':
            try:
                center = geotypes.Point(float(self.request.get('lat')),
                                        float(self.request.get('lon')))
            except ValueError:
                return _simple_error('lat and lon parameters must be valid latitude '
                                     'and longitude values.')
        elif query_type == 'bounds':
            try:
                bounds = geotypes.Box(float(self.request.get('north')),
                                      float(self.request.get('east')),
                                      float(self.request.get('south')),
                                      float(self.request.get('west')))
            except ValueError:
                return _simple_error('north, south, east, and west parameters must be '
                                     'valid latitude/longitude values.')

        max_results = 100
        if self.request.get('maxresults'):
            max_results = int(self.request.get('maxresults'))

        max_distance = 80000 # 80 km ~ 50 mi
        if self.request.get('maxdistance'):
            max_distance = float(self.request.get('maxdistance'))


        experience_keylist = []
        if self.request.get('experience_keylist'):
            experience_keylist = self.request.get('experience_keylist').split(",")
            logging.info("experience_keylist: " + str(experience_keylist))

        try:
            # Can't provide an ordering here in case inequality filters are used.

            base_query = models.Job.all()
            
            # We might only be interested in the "sample" jobs.
            base_query.filter('sample =', self.request.get('sample_search') == "true")

            # Main criteria
            if experience_keylist:
                base_query.filter('required IN', map(db.Key, experience_keylist))
            

            # Perform proximity or bounds fetch.
            if query_type == 'proximity':
                results = models.Job.proximity_fetch(
                    base_query,
                    center, max_results=max_results, max_distance=max_distance)
            elif query_type == 'bounds':
                results = models.Job.bounding_box_fetch(
                    base_query,
                    bounds, max_results=max_results)

            public_attrs = models.Job.public_attributes()

            import json
            from datetime import datetime, time
            results_obj = [
                _merge_dicts({
                  'lat': result.location.lat,
                  'lng': result.location.lon,
                    # Although json usually automatically converts the "datetime" object
                    # to the correct JavaScript representation, it must not recognize
                    # App Engine's DateTimeProperty() as a wrapped instance of "datetime",
                    # so we must convert it manually.
                  'job_key': str(result.key()),
                  'expiration': datetime.combine(result.expiration, time()).ctime()
                  },
                  dict([(attr, getattr(result, attr))
                        for attr in public_attrs]))
                for result in results]

            self.response.out.write(json.dumps({
              'status': 'success',
              'results': results_obj
            }))
        except:
            return _simple_error(str(sys.exc_info()[1]), code=500)


def main():
    application = webapp.WSGIApplication([
        ('/s/search', SearchService),
        ],
        debug=('Development' in os.environ['SERVER_SOFTWARE']))
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
