#!/usr/bin/python

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

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

from datetime import datetime

GEO_ATTRIBUTES = ["lat", "lng"]

SKILL_REQUIRED = "required"
SKILL_PREFERRED = "preferred"
SKILL_PREFERENCE_TYPES = [SKILL_REQUIRED, SKILL_PREFERRED]

SKILL_CATEGORY_APIS = "api"
SKILL_CATEGORY_EQUIPMENT = "equip"
SKILL_CATEGORY_ACTIVITIES = "activity"
SKILL_CATEGORY_APPLICATIONS = "app"
SKILL_CATEGORY_PROGRAMMING_LANGUAGES = "lang"

SKILL_CATEGORIES = [
    SKILL_CATEGORY_APIS,
    SKILL_CATEGORY_EQUIPMENT,
    SKILL_CATEGORY_ACTIVITIES,
    SKILL_CATEGORY_APPLICATIONS,
    SKILL_CATEGORY_PROGRAMMING_LANGUAGES
]

SKILL_CATEGORY_NAMES = [
    "API",
    "Equipment",
    "Activity",
    "Software application",
    "Programming language"
]

# =============================================================================
class SkillExperience():
    def __init__(self, name, years, required):
        self.name = name
        self.years = years
        if not (years is None):
            self.years = float(years)
        self.required = required

    def __str__(self):
        return str(tuple([self.name, self.years, self.required]))

    def __repr__(self):
        return "SkillExperience" + str(self)

# =============================================================================
class Job():
    def __init__(self, handler):
        self.job_id = handler.jobid
        self.geo = handler.geo
        self.title = handler.job_title
	if hasattr(handler, "degree_level"):
	        self.degree_level = handler.degree_level
        	if hasattr(handler, "degree_area"):
			self.degree_area = handler.degree_area

        self.expiration = datetime.strptime(handler.expiration, "%Y-%m-%d").date()
        self.contract = bool(handler.contract)
        self.sample = handler.sample

        self.skills = handler.skills

# =============================================================================
class DuplicateIdException(Exception):
    pass

# =============================================================================
class JobFeedHandler(ContentHandler):

    def __init__ (self):
	self.geo_lookups = 0
        self.job_ids = []   # For error checking only
        self.joblist = []
        self.sample = False # A feed-wide property
	self.site_address = ""
	self.in_address = False
        self.resetJob()

    def resetJob(self):
        self.in_position = False
        self.in_title = False
        self.job_title = ""
        self.skills = {}
        self.skill_preference_type = None
        self.contract = False

    def addJob(self):
        if not hasattr(self, "geo"):
            if self.site_address:
                from geocode import getGeo
                geocoding = getGeo(self.site_address)
                self.geo = [geocoding[key] for key in GEO_ATTRIBUTES]
                self.geo_lookups += 1

        self.joblist.append(Job(self))
        self.resetJob()

    def startElement(self, name, attrs):

        if name == 'position':
            self.in_position = True
            self.jobid = int(attrs.get('id'))
            if self.jobid in self.job_ids:
                raise DuplicateIdException("Job id " + str(self.jobid) + " was already used")
            else:
                self.job_ids.append(self.jobid)
            
            self.contract = attrs.get('contract')
            self.expiration = attrs.get('expires')

        elif name in SKILL_PREFERENCE_TYPES:
            self.skill_preference_type = name

        elif name in SKILL_CATEGORIES:
            sublist = self.skills.setdefault(name, [])
            sublist.append(
                SkillExperience(
                    attrs.get('name'),
                    attrs.get('years', None),
                    self.skill_preference_type == SKILL_REQUIRED
                )
            )
            
        elif name == 'geo':
            self.geo = [float(attrs.get(a)) for a in GEO_ATTRIBUTES]

        elif name == 'address':
            self.in_address = True

        elif name == 'degree':
            self.degree_area = attrs.get('area')
            self.degree_level = attrs.get('level')

        elif name == 'title':
            self.in_title = True
            self.job_title = ""
            
        elif name == 'jobfeed':
            self.sample = attrs.get('sample') == "true"
            self.vocab_version  = attrs.get('vocab')
            # TODO: Do something based on the vocabulary version


    def endElement(self, name):
        if name == 'position':
            self.addJob()

        elif name == 'title':
            self.in_title = False

        elif name == 'address':
            self.in_address = False


    def characters (self, ch):
        if self.in_title:
            self.job_title += ch

        if self.in_address:
            self.site_address += ch

# =============================================================================
def fetchJobList( filehandle ):
    parser = make_parser()
    curHandler = JobFeedHandler()
    parser.setContentHandler(curHandler)


    parser.parse( filehandle )

    print "Length before filtering:", len(curHandler.joblist)
    return curHandler.joblist

# =============================================================================
def dumpJobs(jobs):

    print len(jobs), "jobs."
    for job in jobs:

        print "\t", job.title
        print "\t\t", "Contract employment?", job.contract
        print "\t\t", job.expiration
        print "\t\t", job.job_id
        print "\t\t", job.geo

        if hasattr(job, "degree_level") and hasattr(job, "degree_area"):
            print "\t\t", job.degree_level, "in", job.degree_area
        print "\t\t", "Skills:", job.skills

# =============================================================================
if __name__ == '__main__':

	import sys
	base_url = 'http://localhost:8080/static/example_joblist.xml'
	if len(sys.argv) > 1:
		base_url = sys.argv[1]

	from urllib import urlopen
	jobs = fetchJobList( urlopen(base_url) )
	dumpJobs(jobs)
