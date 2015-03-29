The [excerpt on the main page](http://code.google.com/p/jobfeed/#example) gives an impression of what a feed should look like. Please examine a [complete example](http://code.google.com/p/jobfeed/source/browse/trunk/appengine/static/example_joblist.xml).

Here is the [official jobfeed schema](http://code.google.com/p/jobfeed/source/browse/trunk/appengine/static/jobfeed.xml) written in [RELAX NG](http://en.wikipedia.org/wiki/RELAX_NG). You should validate your own feed (with [this Python script](http://code.google.com/p/jobfeed/source/browse/trunk/appengine/scripts/validate.py) or [a GUI utility](http://xml-copy-editor.sourceforge.net/)) against this schema before [submitting](http://jobcrawlr.appspot.com/register) it.

## job records ##
The following information can be associated with each job record:
  * location
    * Nominal location/address
    * precise geographic coordinates (Lat/Lon)
  * company name
  * company department
  * position title
  * required/preferred skills
  * educational requirements
    * degree area/concentration
    * certifications
  * subject matter keywords
  * contract vs. permanent employment
  * senior vs. entry-level position
  * expiration date

Since there may be many job openings at the same physical site, the XML schema allows one to specify the geographic coordinates just once for the site to be inherited by all of its children.  Likewise for the organization and the (optional) department.

### the `<job>` element ###
The `<job>` element represents an open position within the organization.

Allowed attributes of the `<job>` element are:
| **attribute name** | **required?** | **meaning** | **example values** |
|:-------------------|:--------------|:------------|:-------------------|
| `id` | Y | a numeric ID for the job posting, unique across the organization | 12548 |
| `expires` | Y | expiration date of this job opening in hyphenated [ISO 8601 format](http://en.wikipedia.org/wiki/ISO_8601#Calendar_dates) | 2010-03-15 |
| `link` | Y | a "permalink" to the job posting hosted on the corporate website | `http://www.example.com/careers/job?id=12548` |
| `permanence`<sup>†</sup> | N | an integer representing contract/permanent employment | 2 |
| `seniority`<sup>‡</sup> | N | an integer representing senior/entry-level status | 1 |

<sup>†</sup>Values for `permanence`:
| **value** | **label** | **meaning** |
|:----------|:----------|:------------|
| 0 | intern/co-op | definite-term employment for students |
| 1 | contract | definite-term employment for professionals |
| 2 | permanent | permanent, full-time employment |

<sup>‡</sup>Values for `seniority`:
| **value** | **label** | **meaning** |
|:----------|:----------|:------------|
| 0 | entry-level | first job in this field, just entering the workforce |
| 1 | senior | a highly experienced veteran of the field |

Allowed immediate children of the `<job>` element are:
| **tag name** | **required?** | **meaning** | **example values** |
|:-------------|:--------------|:------------|:-------------------|
| `<title>` | Y | title of the open position | Test Engineer |
| `<description>` | N | short prose description of the job | Applicant should be familiar with six-sigma and... Responsibilities include... |
| `<keyword>`<sup>†</sup> | N | single keyword that describe the subject matter | R&D |
| `<qualifications>` | Y | container for `<education>`, `<preferred>`, and `<required>` | See below |

<sup>†</sup>Multiple `<keyword>` tags may be used to specify up to 4 keywords.

Within the `<required>` or `<preferred>` tags the following types of "competencies" are allowed:
| **tag name** | **meaning** | **example values** |
|:-------------|:------------|:-------------------|
| `<lang>` | programming language | Java, C++ |
| `<api>` | Library/API/environment | Google App Engine, OpenGL, Boost |
| `<app>` | software application | AutoCAD, git |
| `<equip>` | physical equipment or tool | multimeter, cash register |
| `<duty>` | process/task/duty/responsibility or other common activity | system administration, PCB layout |

## supplemental information ##
  * [relax-ng tutorial](http://www.oasis-open.org/committees/relax-ng/tutorial-20011203.html)
  * [standard XML schema datatypes](http://www.w3.org/TR/xmlschema-2/#built-in-datatypes)