#!/usr/bin/env python

import feedparser

# Source: http://en.wikipedia.org/wiki/List_of_United_States_cities_by_population
most_populous_cities = [('New York', 'New York'), ('Los Angeles', 'California'), ('Chicago', 'Illinois'), ('Houston', 'Texas'), ('Phoenix', 'Arizona'), ('Philadelphia', 'Pennsylvania'), ('San Antonio', 'Texas'), ('Dallas', 'Texas'), ('San Diego', 'California'), ('San Jose', 'California'), ('Detroit', 'Michigan'), ('San Francisco', 'California'), ('Jacksonville', 'Florida'), ('Indianapolis', 'Indiana'), ('Austin', 'Texas'), ('Columbus', 'Ohio'), ('Fort Worth', 'Texas'), ('Charlotte', 'North Carolina'), ('Memphis', 'Tennessee'), ('Baltimore', 'Maryland'), ('Boston', 'Massachusetts'), ('El Paso', 'Texas'), ('Milwaukee', 'Wisconsin'), ('Denver', 'Colorado'), ('Seattle', 'Washington'), ('Nashville', 'Tennessee'), ('Washington', 'District of Columbia'), ('Las Vegas', 'Nevada'), ('Portland', 'Oregon'), ('Louisville', 'Kentucky'), ('Oklahoma City', 'Oklahoma'), ('Tucson', 'Arizona'), ('Atlanta', 'Georgia'), ('Albuquerque', 'New Mexico'), ('Kansas City', 'Missouri'), ('Fresno', 'California'), ('Sacramento', 'California'), ('Long Beach', 'California'), ('Mesa', 'Arizona'), ('Omaha', 'Nebraska'), ('Cleveland', 'Ohio'), ('Virginia Beach', 'Virginia'), ('Miami', 'Florida'), ('Oakland', 'California'), ('Raleigh', 'North Carolina'), ('Tulsa', 'Oklahoma'), ('Minneapolis', 'Minnesota'), ('Colorado Springs', 'Colorado'), ('Honolulu', 'Hawaii'), ('Arlington', 'Texas')]

city_geo_coords = [[40.714269100000003, -74.005972900000003], [34.052234200000001, -118.24368490000001], [41.850033000000003, -87.650052299999999], [29.763283600000001, -95.363271499999996], [33.448377100000002, -112.0740373], [39.952334999999998, -75.163788999999994], [29.424121899999999, -98.493628200000003], [32.802954999999997, -96.769923000000006], [32.715329199999999, -117.1572551], [37.339385700000001, -121.89495549999999], [42.331426999999998, -83.0457538], [37.774929499999999, -122.4194155], [30.332183799999999, -81.655651000000006], [39.767015999999998, -86.156255000000002], [30.267153, -97.743060799999995], [39.961175500000003, -82.998794200000006], [32.725408999999999, -97.320849600000003], [35.227086900000003, -80.843126699999999], [35.149534299999999, -90.048980099999994], [39.290384799999998, -76.612189299999997], [42.358430800000001, -71.059773199999995], [31.758719800000001, -106.4869314], [43.038902499999999, -87.906473599999998], [39.739153600000002, -104.9847034], [47.606209499999999, -122.3320708], [36.165889900000003, -86.784443199999998], [38.895111800000002, -77.036365799999999], [36.114646, -115.172816], [45.5234515, -122.6762071], [38.254237600000003, -85.759406999999996], [35.467560200000001, -97.5164276], [32.221742900000002, -110.926479], [33.748995399999998, -84.387982399999999], [35.084490899999999, -106.6511367], [39.099726500000003, -94.578566699999996], [36.7477272, -119.7723661], [38.5815719, -121.49439959999999], [33.766962300000003, -118.18923479999999], [33.422268500000001, -111.8226402], [41.254005999999997, -95.999257999999998], [41.499495400000001, -81.695408799999996], [36.8529263, -75.977985000000004], [25.774265700000001, -80.193658900000003], [37.804372200000003, -122.2708026], [35.772095999999998, -78.638614500000003], [36.153981600000002, -95.992774999999995], [44.979965399999998, -93.263836100000006], [38.833881599999998, -104.8213634], [21.306944399999999, -157.8583333], [32.735686999999999, -97.108065600000003]]

ENABLE_GEO_LOOKUP = False



apis = ['MFC', 'Google App Engine', 'OpenGL', 'DirectX', 'YUI']
equipment = ['multimeter', 'cash register']
activities = ['system administration', 'PCB layout']
applications = ['Visual Studio', 'Blender', 'Eclipse', 'AutoCAD', 'git', 'subversion', 'CVS']
# Source: http://www.langpop.com/
# Also see: http://en.wikipedia.org/wiki/List_of_programming_languages_by_category
languages = ['Java', 'C', 'C++', 'PHP', 'JavaScript', 'Python', 'SQL', 'C#', 'Perl', 'Ruby', 'Shell', 'Visual Basic', 'Assembly', 'Actionscript', 'Delphi', 'Objective C', 'Lisp', 'Pascal', 'Fortran', 'ColdFusion', 'Scheme', 'Lua', 'Haskell', 'D', 'Tcl', 'Ada', 'Cobol', 'Erlang', 'Smalltalk', 'Scala', 'OCaml', 'Forth', 'Rexx']

SKILL_CATEGORY_EXAMPLES = {
    feedparser.SKILL_CATEGORY_APIS: apis,
    feedparser.SKILL_CATEGORY_EQUIPMENT: equipment,
    feedparser.SKILL_CATEGORY_DUTIES: activities,
    feedparser.SKILL_CATEGORY_APPLICATIONS: applications,
    feedparser.SKILL_CATEGORY_PROGRAMMING_LANGUAGES: languages
}



subjects = ["automotive", "control systems", "biomedical", "bioinformatics", "genomics", "aerospace", "quality assurance"]


def generateFeed():
	from random import randint, sample, choice, shuffle

	from xml.dom.minidom import Document
	doc = Document()

	root = doc.createElement("jobfeed")
	root.setAttribute("vocabulary", "0.1")
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
	for i, city_tuple in enumerate(most_populous_cities[:randint(10, 20)]):

		site = doc.createElement("site")
		sites.appendChild(site)

		name = doc.createElement("name")
		name.appendChild( doc.createTextNode("Site Name") )
		site.appendChild(name)

		location = doc.createElement("location")
		site.appendChild(location)

		# Give some the address, but for others provide the geo coords directly
		cityname = ", ".join(city_tuple)
		if randint(0, 3):	# 1 in 4 chance that we do not geocode the address
			geo = doc.createElement("geo")
			if ENABLE_GEO_LOOKUP:
				from geocode import getGeo
				for key, val in getGeo( cityname ).items():
					geo.setAttribute(key, "%.4f" % (val))
			else:
				from feedparser import GEO_ATTRIBUTES
				for idx, key in enumerate(GEO_ATTRIBUTES):
					geo.setAttribute(key, "%.4f" % (city_geo_coords[i][idx]))

			location.appendChild(geo)
		else:
			address = doc.createElement("address")
			address.appendChild( doc.createTextNode( cityname ) )
			location.appendChild(address)

		departments = doc.createElement("departments")
		site.appendChild(departments)

		for department_index in range(randint(1, 3)):

			department = doc.createElement("department")
			departments.appendChild(department)

			name = doc.createElement("name")
			name.appendChild( doc.createTextNode("Department Name") )
			department.appendChild(name)


			openings = doc.createElement("openings")
			department.appendChild(openings)

			for job_index in range(randint(2, 8)):

				position = doc.createElement("position")
				openings.appendChild(position)
				position.setAttribute("id", str(jobcounter))
				jobcounter += 1

				from datetime import datetime, timedelta
				position.setAttribute("expires", (datetime.now().date() + timedelta(days=randint(0, 90))).isoformat() )

				if randint(0,2):	# Set the "link" attribute with 2/3 probability
					position.setAttribute("link", "http://www.example.com/")

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


				if randint(0, 1):
					education = doc.createElement("education")
					qualifications.appendChild(education)
					degree = doc.createElement("degree")
					degree.setAttribute("level", choice(feedparser.degreee_levels))
					education.appendChild(degree)


				skills = doc.createElement("skills")
				qualifications.appendChild(skills)

				for skill_classification in ["required", "preferred"]:
					skillbatch = doc.createElement( skill_classification )
					skills.appendChild( skillbatch )

					skill_elements = []

					for key, value in SKILL_CATEGORY_EXAMPLES.items():
						for skillname in sample(value, randint(0, min(2, len(value)))):

							lang = doc.createElement(key)
							lang.setAttribute("name", skillname)
							lang.setAttribute("years", str(randint(0, 10)))
							skill_elements.append(lang)

					shuffle(skill_elements)
					for skill_element in skill_elements:
						skillbatch.appendChild(skill_element)

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
		doc.writexml( open(output_filename, "w"), addindent="\t", newl="\n" )
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
	from feedparser import fetchJobList, dumpJobs
	jobs = fetchJobList( jobfeed_filehandle )
	print len(jobs), "jobs."
	dumpJobs(jobs)

