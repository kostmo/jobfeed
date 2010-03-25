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
  function stringifyDict(dict) {
    var joined_keyvals = [];
    for (var key in dict) {
      joined_keyvals.push( key + ":" + dict[key]);
    }
    return joined_keyvals.join(";");
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
