#!/usr/bin/env python
from PyZ3950 import zoom, z3950

#z3950.trace_init = 1

conn = zoom.Connection ('alpha.lib.uwo.ca', 210)
conn.databaseName = 'INNOPAC'
conn.preferredRecordSyntax = 'USMARC'

query = zoom.Query ('CCL', 'isbn="0143051490"')

res = conn.search (query)
if (res == None):
    print 'no match is None'
