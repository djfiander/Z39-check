#!/usr/bin/env python

#
# xISBN.py: a Python iterator that translates ISBNs into
# the list of all related ISBNs using OCLC's xISBN service

import urllib
import urllib2
import operator

import json

class BadISBN(Exception):
    pass

_servicepoint = 'http://xisbn.worldcat.org/webservices/xid/isbn/%s'
_affiliateID = None

def validate(isbn):
    """Verify checksum of ISBN.  Returns if valid, throws exception if not."""
    # Canonicalize the ISBN by discarding embedded spaces and dashes
    isbn = ''.join(isbn.split())
    isbn = ''.join(isbn.split('-'))

    if (len(isbn) != 10) and (len(isbn) != 13):
        raise BadISBN('Invalid length', isbn)
    num, ckdig = isbn[:-1], isbn[-1]

    try:
        if ckdig in ('x', 'X'):
            ckdig = 10
        else:
            ckdig = int(ckdig)
        if len(isbn) == 10:
            ck = sum(map(operator.mul, range(10, 1, -1), map(int, num)), ckdig)
            ck %= 11
        else: # len(isbn) == 13
            if isbn[0:3] not in ('978', '979'):
                raise BadISBN('Invalid ISBN', isbn)
            ck = sum(map(operator.mul, ((1, 3) * 6), map(int, num)))
            ck = (10 - (ck % 10)) % 10 - ckdig

        if ck != 0:
            raise BadISBN('Invalid checksum', isbn)
    except ValueError:
        raise BadISBN('Invalid digit', isbn)
    return True

def register(ai):
    """Register my affiliate ID to pass to the service point"""
    global _affiliateID
    _affiliateID = ai

def xISBN(isbn):
    """Send ISBN to the OCLC xISBN service and return the list of related ISBNs.

The input ISBN is removed from the list returned, which means that it might
return an empty list, if there are no other related ISBNs.

Throws a 'BadISBN' exception if the ISBN is invalid."""

    validate(isbn)
    # We don't need to urlencode the ISBN because it's a valid ISBN
    url = (_servicepoint % isbn)
    parms = [('format', 'json')]
    if _affiliateID:
        parms += [('ai', _affiliateID)]
    data = json.load(urllib2.urlopen(url, urllib.urlencode(parms)))

    isbns = set()
    if (data['stat'] == 'ok'):
        for entry in data['list']:
            isbns = isbns.union(i for i in entry['isbn'] if i != isbn)
    elif data['stat'] != 'unknownId':
        # if it's an unknownId, then there are no related ISBNs
        # so just keep going, other errors are a problem.
        raise BadISBN('xISBN Failed', data['stat']+' '+isbn)

    return isbns

def get_metadata(isbn, fields):
    """Send ISBN to the OCLC xISBN service and return the requested metadata."""

    validate(isbn)
    url = (_servicepoint % isbn)
    parms = [('method', 'getMetadata'), ('format', 'json'),
             ('fl', ','.join(fields))]
    if _affiliateID:
        parms += [('ai', _affiliateID)]
    data = json.load(urllib2.urlopen(url, urllib.urlencode(parms)))

    if data['stat'] == 'unknownId':
        raise BadISBN('unknown ISBN', isbn)
    if data['stat'] == 'invalidId':
        raise BadISBN('Invalid ISBN', isbn)
    return data['list'][0]
        
if __name__ == '__main__':
    register('djfiander')
    try:
        validate('8788115092722')
    except BadISBN:
        print "validate('8788115092722') raises BadISBN correctly"
        pass
    else:
        print "validate('8788115092722') says it's OK!"
        raise BadISBN('Invalid ISBN', '8788115092722')

    print xISBN('0-596-00797-3')
    print xISBN('0596007973')
    print xISBN('9780060007447')
