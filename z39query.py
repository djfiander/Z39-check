import sys, time
from PyZ3950 import zoom

connects = 1

def connect(host='alpha.lib.uwo.ca', port=210,
                db='INNOPAC', syntax='USMARC'):
    conn = zoom.Connection(host, port)
    conn.databaseName = db
    conn.preferredRecordSyntax = syntax
    return conn

def query(conn, rec):
    global connects

    query = 'isbn=%(ISBN)s'
    q = zoom.Query('CCL', query % rec)

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

