u"""
Provides a simple Daemon class to ease the process of forking a
python application on Unix systems.
"""

VERSION = (1, 3, 1)

import ConfigParser
import errno
import grp
import logging
from logging.handlers import RotatingFileHandler
import optparse
import os
import pwd
import signal
import sys
import time
import filename
from itertools import imap
from io import open

class Daemon(object):
    u"""Daemon base class"""

    def __init__(self):
        u"""Override to change where the daemon looks for config information.

        By default we use the 'daemon' section of a file with the same name
        as the python module holding the subclass, ending in .conf
        instead of .py.
        """
        if not hasattr(self, u'default_conf'):
            # Grabs the filename that the Daemon subclass resides in...
            #self.daemon_file = sys.modules[self.__class__.__module__].__file__
            #self.default_conf = self.daemon_file.rpartition('.')[0] + '.conf'
            pass
        if not hasattr(self, u'section'):
            self.section = u'daemon'

    def setup_root(self):
        u"""Override to perform setup tasks with root privileges.

        When this is called, logging has been initialized, but the
        terminal has not been detached and the pid of the long-running
        process is not yet known.
        """

    def setup_user(self):
        u"""Override to perform setup tasks with user privileges.

        Like setup_root, the terminal is still attached and the pid is
        temporary.  However, the process has dropped root privileges.
        """

    def run(self):
        u"""Override.

        The terminal has been detached at this point.
        """

    def main(self):
        u"""Read the command line and either start or stop the daemon"""
        self.parse_options()
        action = self.options.action
        self.read_basic_config()
        if action == u'start':
            self.start()
        elif action == u'stop':
            self.stop()
        else:
            raise ValueError(action)

    def parse_options(self):
        u"""Parse the command line"""
        p = optparse.OptionParser()
        p.add_option(u'--start', dest=u'action',
                     action=u'store_const', const=u'start', default=u'start',
                     help=u'Start the daemon (the default action)')
        p.add_option(u'-s', u'--stop', dest=u'action',
                     action=u'store_const', const=u'stop', default=u'start',
                     help=u'Stop the daemon')
        p.add_option(u'-c', dest=u'config_filename',
                     action=u'store', default=self.default_conf,
                     help=u'Specify alternate configuration file name')
        p.add_option(u'-n', u'--nodaemon', dest=u'daemonize',
                     action=u'store_false', default=True,
                     help=u'Run in the foreground')
        self.options, self.args = p.parse_args()
        if not os.path.exists(self.options.config_filename):
            p.error(u'configuration file not found: %s'
                    % self.options.config_filename)

    def read_basic_config(self):
        u"""Read basic options from the daemon config file"""
        self.config_filename = self.options.config_filename
        cp = ConfigParser.ConfigParser(defaults={
            u'logmaxmb': u'5',
            u'logbackups': u'5',
            u'loglevel': u'info',
            u'uid': unicode(os.getuid()),
            u'gid': unicode(os.getgid()),
        })
        cp.optionxform = unicode
        cp.read([self.config_filename])
        self.config_parser = cp

        try:
            self.uid, self.gid = list(imap(int, get_uid_gid(cp, self.section)))
        except ValueError, e:
            sys.exit(unicode(e))

        self.logmaxmb = int(cp.get(self.section, u'logmaxmb'))
        self.logbackups = int(cp.get(self.section, u'logbackups'))
        self.pidfile = os.path.abspath(os.path.join(filename.get_dirname_file(), cp.get(self.section, u'pidfile')))
        self.logfile = os.path.abspath(os.path.join(filename.get_dirname_file(), cp.get(self.section, u'logfile')))
        self.loglevel = cp.get(self.section, u'loglevel')

    def on_sigterm(self, signalnum, frame):
        u"""Handle segterm by treating as a keyboard interrupt"""
        raise KeyboardInterrupt(u'SIGTERM')

    def add_signal_handlers(self):
        u"""Register the sigterm handler"""
        signal.signal(signal.SIGTERM, self.on_sigterm)

    def start(self):
        u"""Initialize and run the daemon"""
        # The order of the steps below is chosen carefully.
        # - don't proceed if another instance is already running.
        self.check_pid()
        # - start handling signals
        self.add_signal_handlers()
        # - create log file and pid file directories if they don't exist
        self.prepare_dirs()

        # - start_logging must come after check_pid so that two
        # processes don't write to the same log file, but before
        # setup_root so that work done with root privileges can be
        # logged.
        try:
            # - set up with root privileges
            self.setup_root()
            # - drop privileges
            self.start_logging()
            # - check_pid_writable must come after set_uid in order to
            # detect whether the daemon user can write to the pidfile
            self.check_pid_writable()
            # - set up with user privileges before daemonizing, so that
            # startup failures can appear on the console
            self.setup_user()

            # - daemonize
            if self.options.daemonize:
                daemonize()
        except:
            logging.exception(u"failed to start due to an exception")
            raise

        # - write_pid must come after daemonizing since the pid of the
        # long running process is known only after daemonizing
        self.write_pid()
        try:
            logging.info(u"started")
            try:
                self.run()
            except (KeyboardInterrupt, SystemExit):
                pass
            except:
                logging.exception(u"stopping with an exception")
                raise
        finally:
            self.remove_pid()
            logging.info(u"stopped")

    def stop(self):
        u"""Stop the running process"""
        if self.pidfile and os.path.exists(self.pidfile):
            pid = int(open(self.pidfile).read())
            os.kill(pid, signal.SIGTERM)
            # wait for a moment to see if the process dies
            for n in xrange(10):
                time.sleep(0.25)
                try:
                    # poll the process state
                    os.kill(pid, 0)
                except OSError, why:
                    if why.errno == errno.ESRCH:
                        # process has died
                        break
                    else:
                        raise
            else:
                sys.exit(u"pid %d did not die" % pid)
        else:
            sys.exit(u"not running")

    def prepare_dirs(self):
        u"""Ensure the log and pid file directories exist and are writable"""
        for fn in (self.pidfile, self.logfile):
            if not fn:
                continue
            parent = os.path.dirname(fn)
            if not os.path.exists(parent):
                os.makedirs(parent)
                self.chown(parent)

    def set_uid(self):
        u"""Drop root privileges"""
        if self.gid:
            try:
                os.setgid(self.gid)
            except OSError, err:
                logging.exception(err)
        if self.uid:
            try:
                os.setuid(self.uid)
            except OSError, err:
                logging.exception(err)

    def chown(self, fn):
        u"""Change the ownership of a file to match the daemon uid/gid"""
        if self.uid or self.gid:
            uid = self.uid
            if not uid:
                uid = os.stat(fn).st_uid
            gid = self.gid
            if not gid:
                gid = os.stat(fn).st_gid
            try:
                os.chown(fn, uid, gid)
            except OSError, err:
                sys.exit(u"can't chown(%s, %d, %d): %s, %s" %
                (repr(fn), uid, gid, err.errno, err.strerror))

    def start_logging(self):
        u"""Configure the logging module"""
        try:
            level = int(self.loglevel)
        except ValueError:
            level = getattr(logging, self.loglevel.upper())

        handlers = []
        if self.logfile:
            if not self.logmaxmb:
                handlers.append(logging.FileHandler(self.logfile))
            else:
                max_log_size_bytes = self.logmaxmb * 1024 * 1024
                handlers.append(RotatingFileHandler(self.logfile,
                                                    maxBytes=max_log_size_bytes,
                                                    backupCount=self.logbackups))
            self.chown(self.logfile)
        handlers.append(logging.StreamHandler())

        log = logging.getLogger()
        log.setLevel(level)
        for h in handlers:
            h.setFormatter(logging.Formatter(
                u"%(asctime)s %(process)d %(levelname)s %(message)s"))
            log.addHandler(h)

    def check_pid(self):
        u"""Check the pid file.

        Stop using sys.exit() if another instance is already running.
        If the pid file exists but no other instance is running,
        delete the pid file.
        """
        if not self.pidfile:
            return
        # based on twisted/scripts/twistd.py
        if os.path.exists(self.pidfile):
            try:
                pid = int(open(self.pidfile, u'rb').read().decode(u'utf-8').strip())
            except ValueError:
                msg = u'pidfile %s contains a non-integer value' % self.pidfile
                sys.exit(msg)
            try:
                os.kill(pid, 0)
            except OSError, err:
                if err.errno == errno.ESRCH:
                    # The pid doesn't exist, so remove the stale pidfile.
                    os.remove(self.pidfile)
                else:
                    msg = (u"failed to check status of process %s "
                           u"from pidfile %s: %s" % (pid, self.pidfile, err.strerror))
                    sys.exit(msg)
            else:
                msg = (u'another instance seems to be running (pid %s), '
                       u'exiting' % pid)
                sys.exit(msg)

    def check_pid_writable(self):
        u"""Verify the user has access to write to the pid file.

        Note that the eventual process ID isn't known until after
        daemonize(), so it's not possible to write the PID here.
        """
        if not self.pidfile:
            return
        if os.path.exists(self.pidfile):
            check = self.pidfile
        else:
            check = os.path.dirname(self.pidfile)
        if not os.access(check, os.W_OK):
            msg = u'unable to write to pidfile %s' % self.pidfile
            sys.exit(msg)

    def write_pid(self):
        u"""Write to the pid file"""
        if self.pidfile:
            open(self.pidfile, u'wb').write(unicode(os.getpid()).encode(u'utf-8'))

    def remove_pid(self):
        u"""Delete the pid file"""
        if self.pidfile and os.path.exists(self.pidfile):
            os.remove(self.pidfile)


def get_uid_gid(cp, section):
    u"""Get a numeric uid/gid from a configuration file.

    May return an empty uid and gid.
    """
    uid = cp.get(section, u'uid')
    if uid:
        try:
            uid = int(uid)
        except ValueError:
            # convert user name to uid
            try:
                uid = pwd.getpwnam(uid)[2]
            except KeyError:
                raise ValueError(u"user is not in password database: %s" % uid)

    gid = cp.get(section, u'gid')
    if gid:
        try:
            gid = int(gid)
        except ValueError:
            # convert group name to gid
            try:
                gid = grp.getgrnam(gid)[2]
            except KeyError:
                raise ValueError(u"group is not in group database: %s" % gid)

    return uid, gid


def daemonize():
    u"""Detach from the terminal and continue as a daemon"""
    # swiped from twisted/scripts/twistd.py
    # See http://www.erlenstar.demon.co.uk/unix/faq_toc.html#TOC16
    if os.fork():   # launch child and...
        os._exit(0)  # kill off parent
    os.setsid()
    if os.fork():   # launch child and...
        os._exit(0)  # kill off parent again.
    os.umask(63)  # 077 in octal
    null = os.open(u'/dev/null', os.O_RDWR)
    for i in xrange(3):
        try:
            os.dup2(null, i)
        except OSError, e:
            if e.errno != errno.EBADF:
                raise
    os.close(null)
