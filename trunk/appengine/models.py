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

# If "-1" is given for the experience, this may be interpreted as "unspecified".
# All of the buckets will then be added to the job record.
EXPERIENCE_YEARS_BUCKETS = [0, 1, 2, 4, 7, 10]

# =============================================================================
class Organization(db.Model):
    name = db.StringProperty()

# =============================================================================
class Subject(db.Model):
    # use the "key_name" kwarg for the canonical (lowercase) name,
    # just like NamedSkill.
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
    years = db.IntegerProperty(required=True, default=-1)   # XXX Duplicates "key_name"
    
# =============================================================================
class JobFeedUrl(db.Model):
    link = db.LinkProperty(required=True)
    contact =  db.EmailProperty(indexed=False)
    since = db.DateTimeProperty(required=True, auto_now_add=True)
    lastcrawl = db.DateTimeProperty(required=True, auto_now=True)
    interval = db.IntegerProperty(indexed=False) # in days
    crawlcount = db.IntegerProperty(default=0, indexed=False)

# =============================================================================
class SavedSearch(db.Model):
    user = db.UserProperty(auto_current_user_add=True)
    title = db.StringProperty(indexed=False)
    address = db.StringProperty(indexed=False)
    geo = db.GeoPtProperty(indexed=False)
    qualifications = db.ListProperty(db.Key, indexed=False)  # SkillExperience
    saved = db.DateTimeProperty(required=True, auto_now=True)

# =============================================================================
class JobFeedSpamReport(db.Model):
    reporter = db.UserProperty(auto_current_user_add=True)
    feed = db.ReferenceProperty(JobFeedUrl, required=True)

# =============================================================================
class JobOpening(GeoModel):
    """A location-aware model for Job postings."""

    job_id = db.IntegerProperty()
    title = db.StringProperty(indexed=False)
    contract = db.BooleanProperty(default=False) # vs. permanent employment
    expiration = db.DateProperty()
    expired = db.BooleanProperty(default=False)
    feed = db.ReferenceProperty(JobFeedUrl, indexed=False)
    
    link = db.LinkProperty(indexed=False)   # Optionally link back to the full description on employer's website
    required = db.ListProperty(db.Key)  # SkillExperience
    preferred = db.ListProperty(db.Key, indexed=False)  # SkillExperience
    # XXX Beware of exploding indexes caused by multiple ListProperty's;
    # it may be better to augment the "SkillExperience" model with a boolean,
    # and duplicate each instance with the True and False version

    # TODO: Allow this property to be indexed, but ensure that it does not occur in the same index
    # as the "required" ListProperty (exploding indexes).
    keywords = db.ListProperty(db.Key, indexed=False)	# Subject
    
    sample = db.BooleanProperty(default=False)  # For debugging/test deployments
    
#    since = db.DateTimeProperty(required=True, auto_now_add=True)   # Redundant with the feed
    updated = db.DateTimeProperty(required=True, auto_now=True, indexed=False)

    @staticmethod
    def public_attributes():
        """Returns a set of simple attributes on job opening entities."""
        return [
          'job_id', 'title', 'link'
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
