/*
Copyright 2009 Roman Nurik

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

var PAGE_PATH = document.location.href.replace(/#.*/, '')
                                      .replace(/\/[^\/]*$/, '/');

var MILES_TO_METERS = 1609.344;

var SCHOOL_TYPES = {
  1: 'Regular elementary or secondary school',
  2: 'Special education school',
  3: 'Vocational/technical school',
  4: 'Other'
};

// Only perform proximity searches on 
// geocode accuracy.
var MIN_PROXIMITY_SEARCH_GEOCODE_ACCURACY = 6;

var MAX_PROXIMITY_SEARCH_MILES = 50;
var MAX_PROXIMITY_SEARCH_RESULTS = 20;
var MAX_BOUNDS_SEARCH_RESULTS = 25;


/**
 * @type google.maps.Map2
 */
var map;

/**
 * @type google.maps.ClientGeocoder
 */
var geocoder;

var g_listView = false; // Whether or not we're in list view.

/**
 * An array of the current search result data objects.
 * Result object properties are:
 *   {Number} lat
 *   {Number} lng
 *   {String} name
 *   {String} icon
 *   {String} site_key
 *   {String} job_key
 *   {google.maps.Marker} marker
 *   {Number} [distance] The distance in meters from the search center.
 *   {jQuery object} listItem The list view item for the result.
 *   ...
 * Along with any other properties returned by the search service.
 */
var g_searchResults = null;

var g_currentSearchXHR = null; // For cancelling current XHRs.
var g_searchOptions = null; // Last options passed to doSearch.
var g_searchCenterMarker = null;

var g_mapAutoScrollInterval = null;
var g_programmaticPanning = false; // Temporary moveend disable switch.
var g_mapPanListener = null;

/**
 * On body/APIs ready callback.
 */
function init() {
  initMap();
  initUI();
}

/**
 * Creates the Google Maps API instance.
 */
function initMap() {
  map = new google.maps.Map2($('#map').get(0));
  map.setCenter(new google.maps.LatLng(39,-96), 4);

  geocoder = new google.maps.ClientGeocoder();
  
  // anything besides default will not work in list view
  map.setUIToDefault();
}








function toggleListViewHelper(toggler) {
    g_programmaticPanning = true;
    var center = map.getCenter();
    
    if (g_listView) {
      $(toggler).html('List view &raquo;');
      $('#content').removeClass('list-view');
      enableSearchOnPan(g_searchOptions != null);
    } else {
      $(toggler).html('&laquo; Map view');
      $('#content').addClass('list-view');
      enableSearchOnPan(false);
    }
    
    g_listView = !g_listView;
    map.checkResize();
    
    enableMapAutoScroll(g_listView);
    
    map.setCenter(center);
    g_programmaticPanning = false;
    return false;
}


function toggleListView() {

    toggleListViewHelper(this);

}




/**
 * Initializes various UI features.
 */
function initUI() {


  
  
  $('#view-toggle a').click(toggleListView);
  
  var advancedOptionsVisible = false;
  
  $('#advanced-options-toggle').click(function() {
    if (advancedOptionsVisible) {
      $('#advanced-options').hide();
    } else {
      $('#advanced-options').show();
    }
    
    advancedOptionsVisible = !advancedOptionsVisible;
    return false;
  });
  
  var resetError = function() {
    $('#search-error').css('visibility', 'hidden');
  };
  
  $('#search-query').change(resetError);
  $('#search-query').keypress(resetError);
}

/**
 * Enables or disables search-on-pan, which performs new queries upon panning
 * of the map.
 * @param {Boolean} enable Set to true to enable, false to disable.
 */
function enableSearchOnPan(enable) {
  if (typeof(enable) == 'undefined')
    enable = true;
  
  if (!enable) {
    if (g_mapPanListener)
      google.maps.Event.removeListener(g_mapPanListener);
    g_mapPanListener = null;
  } else if (!g_mapPanListener) {
    g_mapPanListener = google.maps.Event.addListener(map, 'moveend',
        function() {
          if (g_programmaticPanning ||
              (map.getInfoWindow() && !map.getInfoWindow().isHidden()))
            return;
          
          // Determine whether or not to do a proximity query or
          // a bounds query.
          var bounds = map.getBounds();
          var searchType = 'bounds';
      
          if (g_searchOptions.center &&
              bounds.containsLatLng(g_searchOptions.center))
            searchType = 'proximity';
          
          // On pan, no need to re-do a proximity search.
          if (searchType == 'proximity' &&
              g_searchOptions.type == 'proximity')
            return;
          
          doSearch(updateObject(g_searchOptions, {
            type: searchType,
            bounds: bounds,
            retainViewport: true,
            clearResultsImmediately: false
          }));
        });
  }
}

/**
 * Enables or disables map auto scrolling.
 * @param {Boolean} enable Set to true to enable, false to disable.
 */
function enableMapAutoScroll(enable) {
  if (typeof(enable) == 'undefined')
    enable = true;
  
  if (g_mapAutoScrollInterval) {
    window.clearTimeout(g_mapAutoScrollInterval);
    g_mapAutoScrollInterval = null;
  }

  var mapContainer = $('#map-container');
  var mapContainerOffsetParent = $($('#map-container').get(0).offsetParent)
  
  var TOP_PADDING = 8;

  if (enable) {
    g_mapAutoScrollInterval = window.setInterval(function() {
      var scrollOffset = window.pageYOffset || document.body.scrollTop;
      mapContainer.animate({
        top: Math.max(0, scrollOffset -
                         mapContainerOffsetParent.position().top +
                         TOP_PADDING)
      }, 'fast');
    }, 1000);
  } else {
    mapContainer.css('top', '');
  }
}





function assignSearchOptionsFromUI(commonOptions) {

	// XXX The user may have changed the options since last saving the profile.  Therefore,
	// the "saved_searchable_experience_keys" may be out of date.  To get around this, we
	// will just send the raw label-years pairs as if we were saving the profile.
	if (document.getElementById("checkbox_skill_filter").checked && active_skill_objects.length) {
		var used_keys_dict = compileExperienceDictionary(active_skill_objects);
		commonOptions.experience_dictionary = stringifyDict(used_keys_dict);
	}

	if (document.getElementById("checkbox_keyword_filter").checked && active_keyword_objects.length) {
		var keyword_keys_list = extractKeywordKeys(active_keyword_objects);
		commonOptions.keyword_keylist = keyword_keys_list.join(",");
	}

	var education_dropdown = document.getElementById("education_dropdown");
	if (document.getElementById("checkbox_education_filter").checked && education_dropdown.selectedIndex >= 0) {
		commonOptions.education_level = education_dropdown.value;
	}
	
	var seniority_dropdown = document.getElementById("seniority_dropdown");
	if (document.getElementById("checkbox_seniority_filter").checked && seniority_dropdown.selectedIndex >= 0) {
		commonOptions.seniority_level = seniority_dropdown.value;
	}
	
	var permanence_dropdown = document.getElementById("permanence_dropdown");
	if (document.getElementById("checkbox_permanence_filter").checked && permanence_dropdown.selectedIndex >= 0) {
		commonOptions.permanence_level = permanence_dropdown.value;
	}
	
	// XXX also new:
	commonOptions.sample_search = document.getElementById("checkbox_sample_jobs").checked;
}


function locationAgnosticSearch() {

	var commonOptions = {
		clearResultsImmediately: true
	};
	assignSearchOptionsFromUI(commonOptions);
	doSearch(updateObject(commonOptions, {
		type: 'anywhere'
	}));
}



/**
 * Geocodes the location text in the search box and performs a spatial search
 * via doSearch.
 */
function doGeocodeAndSearch() {

  $('#loading').css('visibility', 'visible');
  geocoder.getLocations($('#search-query').val(), function(response) {
    if (response.Status.code != 200 || !response.Placemark) {
      $('#search-error').text('Location not found.');
      $('#search-error').css('visibility', 'visible');
      $('#loading').css('visibility', 'hidden');
    } else {
      $('#search-query').val(response.Placemark[0].address);
      //alert(response.Placemark[0].AddressDetails.Accuracy);

      var bounds = new google.maps.LatLngBounds(
          new google.maps.LatLng(
            response.Placemark[0].ExtendedData.LatLonBox.south,
            response.Placemark[0].ExtendedData.LatLonBox.west),
          new google.maps.LatLng(
            response.Placemark[0].ExtendedData.LatLonBox.north,
            response.Placemark[0].ExtendedData.LatLonBox.east));

      map.setCenter(bounds.getCenter(), map.getBoundsZoomLevel(bounds));
      
      var proximitySearch = (response.Placemark[0].AddressDetails.Accuracy >=
                             MIN_PROXIMITY_SEARCH_GEOCODE_ACCURACY) || document.getElementById("checkbox_proximity").checked;
      
      var commonOptions = {
        clearResultsImmediately: true
      };
      
      
	assignSearchOptionsFromUI(commonOptions);


      if (proximitySearch) {
        doSearch(updateObject(commonOptions, {
          type: 'proximity',
          centerAddress: response.Placemark[0].address,
          center: bounds.getCenter()
        }));
      } else {
        doSearch(updateObject(commonOptions, {
          type: 'bounds',
          bounds: bounds
        }));
      }
    }
  });
}








function SiteJobs() {
  this.joblist = [];
}

function populateMapResults(options, results, newBounds) {
  
  var listView = $('#list-view');
  
  // A dictionary from Site keys to lists of jobs
  var unique_sites = {}
  for (var i = 0; i < results.length; i++) {
    var result = results[i];


    var resultLatLng = new google.maps.LatLng(result.lat, result.lng);


    if (options.type == 'proximity')
      result.distance = resultLatLng.distanceFrom(options.center);
    
    newBounds.extend(resultLatLng);




    var consolidated_site_jobs;
    if (result.site_key in unique_sites) {
      consolidated_site_jobs = unique_sites[result.site_key];
    } else {
      // First encounter of this Site
      consolidated_site_jobs = new SiteJobs();
      unique_sites[result.site_key] = consolidated_site_jobs;

    }
    consolidated_site_jobs.joblist.push(result);
  }
  

  
  // Go through each unique Site and add it to the map
  var i=0;
  for (var site_key in unique_sites) {
    var joblist = unique_sites[site_key].joblist;
    

	var marker_icon_file = '/static/images/markers/simple.png';
//    if (options.type == 'proximity' && i <= 10) {
    if (i <= 10) {
      marker_icon_file = '/static/images/markers/' +
          String.fromCharCode(65 + i) + '.png';	// Starts lettering at capital 'A'.
    }
    
    
    var map_marker = joblist.length > 1 ? createAggregateResultMarker(joblist, marker_icon_file) : createSingleResultMarker(joblist, marker_icon_file);







    map.addOverlay(map_marker);
    
    
    g_searchResults.push( map_marker );
    
    // Associate result marker.
    for (var j=0; j<joblist.length; j++) {
      var result = joblist[j];
      result.icon = marker_icon_file;
      result.map_marker = map_marker;
      
      // Create result list view item.
      result.listItem = createListViewItem(result);
      listView.append(result.listItem);
    }
    
    i++;
  }
  return unique_sites;
}






/**
 * Performs an asynchronous school search using the search service.
 * @param {Object} options Search options.
 * @param {String} type The type of spatial query to perform; either
 *     'proximity' or 'bounds'.
 * @param {google.maps.LatLng} [center] For proximity searches, the search
 *     center.
 * @param {String} [centerAddress] For proximity searches, an optional address
 *     string representing the search center.
 * @param {google.maps.LatLngBounds} [bounds] For bounds searches, the bounding
 *     box to constrain results to.
 * @param {Boolean} [retainViewport=false] Whether or not to maintain the
 *     map viewport after retrieving search results.
 * @param {Boolean} [clearResultsImmediately=false] Whether or not to clear
 *     search results immediately, as opposed to clearing them only upon a
 *     successful completion of the search.
 */
function doSearch(options) {
  options = options || {};
  
  var oldSearchOptions = g_searchOptions;
  g_searchOptions = options;
  
  if (g_currentSearchXHR && 'abort' in g_currentSearchXHR) {
    g_currentSearchXHR.abort();
  }
  
  $('#search-error').css('visibility', 'hidden');
  $('#loading').css('visibility', 'visible');
  
  if (g_searchCenterMarker) {
    map.removeOverlay(g_searchCenterMarker);
    g_searchCenterMarker = null;
  }
  
  if (options.type == 'proximity') {
    // Set up search center marker.
    var centerIcon = new google.maps.Icon(G_DEFAULT_ICON); 
    centerIcon.image = '/static/images/markers/arrow.png';
    centerIcon.shadow = '/static/images/markers/arrow-shadow.png';
    centerIcon.iconSize = new google.maps.Size(23, 34);
    centerIcon.iconAnchor = new google.maps.Point(11, 34);
  
    g_searchCenterMarker = new google.maps.Marker(options.center, {
      icon: centerIcon,
      draggable: true,
      zIndexProcess: function(){ return 1000; }
    });
  
    google.maps.Event.addListener(g_searchCenterMarker, 'dragend', function() {
      // Perform a new search but persist some old parameters.
      doSearch(updateObject(g_searchOptions, {
        type: 'proximity',
        centerAddress: '', // TODO: reverse geocode?
        center: g_searchCenterMarker.getLatLng(),
        retainViewport: true,
        clearResultsImmediately: false
      }));
    });
  
    map.addOverlay(g_searchCenterMarker);
  }
  
  var newBounds = new google.maps.LatLngBounds(
      options.type == 'proximity' ? options.center : null);
  
  
  if (options.clearResultsImmediately)
    clearSearchResults();
  
  $('#list-view-status').html('Searching...');
  
  var searchParameters = {
    type: options.type
  };
  
  var miles_input_field = document.getElementById("miles_input");
  if (options.type == 'proximity') {
    searchParameters = updateObject(searchParameters, {
      lat: options.center.lat(),
      lon: options.center.lng(),
      maxresults: MAX_PROXIMITY_SEARCH_RESULTS,
      maxdistance: (miles_input_field.value ? parseInt(miles_input_field.value) : MAX_PROXIMITY_SEARCH_MILES) * MILES_TO_METERS
    });
  } else if (options.type == 'bounds') {
    searchParameters = updateObject(searchParameters, {
      north: options.bounds.getNorthEast().lat(),
      east: options.bounds.getNorthEast().lng(),
      south: options.bounds.getSouthWest().lat(),
      west: options.bounds.getSouthWest().lng(),
      maxresults: MAX_BOUNDS_SEARCH_RESULTS
    });
  }
  
  // Add in advanced options.
  if (options.experience_dictionary) {
    searchParameters.experience_dictionary = options.experience_dictionary;
  }

  if (options.keyword_keylist) {
    searchParameters.keyword_keylist = options.keyword_keylist;
  }

  if (options.education_level) {
    searchParameters.education_level = options.education_level;
  }

  if (options.permanence_level) {
    searchParameters.permanence_level = options.permanence_level;
  }  

  if (options.seniority_level) {
    searchParameters.seniority_level = options.seniority_level;
  }  

  if (options.sample_search) {
    searchParameters.sample_search = options.sample_search;
  }
  
  // Perform proximity or bounds search.
  g_currentSearchXHR = $.ajax({
    url: '/s/search',
    type: 'get',
    data: searchParameters,
    dataType: 'json',
    error: function(xhr, textStatus) {
      // TODO: parse JSON instead of eval'ing
      var responseObj;
      eval('responseObj=' + xhr.responseText);
      $('#search-error, #list-view-status').text(
          'Internal error: ' + responseObj.error.message);
      $('#search-error').css('visibility', 'visible');
      $('#loading').css('visibility', 'hidden');
    },
    success: function(obj) {
      g_currentSearchXHR = null;
      
      $('#loading').css({ visibility: 'hidden' });
      
      if (!options.clearResultsImmediately)
        clearSearchResults();
      
      if (obj.status && obj.status == 'success') {
        
        var unique_sites = populateMapResults(options, obj.results, newBounds);
        
        if (newBounds.getNorthEast() &&
            !newBounds.getNorthEast().equals(newBounds.getSouthWest()) &&
            !options.retainViewport &&
            obj.results.length) {
          g_programmaticPanning = true;
          map.panTo(newBounds.getCenter());
          map.setZoom(map.getBoundsZoomLevel(newBounds));
          g_programmaticPanning = false;
        }

        if (!obj.results.length) {
          $('#search-error, #list-view-status').text(
              (options.type == 'proximity')
                ? 'No results within ' + (options.maxdistance / MILES_TO_METERS) + ' miles.'
                : 'No results in view.');
          $('#search-error').css('visibility', 'visible');
        } else {
          $('#list-view-status').html(
              'Found ' + obj.results.length + ' jobs(s) at ' + getAssocArrayLength(unique_sites) + ' site(s)' +
              (options.centerAddress
                ? ' near ' + options.centerAddress + ':'
                : ':'));
        }
      } else {
        $('#search-error, #list-view-status').text(
            'Internal error: ' + obj.error.message);
        $('#search-error').css('visibility', 'visible');
      }
    }
  });
  
  enableSearchOnPan();
}

/**
 * Clears search results from memory, the list view, and the map view.
 */
function clearSearchResults() {
  if (g_searchResults) {
    $('#list-view').html('');
    $('#list-view-status').text('Enter a search location to ' +
                                'search for nearby jobs.');
    for (var i = 0; i < g_searchResults.length; i++) {
      map.removeOverlay( g_searchResults[i] );
    }
  }
  
  g_searchResults = [];
}








function createAggregateBubbleDomTree(results, representative) {

      var bubble = document.createElement('span');
      bubble.appendChild( document.createTextNode( "There are " + results.length + " jobs at this site." ) );

      var expand_link = document.createElement('a');
      expand_link.setAttribute("href", "javascript:");
      expand_link.appendChild( document.createTextNode( "see all" ) );
      
      var footnote = document.createElement('p');
      footnote.appendChild( expand_link );
      bubble.appendChild( footnote );


	expand_link.onclick = function() {scrollToListItem(representative);}; 


	return bubble;
}




/**
 * Creates an aggregate search result marker from the given result objects.
 * @param {Object} result The search result data object.
 * @type google.maps.Marker
 */
function createAggregateResultMarker(results, marker_icon_file) {
  
  // The first of the results will be delegated as the "representative".
  var representative = results[0];
  
  var icon = new google.maps.Icon(G_DEFAULT_ICON);
  icon.image = marker_icon_file;
  icon.iconSize = new google.maps.Size(21, 34);
  
  var resultLatLng = new google.maps.LatLng(representative.lat, representative.lng);
  
  var marker = new google.maps.Marker(resultLatLng, {
    icon: icon,
    title: representative.title + " (" + (results.length - 1) + " more)"
  });
  
//  alert("Result count for this marker: " + results.length);
  
  google.maps.Event.addListener(marker, 'click', (function(representative) {
    return function() {
      if (g_listView && representative.listItem) {
        $.scrollTo(representative.listItem, {duration: 1000});
      } else {
      
      //        var infoHtml = tmpl('tpl_result_info_window', { result: result });
        var node = createAggregateBubbleDomTree(results, representative);
//        var infoHtml = tmpl('tpl_result_info_window', { result: representative });
        
        map.openInfoWindow(marker.getLatLng(), node, {
          pixelOffset: new GSize(icon.infoWindowAnchor.x - icon.iconAnchor.x,
                                 icon.infoWindowAnchor.y - icon.iconAnchor.y)});
      }
    };
  })(representative));
  
  return marker;
}











function createResultBubbleDomTree(representative) {

      var bubble = document.createElement('span');

      var table = document.createElement('table');
      table.setAttribute("class", "bubble_job_table");
      bubble.appendChild( table );
      {
            var row = document.createElement('tr');
      table.appendChild( row );
      var header = document.createElement('th');
      header.setAttribute("colspan", "2");
      row.appendChild( header );
      
      var title_textnode = document.createTextNode( representative.title );
      if (representative.link) {
      	header.appendChild( title_textnode );
      } else {
      var job_link = document.createElement('a');
      job_link.setAttribute("href", representative.link);
      header.appendChild( job_link );
      }
      

      var org_link = document.createElement('a');
      }
      
      {
      var row = document.createElement('tr');
      table.appendChild( row );
      var header = document.createElement('th');
      row.appendChild( header );
      header.appendChild( document.createTextNode( "Employer:" ) );
      var header2 = document.createElement('td');
      row.appendChild( header2 );
      header2.appendChild( document.createTextNode( representative.orgname ) );
      var sup = document.createElement('sup');
      var org_link = document.createElement('a');
      sup.appendChild( org_link );
      org_link.appendChild( document.createTextNode( "?" ) );
      org_link.setAttribute("href", "/orgjobs?job_key=" + representative.job_key);
      header2.appendChild( sup );
      }







      var expand_link = document.createElement('a');
      expand_link.setAttribute("href", "javascript:");
      expand_link.appendChild( document.createTextNode( "details" ) );
      
      var footnote = document.createElement('p');
      footnote.appendChild( expand_link );
      bubble.appendChild( footnote );

	expand_link.onclick = function() {scrollToListItem(representative);}; 


	return bubble;
}


/**
 * Creates an aggregate search result marker from the given result objects.
 * @param {Object} result The search result data object.
 * @type google.maps.Marker
 */
function createSingleResultMarker(results, marker_icon_file) {
  
  // The first of the results will be delegated as the "representative".
  var representative = results[0];
  
  var icon = new google.maps.Icon(G_DEFAULT_ICON);
  icon.image = marker_icon_file;
  icon.iconSize = new google.maps.Size(21, 34);
  
  var resultLatLng = new google.maps.LatLng(representative.lat, representative.lng);
  
  var marker = new google.maps.Marker(resultLatLng, {
    icon: icon,
    title: representative.title + " (" + (results.length - 1) + " more)"
  });
  
//  alert("Result count for this marker: " + results.length);
  
  google.maps.Event.addListener(marker, 'click', (function(representative) {
    return function() {
      if (g_listView && representative.listItem) {
        $.scrollTo(representative.listItem, {duration: 1000});
      } else {
      
      //        var infoHtml = tmpl('tpl_result_info_window', { result: result });
        var node = createResultBubbleDomTree(representative);
//        var infoHtml = tmpl('tpl_result_info_window', { result: representative });
        
        map.openInfoWindow(marker.getLatLng(), node, {
          pixelOffset: new GSize(icon.infoWindowAnchor.x - icon.iconAnchor.x,
                                 icon.infoWindowAnchor.y - icon.iconAnchor.y)});
      }
    };
  })(representative));
  
  return marker;
}


















/**
 * Creates a list view item from the given result object.
 * @param {Object} result The search result data object.
 * @type jQuery object
 */
function createListViewItem(result) {
  var item = $('<li class="result">');
  item.html(tmpl('tpl_result_list_item', { result: result }));
  return item;
}

/**
 * Helper method to update one object's properties with another's.
 */
function updateObject(dest, src) {
  dest = dest || {};
  src = src || {};
  
  for (var k in src)
    dest[k] = src[k];
  
  return dest;
}


/**
 * Formats a distance in meters to a human readable distance in miles.
 * @param {Number} distance The distance in meters.
 * @type String
 */
function formatDistance(distance) {
  return (distance / MILES_TO_METERS).toFixed(1) + ' mi';
}
