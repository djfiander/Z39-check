#!/usr/bin/env python
import sys, getopt, time
import csv

from PyZ3950 import zoom

#z3950.trace_init = 1

fmt = '<a href="http://alpha.lib.uwo.ca/search/?searchtype=f&searcharg=%s" target="cat">%s</a>'
worldcat = '<a href="http://worldcat.org/issn/%s" target="worldcat">worldcat</a>'

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

    query = 'issn=%(ISSN)s' % rec
    q = zoom.Query('CCL', query)

    # The Innovative Z39.50 server has a concurrent use limit, and
    # it seems to decide in the middle of a connection that you're no
    # longer deemed acceptable, so when we lose the connection, just
    # wait a sec (or five) and reconnect.
    while True:
        try:
            res = conn.search(q)
            break
        except zoom.ConnectionError, arg:
            sys.stderr.write("Server disconnected on %s: '%s'\n" %
                             ((query), arg))
            conn.close ()
            if str(arg) != 'graceful close':
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
        ofp.write('</td><td valign="top">')
        ofp.write(worldcat % rec['ISSN'])
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
<tr><th>UWO Catalogue</th><th>WorldCAT</th><th>Title</th></tr>
"""

    conn = z39_connect(host, port, dbname)
    print "Connected to %s, implementation ID = '%s'" % (conn.host, conn.targetImplementationId)

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

    print "Processed %d titles and found %d with %d connections" % (
        inlines, found, connects)

if __name__ == "__main__":
    main()
