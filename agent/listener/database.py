import os
import time
import sqlite3
import sys
import server

# A module to wrap sqllite3 for use with a small database to store things
# like checks accross both passive and active sections

class DB(object):

    def __init__(self):
        if getattr(sys, u'frozen', False):
            self.dbfile = os.path.abspath(os.path.dirname(sys.executable) + '/var/ncpa.db')
        else:
            self.dbfile = os.path.abspath(os.path.dirname(__file__) + '/../var/ncpa.db')
        self.connect()

    # Connect to the NCPA database
    def connect(self):
        self.conn = sqlite3.connect(self.dbfile)
        self.cursor = self.conn.cursor()

    def get_cursor(self):
        return self.cursor

    def close(self):
        self.conn.close()

    # This is called on both passive and listener startup
    def setup(self):
        
        # Create main check results database
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS checks
                               (accessor, run_time_start, run_time_end, result, output, sender, type)''')
        self.conn.commit()
        
        # Create migration database
        self.cursor.execute('CREATE TABLE IF NOT EXISTS migrations (id, version)')
        self.conn.commit()

        # Run migrations
        self.run_migrations()

        # Run maintenance on startup
        self.run_db_maintenance()

    def run_db_maintenance(self):
        days = int(server.get_config_value('general', 'check_logging_time', 30))
        timestamp = time.time() - (days * 86400)
        self.cursor.execute('DELETE FROM checks WHERE run_time_start < %d' % timestamp)
        self.conn.commit()

    # Function that will run migrations in future versions if there needs to be some
    # changes to the database layout
    def run_migrations(self):
        pass

    def commit(self):
        self.conn.commit()

    # Returns the total amount of checks in the DB
    def get_checks_count(self, search='', status='', senders=[]):
        where = False
        data = ()
        cmd = "SELECT COUNT(*) FROM checks"

        # If we are doing a serach... append to the query
        if search != '':
            data += ("%" + search + "%",)
            cmd += " WHERE output LIKE ?"
            where = True

        # Add status where clause
        if status != '':
            data += (status,)
            if where:
                cmd += " AND"
            else:
                cmd += " WHERE"
                where = True
            cmd += " result = ?"

        # Add senders
        if len(senders) > 0:
            for sender in senders:
                data += (sender,)
            if where:
                cmd += " AND"
            else:
                cmd += " WHERE"
                where = True
            cmd += " sender IN (" + ','.join('?'*len(senders)) + ")"

        self.cursor.execute(cmd, data)
        count = self.cursor.fetchone()[0]
        return count

    # Returns a list of distinct senders for filtering
    def get_check_senders(self):
        cmd = "SELECT DISTINCT sender FROM checks"

        self.cursor.execute(cmd)
        objs = self.cursor.fetchall()

        senders = []
        for obj in objs:
            senders.append(obj[0])

        return senders

    # Special functions for getting check results
    def get_checks(self, search='', size=20, page=1, status='', senders=[]):
        where = False
        data = ()
        cmd = "SELECT * FROM checks"

        # If we are doing a serach... append to the query
        if search != '':
            data += ("%" + search + "%",)
            cmd += " WHERE output LIKE ?"
            where = True

        # Add status where clause
        if status != '':
            data += (status,)
            if where:
                cmd += " AND"
            else:
                cmd += " WHERE"
                where = True
            cmd += " result = ?"

        # Add senders
        if len(senders) > 0:
            for sender in senders:
                data += (sender,)
            if where:
                cmd += " AND"
            else:
                cmd += " WHERE"
                where = True
            cmd += " sender IN (" + ','.join('?'*len(senders)) + ")"

        # Apply order by
        cmd += " ORDER BY run_time_start DESC"

        # Apply limiting based on page and size
        if page < 1:
            page = 1
        start = (page - 1) * size
        limit = "%d,%d" % (start, size)
        cmd += " LIMIT " + limit

        self.cursor.execute(cmd, data)

        # Get the requested objects
        objs = self.cursor.fetchall()
        columns = self.cursor.description

        # Get a real list of checks
        checks = []
        for obj in objs:
            i = 0
            check = { }
            for col in columns:
                check[col[0]] = obj[i]
                i += 1
            checks.append(check)

        return checks