#!/usr/bin/env python

# Source: http://en.wikipedia.org/wiki/List_of_United_States_cities_by_population
most_populous_cities = [('New York', 'New York '), ('Los Angeles', 'California '), ('Chicago', 'Illinois '), ('Houston', 'Texas '), ('Phoenix', 'Arizona '), ('Philadelphia', 'Pennsylvania '), ('San Antonio', 'Texas '), ('Dallas', 'Texas '), ('San Diego', 'California '), ('San Jose', 'California '), ('Detroit', 'Michigan '), ('San Francisco', 'California '), ('Jacksonville', 'Florida '), ('Indianapolis', 'Indiana '), ('Austin', 'Texas '), ('Columbus', 'Ohio '), ('Fort Worth', 'Texas '), ('Charlotte', 'North Carolina '), ('Memphis', 'Tennessee '), ('Baltimore', 'Maryland '), ('Boston', 'Massachusetts '), ('El Paso', 'Texas '), ('Milwaukee', 'Wisconsin '), ('Denver', 'Colorado '), ('Seattle', 'Washington '), ('Nashville', 'Tennessee '), ('Washington', 'District of Columbia '), ('Las Vegas', 'Nevada '), ('Portland', 'Oregon '), ('Louisville', 'Kentucky '), ('Oklahoma City', 'Oklahoma '), ('Tucson', 'Arizona '), ('Atlanta', 'Georgia '), ('Albuquerque', 'New Mexico '), ('Kansas City', 'Missouri '), ('Fresno', 'California '), ('Sacramento', 'California '), ('Long Beach', 'California '), ('Mesa', 'Arizona '), ('Omaha', 'Nebraska '), ('Cleveland', 'Ohio '), ('Virginia Beach', 'Virginia '), ('Miami', 'Florida '), ('Oakland', 'California '), ('Raleigh', 'North Carolina '), ('Tulsa', 'Oklahoma '), ('Minneapolis', 'Minnesota '), ('Colorado Springs', 'Colorado '), ('Honolulu', 'Hawaii '), ('Arlington', 'Texas ')]

# Source: http://www.langpop.com/
# Also see: http://en.wikipedia.org/wiki/List_of_programming_languages_by_category
languages = ['Java', 'C', 'C++', 'PHP', 'JavaScript', 'Python', 'SQL', 'C#', 'Perl', 'Ruby', 'Shell', 'Visual Basic', 'Assembly', 'Actionscript', 'Delphi', 'Objective C', 'Lisp', 'Pascal', 'Fortran', 'ColdFusion', 'Scheme', 'Lua', 'Haskell', 'D', 'Tcl', 'Ada', 'Cobol', 'Erlang', 'Smalltalk', 'Scala', 'OCaml', 'Forth', 'Rexx']


subjects = ["automotive", "control systems", "biomedical", "bioinformatics", "genomics", "aerospace"]


def generateFeed():
	from random import randint, sample

	from xml.dom.minidom import Document
	doc = Document()

	root = doc.createElement("jobfeed")
	root.setAttribute("vocabulary", "1.0")
	root.setAttribute("sample", "true")
	doc.appendChild(root)

	organization = doc.createElement("organization")
	root.appendChild(organization)

	name = doc.createElement("name")
	name.appendChild( doc.createTextNode("Organization Name") )
	organization.appendChild(name)

	sites = doc.createElement("sites")
	organization.appendChild(sites)

	jobcounter = 0
	for city_tuple in most_populous_cities:

		site = doc.createElement("site")
		sites.appendChild(site)

		name = doc.createElement("name")
		name.appendChild( doc.createTextNode("Site Name") )
		site.appendChild(name)

		location = doc.createElement("location")
		site.appendChild(location)

		# Give some the address, but for others provide the geo coords directly
		cityname = ", ".join(city_tuple)
		if randint(0, 1):
			geo = doc.createElement("geo")
			from geocode import getGeo
			for key, val in getGeo( cityname ).items():
				geo.setAttribute(key, "%.4f" % (val))
			location.appendChild(geo)
		else:
			address = doc.createElement("address")
			address.appendChild( doc.createTextNode( cityname ) )
			location.appendChild(address)

		departments = doc.createElement("departments")
		site.appendChild(departments)

		for i in range(randint(1, 3)):

			department = doc.createElement("department")
			departments.appendChild(department)

			name = doc.createElement("name")
			name.appendChild( doc.createTextNode("Department Name") )
			department.appendChild(name)


			openings = doc.createElement("openings")
			department.appendChild(openings)

			for j in range(randint(2, 8)):

				position = doc.createElement("position")
				openings.appendChild(position)
				position.setAttribute("id", str(jobcounter))
				jobcounter += 1

				from datetime import datetime, timedelta
				position.setAttribute("expires", (datetime.now().date() + timedelta(days=randint(0, 90))).isoformat() )

				title = doc.createElement("title")
				title.appendChild( doc.createTextNode("Position Title") )
				position.appendChild(title)


				subject_matter = doc.createElement("subject_matter")
				position.appendChild(subject_matter)

				for subject in sample(subjects, randint(1, min(4, len(subjects)))):
					keyword = doc.createElement("keyword")
					keyword.appendChild( doc.createTextNode( subject ) )
					subject_matter.appendChild(keyword)

				qualifications = doc.createElement("qualifications")
				position.appendChild(qualifications)

				skills = doc.createElement("skills")
				qualifications.appendChild(skills)

				for skill_classification in ["required", "preferred"]:

					skillbatch = doc.createElement( skill_classification )
					skills.appendChild( skillbatch )

					for language in sample(languages, randint(0, min(4, len(languages)))):

						lang = doc.createElement("lang")
						lang.setAttribute("name", language)
						lang.setAttribute("years", str(randint(0, 10)))
						skillbatch.appendChild(lang)

		break
	return doc



# =============================================================================
if __name__ == '__main__':

	import sys

	output_filename = None
	if len(sys.argv) > 1:
		output_filename = sys.argv[1]

	print "Generating feed..."

	doc = generateFeed()
#	print doc.toprettyxml(indent="\t")

	if output_filename:
		filename = "foo.xml"
		doc.writexml( open(output_filename, "w") )
	else:
		import StringIO
		fileHandle = StringIO.StringIO()
		doc.writexml( fileHandle )


	print "Validating feed..."

	if output_filename:
		jobfeed_filehandle = open(output_filename, "r")
	else:
		jobfeed_filehandle = fileHandle
		jobfeed_filehandle.seek(0)

	from validate import doValidation, JOBFEED_SCHEMA_URL
	validation_error = doValidation(jobfeed_filehandle, JOBFEED_SCHEMA_URL)
	if validation_error:
		print validation_error
		exit(1)


	print "Parsing feed..."

	jobfeed_filehandle.seek(0)
	from parse_jobs import fetchJobList, dumpJobs
	jobs = fetchJobList( jobfeed_filehandle )
	print len(jobs), "jobs."
#	dumpJobs(jobs)

