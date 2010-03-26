/*
Copyright 2010 Karl Ostmo

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

  
  // ==========================================================================

  var SKILL_DROPDOWN_PREFIX = "dropdown_";
  
  // ==========================================================================  
  String.prototype.startsWith = function(str)
{return (this.match("^"+str)==str)}
    
  String.prototype.endsWith = function(str)
{return (this.match(str+"$")==str)}
  

  // ==========================================================================
  // For "index.html"
  // ==========================================================================
  // ==========================================================================
  // ==========================================================================


var saved_searchable_experience_keys = [];


function parseSkills(skill_keys_string, parent) {

  var skill_keys = eval( "(" + skill_keys_string + ")" );

  var categorized_skills = skill_keys["categorized_skills"];
  generateSkillsTable(categorized_skills, parent);


  var keyword_list = skill_keys["keyword_list"];


  // FIXME Crawl up the DOM tree until our parent is a <table>
/*
  var realparent = parent;
  while (realparent && realparent.nodeName != "table") {
    realparent = realparent.parentNode;
  }
*/
  var realparent = parent.parentNode.parentNode.parentNode;	// must go up through a <td>, a <tr>, and a <table>

  var spans = realparent.getElementsByTagName("span");
  for (var i=0; i<spans.length; i++) {
    var target_span = spans[i];
    if (target_span.getAttribute("class") == "keyword_container") {
      target_span.innerHTML = keyword_list.join(", ");
    }
  }
}

// =============================================================================
function parseSkills2(skill_keys_string, parent) {

  if (!skill_keys_string) return;
  var skill_keys = eval( "(" + skill_keys_string + ")" );

//  var searchable_skill_keys = skill_keys["searchable_skill_keys"];
  var searchable_skill_keys = skill_keys["experience_keys"];
  saved_searchable_experience_keys = searchable_skill_keys;  // Make a global copy for later use

  var categorized_skills = skill_keys["categorized_skills"];
  generateSkillsTable(categorized_skills, parent);
}

// =============================================================================
function populateProfile(skill_keys_string) {

	if (!skill_keys_string) return;
	var skill_keys = eval( "(" + skill_keys_string + ")" );

	//  var searchable_skill_keys = skill_keys["searchable_skill_keys"];
	var searchable_skill_keys = skill_keys["experience_keys"];
	saved_searchable_experience_keys = searchable_skill_keys;  // Make a global copy for later use


	// Clear the array
//	active_skill_objects = [];	// XXX This way is BAD; we must not destroy our old references!
//	while (active_skill_objects.length) active_skill_objects.pop();	// XXX This way is inefficient!
	active_skill_objects.length = 0;

	var categorized_skills = skill_keys["categorized_skills"];
	for (var category in categorized_skills) {
		var category_dict = categorized_skills[category];
		for (var i=0; i<category_dict.length; i++) {
			var triple = category_dict[i];
			var label = triple[0];
			var years = triple[1];
			var key = triple[2];

			var skill_object = new SkillObject(label, key);
			skill_object.years = years;
			active_skill_objects.push( skill_object );
		}
	}

	var skills_table = document.getElementById("pending_skills_list");
	regenerateExperienceTable(active_skill_objects, skills_table);




	// Clear the array without creating a new reference
	active_keyword_objects.length = 0;
	
	var keyword_list = skill_keys["keyword_list"];
	for (var i=0; i<keyword_list.length; i++) {
		var tuple = keyword_list[i];
		active_keyword_objects.push( new KeywordObject(tuple[0], tuple[1]) );
	}

	var keywords_table = document.getElementById("pending_keywords_list");
	regenerateKeywordsTable(active_keyword_objects, keywords_table);
}

// =============================================================================
function generateSkillsTable(categorized_skills, parent) {

  removeChildren(parent);
  
  var table = document.createElement("table");
  table.style.borderSpacing = "10px 0px";
  table.style.borderCollapse = "separate";
  table.setAttribute("class", "skills_table");
  var row = document.createElement("tr");
  table.appendChild(row);
  var header1 = document.createElement("th");
  header1.setAttribute("class", "underlined");
  row.appendChild(header1);
  header1.appendChild(document.createTextNode("Experience"));
  var header2 = document.createElement("th");
  header2.setAttribute("class", "underlined");
  row.appendChild(header2);
  header2.appendChild(document.createTextNode("Years"));
  
  parent.appendChild(table);
  for (var category in categorized_skills) {

    var table_row = document.createElement("tr");
    table.appendChild(table_row);
    var table_header = document.createElement("th");
    table_header.colSpan = "2";
    table_row.appendChild(table_header);
    table_header.appendChild(document.createTextNode(category));
    
    var category_dict = categorized_skills[category];
    
    for (var i=0; i<category_dict.length; i++) {
      var pair = category_dict[i];
     
      var table_row2 = document.createElement("tr");
      table_row2.setAttribute("class", i % 2 ? "even" : "odd");
      table.appendChild(table_row2);
      var table_data1 = document.createElement("td");
      table_row2.appendChild(table_data1);
      table_data1.appendChild(document.createTextNode(pair[0]));
      var table_data2 = document.createElement("td");
      table_row2.appendChild(table_data2);
      table_data2.appendChild(document.createTextNode(yearRange(pair[1])));
    }
  }
}

// ============================================================================
function loadJobExperience2(job_key) {
   ajaxGet( "/jobdata?job_posting_key=" + job_key, "", function(x) {parseSkills(x, document.getElementById("skills_list_item_" + job_key))} );
}

// ============================================================================
function loadJobExperience(job_key) {
   ajaxGet( "/jobdata?job_posting_key=" + job_key, "", function(x) {parseSkills(x, document.getElementById("skills_bubble_" + job_key))} );
}

// ============================================================================
function pickNewProfile(select_form_element) {
   ajaxGet( "/profiledata?load_key=" + select_form_element.value, "", function(x) {parseSkills2(x, document.getElementById("experience_table_holder"))} );
}

// ============================================================================
function pickNewProfileAdvanced(select_form_element) {
   ajaxGet( "/profiledata?load_key=" + select_form_element.value, "", populateProfile );
}

// AJAX Stuff
// ============================================================================
var pending_transaction_count = 0;

function get_ajax_handle() {

	var http;
	// Mozilla/Safari
	if (window.XMLHttpRequest)
		http = new XMLHttpRequest();
	// IE
	else if (window.ActiveXObject)
		http = new ActiveXObject("Microsoft.XMLHTTP");

	return http;
}

// ============================================================================
function ajaxGet( url, params, result_function ) {

	var http = get_ajax_handle();

	http.open("GET", url, true);

	//Send the proper header information along with the request
	http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	http.setRequestHeader("Content-length", params.length);
	http.setRequestHeader("Connection", "close");

	http.onreadystatechange = function () {	//Call a function when the state changes.
		if (http.readyState == 4 && http.status == 200) {

			var status_bar = document.getElementById("status_bar");
            status_bar.innerHTML = ""

			result_function( http.responseText );

			pending_transaction_count--;
		}
	}

    var status_bar = document.getElementById("status_bar");
    status_bar.innerHTML = "working..."
	pending_transaction_count++;
	http.send(params);
}


// ============================================================================
function ajaxPost( url, params ) {

	var http = get_ajax_handle();

	http.open("POST", url, true);

	//Send the proper header information along with the request
	http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	http.setRequestHeader("Content-length", params.length);
	http.setRequestHeader("Connection", "close");

	http.onreadystatechange = function () {	//Call a function when the state changes.
		if (http.readyState == 4 && http.status == 200) {

			var status_bar = document.getElementById("status_bar");

//			status_bar.innerHTML += http.responseText;
			status_bar.innerHTML = http.responseText;

			pending_transaction_count--;
		}
	}


	pending_transaction_count++;
	http.send(params);
}

// ============================================================================
  function beautifyTable(table) {

    // If there are no <td> elements, clear the table (that means remove the headers, also).
    if (!table.getElementsByTagName("td").length) {
      removeChildren(table);
      return;
    }

    var rows = table.getElementsByTagName("tr")
    var index = 0;
    for (var i=0; i<rows.length; i++) {

      element = rows[i];
      if (element.getElementsByTagName("th").length) {
        index = 0;
        continue;
      }

      element.setAttribute("class", index % 2 ? "odd" : "even");
      index++;
    }
  }

// ============================================================================
  function makeSkillListItem(skill_object, skills_table, index) {

      var row = document.createElement('tr');
      row.setAttribute("class", index % 2 ? "odd" : "even");
      var data = document.createElement('td');
      row.appendChild(data);

//      data.style.verticalAlign = "middle"; // doesn't work?

      data.appendChild( document.createTextNode( skill_object.label ) );
      

	
	var populated_years = skill_object.years != null ? skill_object.years : document.getElementById("experience_years_textbox").value;

      var years_textbox = document.createElement('input');
      skill_object.years_textbox = years_textbox;
      years_textbox.id = "years_textbox_" + skill_object.key;
      years_textbox.onkeypress = function(event){return disableEnterKey(event);};
      years_textbox.type = "text";
      years_textbox.size = "1";
      years_textbox.maxLength = "2";
      years_textbox.value = populated_years ? populated_years : "0";
      years_textbox.onchange = function(){validateYearsTextbox(this);};  // register input validator
      years_textbox.style.verticalAlign = "middle"; // This works!
      
      var data2 = document.createElement('td');
      row.appendChild(data2);
      data2.appendChild(years_textbox);



      var delete_icon = document.createElement('img');
      delete_icon.style.verticalAlign = "middle"; // This works!
      delete_icon.setAttribute("src", "/static/images/delete_x.gif");
      delete_icon.onclick = function() {skills_table.removeChild(row); active_skill_objects.splice(active_skill_objects.indexOf(skill_object), 1); beautifyTable(skills_table);};

      var data3 = document.createElement('td');
      row.appendChild(data3);
      data3.appendChild( delete_icon );

      skills_table.appendChild( row );
  }


// ============================================================================
  function makeKeywordListItem(keyword_object, keywords_table, index) {

      var row = document.createElement('tr');
      row.setAttribute("class", index % 2 ? "odd" : "even");
      var data = document.createElement('td');
      row.appendChild(data);
//      data.style.verticalAlign = "middle"; // doesn't work?
      data.appendChild(document.createTextNode( keyword_object.label ));


      var delete_icon = document.createElement('img');
      delete_icon.style.verticalAlign = "middle"; // This works!
      delete_icon.setAttribute("src", "/static/images/delete_x.gif");
      delete_icon.onclick = function() {keywords_table.removeChild(row); active_keyword_objects.splice(active_keyword_objects.indexOf(keyword_object), 1); beautifyTable(keywords_table);};


      var data2 = document.createElement('td');
      row.appendChild(data2);
//      data.style.verticalAlign = "middle"; // doesn't work?
      data2.appendChild(delete_icon);



      keywords_table.appendChild( row );
  }


  
