#!/usr/bin/python

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

from datetime import datetime

SKILL_REQUIRED = "required"
SKILL_PREFERRED = "preferred"
SKILL_PREFERENCE_TYPES = [SKILL_REQUIRED, SKILL_PREFERRED]

SKILL_CATEGORY_APIS = "apis"
SKILL_CATEGORY_APPLICATIONS = "applications"
SKILL_CATEGORY_PROGRAMMING_LANGUAGES = "programming_languages"
SKILL_CATEGORIES = [SKILL_CATEGORY_APIS, SKILL_CATEGORY_APPLICATIONS, SKILL_CATEGORY_PROGRAMMING_LANGUAGES]

# =============================================================================
class LanguageExperience():
    def __init__(self, name, years):
        self.name = name
        self.years = years
        if not (years is None):
            self.years = float(years)

    def __str__(self):
        return str(tuple([self.name, self.years]))

    def __repr__(self):
        return str(self)

# =============================================================================
class Job():
    def __init__(self, handler):
        self.job_id = int(handler.jobid)
        self.geo = handler.geo
        self.title = handler.job_title
        self.degree_level = handler.degree_level
        self.degree_area = handler.degree_area
        self.expiration = datetime.strptime(handler.expiration, "%Y-%m-%d").date()

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
        self.skill_category = None
        self.skill_preference_type = None

    def startElement(self, name, attrs):

        if name == 'position':
            self.in_position = True
            self.jobid = attrs.get('id', "")
            self.expiration = attrs.get('expires', "")

        elif name in SKILL_PREFERENCE_TYPES:
            self.skill_preference_type = name
            self.skills[self.skill_preference_type] = {}

        elif name in SKILL_CATEGORIES:
            self.skill_category = name
            self.skills[self.skill_preference_type][self.skill_category] = []

        elif name == 'geo':
            self.geo = map(float, [attrs.get('lat', ""), attrs.get('lon', "")])

        elif name == 'degree':
            self.degree_level = attrs.get('level', "")
            self.degree_area = attrs.get('area', "")

        elif name == 'title':
            self.in_title = True
            self.job_title = ""

        elif name == 'lang':

            self.skills[self.skill_preference_type][self.skill_category].append(
                    LanguageExperience(
                            attrs.get('name', ""),
                            attrs.get('years', None)
                    )
            )

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
        print "\t\t", job.expiration
        print "\t\t", job.job_id
        print "\t\t", job.geo
        print "\t\t", job.degree_level, "in", job.degree_area
        print "\t\t", "Skills:", job.skills
