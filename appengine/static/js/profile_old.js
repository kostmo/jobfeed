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
  function createFormLabelFor(label_id, for_element, text) {
      var label = document.createElement('label');
      label.id = label_id;
      label.setAttribute("for", for_element.id);
      
      label.appendChild( document.createTextNode( text ) );
      return label;
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

      var label = createFormLabelFor("label_checkbox_" + dropdown.value, checkbox, selected_option.text);
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
      var label2 = createFormLabelFor("label_years_" + dropdown.value, years_textbox, " year(s)");
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
  function clearForm() {
    var form = document.forms["load_form"];
    form["load_key"].selectedIndex = -1;
    form.submit();
  }


