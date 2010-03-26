#!/usr/bin/env python

import models
from google.appengine.ext import db


# =============================================================================
def recoverExperienceEntity(parent_keystring, years_int):
        parent_key_object = db.Key(parent_keystring)
        return db.Key.from_path(parent_key_object.kind(), parent_key_object.name(), 'Exp', str(years_int))


# =============================================================================
# skill_experience_entities is guaranteed to have at least one item
def getHighestBinWithAtMost(bins, years):
    
    last_bucket = bins[0]
    for bin in bins:
        if bin > years:
            return last_bucket
        last_bucket = bin
    return last_bucket

# =============================================================================
# skill_experience_entities is guaranteed to have at least one item
def getHighestBucketWithAtMost(skill_experience_entities, years):
    
    last_bucket = skill_experience_entities[0]
    for bucket in skill_experience_entities:
        if bucket.years > years:
            return last_bucket
        last_bucket = bucket
    return last_bucket

# =============================================================================
# skill_experience_entities is guaranteed to have at least one item
def getBucketsAtOrAbove(skill_experience_entities, years):
    
    min_bin = getHighestBinWithAtMost(models.EXPERIENCE_YEARS_BUCKETS, years)
    
    qualifying_buckets = []
    for bucket in skill_experience_entities:
        if bucket.years >= min_bin:
            qualifying_buckets.append(bucket)

#    logging.info("Qualifying buckets: " + str(qualifying_buckets))

    return qualifying_buckets


# =============================================================================
def parseStringifiedExperienceDict(stringified_dict):
	experience_keys_list = []
	if stringified_dict:

		stringified_experience_keys_list = stringified_dict.split(";")
		for binned_skill_lump in stringified_experience_keys_list:

			parent_keystring, years = binned_skill_lump.split(":")
			appropriate_bin = getHighestBinWithAtMost(models.EXPERIENCE_YEARS_BUCKETS, int(years))

			k = recoverExperienceEntity(parent_keystring, appropriate_bin)
			experience_keys_list.append(k)

	return experience_keys_list


# =============================================================================
if __name__ == '__main__':
	pass
