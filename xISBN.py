#!/usr/bin/env python

#
# xISBN.py: a Python iterator that translates ISBNs into
# the list of all related ISBNs using OCLC's xISBN service

import urllib
import operator

import xml.sax.handler

class BadISBN(Exception):
    pass

_servicepoint = 'http://old-xisbn.oclc.org/webservices/xisbn/%s'

class idlistHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.inIDlist = None;
        self.inISBN = None;
        self.isbns = [];

    def startElement(self, name, attributes):
        if name == 'idlist':
            if self.inIDlist: raise xml.sax.SAXParseException('Nested idlists')
            self.inIDlist = 1
        elif name == 'isbn':
            if not self.inIDlist:
                raise xml.sax.SAXParseException('Unnested ISBN')
            self.buffer = ''
            self.inISBN = 1

    def characters(self, data):
        if self.inISBN:
            self.buffer += data

    def endElement(self, name):
        if name == 'isbn':
            self.inISBN = None
            self.isbns.append(self.buffer)
        elif name == 'idlist':
            self.inIDlist = None
            assert self.inISBN == None
            

def validate(isbn):
    """Verify checksum of ISBN.  Returns if valid, throws exception if not."""
    if len(isbn) != 10:
        raise BadISBN('Invalid length', isbn)
    num, ckdig = isbn[:-1], isbn[-1]

    try:
        if ckdig in ('x', 'X'):
            ckdig = 10
        else:
            ckdig = int(ckdig)
        ck = sum(map(operator.mul, range(10, 1, -1), map(int, num))) + ckdig
    except ValueError:
        raise BadISBN('Invalid digit', isbn)
    if (ck % 11) != 0:
        raise BadISBN('Invalid checksum', isbn)

def xISBN(isbn):
    """Send ISBN to the OCLC xISBN service and return the list of related ISBNs.

The input ISBN is removed from the list returned, which means that it might
return an empty list, if there are no other related ISBNs.

Throws a 'BadISBN' exception if the ISBN is invalid."""

    # Canonicalize the ISBN by discarding embedded spaces and dashes
    isbn = ''.join(isbn.split())
    isbn = ''.join(isbn.split('-'))

    validate(isbn)
    urlf = urllib.urlopen(_servicepoint % isbn)
    
    parser = xml.sax.make_parser()
    handler = idlistHandler()
    parser.setContentHandler(handler)
    parser.parse(urlf)

    isbns = []
    for i in handler.isbns:
        if not (i == isbn):
            isbns.append(i)
    return isbns

if __name__ == '__main__':
    print xISBN('0-596-00797-3')
