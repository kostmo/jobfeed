## feeds ##
  * Job ID numbers must be unique per Feed
  * keywords and skills in a feed should be listed in decreasing order of importance
  * only the first 5 skills and first 3 keywords in a job are made searchable
    * This is to limit the space consumed by [exploding indexes](http://code.google.com/appengine/docs/python/datastore/queriesandindexes.html#Big_Entities_and_Exploding_Indexes)
  * Order of heterogeneous tags in certain elements is enforced by the schema, due to how the the SAX parser works.
    * In a `<site>`, the `<location>` tag must precede any `<department>` or `<job>` tags.
  * The `<department>` tag is optional. `<job>` tags may be placed inside this or as direct children of `<site>`.
  * The `link` attribute of a `<job>` **must** have a URL within the domain or a subdomain of that specified in the `domain` attribute of the `<organization>` tag.
  * Feed search is an "opt-in" service. Anyone can submit a job feed on behalf of any organization. However, only feeds that originate from the same domain as the organization domain shall be considered "authoritative".
## skills matching ##
  * queries based on skill-experience are performed using the `IN` filter operator.
    * A list of "experience" entity keys is stored in each job record. The client has a list of experience keys for the current search.
      * According to App Engine documentation: When testing a ListProperty, the equality (`=`) filter operator checks whether the argument exists as an element in the list.  If it is present, the record passes the test and may be returned with `fetch()`.  For the `IN` operator, the filter argument is a list, and a separate equality test is performed for each element.  If **any** of these tests succeeds, then the record passes the `IN` test.
    * To get around the "single-property inequality filter" limitation of App Engine, years of experience are split up into "bins" rather than measured on a continuous scale.  The client maintains a list of their highest attained bins for each skill. A job feed specifies only the minimum level of experience for the job.  However, to enable matching a job where the client's experience level falls in a higher bin than the minimum required (i.e. simulating a ">=" operator), all experience bins that meet or exceed the stated minimum are added to the job record. Thus if the possible bins include `[...2, 4, 7, 10]`, the client has specified 7 years of experience in a skill, and the job requires 4 years of experience, the bins `[4, 7, 10]` will be added to the job record, permitting 7 to match.