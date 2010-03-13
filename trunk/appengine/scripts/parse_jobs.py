#!/usr/bin/python

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

from datetime import datetime

GEO_ATTRIBUTES = ["lat", "lon"]

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
        self.job_id = int(handler.jobid)
        self.geo = handler.geo
        self.title = handler.job_title
        self.degree_level = handler.degree_level
        self.degree_area = handler.degree_area
        self.expiration = datetime.strptime(handler.expiration, "%Y-%m-%d").date()
        self.contract = bool(handler.contract)

        self.skills = handler.skills

# =============================================================================
class JobFeedHandler(ContentHandler):

    def __init__ (self):
        self.joblist = []
        self.resetJob()

    def resetJob(self):
        self.in_position = False
        self.in_title = False
        self.job_title = ""
        self.skills = {}
        self.skill_preference_type = None
        self.contract = False

    def startElement(self, name, attrs):

        if name == 'position':
            self.in_position = True
            self.jobid = attrs.get('id')
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

        elif name == 'degree':
            self.degree_level = attrs.get('level')
            self.degree_area = attrs.get('area')

        elif name == 'title':
            self.in_title = True
            self.job_title = ""


    def endElement(self, name):
        if name == 'position':
            self.joblist.append(Job(self))
            self.resetJob()

        elif name == 'title':
            self.in_title = False


    def characters (self, ch):
        if self.in_title:
            self.job_title += ch

# =============================================================================
def fetchJobList(base_url):
    parser = make_parser()
    curHandler = JobFeedHandler()
    parser.setContentHandler(curHandler)

    from urllib import urlencode, urlopen

    query_dict = {
                "action" : "query",
                "format" : "xml",
        }

#    url = base_url + '?' + urlencode(query_dict)
    url = base_url
#    print url

    parser.parse(urlopen(url))

    print "Length before filtering:", len(curHandler.joblist)
    return curHandler.joblist

# =============================================================================
if __name__ == '__main__':

    import sys
    base_url = 'http://localhost:8080/static/example_joblist.xml'
    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    jobs = fetchJobList(base_url)

    print len(jobs), "jobs."
    for job in jobs:

        print "\t", job.title
        print "\t\t", "Contract employment?", job.contract
        print "\t\t", job.expiration
        print "\t\t", job.job_id
        print "\t\t", job.geo
        print "\t\t", job.degree_level, "in", job.degree_area
        print "\t\t", "Skills:", job.skills
