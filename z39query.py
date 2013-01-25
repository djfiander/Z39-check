import sys, time
from PyZ3950 import zoom

# The Innovative Z39.50 server has a concurrent use limit, and
# it seems to decide in the middle of a connection that you're no
# longer deemed acceptable, so when we lose the connection, just
# wait a sec (or five) and reconnect.
#
# This class just wraps around the zoom API to hide the connection
# flakiness

class Z39query:
    def __init__(self, host, port, db, syntax):
        self.conn = zoom.Connection(host, port, databaseName=db,
                                    preferredRecordSyntax = syntax)
        self.connects = 1
        self.close = self.conn.close
        self.targetImplementationId = self.conn.targetImplementationId

    def query(self, qstr):
        q = zoom.Query('CCL', qstr)

        while True:
            try:
                res = self.conn.search(q)
                break
            except zoom.ConnectionError, arg:
                self.conn.close ()
                if str(arg) != 'graceful close':
                    sys.stderr.write("Server disconnected on %s: '%s'\n" %
                                     (qstr, arg))
                    print self.conn.__dict__
                    sys.exit()
                time.sleep(5)
                self.conn.connect()
                self.connects += 1
        return res

