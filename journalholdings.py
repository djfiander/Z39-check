#!/usr/bin/env python
import sys, getopt, time
import csv

from PyZ3950 import zoom

#z3950.trace_init = 1

fmt = '<a href="http://alpha.lib.uwo.ca/search/?searchtype=i&searcharg=%s" target="cat">%s</a>'

inlines = 0
found = 0
connects = 1

def z39_connect(host='alpha.lib.uwo.ca', port=210,
                db='INNOPAC', syntax='USMARC'):
    conn = zoom.Connection(host, port)
    conn.databaseName = db
    conn.preferredRecordSyntax = syntax
    return conn

def z39_query(conn, rec):
    global connects

    query = 'issn=%s'
    
    q = zoom.Query('CCL', query % ''.join(rec['ISSN'].split('-')))

    # The Innovative Z39.50 server has a concurrent use limit, and
    # it seems to decide in the middle of a connection that you're no
    # longer deemed acceptable, so when we lose the connection, just
    # wait a sec (or five) and reconnect.
    while True:
        try:
            res = conn.search(q)
            break
        except zoom.ConnectionError, arg:
            conn.close ()
            if str(arg) != 'graceful close':
                sys.stderr.write("Server disconnected on %s: '%s'\n" %
                                 ((query % rec), arg))
                print conn.__dict__
                sys.exit()
            time.sleep(5)
            conn.connect()
            connects += 1
    return res

def processFile(ifp, ofp, conn):
    global inlines, found
    icvs = csv.DictReader(ifp)

    for rec in (icvs):
        inlines += 1
        status = 'own'
        res = z39_query(conn, rec)
        ofp.write('<tr><td valign="top">')
        if (len(res) > 0):
            found += 1
            ofp.write(fmt % (rec['ISSN'], status))
        ofp.write('</td><td>')
        try:
            ofp.write('<cite>%s</cite>' % rec['Title'])
        except UnicodeDecodeError:
            sys.stderr.write("Invalid Unicode in title '%s'\n" %
                             rec['Title'])
        ofp.write('</td></tr>\n')

def main():
    global connects
    host = 'alpha.lib.uwo.ca'
    port = 210
    dbname = 'INNOPAC'
    outfile = None
    ofp = sys.stdout

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:p:d:o:vx")
    except getopt.GetoptError:
        sys.stderr.write("Usage: %s [-h host] [-p port] [-d dbname] [-o outfile] [-v]\n" %
                         sys.argv[0])
        sys.exit(2)

    for o, a in opts:
        if o == '-h':
            host = a
        elif o == '-p':
            port = int(a)
        elif o == '-o':
            outfile = a
        elif o == '-d':
            dbname = a

    if outfile:
        ofp = open(outfile, "wb")

    print >>ofp, """<html>
<body>
<table>
<caption>Holdings Information for EBL titles</caption>
<tr><th>UWO Catalogue</th><th>Title</th></tr>
"""

    conn = z39_connect(host, port, dbname)
    sys.stderr.write("Connected to %s, implementation ID = '%s'\n" %
                     (conn.host, conn.targetImplementationId))

    if not args:
        processFile(sys.stdin, ofp, conn)
    else:
        for fname in args:
            ifp = open(fname, "rb")
            processFile(ifp, ofp, conn)
            ifp.close

    conn.close()

    print >>ofp, """</table>
</body>
</html>"""
    ofp.close()

    sys.stderr.write("Processed %d titles and found %d with %d connections\n" %
                     (inlines, found, connects))

if __name__ == "__main__":
    main()
