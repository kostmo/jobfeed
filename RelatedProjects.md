## ping servers ##
The "feed crawler" implementation would use a [ping server](http://en.wikipedia.org/wiki/Ping_%28blogging%29) like those in blogging.  Inspiration is drawn from [this "push" concept recently discussed by Google](http://search.slashdot.org/story/10/03/04/1518249/Google-Indexing-In-Near-Realtime?art_pos=153).

I envision the feeds to serve a role similar to Google's [Sitemaps format](http://en.wikipedia.org/wiki/Sitemaps). Maybe they could be called "Jobmaps: crawler friendly job listings".

## XML standards ##

[The XML Résumé Library](http://xmlresume.sourceforge.net/)
> "... an XML and XSL based system for marking up, adding metadata to, and formatting résumés and curricula vitae."

[The HR-XML Consortium](http://www.hr-xml.org)
> "... the only independent, non-profit, volunteer-led organization dedicated to the development and promotion of a standard suite of XML specifications to enable e-business and the automation of human resources-related data exchanges."
  * [PositionOpening schema](http://ns.hr-xml.org/schemas/org_hr-xml/3_0/Documentation/ComponentDoc/PositionOpening-noun.php)
  * [PositionCompetencyModel](http://ns.hr-xml.org/schemas/org_hr-xml/3_0/Documentation/ComponentDoc/PositionCompetencyModel-noun.php)
  * [CompetencyDefinitions](http://ns.hr-xml.org/schemas/org_hr-xml/3_0/Documentation/ComponentDoc/CompetencyDefinitions-noun.php)

[Juju XML Job Feed Specification](http://www.job-search-engine.com/add-jobs/feeds/)

## feed solicitation ##

This is not the first effort to solicit XML job feeds from companies.
Here are just a couple I found in a Google search, along with some aspects to compare/contrast **jobfeed** with.

[SimplyHired](http://www.simplyhired.com/a/add-jobs/feed#feed_spec)

  * lacks Google Maps integration
  * has way more jobs listed (as of now)
  * does not facilitate fine-grained search based on individual skills.

[InovaHire](http://www.inovahire.com/xml-job-feed)

  * site is ad-sponsored.
  * lacks Google Maps integration
  * not as focused in scope (they also offer "live interview" services)
  * does not facilitate fine-grained search based on individual skills.

[Juju](http://www.job-search-engine.com/add-jobs/)
  * Also a commercial site

## skill search ##

Wikipedia's [userboxes](http://en.wikipedia.org/wiki/User_box) identify discrete, quantifiable skills.
  * [Educational degrees](http://en.wikipedia.org/wiki/Wikipedia:Userboxes/Education#Specialized_degrees)
  * [Programming skills](http://en.wikipedia.org/wiki/Wikipedia:Userboxes/Programming)
Excerpt:
> Placing one of these `[`programming language userboxes`]` on your userpage automatically lists you in Wikipedia's category system under the corresponding category so that other users may find you based on your skills.

[RentACoder](http://www.rentacoder.com/)

  * Allows detailed specification of requirements to solicit bids for a single project, including programming languages
  * not intended for long-term employment
  * commercial in nature