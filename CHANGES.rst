Changelog
+++++++++

2.1.0 - ??/??/2017
==================
- Removed deprecated aliases (service, process, and agent) as stated in 2.0.0 changelog section
- Added a new config option (allowed_hosts) to the [listener] section to block access except from specified addresses
- Added a new config option (run_with_sudo) to the [plugin directives] section to prepend the sudo command
- Added shell script to uninstall NCPA on Mac OS X by running "sudo /usr/local/ncpa/uninstall.sh"
- Added /IP and /PORT to silent install options for the Windows installer
- Added LD_LIBRARY_PATH to ncpa init scripts and include libssl and libcrypto so we have the latest OpenSSL libraries
- Added default_units configuration value to allow setting a default unit such as G or Gi for checks
- Added exclude_fs_types configuration value to remove certain file system types from the disk check
- Fixed searching for cmd causing any process with no cmd given to show up with any search

2.0.6 - 11/09/2017
==================
- Updated Python version to 2.7.14
- Updated gevent-websocket to version 0.10.1 so we do not need to use patched version
- Fixed passive checks not writing to the check history database
- Fixed API section for Internet Explorer
- Fixed issue when using the event_id filter on Windows event logs
- Fixed issue with spaces in URL-based passive checks
- Fixed catching of IOError with systems (typically virtual) that do not have any accessible partitions
- Fixed encoding problems in Timezones and Interfaces on Windows with non-English characters
- Fixed delta time values not working properly due to caching data on websockets
- Fixed large values showing up on initial check when viewing deltas

2.0.5 - 09/01/2017
==================
- Fixed the windows event log setting event_id to give the proper ID for some events that has bogus IDs
- Fixed issue with DB maintenance where DB is not accessible (both processes use it)
- Fixed non-integer PID file value causing startup issues
- Fixed issues with NFS errors causing failed starts (such as permission denied)

2.0.4 - 06/24/2017
==================
- Updated the API browser to grab your current hostname and port from the URL to show better active check output
- Updated processes API endpoint to properly also show full command with arguments
- Updated Windows installer to open incoming port in firewall for the port specified during install
- Fixed admin login page redirecting to "admin/config" which does not exists
- Fixed some JSON encoding errors from happening when utf-8 cannot decode properly
- Fixed issue with missing logging import in services.py
- Fixed upgrade issue where NCPA services would be stopped after upgrade (will start working after 2.0.4)
- Fixed issue in windows logging module where an infinite loop could be triggered based on logged_after time frame
- Fixed sqlite db timeout only being 5 seconds
- Fixed issue where initctl would override sysv initd script statuses for services
- Fixed file permissions on Linux with an updated .spec file
- Fixed match argument to be set when showing examples of active or passive check definitions from the GUI
- Fixed passive check definition for processes, services, and plugins endpoints

2.0.3 - 03/17/2017
==================
- Fixed some typos in the ncpa.cfg and sample config
- Fixed issue with Windows silent install setting various values to blank instead of defaults
- Fixed check for service scripts in init.d folder to ignore OSError exceptions
- Fixed typo in ncpa.cfg file that meant to say nrdp

2.0.2 - 01/19/2017
==================
- Updated plugins list to be sorted alphabetically when returning plugin list
- Updated plugins endpoint to use the debug URL parameter to have check also return the cmd line string
- Fixed issue with the parsing of command-line arguments sent to plugins quoting spaces unnecessarily
- Fixed default IP and Port definitions if either are not specified in ncpa.cfg
- Fixed issue with / in arguments passed to plugins (via check_ncpa.py and the API)
- Fixed output of check_ncpa.py in the "view alternative format" popup to use proper units argument
- Fixed service status output to display proper messages when pid file exists but daemon is not running

2.0.1 - 01/03/2017
==================
- Updated popover info boxes so they auto-hide when no longer in focus (once you click anywhere but the ?)
- Updated Windows service log file locations to var/log/win32service_ncpa<type>.log (logs for the services not NCPA)
- Updated Mac OS X install to give information about whether the install/upgrade finished or not
- Updated etc section to come with an ncpa.cfg.example version that shows new config values
- Updated Windows install to no longer reset the service settings by uninstalling/reinstalling the services
- Fixed issue with passive service when nrds was set (typically on upgrades) sending lots of errors to the log
- Fixed issue on Top Processes page where warning and critical thresholds didn't highlighting values
- Fixed issue with string encoding errors on certain systems in some API nodes
- Fixed issue with upgrades on unix systems ncpa- tmp files caused checks to give 500 errors from permission denied
- Fixed a 500 error in the admin section when no passive checks are defined
- Fixed services check with different match options (regex, search) to work as a check
- Fixed issue with services node not saving active check results
- Fixed issue with libffi not being included due to it being a shared library on most systems
- Fixed Windows threading issues with the win32service base

2.0.0 - 12/15/2016
==================

**Additions**

- Added SQLite3 DB backend for check results
- Added a new tab in the GUI for viewing past check results
- Added support for SSL protocols TLSv1.1 & TLSv1.2
- Added ability to adjust units B and b with T, Ti, Gi, Mi, Ki to match windows disk sizes using untis=x
- Added comments/help to the config file itself to help understand certain areas of the config that are confusing
- Added API endpoints system/time and system/timezone with current timestamp and timezone information
- Added plugin_timeout config option in ncpa.cfg [plugin directives] section
- Added default __HOST__ passive check definition so it doesn't show up as unknown forever
- Added delay_start option to listener and passive section of ncpa.cfg to actually run after a # of seconds
- Added ability to relocate RPM install (ex: --prefix=/opt would install /opt/ncpa)
- Added disk/mount for giving information on partitions that aren't currently accessible, such as cdroms
- Added redirection when logging in if the user was trying to access a protected page
- Added better output messages for multi-checks (ex: memory/virtual?check=true, disk/C:|?check=true)
- Added API browser which allows going through the API and creating checks, understanding units, etc
- Added admin web GUI section for in-browser viewing of passive checks, process control, etc
- Added admin_x config values into default ncpa.cfg for Web GUI admin section
- Added information into api/logs node to explain how to get logs to be populated
- Added '/s' onto the unit when using the delta argument outside of checks
- Added all new documentation and examples for setting up NCPA on any type of system
- Added in the Windows Event Log tail functionality that was never released
- Added new config options for managing check result retention and if check results should be retained

**Updates**

- Updated api/agent/plugin to just api/plugins (check deprecation to see more about api/agent/plugins)
- Updated web UI with modern theme with better graph styling
- Updated self-signed SSL certs to use 2048bit RSA and sha256 signature
- Updated unit names that were set to c that weren't actually generic counters for better graphing
- Updated top processes to not show Idle process on Windows and added % / rounding
- Updated default locations on fresh install for log files on windows and linux
- Updated openssl and PyOpenSSL libraries which no longer accept SSLv2 & SSLv3
- Updated API to round most values that had been calculated to 2 decimals including check results and perfdata
- Updated default configuration for passive checks to be located in the ncpa.cfg.d/ folder
- Updated RPM .spec file information for new locations and summary/description information
- Updated API to now automatically update disk partitions and other static items except while websocket is open
- Updated Linux and Mac OS X installs to use nagios group instead of nagcmd group like other Nagios products
- Updated Windows installer to now have multiple sections that edit listener, passive, and passive check configs
- Updated RPM, DEB, and DMG to allow upgrading from older versions without issues
- Updated api/services check to default to running (currently leaving off status=x will always return critical)
- Updated output of certain checks to have more information (api/services, api/memory/logical/percent)
- Updated processes output to include 'mem_percent' since it can be used as a filter
- Updated processes output of 'mem_rss' and 'mem_vms' to show units and respect the 'units' modifier
- Updated filtering processes by 'name' and 'exe' field to also be able to use 'match' type (exact, search, or regex)
- Updated filtering services by 'service' field to allow using the 'match' type too (exact, search, or regex)
- Updated delta values to not cause weird issues when calling the same endpoint from different sources
- Updated ncpa_listener and ncpa_passive init.d files to be more reliable
- Updated the services ncpa_posix_type to now be ncpa_type on Unix systems to conform to init.d service names
- Updated websocket endpoints to be /ws/top, /ws/tail, /ws/api instead of <name>-websocket
- Updated the way that the init scripts work on Linux systems to give better output

**Bug Fixes**

- Fixed single value objects that are given a conversion value via units from becoming lists (#250)
- Fixed services list on el7 (and all systemctl systems)
- Fixed registry key placement for fresh installs on Windows
- Fixed using multiple values passed to nodes for filtering in API and active checks (ex. service=x&service=y)
- Fixed units=x setting to only affecting b and B units not all unit types
- Fixed API showing b instead of B for bytes in multiple locations
- Fixed ncpa.cfg ssl_version option not actually working for Windows version
- Fixed handlers config variable from throwing errors when empty or set to None
- Fixed issue with large plugin output (4KB+ on windows and 64KB+ on linux) could crash NCPA
- Fixed errors thrown by clients ending websocket connections by changing pages not being caught and handled properly
- Fixed issue where having no passive NRDP checks would give errors in ncpa_passive.log
- Fixed regex issue for warning and critical values
- Fixed stdout and returncode swapped when doing checks on nodes that can't be checked (ex: user/list)
- Fixed RPM uninstall to stop the NCPA processes before it removes the NCPA files
- Fixed issue on OS X where plugin directory was not readable by nagios due to LaunchDaemon permissions
- Fixed issue on Windows systems not having accurate network I/O if bytes > 4.3GB
- Fixed issue with iptables showing up as stopped even while running in CentOS/RHEL 6 and 7
- Fixed issue with multiple services always showing stopped in CentOS/RHEL 6 systems relying on initd
- Fixed zombie process error in Mac OS X top websocket making the GUI top display nothing
- Fixed graphs tab not displaying graphs of interfaces with multiple spaces in their names
- Fixed passive service on Windows only able to successfully run a plugin-based check once after restarting
- Fixed output of disk space on Linux servers not showing reserved root disk space as used
- Fixed check output formatting on parent nodes when running multi-checks
- Fixed device_name on api/disk/logical node when units passed giving an error
- Fixed perfdata output for windows log checks
- Fixed issue on Mac OS X where running as nagios (default) would cause process data not to show
- Fixed issue where global config parser defaults caused issues with sections in separate files
- Fixed issue where services in Unix systems ran as root no matter what the uid/gid specified in ncpa.cfg
- Fixed delta value returning 0 the first time it's called even if there should be 1 second of data
- Fixed Mac OS X plist to no longer set user/group (bug fix for Unix systems running as specified uid/gid is related)
- Fixed processor type not showing up on all Linux distros on GUI dashboard
- Fixed issue with relative plugin paths on Linux systems when they are built

**Deprecated**

- Both API endoints api/service/<servicename> and api/process/<processname> will be removed in version 3 and should be replaced by api/services?service=<servicename> and api/processes?name=<processname> instead
- The API endpoint api/agent/plugin/<pluginname> will be removed in version 3 in favor of api/plugins/<pluginname> which better matches the current API node naming conventions and is a less confusing name

1.8.1 - 04/09/2015
==================
- Fixed aggregation of CPU percent only working on Windows
- Fixed system/uptime not working on Windows

1.8.0 - 04/02/2015
==================
- Added graphing frontend, available via /graph-picker.html
- Added PID to process information returned by the API
- Adding aggregate function to aggregate list values for checks
- Adding uptime under /api/system/uptime
- Added delayed starting to windows NCPA services
- Changed web sockets to fail gracefully
- Changed uninstall key location for Windows users to be under HKCU
- Changed unit for the user count to be ‘’ rather than c
- Changed plugin to allow passed query arguments to URL
- Changed plugin to remove perfdata
- Changed windows NCPA services to be more windows-like
- Fixed Mac OS installer group/user issues
- Fixed NRDS file path issue on windows
- Fixing issues with /graph and accessing the same state file
- Fixed issue where page head links showed up on /login page
- Fixed issue where server would reject API POST queries
- Fixed windows installer to now upgrade NCPA when NCPA is installed already
- Fixed windows installer to not overwrite configuration file

1.7.2 - 08/28/2014
==================
- Fixed API giving 500 error on windows when filtering processes
- Fixed services filtering by single service name
- Fixed NCPA Passive init.d script on Debian systems
- Fixed issue where warning/critical values were truncated

1.7.1 - 08/19/2014
==================
- Added backwards compatability with the api/service(s) call to work with old plugins/checks
- Added log rotation to all clients, logs rotate at 20MB and will rotate once before overwriting old logs
- Added safeguards when importing disk nodes that prevented the listener from starting in certain circumstances
- Added link to the /top service in the web UI
- Added "diskperf -Y" command to automatically run during Windows install
- Added favicon to the web UI
- Removed unused files and old static docs
- Updated log format to be more descriptive
- Updated test runner to be Python rather than sh to run tests on Windows
- Updated plugin/file type directives to now retain quotes around $plugin_name when being passed to the command line
- Updated styling of main web UI screen
- Fixed issue with SSL certificates using the same serial number
- Fixed threading error on NCPA listener start/stop
- Fixed 500 access error on access
- Fixed Windows logging issue where logs were not at var/\*.log
- Fixed process count checks returning wrong number of processes

1.7.0 - 07/29/2014
==================
- Added full tests for NRDP
- Added realtime graphs
- Added Windows Event Log monitoring
- Added Windows counters monitoring ability
- Added manually creating SSL certificates, and added ability to specify cert and key files by specifying in the
  certificate field by a comma-delimited [path/to/cert],[path/to/key]
- Updated help documentation to include changes in 1.7.0
- Updated to non-blocking system using gevent to accomodate many connections
- Updated from the Flask development server for serving HTTPS requests
- Fixed init script for listener not getting the PID file correctly
- Fixed build issue with cx_Freeze which caused the built agent to not run
- Fixed build issue with docs not building during build process
- Fixed dependency issues with Debian systems
- Fixed doc builds during compilation
