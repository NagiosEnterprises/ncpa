#!/usr/bin/env python3

# Monkey patch for gevent
from gevent import monkey
monkey.patch_all()

import threading
import logging
import glob
import os
import sys
import ssl
import time
import datetime
import tempfile

from multiprocessing import Process
from gevent.pywsgi import WSGIServer
from gevent.pool import Pool
from geventwebsocket.handler import WebSocketHandler
from logging.handlers import RotatingFileHandler
from argparse import ArgumentParser
from io import open
from configparser import ConfigParser

# NCPA-specific module imports
import listener.server
import listener.psapi
import listener.certificate as certificate
import listener.database as database

# Imports for different system types
if os.name == 'posix':
    import grp
    import pwd
    import signal
    import errno


# Set some global variables for later
__FROZEN__ = getattr(sys, 'frozen', False)
__VERSION__ = '3.0.0'
__DEBUG__ = False
__SYSTEM__ = os.name
__STARTED__ = datetime.datetime.now()


# The base class for the Listener and Passive classes, which sets things
# like options, config, autostart, etc so that they can be accesssed inside
# the other classes
class Base():

    def __init__(self, options, config, autostart=False):
        self.options = options
        self.config = config

        if autostart:
            self.run()


# The listener, which serves the web GUI and API - starting in NCPA 3
# we will be using a seperate process that is forked off the main process
# to run the listener so all of NCPA is bundled in a single service
class Listener(Base):

    def run(self):

        # Check if there is a start delay
        try:
            delay_start = self.config.get('listener', 'delay_start')
            if delay_start:
                logging.info('Delayed start in configuration. Waiting %s seconds to start.', delay_start)
                time.sleep(int(delay_start))
        except Exception:
            pass

        try:
            try:
                address = self.config.get('listener', 'ip')
            except Exception:
                # Set the Windows default IP address to 0.0.0.0 because :: only allows connections
                # via IPv6 unlike Linux which can bind to both at once
                if __SYSTEM__ == 'nt':
                    address = '0.0.0.0'
                else:
                    address = '::'
                self.config.set('listener', 'ip', address)

            try:
                port = self.config.getint('listener', 'port')
            except Exception:
                self.config.set('listener', 'port', 5693)
                port = 5693

            try:
                ssl_str_ciphers = self.config_parser.get('listener', 'ssl_ciphers')
            except Exception:
                ssl_str_ciphers = None

            listener.server.listener.config['iconfig'] = self.config

            try:
                ssl_str_version = self.config.get('listener', 'ssl_version')
                ssl_version = getattr(ssl, 'PROTOCOL_' + ssl_str_version)
            except:
                ssl_version = getattr(ssl, 'PROTOCOL_TLSv1')
                ssl_str_version = 'TLSv1'

            logging.info('Using SSL version %s', ssl_str_version)

            user_cert = self.config.get('listener', 'certificate')

            if user_cert == 'adhoc':
                cert, key = certificate.create_self_signed_cert(get_filename('var'), 'ncpa.crt', 'ncpa.key')
            else:
                cert, key = user_cert.split(',')

            ssl_context = {
                'certfile': cert,
                'keyfile': key,
                'ssl_version': ssl_version
            }

            # Add SSL cipher list if one is given
            if ssl_str_ciphers:
                ssl_context['ciphers'] = ssl_str_ciphers

            # Create connection pool
            try:
                max_connections = self.config_parser.get('listener', 'max_connections')
            except Exception:
                max_connections = 200

            listener.server.listener.secret_key = os.urandom(24)
            http_server = WSGIServer(listener=(address, port),
                                     application=listener.server.listener,
                                     handler_class=WebSocketHandler,
                                     spawn=Pool(max_connections),
                                     **ssl_context)
            http_server.serve_forever()
        except Exception as exc:
            logging.exception(exc)


# The passive service that runs in the background - this is ran in a
# separate thread since it is what the main process is used for
class Passive(Base):

    def run_all_handlers(self, *args, **kwargs):
        """
        Will run all handlers that exist.

        The handler must:
        - Have a config header entry
        - Abide by the handler API set forth by passive.abstract.NagiosHandler
        - Terminate in a timely fashion
        """
        handlers = self.config.get('passive', 'handlers').split(',')
        run_time = time.time()

        # Empty passive handlers will skip trying to run any handlers
        if handlers[0] == 'None' or handlers[0] == '':
            return

        for handler in handlers:
            try:
                handler = handler.strip()
                module_name = 'passive.%s' % handler
                __import__(module_name)
                tmp_handler = sys.modules[module_name]
            except ImportError as e:
                logging.error('Could not import module passive.%s, skipping. %s' % (handler, str(e)))
                logging.exception(e)
            else:
                try:
                    ins_handler = tmp_handler.Handler(self.config)
                    ins_handler.run(run_time)
                    logging.debug('Successfully ran handler %s' % handler)
                except Exception as e:
                    logging.exception(e)

    def run(self):

        # Check if there is a start delay
        try:
            delay_start = self.config.get('passive', 'delay_start')
            if delay_start:
                logging.info('Delayed start in configuration. Waiting %s seconds to start.', delay_start)
                time.sleep(int(delay_start))
        except Exception:
            pass

        # Set next DB maintenance period to +1 day
        self.db = database.DB()
        self.db.run_db_maintenance(self.config)
        next_db_maintenance = datetime.datetime.now() + datetime.timedelta(days=1)

        try:
            while True:
                self.run_all_handlers()

                # Do DB maintenance if the time is greater than next DB maintenance run
                if datetime.datetime.now() > next_db_maintenance:
                    self.db.run_db_maintenance(self.config)
                    next_db_maintenance = datetime.datetime.now() + datetime.timedelta(days=1)

                time.sleep(1)
        except Exception as exc:
            logging.exception(exc)


# Re-done Daemon class does the startup and control options for the NCPA
# program on Linux and Mac OS X
class Daemon():

    # Set the options
    def __init__(self, options, config):
        self.options = options
        self.config = config

        # Default settings (can be overwritten)
        self.pidfile = get_filename('var/ncpa.pid')
        self.logfile = get_filename(self.config.get('general', 'logfile'))
        self.loglevel = self.config.get('general', 'loglevel')
        self.logmaxmb = 5
        self.logbackups = 5

    def main(self):
        action = self.options['action']

        # Set the uid and gid
        try:
            self.uid, self.gid = list(map(int, self.get_uid_gid(self.config, 'general')))
        except ValueError as e:
            sys.exit(e)

        if action == 'start':
            self.start()
        elif action == 'stop':
            self.stop()
        elif action == 'status':
            self.status()
        else:
            raise ValueError(action)

    def setup_root(self):
        """Override to perform setup tasks with root privileges.

        When this is called, logging has been initialized, but the
        terminal has not been detached and the pid of the long-running
        process is not yet known.
        """

        # We need to chown any temp files we wrote out as root (or any other user)
        # to the currently set user and group so checks don't error out
        try:
            tmpdir = os.path.join(tempfile.gettempdir())
            for file in os.listdir(tmpdir):
                if os.path.isfile(file):
                    if 'ncpa-' in file:
                        self.chown(os.path.join(tmpdir, file))
        except OSError as err:
            logging.exception(err)
            pass

    def setup_user(self):
        pass

    def on_sigterm(self, signalnum, frame):
        """Handle segterm by treating as a keyboard interrupt"""
        raise KeyboardInterrupt('SIGTERM')

    def add_signal_handlers(self):
        """Register the sigterm handler"""
        signal.signal(signal.SIGTERM, self.on_sigterm)

    def start(self):
        """Initialize and run the daemon"""

        # Don't proceed if another instance is already running.
        self.check_pid()

        # Start handling signals
        self.add_signal_handlers()

        # Create log file and pid file directories if they don't exist
        self.prepare_dirs()

        # Start_logging must come after check_pid so that two
        # processes don't write to the same log file, but before
        # setup_root so that work done with root privileges can be
        # logged.
        try:

            # Setup with root privileges
            self.setup_root()

            # Start logging
            self.start_logging()

            # Drop permissions to specified user/group in ncpa.cfg
            self.set_uid_gid()

            # Function check_pid_writable must come after set_uid_gid in 
            # order to detect whether the daemon user can write to the pidfile
            self.check_pid_writable()

            # Set up with user before daemonizing, so that startup failures
            # can appear on the console
            self.setup_user()

            # Daemonize
            if not self.options['non_daemon']:
                self.daemonize()

        except:
            logging.exception("failed to start due to an exception")
            raise

        # Function write_pid must come after daemonizing since the pid of the
        # long running process is known only after daemonizing
        self.write_pid()

        try:
            logging.info("started")
            try:
                start_modules(self.options, self.config)
            except (KeyboardInterrupt, SystemExit):
                pass
            except:
                logging.exception("stopping with an exception")
                raise
        finally:
            self.remove_pid()
            logging.info("stopped")

    def stop(self):
        """Stop the running process"""
        if self.pidfile and os.path.exists(self.pidfile):
            pid = int(open(self.pidfile).read())
            os.kill(pid, signal.SIGTERM)
            # wait for a moment to see if the process dies
            for n in range(10):
                time.sleep(0.25)
                try:
                    # poll the process state
                    os.kill(pid, 0)
                except OSError as err:
                    if err.errno == errno.ESRCH:
                        # process has died
                        break
                    else:
                        raise
            else:
                sys.exit("pid %d did not die" % pid)
        else:
            sys.exit("not running")

    def status(self):
        if self.pidfile and os.path.exists(self.pidfile):
            pid = int(open(self.pidfile).read())

            # Check if the value is in ps aux
            if pid > 0:
                try:
                    os.kill(pid, 0)
                    sys.exit("service is running (pid %d)" % pid)
                except OSError as err:
                    if err.errno != errno.ESRCH:
                        sys.exit("service is not running but pid file exists")
        else:
            sys.exit("service is not running")

    def prepare_dirs(self):
        """Ensure the log and pid file directories exist and are writable"""
        for fn in (self.pidfile, self.logfile):
            if not fn:
                continue
            parent = os.path.dirname(fn)
            if not os.path.exists(parent):
                os.makedirs(parent)
                self.chown(parent)

    def set_uid_gid(self):
        """Drop root privileges"""
        if self.gid:
            try:
                os.setgid(self.gid)
            except OSError as err:
                logging.exception(err)
        if self.uid:
            try:
                os.setuid(self.uid)
            except OSError as err:
                logging.exception(err)

    def chown(self, fn):
        """Change the ownership of a file to match the daemon uid/gid"""
        if self.uid or self.gid:
            uid = self.uid
            if not uid:
                uid = os.stat(fn).st_uid
            gid = self.gid
            if not gid:
                gid = os.stat(fn).st_gid
            try:
                os.chown(fn, uid, gid)
            except OSError as err:
                sys.exit("can't chown(%s, %d, %d): %s, %s" %
                (repr(fn), uid, gid, err.errno, err.strerror))

    def start_logging(self):
        """Configure the logging module"""
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
            h.setFormatter(logging.Formatter("%(asctime)s %(process)d %(levelname)s %(message)s"))
            log.addHandler(h)

    def check_pid(self):
        """Check the pid file.

        Stop using sys.exit() if another instance is already running.
        If the pid file exists but no other instance is running,
        delete the pid file.
        """
        if not self.pidfile:
            return
        # based on twisted/scripts/twistd.py
        if os.path.exists(self.pidfile):
            try:
                pid = int(open(self.pidfile, 'r').read().strip())
            except ValueError:
                msg = 'pidfile %s contains a non-integer value' % self.pidfile
                sys.exit(msg)
            try:
                os.kill(pid, 0)
            except OSError as err:
                if err.errno == errno.ESRCH:
                    # The pid doesn't exist, so remove the stale pidfile.
                    os.remove(self.pidfile)
                else:
                    msg = ("failed to check status of process %s "
                           "from pidfile %s: %s" % (pid, self.pidfile, err.strerror))
                    sys.exit(msg)
            else:
                msg = ('another instance seems to be running (pid %s), '
                       'exiting' % pid)
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
            msg = 'unable to write to pidfile %s' % self.pidfile
            sys.exit(msg)

    def write_pid(self):
        u"""Write to the pid file"""
        if self.pidfile:
            open(self.pidfile, 'w').write(str(os.getpid()))

    def remove_pid(self):
        u"""Delete the pid file"""
        if self.pidfile and os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def get_uid_gid(self, cp, section):
        user_uid = cp.get(section, 'uid')
        user_gid = cp.get(section, 'gid')

        if not isinstance(user_uid, int):
            if not user_uid.isdigit():
                username = user_uid
                u = pwd.getpwnam(user_uid)
                uid = u.pw_uid
            else:
                uid = int(user_uid)
                username = pwd.getpwuid(user_uid).pw_name

        if not isinstance(user_gid, int):
            if not user_gid.isdigit():
                g = grp.getgrnam(user_gid)
                gid = g.gr_gid
            else:
                gid = int(user_gid)

        return uid, gid

    def daemonize(self):
        """Detach from the terminal and continue as a daemon"""
        # swiped from twisted/scripts/twistd.py
        # See http://www.erlenstar.demon.co.uk/unix/faq_toc.html#TOC16
        if os.fork():   # launch child and...
            os._exit(0)  # kill off parent
        os.setsid()
        if os.fork():   # launch child and...
            os._exit(0)  # kill off parent again.
        os.umask(63)  # 077 in octal
        null = os.open('/dev/null', os.O_RDWR)
        for i in range(3):
            try:
                os.dup2(null, i)
            except OSError as e:
                if e.errno != errno.EBADF:
                    raise
        os.close(null)


# Windows service handler, this can be effectively ignored on systems like
# Mac OS X and Linux since they use Daemon instead
class WinService():

    # No parameters here, everything should be set in Initialize()
    def __init__(self):
        self.options = {}
        self.config = get_configuration()
        self.stopEvent = threading.Event()
        self.stopRequestedEvent = threading.Event()

    def setup_plugins(self):
        plugin_path = self.config.get('plugin directives', 'plugin_path')
        abs_plugin_path = get_filename(plugin_path)
        self.abs_plugin_path = os.path.normpath(abs_plugin_path)
        self.config.set('plugin directives', 'plugin_path', self.abs_plugin_path)

    # Set up the logger
    def setup_logging(self, *args, **kwargs):
        config = dict(self.config.items('general', 1))

        # Now we grab the logging specific items
        log_file = os.path.normpath(config['logfile'])
        if not os.path.isabs(log_file):
            log_file = get_filename(log_file)

        logging.getLogger().handlers = []

        # Max size of log files will be 20MB, and we'll keep one of them as backup
        max_log_size_bytes = int(config.get('logmaxmb', 5))
        max_log_rollovers = int(config.get('logbackups', 5))
        max_file_size = max_log_size_bytes * 1024 * 1024
        file_handler = logging.handlers.RotatingFileHandler(log_file,
                                                            maxBytes=max_file_size,
                                                            backupCount=max_log_rollovers)
        file_format = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(message)s')
        file_handler.setFormatter(file_format)

        logging.getLogger().addHandler(file_handler)

        # Set log level
        log_level_str = config.get('loglevel', 'INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        logging.getLogger().setLevel(log_level)

    def initialize(self, config_ini):
        self.setup_logging()
        self.setup_plugins()
        logging.info("Looking for plugins at: %s" % self.abs_plugin_path)

    # Called when the service is starting immediately after Initialize()
    # use this to perform the work of the service; don't forget to set or check
    # for the stop event or the service GUI will not respond to requests to
    # stop the service
    def run(self):
        start_modules(self.options, self.config)
        self.stopRequestedEvent.wait()
        self.stopEvent.set()

    # called when the service is being stopped by the service manager GUI
    def stop(self):
        self.stopRequestedEvent.set()
        self.stopEvent.wait()


# --------------------------
# Utility Functions
# --------------------------


# Gets the proper file name when the application is frozen
def get_filename(file):
    if __FROZEN__:
        appdir = os.path.dirname(sys.executable)
    else:
        appdir = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(appdir, file))


# Get all the configuration options and return the config parser for them
def get_configuration(config=None, configdir=None):

    # Use default config/directory if none is given to us
    if config is None:
        config = os.path.join('etc', 'ncpa.cfg')
        configdir = os.path.join('etc', 'ncpa.cfg.d', '*.cfg')

    # Get the configuration
    config_filenames = [get_filename(config)]

    # Add config directory if it is defined
    if configdir is not None:
        config_filenames.extend(sorted(glob.glob(get_filename(configdir))))

    cp = ConfigParser()
    cp.optionxform = str
    cp.read(config_filenames)
    return cp


# Actually starts the processes for the components that will be used
def start_modules(options, config):
    try:

        # Create the database structure for checks
        db = database.DB()
        db.setup()

        # Create the passive thread
        p = Process(target=Passive, args=(options, config, True))
        p.daemon = True
        p.start()

        # Create the listener process
        l = Process(target=Listener, args=(options, config, True))
        l.daemon = True
        l.start()

        return p, l

    except Exception as exc:
        logging.exception(exc)
        sys.exit(1)


# This handles calls to the main NCPA binary
def main():
    parser = ArgumentParser(description='''NCPA has multiple options and can
        be used to run Python scripts with the embedded version of Python or
        run the service/daemon in debug mode.''')

    # Script that should be ran through the main binary if we want to use the
    # internal version of Python...

    # Commands for running the application (Linux/Mac OS X only)
    if __SYSTEM__ == 'posix':

        parser.add_argument('--start', dest='action', action='store_const',
                            const='start', default='start',
                            help='start the daemon')

        parser.add_argument('--stop', dest='action', action='store_const', 
                            const='stop', default='start',
                            help='stop the daemon')

        parser.add_argument('--status', dest='action', action='store_const',
                            const='status', default='start',
                            help='get the status of the daemon')

        # Non-Daemonizing mode
        parser.add_argument('-n', '--non-daemon', action='store_true', default=False,
                            help='run NCPA in the foreground')

    # Allow using an external configuration file
    parser.add_argument('-c', '--config-file', action='store', default=None,
                        help='specify alternate configuration file name')

    # Allow using an external configuration directory
    parser.add_argument('-C', '--config-dir', action='store', default=None,
                        help='specify alternate configuration directory location')

    # Debug mode (should work on all OS)
    parser.add_argument('-d', '--debug-mode', action='store_true', default=False,
                        help='''run NCPA in the foreground with debug mode
                        enabled (this option is useful for development)''')

    # Add version argument
    parser.add_argument('-v', '--version', action='version',
                        version=__VERSION__)

    # Get all options as a dict
    options = vars(parser.parse_args())

    # Read and parse the configuration file
    config = get_configuration(options['config_file'], options['config_dir'])

    # If we are running this in debug mode from the command line, we need to
    # wait for the proper output to exit and kill the Passive and Listener
    # Note: We currently do not care about "safely" exiting them
    if options['debug_mode']:
        __DEBUG__ = True

        # Set config value for port to 5700 and start Listener and Passive
        config.set('listener', 'port', '5700')

        # Temporary set up logging
        log = logging.getLogger()
        log.addHandler(logging.StreamHandler())
        log.setLevel('DEBUG')

        p, l = start_modules(options, config)
        
        # Wait for exit
        print("Running in Debug Mode (https://localhost:5700/)")
        input("Press enter to exit..\n")
        sys.exit(0)

    # If we are running on Linux or Mac OS X we will be using the
    # Daemon class to control the agent
    if __SYSTEM__ == 'posix':
        d = Daemon(options, config)
        d.main()
    else:
        start_modules(options, config)

if __name__ == '__main__':
    main()
