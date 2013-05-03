#!/usr/bin/env python

# Open Library utility to fetch related ISBNs to those given

import urllib
import urllib2
import operator
import json

class BadISBN(Exception):
    pass

_isbn_svcpoint = 'http://openlibrary.org/query.json?type=/type/edition&isbn_10=%s&*='
_work_svcpoint = 'http://openlibrary.org/query.json?type=/type/edition&works=%s&isbn_10=&isbn_13='

def related_isbns(isbn):
    isbns = set()
    works = set()

    # clean up the input by removing dashes
    isbn = urllib.quote(''.join(isbn.split('-')))

    # First, get all the data out of the books that match this ISBN
    data = json.load(urllib2.urlopen(_isbn_svcpoint % isbn))
    for entry in data:
        if 'isbn_10' in entry:
            isbns = isbns.union(entry['isbn_10'])
        if 'works' in entry:
            works = works.union(work['key'] for work in entry['works'])

    # Now, get the data for all the related works based on the work keys
    for workid in works:
        data = json.load(urllib2.urlopen(_work_svcpoint % workid))
        for entry in data:
            if 'isbn_10' in entry:
                isbns = isbns.union(entry['isbn_10'])
    return isbns

if __name__ == '__main__':
    import sys
    for isbn in related_isbns(sys.argv[1]):
        print isbn
