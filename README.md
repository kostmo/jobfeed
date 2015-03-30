[http://jobcrawlr.appspot.com/ Try it out!]

==goal==
To proliferate standard-format, machine-readable, employer-hosted job listings.
==overview==
http://jobfeed.googlecode.com/svn/graphics/inkscape/ecosystem_diagram.png

Many companies already post job openings in a "Careers" tab (or something similar) on their website. Generally, the job descriptions are written in prose, and sometimes users are forced to navigate unfamiliar CRM software to browse them all for relevant openings.

Why shouldn't employers post jobs in a machine-readable format? Such a format should semantically tag programming languages and other required or preferred skills that job seekers can easily match against their own profile.
==example feed (excerpt)==
{{{
<organization name="Example Industries" domain="example.com">
  <site name="Corporate Headquarters">
    <location><geo lat="45.52" lng="-122.68" /><address>221B Baker Street, London</address></location>
    <department name="Research and Development">
      <job id="153" expires="2010-03-13" link="http://example.com/jobs#153">
        <title>Sr. Electrical Engineer</title>
        <keyword>automotive</keyword>
        <keyword>control systems</keyword>
        <qualifications>
          <education>
            <degree level="Bachelors" area="Electrical Engineering"/>
          </education>
          <skills>
            <required>
              <api name="OpenGL" years="4" />
              <!-- programming languages -->
              <lang name="MATLAB" years="2" />
}}}

Companies could then [http://jobcrawlr.appspot.com/register register] the URL of their job feeds with feed search engines, or a third party could register the feed on their behalf. This project aims to build a [http://jobcrawlr.appspot.com/ reference implementation] for such a search engine while promoting a [FeedSchema standard XML schema] for feeds. Publishing a direct XML feed of job openings is mutually beneficial for employers and job seekers. Hopefully this will become standard practice (especially for technology-oriented companies) in the near future.

### Open Source Dependencies

Note: This project makes use of the "geomodel" project:
https://code.google.com/p/geomodel/
