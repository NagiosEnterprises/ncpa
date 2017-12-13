import os
import time
import sqlite3
import sys
import server
import logging

# A module to wrap sqlite3 for use with a small database to store things
# like checks across both passive and active sections

class DB(object):

    def __init__(self):
        if getattr(sys, u'frozen', False):
            self.dbfile = os.path.abspath(os.path.dirname(sys.executable) + '/var/ncpa.db')
        else:
            self.dbfile = os.path.abspath(os.path.dirname(__file__) + '/../var/ncpa.db')
        self.connect()

    # Connect to the NCPA database
    def connect(self):
        self.conn = sqlite3.connect(self.dbfile, isolation_level=None, timeout=30)
        self.cursor = self.conn.cursor()

    def get_cursor(self):
        return self.cursor

    def close(self):
        self.conn.close()

    def truncate(self, dbname):
        self.cursor.execute('DROP TABLE %s' % dbname)
        self.cursor.execute('VACUUM')
        self.setup()
        return True

    # This is called on both passive and listener startup
    def setup(self):
        
        # Create main check results database and migration database
        self.cursor.execute('CREATE TABLE IF NOT EXISTS checks (accessor, run_time_start, run_time_end, result, output, sender, type)')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS migrations (id, version)')

        # Run migrations
        self.run_migrations()

    def run_db_maintenance(self, config):
        try:
            days = int(config.get('general', 'check_logging_time'))
        except Exception as e:
            days = 30;
        timestamp = time.time() - (days * 86400)
        try:
            self.cursor.execute('DELETE FROM checks WHERE run_time_start < %d' % timestamp)
        except Exception as e:
            logging.exception(e)

    # Function that will run migrations in future versions if there needs to be some
    # changes to the database layout
    def run_migrations(self):
        pass

    # Add a check to the check database
    def add_check(self, accessor, run_time_start, run_time_end, result, output, sender, checktype):
        data = (accessor, run_time_start, run_time_end, result, output, sender, checktype)
        try:
            self.cursor.execute('INSERT INTO checks VALUES (?, ?, ?, ?, ?, ?, ?)', data)
        except Exception as ex:
            logging.exception(ex)

    # Returns the total amount of checks in the DB
    def get_checks_count(self, search='', status='', senders=[]):
        where = False
        data = ()
        cmd = "SELECT COUNT(*) FROM checks"

        # If we are doing a search... append to the query
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
    def get_checks(self, search='', size=20, page=1, status='', ctype='', senders=[]):
        where = False
        data = ()
        cmd = "SELECT * FROM checks"

        # If we are doing a search... append to the query
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

        # Add type
        if ctype != '':
            data += (ctype,)
            if where:
                cmd += " AND"
            else:
                cmd += " WHERE"
                where = True
            cmd += " type = ?"

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

            # Process output types
            output = check['output'].split("\n")
            check['output'] = output[0]

            # Give long output if it exists
            check['longoutput'] = ''
            if len(output) > 1:
                check['longoutput'] = "<br>".join(output[1:])

            checks.append(check)

        return checks