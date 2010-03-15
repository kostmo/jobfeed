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

"""Defines models for the "jobfeed" application."""

__author__ = 'kostmo@gmail.com (Karl Ostmo)'

from google.appengine.ext import db

from geo.geomodel import GeoModel

EXPERIENCE_YEARS_BUCKETS = [1, 2, 4, 7, 10]

# =============================================================================
class Organization(db.Model):
    name = db.StringProperty()
    
# =============================================================================
class JobSite(db.Model):
    name = db.StringProperty()
    geo = db.GeoPtProperty()
    org = db.ReferenceProperty(Organization, required=True)

# =============================================================================
class DegreeArea(db.Model):
    name = db.StringProperty()

# =============================================================================
class DegreeLevel(db.Model):
    name = db.StringProperty()

# =============================================================================
class SimpleCounter(db.Model):
    count = db.IntegerProperty(default=0)

# =============================================================================
class NamedSkill(db.Model):
    name = db.StringProperty()
    # XXX Instead of an additional property, we'll use the "key_name" kwarg.
#    canonical = db.StringProperty()    # Lowercase version

# =============================================================================
class ApiSkill(NamedSkill):
    pass

# =============================================================================
class EquipmentSkill(NamedSkill):
    pass

# =============================================================================
class ActivitySkill(NamedSkill):
    pass

# =============================================================================
class ApplicationSkill(NamedSkill):
    pass

# =============================================================================
class ProgrammingLanguageSkill(NamedSkill):
    pass

# =============================================================================
class SkillExperience(db.Model):
#    skill = db.ReferenceProperty(NamedSkill, required=True)    # We can set the parent instead
    years = db.IntegerProperty(required=True)   # XXX Duplicates "key_name"
    
# =============================================================================
class JobFeedUrl(db.Model):
    link = db.LinkProperty(required=True)
    contact =  db.EmailProperty()
    since = db.DateTimeProperty(required=True, auto_now_add=True)
    lastcrawl = db.DateTimeProperty(required=True, auto_now=True)
    interval = db.IntegerProperty() # in days
    crawlcount = db.IntegerProperty(default=0)

# =============================================================================
class SavedSearch(db.Model):
    user = db.UserProperty(auto_current_user_add=True)
    title = db.StringProperty()
    address = db.StringProperty()
    geo = db.GeoPtProperty()
    qualifications = db.ListProperty(db.Key)  # SkillExperience
    saved = db.DateTimeProperty(required=True, auto_now=True)

# =============================================================================
class JobFeedSpamReport(db.Model):
    reporter = db.UserProperty(auto_current_user_add=True)
    feed = db.ReferenceProperty(JobFeedUrl, required=True)

# =============================================================================
class JobOpening(GeoModel):
    """A location-aware model for Job postings."""

    job_id = db.IntegerProperty()
    title = db.StringProperty()
    contract = db.BooleanProperty(default=False) # vs. permanent employment
    expiration = db.DateProperty()
    expired = db.BooleanProperty(default=False)
    feed = db.ReferenceProperty(JobFeedUrl)
    
    fullpost = db.LinkProperty()   # Optionally link back to the full description on employer's website
    required = db.ListProperty(db.Key)  # SkillExperience
    preferred = db.ListProperty(db.Key)  # SkillExperience
    
#    since = db.DateTimeProperty(required=True, auto_now_add=True)   # Redundant with the feed
    updated = db.DateTimeProperty(required=True, auto_now=True)

    @staticmethod
    def public_attributes():
        """Returns a set of simple attributes on job opening entities."""
        return [
          'job_id', 'title'
        ]

    def _get_latitude(self):
        return self.location.lat if self.location else None

    def _set_latitude(self, lat):
        if not self.location:
            self.location = db.GeoPt()

        self.location.lat = lat

    latitude = property(_get_latitude, _set_latitude)

    def _get_longitude(self):
        return self.location.lon if self.location else None

    def _set_longitude(self, lon):
        if not self.location:
            self.location = db.GeoPt()

        self.location.lon = lon

    longitude = property(_get_longitude, _set_longitude)
