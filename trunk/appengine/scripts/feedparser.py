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
SKILL_CATEGORY_DUTIES =			"duty"
SKILL_CATEGORY_APPLICATIONS =		"app"
SKILL_CATEGORY_PROGRAMMING_LANGUAGES =	"lang"

SKILL_CATEGORIES = [
    SKILL_CATEGORY_APIS,
    SKILL_CATEGORY_EQUIPMENT,
    SKILL_CATEGORY_DUTIES,
    SKILL_CATEGORY_APPLICATIONS,
    SKILL_CATEGORY_PROGRAMMING_LANGUAGES
]

SKILL_CATEGORY_NAMES = [
    "API",
    "Equipment",
    "Duty",
    "Application",
    "Language"
]

SKILL_CATEGORY_SUMMARIES = [
	"library, API, or environment",
	"physical tool or equipment",
	"process, task, duty, responsibility or other common activity",
	"software application",
	"programming language"
]


DEGREE_LEVEL_ASSOCIATES = "Associates"
DEGREE_LEVEL_BACHELORS = "Bachelors"
DEGREE_LEVEL_MASTERS = "Masters"
DEGREE_LEVEL_DOCTORATE = "Doctorate"

# TODO Use this somehow
DEGREE_LEVEL_SYNONYMS = {
	DEGREE_LEVEL_ASSOCIATES: ["AAS", "AES"],
	DEGREE_LEVEL_BACHELORS: ["BS"],
	DEGREE_LEVEL_MASTERS: ["MS"],
	DEGREE_LEVEL_DOCTORATE: ["PhD"]
}

degreee_levels = [DEGREE_LEVEL_ASSOCIATES, DEGREE_LEVEL_BACHELORS, DEGREE_LEVEL_MASTERS, DEGREE_LEVEL_DOCTORATE]
degree_level_years = [2, 4, 5, 7]

DEGREE_LEVEL_YEARS_DICT = {}
for i, level_name in enumerate(degreee_levels):
	DEGREE_LEVEL_YEARS_DICT[level_name.lower()] = degree_level_years[i]

# =============================================================================
class SkillExperience:
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

def isValidHostname(hostname):
    # Process each DNS label individually by excluding invalid characters and ensuring proper length
    if len(hostname) > 255:
        return False
    hostname = hostname.rstrip(".")
    import re
    disallowed = re.compile("[^A-Z\d-]", re.IGNORECASE)
    parts = [(label and len(label) <= 63 and
        not label.startswith("-") and not label.endswith("-") and
        not disallowed.search(label)) for label in hostname.split(".")]
#   print parts
    return all(parts)

# =============================================================================
class Department:
    def __init__(self, name):
        self.name = name

# =============================================================================
class JobSite:
    def __init__(self, name):
        self.name = name
        self.geo = None
        self.address = None

# =============================================================================
class Organization:
    def __init__(self, name, domain, ein=None):
        self.name = name
        if not isValidHostname(domain):
            raise ValueError("Invalid hostname: " + domain)
        self.domain = domain
        self.ein = ein

# =============================================================================
class ParsedJob:
    def __init__(self, handler):
        self.job_id = handler.jobid
        self.geo = handler.geo
        self.link = handler.link
        self.title = handler.job_title.strip()
        self.description = handler.job_description.strip()

        self.degree_level = None
        self.degree_area = None
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
    # The data structure returned is a dictionary representing jobs in an
    # organizational tree.
    # The layers are:
    # Organization
    #    -> Site
    #        -> Department	# TODO
    #            -> Job

    def __init__ (self):
		self.geo_lookups = 0
		self.geo = None
		
		self.sample = False # A feed-wide property
		self.site_address = ""
		self.in_address = False
		self.resetJob()
		
		self.org_hierarchy = {}

    # -------------------------------------------------------------------------
    def resetJob(self):
        self.in_position = False
        self.in_title = False
        self.in_description = False
        self.job_title = ""
        self.job_description = ""
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
                self.current_site.geo = self.geo
                self.geo_lookups += 1

#		print "Forced geo lookups:", self.geo_lookups

            else:
                raise MissingLocationException("Location must be specified preceeding job " + str(self.job_id))

        self.org_hierarchy[self.current_organization][self.current_site][self.current_department].append( ParsedJob(self) )
#        self.joblist.append(ParsedJob(self))
        self.resetJob()

    # -------------------------------------------------------------------------
    def startElement(self, name, attrs):
        # These checks are ordered by descending frequency of occurrence within a feed.

        if name in SKILL_CATEGORIES:
            sublist = self.skills.setdefault(name, [])
            sublist.append(
                SkillExperience(
                    attrs.get('name'),
                    attrs.get('years', None),
                    self.skill_preference_type == SKILL_REQUIRED
                )
            )

        elif name == 'keyword':
            self.last_keyword = ""
            self.in_keyword = True

        elif name in SKILL_PREFERENCE_TYPES:
            self.skill_preference_type = name

        elif name == 'position':
            self.in_position = True
            self.jobid = int(attrs.get('id'))
            self.link = attrs.get('link')
            if self.jobid in self.org_job_ids:
                raise DuplicateIdException("Job id " + str(self.jobid) + " was already used in " + self.current_organization.name)
            else:
                self.org_job_ids.append(self.jobid)
            
            self.contract = attrs.get('contract')
            self.expiration = attrs.get('expires')

        elif name == 'geo':
            self.geo = [float(attrs.get(a)) for a in GEO_ATTRIBUTES]
            self.current_site.geo = self.geo

        elif name == 'address':
            self.in_address = True

        elif name == 'degree':
            self.degree_area = attrs.get('area')
            self.degree_level = attrs.get('level')

        elif name == 'title':
            self.in_title = True
            self.job_title = ""

        elif name == 'description':
            self.in_description = True
            self.job_description = ""

        elif name == 'department':
            self.current_department = Department(attrs.get('name'))
            # Initialize a list of jobs for this department.
            self.org_hierarchy[self.current_organization][self.current_site][self.current_department] = []

        elif name == 'site':
            self.current_site = JobSite(attrs.get('name'))
            # Initialize a dictionary of departments for this site.
            # Each department will conatain a list of jobs.
            self.org_hierarchy[self.current_organization][self.current_site] = {}

        elif name == 'organization':
            self.org_job_ids = []   # For error checking only
            self.current_organization = Organization(attrs.get('name'), attrs.get('domain'))
            ein = attrs.get('ein', None)
            if not (ein is None):
                self.current_organization.ein = int(ein)

            # Initialize a dictionary of physical sites for this organization.
            # Each site, in turn, will contain departments and jobs.
            self.org_hierarchy[self.current_organization] = {}

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

        elif name == 'description':
            self.in_description = False

        elif name == 'keyword':
            self.in_keyword = False
            self.keywords.append( self.last_keyword.strip() )

        elif name == 'address':
            self.in_address = False
            self.current_site.address = self.site_address

        # The location is valid only within the context of a <site>;
        # We clear the location when the closing </site> tag is encountered.
        elif name == 'site':

            if not self.current_site.geo:
                raise MissingLocationException("site was missing geo")

            self.geo = None
            self.site_address = ""

    # -------------------------------------------------------------------------
    def characters (self, ch):
        if self.in_title:
            self.job_title += ch

        elif self.in_description:
            self.job_description += ch

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

#    print "Length before filtering:", len(curHandler.joblist)
    return curHandler.org_hierarchy

# =============================================================================
def flattenJobs(org_hierarchy):
	jobs = []
	for organization, sites_dict in org_hierarchy.items():
		for site, departments_dict in sites_dict.items():
			for department, joblist in departments_dict.items():
				jobs.extend( joblist )
				
	return jobs

# =============================================================================
def dumpJobs(jobs_dict):

    jobs = flattenJobs(jobs_dict)
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
		
	return jobs

# =============================================================================
if __name__ == '__main__':

	import sys
	base_url = 'http://localhost:8080/static/example_joblist.xml'
	if len(sys.argv) > 1:
		base_url = sys.argv[1]

	from urllib import urlopen
	jobs = fetchJobList( urlopen(base_url) )
	print jobs
#	print len(jobs), "jobs."
#	dumpJobs(jobs)

