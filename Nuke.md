Sometimes when developing a new App Engine app, you want to start fresh with the datastore, wiping everything. Unfortunately, this can be a cumbersome process with the existing interface.

**Nuke** is a "add-in" to the admin panel that lets you delete all entities of a _specific kind_, or all entities of _all kinds_ with a button click.

![http://jobfeed.googlecode.com/svn/screenshots/nuke_torn.png](http://jobfeed.googlecode.com/svn/screenshots/nuke_torn.png)

  1. Copy [bulkupdate](http://github.com/arachnid/bulkupdate) into your application's root directory:
```
git clone git://github.com/Arachnid/bulkupdate.git
```
  1. Copy `nuke` into your application's root directory:
```
svn export http://jobfeed.googlecode.com/svn/trunk/appengine/nuke
```
  1. Modify your app.yaml to include the following (this will install both **nuke** and **bulkupdate**):
```
admin_console:
  pages:
  - name: Bulk Update Jobs
    url: /_ah/bulkupdate/admin/

  - name: Nuke
    url: /_ah/nuke/

handlers:
- url: /_ah/queue/deferred
  script: $PYTHON_LIB/google/appengine/ext/deferred/handler.py
  login: admin
  
- url: /_ah/bulkupdate/admin/.*
  script: bulkupdate/handler.py
  login: admin

- url: /_ah/nuke/.*
  script: nuke/nuke.py
  login: admin
```
  1. Redeploy your application
```
appcfg.py update .
```
  1. Nuke your datastore
    * **Nuke** expects all of your models to be defined in a file named `models.py` ([example](http://code.google.com/p/jobfeed/source/browse/trunk/appengine/models.py)) in your root application directory. If this is not the case, you may edit the [nuke.py](http://code.google.com/p/jobfeed/source/browse/trunk/appengine/nuke/nuke.py) script as desired.