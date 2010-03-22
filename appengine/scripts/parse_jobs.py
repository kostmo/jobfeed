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

SKILL_CATEGORY_APIS = 			"api"
SKILL_CATEGORY_EQUIPMENT =		"equip"
SKILL_CATEGORY_ACTIVITIES =		"activity"
SKILL_CATEGORY_APPLICATIONS =		"app"
SKILL_CATEGORY_PROGRAMMING_LANGUAGES =	"lang"

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
        self.link = handler.link
        self.title = handler.job_title.strip()
	if hasattr(handler, "degree_level"):
	        self.degree_level = handler.degree_level
        	if hasattr(handler, "degree_area"):
			self.degree_area = handler.degree_area

        self.expiration = datetime.strptime(handler.expiration, "%Y-%m-%d").date()
        self.contract = bool(handler.contract)
        self.sample = handler.sample

        self.skills = handler.skills
        self.keywords = handler.keywords

# =============================================================================
class DuplicateIdException(Exception):
    pass

# =============================================================================
# We give the submitter 20 geocoding freebies. Too many and we risk exceeding
# the 30 second HTTP request/response timeout.
GEOCODING_LIMIT = 20
class ExcessiveGeocodingException(Exception):
    pass

# =============================================================================
class MissingLocationException(Exception):
    pass

# =============================================================================
class JobFeedHandler(ContentHandler):

    def __init__ (self):
	self.geo_lookups = 0
	self.geo = None
        self.job_ids = []   # For error checking only
        self.joblist = []
        self.sample = False # A feed-wide property
	self.site_address = ""
	self.in_address = False
        self.resetJob()

    # -------------------------------------------------------------------------
    def resetJob(self):
        self.in_position = False
        self.in_title = False
        self.job_title = ""
        self.last_keyword = ""
        self.skills = {}
	self.in_keyword = False
	self.keywords = []
        self.skill_preference_type = None
        self.contract = False
        self.link = None

    # -------------------------------------------------------------------------
    def addJob(self):
        if not (hasattr(self, "geo") and self.geo):
            if self.site_address:

                if self.geo_lookups >= GEOCODING_LIMIT:
                    raise ExcessiveGeocodingException("Too many geo lookups required. Please geocode your addresses before submitting feed.")
                from geocode import getGeo
                geocoding = getGeo(self.site_address)
                self.geo = [geocoding[key] for key in GEO_ATTRIBUTES]
                self.geo_lookups += 1

#		print "Forced geo lookups:", self.geo_lookups

            else:
                raise MissingLocationException("Location must be specified preceeding job " + str(self.job_id))

        self.joblist.append(Job(self))
        self.resetJob()

    # -------------------------------------------------------------------------
    def startElement(self, name, attrs):

        if name == 'position':
            self.in_position = True
            self.jobid = int(attrs.get('id'))
            self.link = attrs.get('link')
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

        elif name == 'keyword':
            self.last_keyword = ""
            self.in_keyword = True
	
        elif name == 'jobfeed':
            self.sample = attrs.get('sample') == "true"
            self.vocab_version  = attrs.get('vocabulary')
            # TODO: Do something based on the vocabulary version

    # -------------------------------------------------------------------------
    def endElement(self, name):
        if name == 'position':
            self.addJob()

        elif name == 'title':
            self.in_title = False

        elif name == 'keyword':
            self.in_keyword = False
            self.keywords.append( self.last_keyword.strip() )

        elif name == 'address':
            self.in_address = False

	# The location is valid only within the context of a <site>;
	# We clear the location when the closing </site> tag is encountered.
        elif name == 'site':
            self.geo = None
            self.site_address = ""

    # -------------------------------------------------------------------------
    def characters (self, ch):
        if self.in_title:
            self.job_title += ch

        elif self.in_address:
            self.site_address += ch

        elif self.in_keyword:
            self.last_keyword += ch

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

    for job in jobs:

        print "\t", job.title
        print "\t\t", "Contract employment?", job.contract
        print "\t\t", job.expiration
        print "\t\t", job.job_id
        print "\t\t", job.geo
        if hasattr(job, "degree_level") and hasattr(job, "degree_area"):
            print "\t\t", job.degree_level, "in", job.degree_area
	print "\t\t", "Keywords:", job.keywords
        print "\t\t", "Skills:", job.skills

# =============================================================================
if __name__ == '__main__':

	import sys
	base_url = 'http://localhost:8080/static/example_joblist.xml'
	if len(sys.argv) > 1:
		base_url = sys.argv[1]

	from urllib import urlopen
	jobs = fetchJobList( urlopen(base_url) )
	print len(jobs), "jobs."
	dumpJobs(jobs)

