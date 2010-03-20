#!/usr/bin/python

#!/usr/bin/python2.5
#
# Copyright 2010 Karl Ostmo
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from lxml import etree

JOBFEED_SCHEMA_URL = "http://localhost:8080/static/jobfeed.xml"

def doValidation(document_filehandle, schema_url=JOBFEED_SCHEMA_URL):
    from urllib import urlopen

    relaxng_doc = etree.parse( urlopen( schema_url ) )
    relaxng = etree.RelaxNG( relaxng_doc )

    jobs_doc = etree.parse( document_filehandle )
    print "Is valid?", relaxng.validate( jobs_doc )

    from lxml.etree import DocumentInvalid
    try:
        relaxng.assertValid( jobs_doc )
    except DocumentInvalid, e:
        return e

# =============================================================================
if __name__ == '__main__':

    import sys
    document_url = 'http://localhost:8080/static/example_joblist.xml'
    if len(sys.argv) > 1:
        document_url = sys.argv[1]

    schema_url = JOBFEED_SCHEMA_URL
    if len(sys.argv) > 2:
        schema_url = sys.argv[2]


    from urlparse import urlsplit
    parsed_url = urlsplit(document_url)
    print "Host:", parsed_url.hostname

    from urllib import urlopen
    doValidation( urlopen( document_url ), schema_url )
