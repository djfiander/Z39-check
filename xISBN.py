#!/usr/bin/env python

#
# xISBN.py: a Python iterator that translates ISBNs into
# the list of all related ISBNs using OCLC's xISBN service

import urllib
import operator

import json

class BadISBN(Exception):
    pass

_servicepoint = 'http://xisbn.worldcat.org/webservices/xid/isbn/%s?format=json'
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
    url = (_servicepoint % isbn)
    if _affiliateID:
        url += '&ai=' + _affiliateID
    data = json.load(urllib.urlopen(url))

    if (data['stat'] == 'ok'):
        isbns = []
        for entry in data['list']:
            for i in entry['isbn']:
                if not (i == isbn):
                    isbns.append(i)
    else:
        raise BadISBN('xISBN Failed', data['stat'])
    return isbns

if __name__ == '__main__':
    register('djfiander')
    print xISBN('0-596-00797-3')
    print xISBN('0596007973')
    print xISBN('9780060007447')
