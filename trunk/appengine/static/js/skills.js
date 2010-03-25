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


var saved_skill_keys = {};


function parseSkills(skill_keys_string, parent) {

  var skill_keys = eval( "(" + skill_keys_string + ")" );

  var readable_skills = skill_keys["readable_skills"];
  generateSkillsTable(readable_skills, parent);
}

  // ==========================================================================
function parseSkills2(skill_keys_string, parent) {

  if (!skill_keys_string) return;
  var skill_keys = eval( "(" + skill_keys_string + ")" );

//  var searchable_skill_keys = skill_keys["searchable_skill_keys"];
  var searchable_skill_keys = skill_keys["raw_search_keys"];
  saved_skill_keys = searchable_skill_keys;  // Make a global copy for later use

  var readable_skills = skill_keys["readable_skills"];
  generateSkillsTable(readable_skills, parent);
}

  // ==========================================================================
function generateSkillsTable(readable_skills, parent) {

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
  header1.appendChild(document.createTextNode("Skill"));
  var header2 = document.createElement("th");
  header2.setAttribute("class", "underlined");
  row.appendChild(header2);
  header2.appendChild(document.createTextNode("Years"));
  
  parent.appendChild(table);
  for (var category in readable_skills) {

    var table_row = document.createElement("tr");
    table.appendChild(table_row);
    var table_header = document.createElement("th");
    table_header.colSpan = "2";
    table_row.appendChild(table_header);
    table_header.appendChild(document.createTextNode(category));
    
    var category_dict = readable_skills[category];
    
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



  function makeSkillListItem(skill_object, skills_table) {


      var row = document.createElement('tr');
//      row.id = "item_" + keyword_object.key;
      var data = document.createElement('td');
      row.appendChild(data);

//      data.style.verticalAlign = "middle"; // doesn't work?

      data.appendChild( document.createTextNode( skill_object.label ) );
      

	var populated_years = document.getElementById("experience_years_textbox").value;

      var years_textbox = document.createElement('input');
      years_textbox.id = "years_textbox_" + skill_object.key;
      years_textbox.onkeypress = function(event){return disableEnterKey(event);};
      years_textbox.type = "text";
      years_textbox.size = "1";
      years_textbox.maxLength = "2";
      years_textbox.value = populated_years ? populated_years : "1";
      years_textbox.onchange = function(){validateYearsTextbox(this);};  // register input validator
      years_textbox.style.verticalAlign = "middle"; // This works!
      
      var data2 = document.createElement('td');
      row.appendChild(data2);
      data2.appendChild(years_textbox);



      var delete_icon = document.createElement('img');
      delete_icon.style.verticalAlign = "middle"; // This works!
      delete_icon.setAttribute("src", "/static/images/delete_x.gif");
      delete_icon.onclick = function() {skills_table.removeChild(row); active_skill_objects.splice(active_skill_objects.indexOf(skill_object), 1);};

      var data3 = document.createElement('td');
      row.appendChild(data3);
      data3.appendChild( delete_icon );

      skills_table.appendChild( row );
  }


  function makeKeywordListItem(keyword_object, keywords_table) {

      var row = document.createElement('tr');
//      row.id = "item_" + keyword_object.key;
      var data = document.createElement('td');
      row.appendChild(data);
//      data.style.verticalAlign = "middle"; // doesn't work?
      data.appendChild(document.createTextNode( keyword_object.label ));


      var delete_icon = document.createElement('img');
      delete_icon.style.verticalAlign = "middle"; // This works!
      delete_icon.setAttribute("src", "/static/images/delete_x.gif");
      delete_icon.onclick = function() {keywords_table.removeChild(row); active_keyword_objects.splice(active_keyword_objects.indexOf(keyword_object), 1);};


      var data2 = document.createElement('td');
      row.appendChild(data2);
//      data.style.verticalAlign = "middle"; // doesn't work?
      data2.appendChild(delete_icon);



      keywords_table.appendChild( row );
  }


  // ==========================================================================
  // For "profile.html"
  // ==========================================================================
  // ==========================================================================
  // ==========================================================================  
  function clickAddSkill(category) {
    var dropdown = document.getElementById(SKILL_DROPDOWN_PREFIX + category);

    if (dropdown.selectedIndex >= 0) {
      var selected_option = dropdown.options[dropdown.selectedIndex];
      markUsed(category, dropdown, selected_option, dropdown.value);
      
      updateUsedCount();
    }
  }

  // ==========================================================================  
  function yearRange(years) {

    var idx = years_bins.indexOf(years);
    var suffix = idx < years_bins.length - 1 ? "-" + years_bins[idx+1] : "+";
    return years + suffix;
  }

  // ==========================================================================  
  function removeChildren(cell) {
    while(cell.hasChildNodes()) cell.removeChild(cell.firstChild);
  }
  
  // ==========================================================================  
  function updateUsedCount() {
     var checkboxes = []
     var inputs = document.getElementsByTagName("input");
     for (var key in inputs) {
      if (inputs[key].type == "checkbox") checkboxes.push(inputs[key]);
     }
     
     document.getElementById("checkbox_counter").innerHTML = "" + checkboxes.length;
  }
  
  // ==========================================================================  
  function removeCheckedSkills(category) {
    var dropdown = document.getElementById(SKILL_DROPDOWN_PREFIX + category);
    var table = document.getElementById("table_" + category);

    var children = table.getElementsByTagName("input");
    var removable = []
    for (var child_key in children) {
      var child = children[child_key];

      if (child && child.type == "checkbox") {
        if (child.checked) {

          var label = document.getElementById("label_checkbox_" + child.value);

          var option = document.createElement('option');
          option.text = label.firstChild.nodeValue;
          option.value = child.value;
          dropdown.appendChild( option )
          
          var row = document.getElementById("row_" + child.value);
          removable.push(row)
        }
      }
    }
    
    for (var key in removable) table.removeChild(removable[key]);
    
    updateUsedCount();
  }

  // ==========================================================================  
  function findDropdownOptionIndexForLabel(dropdown, value) {
    return findDropdownOptionIndexFor(dropdown, value, "text");
  }

  // ==========================================================================  
  function findDropdownOptionIndexForValue(dropdown, value) {
    return findDropdownOptionIndexFor(dropdown, value, "value");
  }
  
  // ==========================================================================  
  function findDropdownOptionIndexFor(dropdown, value, attribute) {
    for (var i=0; i<dropdown.options.length; i++) {
      var option = dropdown.options[i];
      if (option[attribute] == value) return i;
    }
    return -1;
  }
  
  // ==========================================================================
  function formLabelFor(label_id, for_element, text) {
      var label = document.createElement('label');
      label.id = label_id;
      label.setAttribute("for", for_element.id);
      
      label.appendChild( document.createTextNode( text ) );
      return label;
  }
  
  // ==========================================================================
  function getHighestBucketWithAtMost(years) {
    
    last_bucket = years_bins[0];
    for (var i=0; i<years_bins.length; i++) {
        if (years_bins[i] > years) {
            return last_bucket;
        }
        last_bucket = years_bins[i];
    }
    return last_bucket;
  }

  // ==========================================================================
  function validateYearsTextbox(x) {
    x.value = (x.value.length > 0 ? getHighestBucketWithAtMost(parseInt(x.value)) : -1); return false;
  }
  
  // ==========================================================================
  function markUsed(category, dropdown, selected_option, keystring, populated_years) {
    
      var table = document.getElementById("table_" + category);
      var row = document.createElement('tr');
      row.id = "row_" + keystring;
      table.appendChild(row);
      var data = document.createElement('td');
      data.style.verticalAlign="middle"; // doesn't work?
      row.appendChild(data);
      var checkbox = document.createElement('input');
      checkbox.type = "checkbox";
      checkbox.value = keystring;
      checkbox.id = "checkbox_skill_" + keystring;
     
      data.appendChild(checkbox);

      var label = formLabelFor("label_checkbox_" + dropdown.value, checkbox, selected_option.text);
      data.appendChild(label)
      
      data.appendChild(document.createTextNode( " " ))  // spacer
      
      var years_textbox = document.createElement('input');
      years_textbox.id = "years_textbox_" + dropdown.value;
      years_textbox.onkeypress = function(event){return disableEnterKey(event);};
      years_textbox.type = "text";
      years_textbox.size = "1";
      years_textbox.maxLength = "2";
      years_textbox.value = populated_years ? populated_years : "1";
      years_textbox.onchange = function(){validateYearsTextbox(this);};  // register input validator
      
      data.appendChild(years_textbox);
      var label2 = formLabelFor("label_years_" + dropdown.value, years_textbox, " year(s)");
      data.appendChild(label2)
      
      dropdown.removeChild(selected_option);
  }
  
  // ==========================================================================
  function findUsed(keystring, years) {
    
    var dropdowns = document.forms["save_form"].getElementsByTagName("select");
    for (var key in dropdowns) {
      var dropdown = dropdowns[key];
      if (dropdown.id && dropdown.id.startsWith(SKILL_DROPDOWN_PREFIX)) {
        var category = dropdown.id.substr(SKILL_DROPDOWN_PREFIX.length);
        var found_index = findDropdownOptionIndexForValue(dropdown, keystring);
        if (found_index >= 0) {
          var option = dropdown.options[found_index];
          markUsed(category, dropdown, option, keystring, years);
        }
      }
    }
  }
  
  // ==========================================================================
  function loadSearch() {
    for (var key in loaded_skills) {
      findUsed(key, "" + loaded_skills[key]);
    }
  }

  // ==========================================================================
  function getUsedKeys(form) {
        var children = form.getElementsByTagName("input");
    
    var filtered = {};
    for (var key in children) {
      if (children[key].type == "checkbox" && children[key].id.startsWith("checkbox_skill_")) {
        
        var years_textbox = document.getElementById("years_textbox_" + children[key].value);
        var years = parseInt(years_textbox.value);
        
        filtered[ children[key].value ] = years;
      }
    }
    
    return filtered;
  }

  // ==========================================================================
  function stringifyDict(dict) {
    var joined_keyvals = [];
    for (var key in dict) {
      joined_keyvals.push( key + ":" + dict[key]);
    }
    return joined_keyvals.join(";");
  }
  
  // ==========================================================================
  function saveSearch(form) {
    // Populate form values before submitting
    var used_keys_dict = getUsedKeys(form);
//    form["skill_keys"].value = used_keys_dict.join(",");
    form["skill_keys"].value = stringifyDict(used_keys_dict);
    
    var dropdown = document.forms["load_form"]["load_key"];
    var name = form["saved_name"].value;
    if (findDropdownOptionIndexForLabel(dropdown, name) >= 0) {
      return confirm("Name \"" + name + "\" is taken. Continue anyway?");
    }

    return true;
  }
  
  // ==========================================================================
  function deleteSaved() {
    
    var form = document.forms["load_form"];
    
    var dropdown = form["load_key"];
    if (dropdown.selectedIndex >= 0) {
      var selected_option = dropdown.options[dropdown.selectedIndex]
      var key = selected_option.value;
      var name = selected_option.text;
      if (confirm("Delete \"" + name + "\"?")) {
        form["deleting"].value = "true";
        form.submit();
      }
    }
  }

  // ==========================================================================
  function clearForm() {
    var form = document.forms["load_form"];
    form["load_key"].selectedIndex = -1;
    form.submit();
  }
  
  
  
  
  
  
  
  
  

  // ==========================================================================
  
  function disableEnterKey(e)
{
     var key;

     if(window.event)
          key = window.event.keyCode;     //IE
     else
          key = e.which;     //firefox

     if(key == 13)
          return false;
     else
          return true;
}
  
