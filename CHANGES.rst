Changelog
+++++++++
3.2.2 - 12/xx/2025
==================
**Updates**

- Update login shell for nagios user on linux systems to /sbin/nologin for improved security. [GH#:1289] - CPD
- Update Python to 3.13.9 on Windows builds. [GH#1304] - CPD

**Bug Fixes** 

- Fixed an issue where stopping the NCPA service would cause errors in the scm and event viewer on Windows systems. - CPD
- Fixed an issue where some log lines were showing up twice on Windows systems. - CPD

3.2.1 - 10/29/2025
==================
**Bug Fixes** 

- Fixed an issue where the services endpoint would break on Solaris. [GL-NCPA#18] - BB, CPD
- Fixed an issue where NCPA wouldn't build properly on Fedora per MrPippin66's instructions. [GH:#1148] - BB
- Fixed an issue where the build would fail because a venv directory was missing from the PATH with cyanarmadillo's help. [GH:#1295] - CPD

3.2.0 - 08/21/2025
==================
**Added**

- Added experimental support for Solaris 11.4 builds. (Blake Bahner)

**Updates**

- Rewrote the build process for Unix environments to use virtual environments for Python dependencies, improving compatibility and build reliability. (Blake Bahner)
- Improved process killing logic on Unix and Windows systems to handle more edge cases and ensure all child processes are terminated. (Blake Bahner)
- Updated passive check sending to attempt certificate verification when possible, falling back to legacy behavior if verification fails. (Blake Bahner)

**Bug Fixes**

- Fixed an issue where the API form would not clear fields after certain actions. (Blake Bahner)
- Fixed an issue where NCPA couldn't upgrade or uninstall on Windows due to a locked file. [GH:#1210,#1281,GL-NCPA:#17] (Blake Bahner)

3.1.4 - 07/30/2025
==================
**Added**

- Added support for ARM64 builds for Linux. (DevSysEngineer)
- Added psutil version to the dashboard to help diagnose issues. (Blake Bahner)
- Added the ability to disable NCPA's web UI in the configuration file. [GH:#1254] (Blake Bahner)

**Updates**

- Improved .deb build process to improve compatibility with various Debian-based distributions. (Blake Bahner)
- Improved service handling on Windows to reduce/resolve startup/running issues, particularly around conflicts with Windows' Event Log process. (Blake Bahner)
- Improved the efficiency of several API endpoints. (Blake Bahner)
- Updated the bundled Python version to resolve CVEs and improve compatibility. (Blake Bahner)
- Updated the bundled OpenSSL version to resolve CVEs and improve compatibility. (Blake Bahner)
- Updated psutil to version 7.0.0, resolving many issues.

3.1.3 - 01/28/2025
==================
**Bug Fixes**

- Fixed an issue on Windows where upgrading NCPA to a new Python minor version would cause the service to fail to start. [GH:#1242] (Blake Bahner)

3.1.2 - 01/15/2025
==================
**Updates**

- Added debug logging to reverse DNS lookups to help diagnose issues. (Craig Dienger)
- Added interface status to the interface endpoint. [GH:#1220] (Blake Bahner)
- Reworked the interface endpoint to be more efficient. [GH:#1001] (Blake Bahner)
- Updated check logging to give more details when a check fails due to unexpected types. (Blake Bahner)
- Updated our instantiation of WSGI server to properly set the error log file. [GH:#1227] (Blake Bahner)
- Updated OpenSSL to 3.2.3 on Linux builds. (Blake Bahner)
- Updated Python to 3.12.8 on Windows builds. (Blake Bahner)

**Bug Fixes**

- Fixed an issue where API endpoints could report an erroneous unexpected type error. (Blake Bahner)
- Improved service handling on Windows to reduce the likelihood of problems arising and to resolve an error that was being sent to Windows Event Log. (Blake Bahner)
- Updated processes check output to preserve perfdata formatting for RRD graphs. [GH:#1224] (Blake Bahner)

3.1.1 - 09/19/2024
==================
**Updates**

- Updated to OpenSSL 3.0.15 to resolve some CVEs. [GH:#1176] (Blake Bahner)
- Updated to Python to 3.12.6 for Windows builds to resolve some CVEs. (Blake Bahner)
- Updated the RPM hash to SHA256 to enable the installation of NCPA in FIPS mode. [GH:#1168] (Blake Bahner)
- Dropped support for CentOS 8, RHEL/Oracle 7, Debian 10 and Ubuntu 18 due to OpenSSL no longer supporting these platforms. (Blake Bahner)

**Bug Fixes**

- Fixed an issue where NCPA would show an error if the logs were missing. (Ivan-Roger)
- Fixed an issue that would cause NCPA to crash in debug mode due to a wrongly called function. (Ivan-Roger)
- Fixed an issue where new NCPA builds would fail because of a cx_Freeze update. [GH:#1177,#1178] (Blake Bahner)
- Fixed an issue where several disk endpoints could give errors instead of values. [GH:#1191] (Blake Bahner)

3.1.0 - 05/16/2024
==================
**Updates**

- Added the ability to configure certain settings in the NCPA interface. [GH#1144] (Blake Bahner)
- Added migration of NCPA 2 configuration files and plugins to NCPA 3. [GH#1097] (Blake Bahner)
- Made the NCPA 3 plugins and directives case-insensitive on Windows to match standard Windows behavior. [GH#1137] (Blake Bahner)
- Removed misleading information from the NCPA 3 configuration file.  (Blake Bahner)
- Updated passive checks to allow escaped spaces. [GH#1089] (Blake Bahner)
- Improved the NCPA token filter to cause significantly fewer crashes when something else goes wrong. (Blake Bahner)

**Bug Fixes**

- Fixed the allocation of loggers for sections of NCPA that were not logging properly. (Blake Bahner)
- Fixed an issue where passive checks would malfunction when handling API endpoints and hostnames/servicenames with whitespaces that were escaped or encapsulated in quotes. (Blake Bahner)
- Fixed an issue where NCPA would crash when psutil couldn't find certain file systems. [GH#1141] (Blake Bahner)
- Fixed an issue where NCPA would crash if it couldn't process disk information. (Blake Bahner)

3.0.2 - 03/20/2024
==================
**Updates**

- Added a filter to log output to remove tokens from the WSGI Server's log output. (Blake Bahner)
- Added busy_time to the disk/physical endpoint on posix systems to provide the percentage of time the disk is busy. (Blake Bahner)
- Updated the bundled Python version to 3.11.8 and OpenSSL version to 3.0.13 to resolve CVEs. (Blake Bahner)
- Updated the bundled zLib version and link so the build won't break when zLib is updated. (Blake Bahner)

**Bug Fixes**

- Fixed an issue where plugins with unrecognized file extensions would not be executed. (Blake Bahner)
- Fixed an issue where NCPA would fail to restart after rebooting the host server (Sebastian Wolf, Blake Bahner)
- Fixed an issue where NCPA would crash if the passive log file was not present. (Ivan-Roger)
- Fixed an issue where plugins would fail to execute if the user's group had permission, but the user did not. (graham-collinson)
- Fixed an issue where NCPA would crash if ssl_ciphers was set for the listener. (Ivan-Roger)
- Fixed a documentation issue where the pid file name was not updated to reflect the NCPA 3 changes. (Blake Bahner)
- Fixed an issue where NCPA would crash if a plugin had no output. (Blake Bahner)
- Fixed an issue where Windows logs with a different date format would fail to parse. (gittethis)
- Fixed an issue where certain RHEL systems would fail to start NCPA on reboot. (Blake Bahner)
- Fixed an issue where Mac builds would fail due to a change in a dependency library. (Blake Bahner)

3.0.1 - 12/13/2023
==================
**Updates**

- Updated more documentation to reflect changes in NCPA 3.0.0 (Michael Bellerue)

**Bug Fixes**

- Fixed an issue where the API ordering varied from NCPA 2, breaking historical data. (Blake Bahner)
- Fixed an issue where NCPA would fail to start if IPv6 was disabled. (Blake Bahner)
- Corrected several issues with NCPA 2 file removal during Debian system upgrades. (Blake Bahner, Jason Michaelson)
- Disabled config interpolation to match the behavior of NCPA 2 and allow the `%` character to be unescaped in configuration files. (Blake Bahner)
- Resolved errors appearing in Linux installs where the installation was actually successful. (Blake Bahner, Jason Michaelson)
- Enhanced build process to support building on Oracle Linux 8 & 9. (Blake Bahner)
- Added a check for NCPA 2 processes in Linux builds on distributions utilizing chkconfig. (Jason Michaelson)
- Added various checks for NCPA services before attempting to interact with them. (Blake Bahner)

3.0.0 - 11/17/2023
==================
**Updates**

- Updated the bundled Python version to 3.11.3 (PhreditorNG)
- Updated to bundle OpenSSLv3 in all packages (PhreditorNG/Blake Bahner)
- Updated to bundle zLib in all packages (PhreditorNG)
- Simplified environment setup and build process to use only one script (PhreditorNG/Blake Bahner)
- The listener and passive services/daemons are now combined into one service/daemon called ncpa
- Added configuration option to allow only "Listener" or "Passive" functionality to be used (PhreditorNG)
- Improved logging and installation output (PhreditorNG)
- Added systemd service file (PhreditorNG)
- Listener web UI Admin section provides additional system information (PhreditorNG)
- Updated jQuery to 3.6.4
- Removed support for 32-bit systems.

**Bug Fixes**

- Fixed errors from different language encodings due to python not being able to encode/decode strings


2.4.1 - 02/27/2023
==================
- Note: For the time being, we're stopping 1st-party builds for the following platforms:
   - 32-bit Macintosh
   - CentOS 8 on ARM
   - Solaris 11
   - SLES 11
   - AIX 7 (as of NCPA 2.2.2)
   - Raspbian (as of NCPA 2.3.0)
- (cont.) You are still welcome to build these packages yourself - see BUILDING.rst for details (Sebastian Wolf)
- Replaced timing attack vulnerable password/token comparisons with HMAC compare_digest (#902) (PhreditorNG)
- Made minor modifications to dependencies and build code to maintain Python 2 build process (PhreditorNG)

2.4.0 - 12/16/2021
==================
- Added new disk metrics max_file_length and max_path_length (#760) (ccztux)
- Added php and perl to the default plugin extensions (#766) (ccztux)
- Changed the default plugin_timeout value from 60s to 59s (#761) (ccztux)
- Changed python default plugin extension to python3 (#786) (ccztux)
- Fixed ZeroDivisionError: float division by zero (#769) (ccztux)
- Fixed connection to NRDP server can hang indefinitely (#776) (ccztux)
- Fixed toggle long output doesnt work (#778) (ccztux)
- Fixed the filter Type gets lost on pages > 1 (#780) (ccztux)
- Fixed some configuration directives doesnt work, e.g. all_partitions and follow_symlinks (#757) (ccztux)
- Fixed issue with systemctl not showing services due to output (#791)
- Fixed default value of exlude_fs_types differs from documented default value (#823) (ccztux)
- Fixed ERROR an integer is required on max_connections configuration (#812) (ccztux)
- Fixed Minor bug. Delta checkbox isn't showing in NCPA interface on Windows (#747) (ccztux)
- Fixed XSS security vulnerability in tail event log gui page (CVE-2021-43584) (#830)

2.3.1 - 02/11/2021
==================
- Fixed uninstalling DEB package leaves systemd service active (#651) (ccztux)
- Fixed error when running a service check using match=search or match=regex searching (#626,#679,#742)
- Fixed perfdata variable not being set for child node run_check command causing 500 error if the check errors (#733)
- Fixed API page output for active/passive checks using windowscounters sleep options (#722)
- Fixed warning/critical values in perfdata output when values were not actually related to the data (#712,#713)

2.3.0 - 01/28/2021
==================
- Added option to to use symlinks in the plugin path directory (#577) (infraweavers, ccztux)
- Added version option to ncpa_listener and ncpa_passive (ccztux)
- Added support of hostnames in allowed_hosts (#653) (ccztux)
- Added secure cookie attribute (#659)
- Added new memory endpoints swap/swapped_in and swap/swapped_out (#674) (ccztux)
- Added new disk endpoint inodes_used_percent (#672) (ccztux)
- Fixed issue with allowed_hosts config directive doesnt work (#638, #660) (ccztux)
- Fixed ncpa_listener fails to start when IPv6 is disabled. (#648) (ccztux)
- Fixed if an exception was thrown in one api endpoint it breaks the wohle api (#670) (ccztux)
- Fixed missing unit (%) for some process checks (#681) (ccztux)
- Fixed childs started from a plugin will not be killed in case plugin_timeout was reached (#714) (ccztux)
- Fixed error message in case plugin runs into timeout out was not shown (#714) (ccztux)
- Fixed passive checks stop sending if there are multiple NRDP servers configured and both NRDP servers are not listening. (#715) (ccztux)
- Fixed missing configuration options in the default ncpa.cfg (#726) (ccztux)
- Updated bootstrap to 3.4.1 to fix security issue in CVE-2019-8331 (#728) (ccztux)
- Fixed missing configuration sections in the admin section of the GUI (#725) (ccztux)
- Fixed Swap Memory issue causing errors for Solaris 10/11 builds

2.2.2 - 06/19/2020
==================
- Updated jQuery to 3.5.1 to fix security issues in CVE-2020-11022
- Fixed issue with Windows silent install where not defining /PORT would open firewall for any port (#631)
- Fixed documentation issue with run_with_sudo (#623)

2.2.1 - 02/24/2020
==================
- Updated jQuery to 3.4.1 to fix security issues in CVE-2015-9251 and CVE-2019-11358
- Updated D3.js graphing library from version 4.x to 5.x
- Updated service API endpoint UNKNOWN output to explain what services were not found (#600,#601)
- Fixed ncpa.db file would being rewritten on upgrades, future upgrades will not have this happen (#589)
- Fixed issue with Solaris 11.4 services output parsing (thanks ljlapierre) (#610)
- Fixed GUI API browser active/passive check examples for the logs module missing filters (#595)
- Fixed issue with Kernel version 5.5+ not working properly on disk checks

2.2.0 - 10/24/2019
==================
- Added registry ProductID to Windows install registery key for easier lookup (#579)
- Added proper UNKNOWN output text prefix on checks that return UNKNOWN states (#575)
- Added X-Frame-Options and Content-Security-Policy to not allow NCPA in frames by default
- Added allowed_sources option in ncpa.cfg to give allowed sources to bypass the frame restrictions
- Added autocomplete="off" tag to stop autocomplete on login pages for GUI and Admin section
- Updated windowscounters API to use AddEnglishCounter instead of AddCounter to not translate counter names
- Fixed get_counter_path() throwing exception for counter names which contain parentheses (#564)
- Fixed GUI creating improper check_ncpa.py active check command when using the delta option (#583)
- Fixed unnecessary perfdata value in JSON output that is only used internally (#570)
- Fixed old uninstall registry key on Windows systems (#551)
- Fixed random UNKNOWN check_ncpa.py responses from gevent causing socket disconnects (#532)

2.1.9 - 09/04/2019
==================
- Added option all_partitions to ncpa.cfg to only display what psutil says are physical local disks
- Fixed issue in Admin section where URLs not working properly
- Fixed max_connections setting not working on Windows
- Fixed get_root_node() not reading and applying config on initial startup
- Fixed allowed_hosts config option causing forbidden error messages when using passive checks

2.1.8 - 07/17/2019
==================
- Fixed issue with HTTP 308 redirection when connecting to API endpoints without forward slash
- Fixed error when using windowscounters "bad file descriptor"
- Fixed windowscounters not properly displaying errors in the check output or API output
- Fixed windowscounters checks with errors now return unknown
- Fixed default IP address in Windows when IP address is empty in the config
- Fixed issue with Solaris installs not properly stopping the ncpa listener service
- Fixed issue on Windows install where the proper registry key was not being set

2.1.7 - 05/09/2019
==================
- Updated builds to not use shared python library which causes issues on certain systems
- Fixed issue with Windows silent installs not having 0.0.0.0 set as default when no IP is defined
- Fixed issue where some special Windows counters could not be identified
- Fixed issue with pipe characters in returned error output for disk nodes
- Fixed uninstall registry key in Windows not selecting the proper location due to missing install page
- Fixed issue with mountpoints that cannot access filesystem info causing error

2.1.6 - 10/12/2018
==================
- Added max_connections listener config value to set the amount of concurrent connections
- Added Solaris support and build process
- Added new build process that automatically creates build for OS type
- Fixed issue with temp directory having too many files causing python exception at launch
- Fixed running checks on processes with float values for AIX and Mac OS X systems
- Fixed file permissions on Linux systems to increase security

2.1.5 - 06/11/2018
==================
- Fixed issue with a few Windows counters that required forward slashes in the path name
- Fixed issue where Windows counters were not clearing the counter/query handler
- Fixed issues with SLES installs not working properly

2.1.4 - 04/17/2018
==================
- Added ssl_ciphers config option to only allow specific SSL ciphers
- Added more filesystems types to ignore
- Fixed issue where total CPU and memory usage in processes were actually averages
- Fixed error when trying to run check on a full interface node
- Fixed issue with processes not doing proper exact matches for most properties
- Fixed folder mountpoints not showing on Windows up due to psutil version on build

2.1.3 - 02/28/2018
==================
- Fixed issue with plugins not executing the plugin return function properly

2.1.2 - 02/27/2018
==================
- Added more pseudo devices into default list of devices to skip
- Fixed websockets (live graphs, top, and tail) not displaying data due to encoding changes
- Fixed issue where user's groups were not being set when dropping from root privileges
- Fixed Mac OS X uninstall.sh script being installed properly
- Fixed issue with nagios user and group on Mac OS X not being created
- Fixed issue in windowscounters node creating a 500 error
- Fixed service name check on EL6 causing services to show as running when stopped or unknown
- Fixed python plugins not running properly due to the LD_LIBRARY_PATH environment variable

2.1.1 - 12/21/2017
==================
- Fixed the return values for checks that do not return int/float values

2.1.0 - 12/19/2017
==================
- Removed deprecated aliases (service, process, and agent) as stated in 2.0.0 changelog section
- Added a new config option (allowed_hosts) to the [listener] section to block access except from specified addresses
- Added a new config option (run_with_sudo) to the [plugin directives] section to prepend the sudo command
- Added shell script to uninstall NCPA on Mac OS X by running "sudo /usr/local/ncpa/uninstall.sh"
- Added /IP and /PORT to silent install options for the Windows installer
- Added LD_LIBRARY_PATH to ncpa init scripts and include libssl and libcrypto so we have the latest OpenSSL libraries
- Added default_units configuration value to allow setting a default unit such as G or Gi for checks
- Added exclude_fs_types configuration value to remove certain file system types from the disk check
- Added a Kafka-Producer for passive checks
- Added log message (and other log data) in to check as long output for Windows logs
- Added processes into long output for processes endpoint and performance data output for all processes matched
- Added ability run "interface/<interface name>" as a check to return all interface data
- Added unknown service state when permissions of the nagios user stop service from checking running state
- Added processes filter for username and updated GUI API browser
- Added AIX support to the main branch (merged aix branch in)
- Added long output toggle button in checks page to show all long output for process/log checks
- Added ability to pass plugin arguments through the args POST/GET parameter instead of only through path
- Added ability to have comma separated nrdp servers set for parent (and comma separated tokens)
- Fixed searching for cmd causing any process with no cmd given to show up with any search
- Fixed services on el6 to no longer use a grep for the a process and rely on psutil and service instead
- Fixed issue with Firefox running in Windows causing websocket encoding errors
- Fixed thresholds with colon (:) in front to be treated like a regular number instead of giving an error
- Fixed problem with multiple arguments passed via query string for passive URL-based checks
- Fixed upgrades on Windows to only start the ncpa services that were running before upgrade
- Fixed check settings not showing up on system/uptime and added human readable output to check return output

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
- Fixed issue where services in Unix systems run as root no matter what the uid/gid specified in ncpa.cfg
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
