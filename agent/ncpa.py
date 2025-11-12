#!/usr/bin/env python3

"""
Main NCPA python script

This script is the main entry point for the NCPA agent. It handles the
command line arguments and starts the appropriate processes.

This script will start as a daemon on Linux and a Windows service on Windows.
It will spawn a listener and passive child processes.

Main entry points:
Linux/Mac OS X: Daemon class
Windows:        WinService class
"""

import os
# Monkey patch for gevent
from gevent import monkey

if os.name == 'posix':
    monkey.patch_all()
else:
    monkey.patch_all(subprocess=True, thread=False)

import datetime
import glob
import logging
import ssl
from zlib import ZLIB_VERSION as zlib_version
import sys
import tempfile
import time
import psutil

import errno
import signal

from argparse import ArgumentParser
from configparser import ConfigParser
from gevent.pool import Pool
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from socket import error as SocketError
from io import open
from logging.handlers import RotatingFileHandler
from multiprocessing import Process, Value, current_process, freeze_support
import process.daemon_manager

# Create the listener logger instance, now, because it is required by listener.server.
# It will be configured later via setup_logger(). See note 'About Logging' below.
listener_logger = logging.getLogger("listener")
def tokenFilter(record):
    if hasattr(record, 'msg') and isinstance(record.msg, str) and record.msg:
        try:
            if record.msg and 'token' in record.msg:
                parts = record.msg.split('token=')
                new_parts = [parts[0]]
                for part in parts[1:]:
                    sub_parts = part.split('&', 1)
                    sub_parts[0] = '********'
                    new_parts.append('&'.join(sub_parts))
                record.msg = 'token='.join(new_parts)
            return True
        except AttributeError:
            pass
        except Exception as e:
            return f"Error filtering log record: {e}"
    return record


# NCPA-specific module imports
import listener.server
import listener.psapi
import listener.certificate as certificate
import listener.database as database

# Imports for different system types
if os.name == 'posix':
    import grp
    import pwd

if os.name == 'nt':
    # ctypes for Windows service control
    import ctypes
    # pywin32 imports
    import servicemanager
    import win32event
    import win32service
    import win32serviceutil
    # threading for Windows service
    import threading


# Set some global variables for later
__FROZEN__ = getattr(sys, 'frozen', False)
__VERSION__ = '3.2.2'
__DEBUG__ = False
__SYSTEM__ = os.name
__STARTED__ = datetime.datetime.now()

options = {}

print("***** Starting NCPA version: ", __VERSION__)

# About Logging
# Asynchronous processes require separate loggers. Additionally, the parent process
# gets a logger to cover the startup code, global functions and the Daemon or Winservice classes used
# to spawn Listener and Passive processes on posix and Windows respectively.
#
# The root logger, parent log and listener log share the listener log file. This allows
# the various components' loggers, which are primarily associated with the listener, to be
# aggregated in the listener log file.
#
# The listener and parent logger instances are global to let the listener logger be accessed
# by server.py, and the parent logger to be available to the start up code.
#
# Here, we only create the instances. They are configured later via setup_logger().
parent_logger = logging.getLogger("parent")
passive_logger = logging.getLogger("passive")

# Define config defaults
# We assign a lot of (but not all) defaults in the code, so let's keep them in one place.

# Set the Windows default IP address to 0.0.0.0 because :: only allows connections
# via IPv6 unlike Linux which can bind to both at once
address = '::'
if __SYSTEM__ == 'nt':
    address = '0.0.0.0'

cfg_defaults = {
            'general': {
                'check_logging': '1',
                'check_logging_time': '30',
                'loglevel': 'info',
                'logmaxmb': '5',
                'logbackups': '5',
                'pidfile': 'var/run/ncpa.pid',
                'uid': 'nagios',
                'gid': 'nagios',
                'all_partitions': '1',
                'exclude_fs_types': 'aufs,autofs,binfmt_misc,cifs,cgroup,configfs,debugfs,devpts,devtmpfs,encryptfs,efivarfs,fuse,fusectl,hugetlbfs,mqueue,nfs,overlayfs,proc,pstore,rpc_pipefs,securityfs,selinuxfs,smb,sysfs,tmpfs,tracefs,nfsd,xenfs',
                'default_units': 'Gi',
                'allow_remote_restart': '0',
            },
            'listener': {
                'ip': address,
                'port': '5693',
                'ssl_version': 'TLSv1_2',
                'certificate': 'adhoc',
                'ssl_ciphers': 'None',
                'logfile': 'var/log/ncpa_listener.log',
                'delay_start': '0',
                'admin_gui_access': '1',
                'admin_password': 'None',
                'admin_auth_only': '0',
                'allowed_hosts': '',
                'max_connections': '200',
                'allowed_sources': '',
                'allow_config_edit': '1', # Note: this is limited to non-sensitive settings
                'disable_gui': '0',  # Disable web GUI while preserving API
            },
            'api': {
                'community_string': 'mytoken',
            },
            'passive': {
                'handlers': 'None',
                'sleep': '300',
                'logfile': 'var/log/ncpa_passive.log',
                'delay_start': '0',
            },
            'nrdp': {
                'parent': '',
                'token': '',
                'hostname': 'NCPA',
                'connection_timeout': '10',
            },
            'kafkaproducer': {
                'hostname': 'None',
                'servers': 'localhost:9092',
                'clientname': 'NCPA-Kafka',
                'topic': 'ncpa',
            },
            'plugin directives': {
                'plugin_path': 'plugins/',
                'follow_symlinks': '0',
                'plugin_timeout': '59',
                'run_with_sudo': '',
                '.sh': '/bin/sh $plugin_name $plugin_args',
                '.py': 'python3 $plugin_name $plugin_args',
                '.pl': 'perl $plugin_name $plugin_args',
                '.php': 'php $plugin_name $plugin_args',
                '.ps1': 'powershell -ExecutionPolicy Bypass -File $plugin_name $plugin_args',
                '.vbs': 'cscript $plugin_name $plugin_args //NoLogo',
                '.wsf': 'cscript $plugin_name $plugin_args //NoLogo',
                '.bat': 'cmd /c $plugin_name $plugin_args',
            },
            'passive checks' : {}
        }

# --------------------------
# Core Classes -- TODO: Move to a sub-module, add starting/restarting of passive checks for GUI
# --------------------------

class Base():
    """
    The base class for the Listener and Passive classes, which sets things
    like options, config, autostart, etc so that they can be accesssed inside
    the other classes
    """
    def __init__(self, options, config, has_error, autostart=False):
        self.options = options
        self.config = config
        self.has_error = has_error
        self.loglevel = self.config.get('general', 'loglevel')

        if self.loglevel == 'debug':
            print(self.__class__.__name__ + " - init()")

        if autostart:
            self.run()

    def set_process_name(self, name):
        current_process().name = name
        if __SYSTEM__ == 'nt':
            ctypes.windll.kernel32.SetConsoleTitleW(name)

    # Set error flag for parent process to true
    def send_error(self):
        self.has_error.value = True

    def init_logger(self, logger_name):
        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False
        logfile = get_filename(self.config.get(logger_name, 'logfile'))
        setup_logger(self.config, self.logger, logfile)

class Listener(Base):
    """
    The listener, which serves the web GUI and API - starting in NCPA 3
    we will be using a seperate process that is forked off the main process
    to run the listener so all of NCPA is bundled in a single service
    """
    def __init__(self, options, config, has_error, autostart=False):
        super().__init__(options, config, has_error, autostart)
        set_process_name("Nagios Cross-Platform Agent - Listener")

    def run(self):
        self.init_logger('listener')
        logger = self.logger
        logger.info("Starting Listener")
        logger.info("run()")

        try:
            try:
            # Build config
                delay_start = self.config.getint('listener', 'delay_start')
                logger.debug("delay_start: %s", delay_start)
                if delay_start:
                    logger.debug('Delayed start in configuration. Waiting %s seconds to start.', delay_start)
                    time.sleep(delay_start)

                address = self.config.get('listener', 'ip')
                logger.debug("address1: %s", address)

                port = self.config.getint('listener', 'port')
                logger.debug("port: %s", port)

                ssl_context = dict()
                ssl_str_ciphers = self.config.get('listener', 'ssl_ciphers')
                if  (ssl_str_ciphers == 'None'):
                    ssl_str_ciphers = ''
                else:
                    logger.debug("run() - ssl_str_ciphers: %s", ssl_str_ciphers)
                    ssl_context['ciphers'] = ssl_str_ciphers
                logger.debug("ssl_str_ciphers: %s", ssl_str_ciphers)

                ssl_str_version = self.config.get('listener', 'ssl_version')
                ssl_version = getattr(ssl, 'PROTOCOL_' + ssl_str_version)
                logger.debug('Using SSL version %s', ssl_str_version)

                max_connections = self.config.getint('listener', 'max_connections')
                logger.debug("max_connections: %s", max_connections)

                user_cert = self.config.get('listener', 'certificate')

            except Exception as e:
                logger.exception("run() - config exception: %s", e)
                self.send_error()
                return

            # Set up certs and start http server
            if user_cert == 'adhoc':
                logger.debug('Start create cert')
                cert, key = certificate.create_self_signed_cert(get_filename('var'), 'ncpa.crt', 'ncpa.key')
                logger.debug('Cert created')
            else:
                cert, key = user_cert.split(',')

            ssl_context['certfile'] = cert
            ssl_context['keyfile'] = key
            ssl_context['ssl_version'] = ssl_version

            # Pass config to Flask instance
            listener.server.listener.config['iconfig'] = self.config

            # Create connection pool
            listener.server.listener.secret_key = os.urandom(24)
            logger.debug("run() - define http_server")
            http_server = WSGIServer(listener=(address, port),
                                        application=listener.server.listener,
                                        handler_class=WebSocketHandler,
                                        log=listener_logger,
                                        error_log=listener_logger,
                                        spawn=Pool(max_connections),
                                        **ssl_context)
            logger.debug("run() - start http_server")
            http_server.serve_forever()
            logger.debug("run() - http_server running")

        # If we fail to start in dual stack mode, try IPv4 only
        except SocketError as e:
            if address == '::':
                logging.info("Failed to start in dual stack mode: %s", e)
                logging.info("Trying IPv4 only")
            else: 
                logging.exception("run() - exception: %s", e)
            address = '0.0.0.0'
            http_server = WSGIServer(listener=(address, port),
                                        application=listener.server.listener,
                                        handler_class=WebSocketHandler,
                                        log=listener_logger,
                                        error_log=listener_logger,
                                        spawn=Pool(max_connections),
                                        **ssl_context)
            http_server.serve_forever()

        except Exception as e:
            logger.exception("exception: %s", e)
            self.send_error()
            return

class Passive(Base):
    """
    The passive service that runs in the background - this is run in a
    separate thread since it is what the main process is used for
    """
    def __init__(self, options, config, has_error, autostart=False):
        super().__init__(options, config, has_error, autostart)
        set_process_name("Nagios Cross-Platform Agent - Passive")

    def run_all_handlers(self, *args, **kwargs):
        """
        Will run all handlers that exist.

        The handler must:
        - Have a config header entry
        - Abide by the handler API set forth by passive.abstract.NagiosHandler
        - Terminate in a timely fashion
        """
        logger = self.logger
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
                logger.error('Could not import module passive.%s, skipping. %s' % (handler, str(e)))
                logger.exception(e)
            else:
                try:
                    ins_handler = tmp_handler.Handler(self.config)
                    ins_handler.run(run_time)
                    logger.debug('Successfully ran handler %s' % handler)
                except Exception as e:
                    logger.exception(e)
                    self.send_error()
                    return

    def run(self):
        self.init_logger('passive')
        logger = self.logger
        logger.info("Starting Passive")
        logger.info("run()")

        # Check if there is a start delay
        try:
            delay_start = self.config.getint('passive', 'delay_start')
            if delay_start:
                time.sleep(delay_start)
        except Exception as e:
            logger.exception("run() - exception: %s", e)
            pass

        # Set next DB maintenance period to +1 day
        self.db = database.DB()
        self.db.run_db_maintenance(self.config)
        next_db_maintenance = datetime.datetime.now() + datetime.timedelta(days=1)

        try:
            while not self.has_error.value:
                self.run_all_handlers()

                # Do DB maintenance if the time is greater than next DB maintenance run
                if datetime.datetime.now() > next_db_maintenance:
                    logger.info("run() - doing DB maintenance")
                    self.db.run_db_maintenance(self.config)
                    next_db_maintenance = datetime.datetime.now() + datetime.timedelta(days=1)

                logger.debug("run() - loop - running")
                time.sleep(1)

        except Exception as e:
            logger.exception("run() - exception: %s", e)
            self.send_error()
            return

# Main class - Linux/Mac OS X
class Daemon():
    """
    Re-done Daemon class does the startup and control options for the NCPA
    program on Linux and Mac OS X
    """
    # Set the options
    def __init__(self, options, config, has_error, logger):
        self.logger = logger
        self.logger.debug("Daemon __init__() - initializing new Daemon class instance")

        self.options = options
        self.config = config
        self.has_error = has_error

        # Default settings (can be overwritten)
        self.pidfile = get_filename(self.config.get('general', 'pidfile'))

        self.listener_logfile = get_filename(self.config.get('listener', 'logfile'))
        self.passive_logfile = get_filename(self.config.get('passive', 'logfile'))
        self.loglevel = self.config.get('general', 'loglevel')
        self.logmaxmb = self.config.getint('general', 'logmaxmb')
        self.logbackups = self.config.getint('general', 'logbackups')

        self.setup_plugins()
        self.logger.debug("Looking for plugins at: %s" % self.abs_plugin_path)

        self.p, self.l = None, None

    def main(self):
        action = self.options['action']

        # Set the uid and gid
        try:
            self.uid, self.gid, self.username = self.get_uid_gid(self.config, 'general')
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

    def root_setup_tasks(self):
        """Override to perform setup tasks with root privileges.

        When this is called, logging has been initialized, but the
        terminal has not been detached and the pid of the long-running
        process is not yet known.
        """
        self.logger.debug("Daemon init - setup_root()")

        # We need to chown any temp files we wrote out as root (or any other user)
        # to the currently set user and group so checks don't error out
        try:
            tmpdir = os.path.join(tempfile.gettempdir())
            for file in os.listdir(tmpdir):
                if os.path.isfile(file):
                    if 'ncpa-' in file:
                        self.chown(os.path.join(tmpdir, file))
        except OSError as e:
            self.logger.exception(e)
            pass

    def user_setup_tasks(self):
        pass

    def setup_plugins(self):
        plugin_path = self.config.get('plugin directives', 'plugin_path')
        abs_plugin_path = get_filename(plugin_path)
        self.abs_plugin_path = os.path.normpath(abs_plugin_path)
        self.config.set('plugin directives', 'plugin_path', self.abs_plugin_path)

    # This (ongoing NCPA) process is normally terminated by a different instance of this code launched with the '--stop' option.
    # The 'stop' instance reads the PID of the parent NCPA process and kills it by sending it SIGTERM. When SIGTERM is received, this
    # function handels it by exiting, which also closes the subordinate processes.
    def on_sigterm(self, signalnum, frame):
        global has_error
        """Handle sigterm and sigint"""
        self.logger.debug("on_sigterm(%s)", signalnum)

        # Forcing exit while in loop's sleep, doesn't always exit cleanly, so
        # on first occurence (system always sends multiples for sigint), set has_error=True to break main loop
        if not self.has_error.value:
            self.has_error.value = True
            self.logger.debug("on_sigterm - set has_error = True")

        # Now, main loop is ended, so we can exit at will
        else:
            self.logger.info("on_sigterm - sys.exit")

            # If SIGINT (CTL-C), make sure to remove PID file
            if signalnum == 2:
                self.remove_pid()

            sys.exit()

    def add_signal_handlers(self):
        """Register the sigterm handler"""
        signal.signal(signal.SIGTERM, self.on_sigterm)
        signal.signal(signal.SIGINT, self.on_sigterm)

    # ATTENTION - This function contains the infinite while loop that prevents
    # the process from exiting during normal operation
    def start(self):
        """Initialize and run the daemon"""
        self.logger.info("Daemon - start() - Initialize and run the daemon")

        # Don't proceed if another instance is already running.
        self.check_pid()

        # Start handling signals
        self.add_signal_handlers()

        # Create log file and pid file directories if they don't exist
        self.prepare_dirs()

        try:
            # Chown the installed passive log file while root still has control
            # Since the listener file is used for the root and parent loggers, it is chowned
            # during the setup_logger process
            if __SYSTEM__ == 'posix' and os.path.isfile(self.passive_logfile):
                chown(self.config.get('general', 'uid'), self.config.get('general', 'gid'), self.passive_logfile)

            # Setup with root privileges
            self.root_setup_tasks()

            # Drop permissions to specified user/group in ncpa.cfg
            self.set_uid_gid()

            # Function check_pid_writable must come after set_uid_gid in
            # order to detect whether the daemon user can write to the pidfile
            self.check_pid_writable()

            # Set up with user before daemonizing, so that startup failures
            # can appear on the console
            self.user_setup_tasks()

            # Daemonize
            if not self.options['non_daemon']:
                try:
                    self.daemonize()
                except Exception as e:
                    self.logger.exception("Daemon - Failed to Daemonize: %s", e)
                    raise

        except Exception as e:
            self.logger.exception("Daemon - Failed to start due to an exception: %s", e)
            raise

        # Function write_pid must come after daemonizing since the pid of the
        # long running process is known only after daemonizing
        self.write_pid()
        self.logger.debug("Daemon - started")

        try:
            self.p, self.l = start_processes(self.options, self.config, self.has_error)

        except Exception as e:
            self.logger.exception("Daemon - Couldn't start processes: %s", e)
            raise

        self.logger.debug("Daemon - start forever loop")

                # ******************************** Main Loop ********************************
                # **************** Loop forever unless process throws error *****************
                # **************** Interrupt sets has_error True ending loop ****************
                # ***************************************************************************

        while not self.has_error.value:
            time.sleep(1)
        else:
            self.logger.debug("Daemon - Exit forever loop - self.has_error.value: %s", self.has_error.value)

        self.remove_pid()
        self.logger.debug("Daemon - start() - Done")
        sys.exit()

    def stop(self):
        """Stop the running process"""
        self.logger.debug("Daemon - stop() - Stop the running process")

        if self.pidfile and os.path.exists(self.pidfile):
            pid = int(open(self.pidfile).read())
            self.logger.debug("Daemon - stop() - Try killing process: %d", pid)
            os.kill(pid, signal.SIGTERM)
            # wait for a moment to see if the process dies
            time.sleep(0.5)
            for n in range(10):
                time.sleep(0.5)
                try:
                    # poll the process state
                    self.logger.debug("Daemon - stop() - Try killing process again: %d", pid)
                    os.kill(pid, 0)

                except OSError as err:
                    if err.errno == errno.ESRCH:
                        # process has died
                        self.remove_pid()
                        self.logger.info("Daemon - stop() - Stopped")
                        break
                    else:
                        raise

                self.logger.debug("Daemon - stop() - Try killing process again: %d", pid)

            else:
                msg = ("Daemon - stop() - pid %d did not die" % pid)
                self.logger.warning(msg)
                sys.exit(msg)
        else:
            sys.exit("Daemon - stop() - Not running")


    def status(self):
        """Return the process status"""
        self.logger.debug("Daemon - status() - Return the process status")

        if self.pidfile and os.path.exists(self.pidfile):
            pid = int(open(self.pidfile).read())

            # Check if the value is in ps aux
            if pid > 0:
                try:
                    self.logger.info("Daemon - status() - Try killing process: %d", pid)
                    os.kill(pid, 0)
                    msg = ("Daemon - status() - Service is running (pid %d)" % pid)
                    self.logger.info(msg)
                    sys.exit(msg)
                except OSError as err:
                    if err.errno != errno.ESRCH:
                        msg = "Daemon - status() - Service is not running but pid file exists"
                        self.logger.warning(msg)
                        sys.exit(msg)
        else:
            msg = "Daemon - status() - Service is not running"
            self.logger.info(msg)
            sys.exit(msg)

    def prepare_dirs(self):
        """Ensure the log and pid file directories exist and are writable"""
        self.logger.debug("Daemon - prepare_dirs()")
        for fn in (self.pidfile, self.listener_logfile, self.passive_logfile):
            if not fn:
                continue
            parent = os.path.dirname(fn)
            if not os.path.exists(parent):
                os.makedirs(parent)
                self.chown(parent)

    def set_uid_gid(self):
        """Drop root privileges"""
        self.logger.debug("Daemon - set_uid_gid()")
        # Get set of gids to set for OS groups
        gids = [ self.gid ]
        if self.username:
            gids = [ g.gr_gid for g in grp.getgrall() if self.username in g.gr_mem ]

        # Set the group first
        try:
            os.setgid(self.gid)
        except OSError as err:
            self.logger.exception("Failed to set group ID: %s", err)
            raise

        # Try to set supplementary groups - this can fail due to security restrictions
        supplementary_groups_set = False
        try:
            os.setgroups(gids)
            supplementary_groups_set = True
            self.logger.debug("Successfully set supplementary groups: %s", gids)
        except OSError as err:
            if (sys.platform == 'darwin' and err.errno == 1) or (sys.platform.startswith('sunos') and err.errno == 1):
                # Operation not permitted on macOS or Solaris
                platform_name = "macOS" if sys.platform == 'darwin' else "Solaris"
                self.logger.warning("setgroups failed on %s (this is common due to security restrictions)", platform_name)
                self.logger.info("Attempting alternative permission setup for %s...", platform_name)
                
                # On these platforms, try to ensure the user is at least in the primary group
                # and warn about potential permission issues
                try:
                    # Verify the user can access group-owned resources by checking the primary group
                    import pwd
                    user_info = pwd.getpwuid(self.uid)
                    self.logger.info("Running as user '%s' (uid:%d) with primary group '%s' (gid:%d)", 
                                   user_info.pw_name, self.uid, grp.getgrgid(self.gid).gr_name, self.gid)
                    
                    # Warn about supplementary groups that couldn't be set
                    if len(gids) > 1:
                        missing_groups = [grp.getgrgid(gid).gr_name for gid in gids if gid != self.gid]
                        self.logger.warning("Could not set supplementary groups on %s: %s", platform_name, missing_groups)
                        self.logger.warning("This may cause permission issues accessing resources owned by these groups")
                        self.logger.info("Consider adjusting file/directory permissions or group ownership if you encounter access issues")
                        
                except Exception as group_err:
                    self.logger.error("Error while checking group information: %s", group_err)
                    
            else:
                self.logger.exception("Failed to set supplementary groups: %s", err)
                raise

        # Finally set the user ID
        try:
            os.setuid(self.uid)
        except OSError as err:
            self.logger.exception("Failed to set user ID: %s", err)
            raise
            
        # Final verification and helpful logging
        try:
            import pwd
            current_user = pwd.getpwuid(os.getuid())
            current_group = grp.getgrgid(os.getgid())
            self.logger.info("Successfully dropped privileges to user '%s' (uid:%d, gid:%d)", 
                           current_user.pw_name, os.getuid(), os.getgid())
            
            if not supplementary_groups_set and (sys.platform == 'darwin' or sys.platform.startswith('sunos')):
                platform_name = "macOS" if sys.platform == 'darwin' else "Solaris"
                self.logger.info("Note: Running with limited group membership due to %s security restrictions", platform_name)
                
        except Exception as verify_err:
            self.logger.debug("Could not verify final user/group state: %s", verify_err)

    def chown(self, fn):
        """Change the ownership of a file to match the daemon uid/gid"""
        self.logger.debug("Daemon - chown()")
        if self.uid or self.gid:
            uid = self.uid
            if not uid:
                uid = os.stat(fn).st_uid
            gid = self.gid
            if not gid:
                gid = os.stat(fn).st_gid
            try:
                os.chown(fn, uid, gid)
                # On macOS, ensure the file is readable/writable after chown
                if sys.platform == 'darwin':
                    if os.path.isdir(fn):
                        os.chmod(fn, 0o755)
                    else:
                        os.chmod(fn, 0o644)
            except OSError as err:
                self.logger.error("Daemon - chown() - can't chown(%s, %d, %d): %s, %s", 
                                 repr(fn), uid, gid, err.errno, err.strerror)
                # Don't exit on macOS chown errors - just log and continue
                if sys.platform != 'darwin':
                    sys.exit("Daemon - chown() - can't chown(%s, %d, %d): %s, %s" %
                    (repr(fn), uid, gid, err.errno, err.strerror))


    def check_pid(self):
        """Check the pid file.

        Stop using sys.exit() if another instance is already running.
        If the pid file exists but no other instance is running,
        delete the pid file.
        """
        self.logger.debug("Daemon - check_pid()")

        if not self.pidfile:
            self.logger.debug("Daemon - check_pid() - Another instance is running. Exit.")
            return

        # based on twisted/scripts/twistd.py
        if os.path.exists(self.pidfile):
            try:
                pid = int(open(self.pidfile, 'r').read().strip())
                self.logger.debug("Daemon - check_pid() - PID in file: %s", pid)

            except ValueError:
                msg = 'Pidfile %s contains a non-integer value' % self.pidfile
                self.logger.debug(msg)
                sys.exit(msg)

            # Check that the process ID corresponds to NCPA
            process_exists = False
            try:
                process = psutil.Process(pid)
                if process.name().lower() in ['ncpa', 'ncpa.exe']:
                    process_exists = True
                self.logger.debug(f"Daemon - check_pid() - Process {pid} is {process.name()} and is {process.status()}")
            except psutil.NoSuchProcess:
                pass

            if not process_exists:
                self.logger.debug("Daemon - check_pid() - The process with PID %s is not running. Removing the stale pidfile.", pid)
                os.remove(self.pidfile)
            if process_exists:
                try:
                    self.logger.debug("Daemon - check_pid() - Try killing process: %d", pid)
                    os.kill(pid, 0)
                    time.sleep(3)
                except OSError as err:
                    if err.errno == errno.ESRCH:
                        # The pid doesn't exist, so remove the stale pidfile.
                        self.logger.debug("Daemon - check_pid() - The pid doesn't exist, so remove the stale pidfile")
                        os.remove(self.pidfile)
                    else:
                        msg = ("Daemon - check_pid() - Failed to check status of process %s "
                            "from pidfile %s: %s" % (pid, self.pidfile, err.strerror))
                        self.logger.debug(msg)
                        sys.exit(msg)
                else:
                    msg = ('Daemon - check_pid() - Another instance is already running (pid %s)' % pid)
                    self.logger.warning(msg)
                    try:
                        self.logger.debug("Daemon - check_pid() - Trying to kill process: %d", pid)
                        if psutil.Process(pid).name().lower() in ['ncpa', 'ncpa.exe']:
                            os.kill(pid, signal.SIGTERM)
                        else:
                            self.logger.debug("Daemon - check_pid() - Process %s is not NCPA or NCPA.exe or is not running", pid)
                    except OSError as err:
                        msg = ("Daemon - check_pid() - Failed to kill process %s: %s" % (pid, err.strerror))
                        self.logger.debug(msg)
                        sys.exit(msg)
                    try:
                        self.logger.debug("Daemon - check_pid() - Trying to remove pidfile: %d", pid)
                        os.remove(self.pidfile)
                    except OSError as err:
                        msg = ("Daemon - check_pid() - Failed to remove pidfile %s: %s" % (self.pidfile, err.strerror))
                        self.logger.debug(msg)
                        sys.exit(msg)
                    else:
                        self.logger.debug("Daemon - check_pid() - Removed pidfile %s", self.pidfile)
                        sys.exit(msg)

    def check_pid_writable(self):
        u"""Verify the user has access to write to the pid file.

        Note that the eventual process ID isn't known until after
        daemonize(), so it's not possible to write the PID here.
        """
        self.logger.debug("Daemon - check_pid_writable()")

        if not self.pidfile:
            return
        if os.path.exists(self.pidfile):
            check = self.pidfile
        else:
            check = os.path.dirname(self.pidfile)
        if not os.access(check, os.W_OK):
            msg = 'Daemon - check_pid_writable() - unable to write to pidfile %s' % self.pidfile
            self.logger.warning(msg)
            sys.exit(msg)

    def write_pid(self):
        u"""Write to the pid file"""
        pid = str(os.getpid())
        self.logger.debug("Daemon - write_pid(): %s", pid)
        if self.pidfile:
            open(self.pidfile, 'w').write(pid)

    def remove_pid(self):
        u"""Delete the pid file"""
        self.logger.debug("Daemon - remove_pid()")
        if self.pidfile and os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def get_uid_gid(self, cp, section):
        self.logger.debug("Daemon - get_uid_gid()")
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

        return uid, gid, username

    def daemonize(self):
        """Detach from the terminal and continue as a daemon"""
        self.logger.info("Daemon - daemonize()")
        
        # swiped from twisted/scripts/twistd.py
        # See http://www.erlenstar.demon.co.uk/unix/faq_toc.html#TOC16
        if os.fork():   # launch child and...
            os._exit(0)  # kill off parent
        os.setsid()
        if os.fork():   # launch child and...
            os._exit(0)  # kill off parent again.
        os.umask(63)  # 077 in octal
        
        # Ensure log files are still accessible after daemonizing
        try:
            null = os.open('/dev/null', os.O_RDWR)
            for i in range(3):
                try:
                    os.dup2(null, i)
                except OSError as e:
                    if e.errno != errno.EBADF:
                        raise
            os.close(null)
        except OSError as e:
            # Log the error but don't fail - this might happen on some systems
            self.logger.warning("daemonize - failed to redirect standard streams: %s", e)

# Main class - Windows
if __SYSTEM__ == 'nt':
    class WinService(win32serviceutil.ServiceFramework):
        """
        Windows service class
        Mac OS X and Linux use the Daemon class instead
        """
        _svc_name_ = 'NCPA'
        _svc_display_name_ = 'NCPA Agent'

        def __init__(self, args):
            self.logger = parent_logger
            self.logger.debug("---------------- Winservice.initialize()")

            # pywin32 service initialization
            win32serviceutil.ServiceFramework.__init__(self, args)
            # handle WaitStop event tells the SCM to stop the service
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            self.running_event = threading.Event()

            # child process handles (Passive, Listener)
            self.p, self.l = None, None

            self.options = get_options()
            self.config = get_configuration()
            self.has_error = Value('i', False)

            self.setup_plugins()
            self.logger.debug("Looking for plugins at: %s" % self.abs_plugin_path)


        def init_logger(self, logger_name):
            self.logger = logging.getLogger(logger_name)
            logfile = get_filename(self.config.get(logger_name, 'logfile'))
            self.logger.debug("Winservice.init_logger() - Name: %s, File: %s", logger_name, logfile)
            setup_logger(self.config, self.logger, logfile)

        def setup_plugins(self):
            plugin_path = self.config.get('plugin directives', 'plugin_path')
            abs_plugin_path = get_filename(plugin_path)
            self.abs_plugin_path = os.path.normpath(abs_plugin_path)
            self.config.set('plugin directives', 'plugin_path', self.abs_plugin_path)

        def setup_logging(self, *args, **kwargs):
            config = dict(self.config.items('general', 1))

            # Now we grab the logging specific items
            log_file = os.path.normpath(config['logfile'])
            if not os.path.isabs(log_file):
                log_file = get_filename(log_file)

            logging.getLogger().handlers = []

            # Max size of log files will be 20MB, and we'll keep one of them as backup
            max_log_size_bytes = config.getint('logmaxmb', 5)
            max_log_rollovers = config.getint('logbackups', 5)
            max_file_size = max_log_size_bytes * 1024 * 1024
            file_handler = logging.handlers.RotatingFileHandler(log_file,
                                                                maxBytes=max_file_size,
                                                                backupCount=max_log_rollovers)
            file_format = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(message)s')
            file_handler.setFormatter(file_format)
            file_handler.addFilter(tokenFilter)

            logging.getLogger().addHandler(file_handler)

            # Set log level
            log_level_str = config.get('loglevel', 'INFO').upper()
            log_level = getattr(logging, log_level_str, logging.INFO)
            print("Winservice.loglevel: ", log_level)
            logging.getLogger().setLevel(log_level)

        def SvcStop(self):
            """
            Stop the service
            This triggers the stop event, which breaks the main loop
            """
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            self.running_event.clear()
            win32event.SetEvent(self.hWaitStop) # set stop event for main thread

        try:
            def SvcRun(self):
                """
                Start the service
                We need to override this method to prevent it reporting NCPA as started before the processes are started
                """
                try:
                    self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
                    self.logger.debug("SvcRun() - Service start pending")
                except Exception as e:
                    self.logger.exception("SvcRun - Failed to report service start pending: %s", e)
                    self.has_error.value = True
                    self.ReportServiceStatus(win32service.SERVICE_STOPPED)
                    return
                self.logger.debug("SvcRun() - running SvcDoRun function")
                self.SvcDoRun()

                # Once SvcDoRun returns, the service has stopped
                # log stopping of service to windows event log
                try:
                    servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                    servicemanager.PYS_SERVICE_STOPPED,
                                    (self._svc_name_, ''))
                except Exception as e:
                    self.logger.exception("SvcRun - Failed to log service stop: %s", e)

        except Exception as e:
            pass

        try:
            def SvcDoRun(self):
                # log starting of service to windows event log
                try:
                    servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                    servicemanager.PYS_SERVICE_STARTED,
                                    (self._svc_name_, ''))
                except Exception as e:
                    self.logger.exception("SvcDoRun - Failed to log service start: %s", e)
                try:
                    self.running_event.set()
                except Exception as e:
                    self.logger.exception("SvcDoRun - Failed to set running event: %s", e)
                try:
                    self.logger.debug("SvcDoRun() - Running main function")
                    self.main()
                except Exception as e:
                    self.logger.exception("SvcDoRun - Failed to run main: %s", e)
                    self.has_error.value = True
                    self.ReportServiceStatus(win32service.SERVICE_STOPPED)
                    # log error to windows event log
                    servicemanager.LogErrorMsg(servicemanager.EVENTLOG_ERROR_TYPE,
                                            servicemanager.PYS_SERVICE_STOPPED,
                                            (self._svc_name_, str(e)))
        except Exception as e:
            pass

        def force_kill(self, proc, name):
            try:
                import os, signal, sys
                if proc.is_alive():
                    self.logger.warning(f"{name} process did not terminate cleanly. Attempting force kill...")
                    if hasattr(proc, 'pid') and proc.pid:
                        os.kill(proc.pid, signal.SIGTERM)
                        proc.join(timeout=5)
                        if proc.is_alive():
                            self.logger.error(f"{name} process (PID {proc.pid}) could not be killed.")
                    else:
                        self.logger.error(f"{name} process has no PID; cannot force kill.")
            except Exception as e:
                self.logger.exception(f"Error force-killing {name} process: {e}")

        def main(self):
            self.logger.debug("main() - Starting main function")
            try:
                ### TODO: Consider using gevent.threadpool.ThreadPoolExecutor or gipc for more compatible multiprocessing support
                # https://github.com/gevent/gevent/blob/master/gevent/threadpool.py
                # https://github.com/benjaminp/gipc
                ### https://github.com/NagiosEnterprises/ncpa/issues/1291

                # instantiate child processes
                self.p, self.l = start_processes(self.options, self.config, self.has_error)
                self.ReportServiceStatus(win32service.SERVICE_RUNNING,
                                 win32service.SERVICE_ACCEPT_STOP | win32service.SERVICE_ACCEPT_SHUTDOWN)
                self.logger.debug("self.p and self.l processes started")
                self.logger.debug("value for self.p: %s", self.p)
                self.logger.debug("value for self.l: %s", self.l)

                # wait for stop event
                while self.running_event.is_set(): # shouldn't loop, but just in case the event triggers without stop being called
                    result = win32event.WaitForSingleObject(self.hWaitStop, 1000)
                    if result == win32event.WAIT_OBJECT_0:
                        break
                    time.sleep(0.1)
            finally:
                try:
                    self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                    self.logger.debug("SvcRun() - Service stop pending")
                except Exception as e:
                    self.logger.exception("SvcRun - Failed to report service stop pending: %s", e)

                # kill/clean up child processes
                try:
                    if self.p:
                        self.logger.info("Terminating passive process...")
                        self.p.terminate()
                        self.p.join(timeout=10)
                        if self.p.is_alive():
                            self.logger.warning("Passive process did not terminate cleanly.")
                            self.force_kill(self.p, "Passive")
                    if self.l:
                        self.logger.info("Terminating listener process...")
                        self.l.terminate()
                        self.l.join(timeout=10)
                        if self.l.is_alive():
                            self.logger.warning("Listener process did not terminate cleanly.")
                            self.force_kill(self.l, "Listener")
                    # Add any additional cleanup here (close files, sockets, etc.)
                    self.logger.debug("self.p and self.l processes terminated")
                    self.logger.debug("value for self.p: %s", self.p)
                    self.logger.debug("value for self.l: %s", self.l)
                    self.logger.info("Service cleanup complete. Exiting.")
                except Exception as e:
                    self.logger.exception("Error during service cleanup: %s", e)


# --------------------------
# Utility Functions
# --------------------------

def get_filename(file):
    """Get the proper file name when the application is frozen"""
    parent_logger.debug("get_filename(%s)", file)
    if __FROZEN__:
        appdir = os.path.dirname(sys.executable)
    else:
        appdir = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(appdir, file))

def get_configuration(config=None, configdir=None):
    """Get the configuration options and return the config parser for them"""
    parent_logger.debug("get_configuration()")

    config = os.path.join('etc', 'ncpa.cfg')
    configdir = os.path.join('etc', 'ncpa.cfg.d', '*.cfg')

    cp = ConfigParser(interpolation=None)
    cp.optionxform = str
    cp.read_dict(cfg_defaults)
    cp.read(get_filename(config))

    if configdir is not None:
        for config_file in sorted(glob.glob(get_filename(configdir))):
            cp.read(config_file)
    return cp

def chown(user_uid, user_gid, fn):
    """Change the ownership of a file to match the daemon uid/gid"""
    parent_logger.debug("Daemon - chown()")
    if not isinstance(user_uid, int):
        if not user_uid.isdigit():
            uid = pwd.getpwnam(user_uid).pw_uid
        else:
            uid = int(user_uid)

    if not isinstance(user_gid, int):
        if not user_gid.isdigit():
            gid = grp.getgrnam(user_gid).gr_gid
        else:
            gid = int(user_gid)

    if uid or gid:
        if not uid:
            uid = os.stat(fn).st_uid
        if not gid:
            gid = os.stat(fn).st_gid
        try:
            os.chown(fn, uid, gid)
        except OSError as err:
            sys.exit("can't chown(%s, %d, %d): %s, %s" %
            (repr(fn), uid, gid, err.errno, err.strerror))

def setup_logger(config, loggerinstance, logfile):
    """Configure the logging module"""
    name = getattr(loggerinstance, 'name')
    if config.get('general', 'loglevel') == 'debug':
        print ("setup_logger() - Name:", name, "File: ", logfile)

    loglevel = config.get('general', 'loglevel')
    logmaxmb = config.getint('general', 'logmaxmb')
    logbackups = config.getint('general', 'logbackups')

    try:
        level = int(loglevel)
    except ValueError:
        level = getattr(logging, loglevel.upper())

    handlers = []
    if logfile:
        if not logmaxmb:
            handlers.append(loggerinstance.FileHandler(logfile))
        else:
            max_log_size_bytes = logmaxmb * 1024 * 1024
            handlers.append(RotatingFileHandler(logfile, maxBytes=max_log_size_bytes, backupCount=logbackups))

        if __SYSTEM__ == 'posix' and os.path.isfile(logfile):
            chown(config.get('general', 'uid'), config.get('general', 'gid'), logfile)

    loggerinstance.setLevel(level)

    for h in handlers:
        h.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
        h.addFilter(tokenFilter)
        h.setLevel(level)
        loggerinstance.addHandler(h)

    hndlrs = loggerinstance.handlers
    loggerinstance.debug("Started log %s! Handlers: %s", loggerinstance, hndlrs)

def start_processes(options, config, has_error):
    """Start the processes for the listener and passive components"""
    try:
        # Create the database structure for checks
        db = database.DB()
        db.setup()
        l = p = ''

        if not options.get('listener_only') or options.get('passive_only'):
            p = Process(target=Passive, args=(options, config, has_error, True)) # old way
            p.daemon = True
            p.start()

        if not options.get('passive_only') or options.get('listener_only'):
            l = Process(target=Listener, args=(options, config, has_error, True))
            l.daemon = True
            l.start()

        return p, l

    except Exception as e:
        parent_logger.exception(e)
        sys.exit(1)

def get_options():
    """Get the options for the application (returns options to WinService)"""
    global options
    parent_logger.debug("get_options()")
    return options

def main(has_error):
    """Main function for the application on Linux/Mac OS X"""
    global options
    parser = ArgumentParser(description='''NCPA has multiple options and can
        be used to run Python scripts with the embedded version of Python or
        run the service/daemon in debug mode.''')

    # Script that should be run through the main binary if we want to use the
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

    parser.add_argument('-l', '--listener-only', action='store_true', default=False,
                        help='start listener without passive (if --passive-only is not selected)')

    parser.add_argument('-p', '--passive-only', action='store_true', default=False,
                        help='start passive without listener (if --listener-only is not selected)')

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
    parser.add_argument('-v', '--version', action='version', version=__VERSION__)

    # Get all options as a dict
    options = vars(parser.parse_args())

    # Read and parse the configuration file
    config = get_configuration(options['config_file'], options['config_dir'])

    if config.get('general', 'loglevel') == 'debug':
        print("main - options: ", options)


    # We set up the root logger here. It uses the listener log file, because the web components,
    # which are part of the listener system, need to propagate up to this log. We don't assign a file
    # handler to the listener_log, since it, too, will propagate up to the root logger and into the
    # listener log file.
    # Note: The passive-logger doesn't propagate up. It is a separate process, and we don't want
    # multiple processes trying to write to the same file.
    # That said, the listener log file will occasionally be used by two processes when --status or --stop
    # commands are executed, and at launch, before the parent daemonizes the listener and passive
    # processes. However, the traffic is very sparse, even in debug level, so it shouldn't cause any problems.
    listener_logfile = get_filename(config.get('listener', 'logfile'))
    log = logging.getLogger()
    setup_logger(config, log, listener_logfile)

    log.info("main - Python version: %s", sys.version)
    log.info("main - SSL version: %s", ssl.OPENSSL_VERSION)
    log.info("main - ZLIB version: %s", zlib_version)
    log.info("main - psutil version: %s", psutil.__version__)

    if __SYSTEM__ == 'nt':
        for sectionName, configSection in config.items():
            if sectionName == 'plugin directives':
                for pluginExtension in list(configSection.keys()):
                    if pluginExtension[0] == '.':
                        config[sectionName][pluginExtension.lower()] = configSection[pluginExtension]


    # If we are running this in debug mode from the command line, we need to
    # wait for the proper output to exit and kill the Passive and Listener
    # Note: We currently do not care about "safely" exiting them
    if options['debug_mode']:
        __DEBUG__ = True
        print("Debug init - options: ", options)

        # Set config value for port to 5700 and start Listener and Passive
        config.set('listener', 'port', '5700')

        # Temporary set up logging
        log = logging.getLogger()
        log.setLevel('DEBUG')

        p, l = start_processes(options, config, has_error)

        # Wait for exit
        print("Running in Debug Mode (https://localhost:5700/)\nPress enter to exit...\n", flush = True)
        input("Press enter to exit..\n")
        sys.exit(0)

    # If we are running on Linux or Mac OS X we will be using the
    # Daemon class to control the agent
    if __SYSTEM__ == 'posix':
        d = Daemon(options, config, has_error, parent_logger)
        process.daemon_manager.set_daemon(d)
        d.main()
    elif __SYSTEM__ == 'nt':
        # using win32serviceutil.ServiceFramework, run WinService as a service
        if len(sys.argv) == 1:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(WinService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            win32serviceutil.HandleCommandLine(WinService)

# --------------------------
# Launch the application
# --------------------------

has_error = Value('i', False)
if __name__ == '__main__':
    if __SYSTEM__ == 'nt': # Windows
        freeze_support() # needed for multiprocessing on Windows
    main(has_error)
