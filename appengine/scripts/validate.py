#!/usr/bin/python

from lxml import etree

JOBFEED_SCHEMA_URL = "http://localhost:8080/static/jobfeed.xml"

def doValidation(document_url, schema_url=JOBFEED_SCHEMA_URL):
    from urllib import urlopen

    relaxng_doc = etree.parse( urlopen( schema_url ) )
    relaxng = etree.RelaxNG( relaxng_doc )

    jobs_doc = etree.parse( urlopen( document_url ) )
#       print "Is valid?", relaxng.validate( jobs_doc )

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

    doValidation(document_url, schema_url)
