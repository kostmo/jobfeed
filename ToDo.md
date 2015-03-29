## bugs ##
  * ?

## potential optimizations ##
  * Limit 250 jobs per feed
  * Limit 1000 jobs per domain?
  * **Enforce limit of 5 searchable skills and 3 keywords**
  * Store key\_name's in `StringListProperty` instead of key's in `ListProperty`?

## features ##
### UI ###
  * signify whether a posting is "authoritative"
  * filter (or at least grey-out) expired jobs
  * Add job count to main page
  * List jobs by domain (may span multiple "feeds")
  * List feeds by domain
  * **perform in-memory (post-datastore fetch) ranking of results by number of skills matched**
    * higher years experience requirement on an equivalent skill across jobs should rank higher (since merely "years >= requirement" qualifies as a "match")

### backend ###
  * implement periodic feed checks
    * Use contact email to notify upon failed feed parse
  * Add (optional and non-indexed) salary field?
  * implement synomyms for keywords
    * Approach 1: use key parents; the canonical word is the parent of all synonyms
    * Approach 2: maintain a ListProperty of all synonyms as a member of the canonical word entity
  * profiles
    * Import existing DOAC XMLfile as search profile
    * Export as DOAC format
    * Project-months as a metric of language proficiency

## Spam Countermeasures ##
Feed submission keeps track of domain name.  Users with a Google Account can mark a particular job listing as Spam.  The domain hosting the feed for that job listing gets a vote against it, also recording the user who submitted the vote.  Domains with too many negative votes are blacklisted.  Blacklistings can be appealed manually, and if so, all votes by that Google Account holder are nullified.