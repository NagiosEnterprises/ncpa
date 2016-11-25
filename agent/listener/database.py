import os
import time
import sqlite3
import sys

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
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS checks
                               (accessor, run_time_start, run_time_end, result, output, sender, type)''')
        self.conn.commit()
        self.close()

    def commit(self):
        self.conn.commit()

    # Special functions for getting check results
    def get_checks(self, search='', size=0):
        data = { }
        cmd = "SELECT * FROM checks"
        
        # If we are doing a serach... append to the query
        if search:
            data['search'] = search
            cmd += " WHERE output LIKE '%:search%'"
        
        # Apply order by
        cmd += " ORDER BY run_time_end DESC"
        self.cursor.execute(cmd, data)

        # Get the requested objects
        if not size:
            objs = self.cursor.fetchall()
        else:
            objs = self.cursor.fetchmany(size)

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