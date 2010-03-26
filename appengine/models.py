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

"""Defines models for the "jobfeed" application."""

__author__ = 'kostmo@gmail.com (Karl Ostmo)'

from google.appengine.ext import db
from geo.geomodel import GeoModel

# If "-1" is given for the experience, this could be interpreted as "unspecified",
# and all of the buckets will then be added to the job record.
EXPERIENCE_YEARS_BUCKETS = [0, 2, 4, 7, 10]


# XXX The most commonly used model names are kept short to save storage space in App Engine
# =============================================================================
class SimpleCounter(db.Model):	# TODO Not used
    count = db.IntegerProperty(default=0)

# =============================================================================
# TODO Not used
class Org(db.Model):	# An Organization or Company
    name = db.StringProperty()

# =============================================================================
class Sub(db.Model):	# Subject matter keyword
    # use the "key_name" kwarg for the canonical (lowercase) name,
    # just like Skill.
    name = db.StringProperty()
    lower = db.StringProperty()    # Lowercase version

# =============================================================================
# TODO Not used
class Site(db.Model):	# A physical job site
    name = db.StringProperty()
    geo = db.GeoPtProperty()
    org = db.ReferenceProperty(Org, required=True)

# =============================================================================
# TODO Not used
class DegreeArea(db.Model):	# Area of concentration
    name = db.StringProperty()

# =============================================================================
# TODO Not used
class DegreeLevel(db.Model):
    name = db.StringProperty()

# =============================================================================
class Skill(db.Model):	# A named skill.
    name = db.StringProperty(required=True)
    # We need this property for prefix matching, even though it is identical to the "key_name" kwarg:
    lower = db.StringProperty(required=True)    # Lowercase version

# =============================================================================
class Api(Skill):	# "Api Skill": A piece of equipment or physical tool
    pass

# =============================================================================
class Equip(Skill):	# "Equipment Skill": A piece of equipment or physical tool
    pass

# =============================================================================
class Duty(Skill):	# procedure/task/duty/responsibility, or other common activity
    pass

# =============================================================================
class App(Skill):	# software application skill
    pass

# =============================================================================
class Lang(Skill):	# Programming Language Skill
    pass

# =============================================================================
class Exp(db.Model):	# Skill Experience
#    skill = db.ReferenceProperty(Skill, required=True)    # We can set the parent instead
    years = db.IntegerProperty(required=True, default=-1)   # XXX Duplicates "key_name"
    
# =============================================================================
class Feed(db.Model):	# Job Feed URL
    link = db.LinkProperty(required=True)
    contact =  db.EmailProperty(indexed=False)
    since = db.DateTimeProperty(required=True, auto_now_add=True)
    lastcrawl = db.DateTimeProperty(required=True, auto_now=True)
    interval = db.IntegerProperty(indexed=False) # in days
    crawlcount = db.IntegerProperty(default=0, indexed=False)

# =============================================================================
class JobFeedSpamReport(db.Model):
    reporter = db.UserProperty(auto_current_user_add=True)
    feed = db.ReferenceProperty(Feed, required=True)

# =============================================================================
class SavedSearch(db.Model):
    user = db.UserProperty(auto_current_user_add=True)
    title = db.StringProperty()
    address = db.StringProperty(indexed=False)
    geo = db.GeoPtProperty(indexed=False)
    qualifications = db.ListProperty(db.Key, indexed=False)  # Exp
    keywords = db.ListProperty(db.Key, indexed=False)  # Sub
    saved = db.DateTimeProperty(required=True, auto_now=True)

# =============================================================================
class Job(GeoModel):	# Job Opening
    """A location-aware model for Job postings."""

    job_id = db.IntegerProperty()
    title = db.StringProperty(indexed=False)
    contract = db.BooleanProperty(default=False) # vs. permanent employment
    expiration = db.DateProperty()
    expired = db.BooleanProperty(default=False)
    feed = db.ReferenceProperty(Feed, indexed=False)
    
    link = db.LinkProperty(indexed=False)   # Optionally link back to the full description on employer's website
    required = db.ListProperty(db.Key)  # Exp
    preferred = db.ListProperty(db.Key, indexed=False)  # Exp
    # XXX Beware of exploding indexes caused by multiple ListProperty's;
    # it may be better to augment the "Exp" model with a boolean,
    # and duplicate each instance with the True and False version

    # TODO: Allow this property to be indexed, but ensure that it does not occur in the same index
    # as the "required" ListProperty, or if it does, limit the number of items (exploding indexes).
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
