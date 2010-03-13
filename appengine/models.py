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

"""Defines models for the PubSchool demo application."""

__author__ = 'kostmo@gmail.com (Karl Ostmo)'

from google.appengine.ext import db

from geo.geomodel import GeoModel

EXPERIENCE_YEARS_BUCKETS = [1, 2, 4, 7, 10]

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
    skill = db.ReferenceProperty(NamedSkill, required=True)
    years = db.IntegerProperty(required=True)
    
# =============================================================================
class JobFeedUrl(db.Model):
    link = db.LinkProperty(required=True)
    contact =  db.EmailProperty()
    since = db.DateTimeProperty(required=True, auto_now_add=True)
    lastcrawl = db.DateTimeProperty(required=True, auto_now=True)
    interval = db.IntegerProperty() # in days
    crawlcount = db.IntegerProperty(default=0)

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
    feed = db.ReferenceProperty(JobFeedUrl, required=True)
    
    required = db.ListProperty(db.Key)
    preferred = db.ListProperty(db.Key)
    
#    since = db.DateTimeProperty(required=True, auto_now_add=True)   # Redundant with the feed
    updated = db.DateTimeProperty(required=True, auto_now=True)

    @staticmethod
    def public_attributes():
        """Returns a set of simple attributes on public school entities."""
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


# =============================================================================
# FIXME DEPRECATED
class PublicSchool(GeoModel):
    """A location-aware model for public school entities.

    See http://nces.ed.gov/ccd/psadd.asp for details on attributes.
    """
    school_id = db.StringProperty()
    name = db.StringProperty()
    address = db.StringProperty()
    city = db.StringProperty()
    state = db.StringProperty()
    zip_code = db.IntegerProperty()
    enrollment = db.IntegerProperty()
    phone_number = db.StringProperty()
    locale_code = db.IntegerProperty()
    school_type = db.IntegerProperty()
    school_level = db.IntegerProperty()
    grades_taught = db.ListProperty(int)

    @staticmethod
    def public_attributes():
        """Returns a set of simple attributes on public school entities."""
        return [
          'school_id', 'name', 'address', 'city', 'state', 'zip_code',
          'enrollment', 'phone_number', 'locale_code', 'school_type', 'school_level'
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
