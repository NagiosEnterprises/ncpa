1.0.0
-----
- Added backwards compatability for 1.7.x and 1.8.x
- Added -s, --secure flag on Python 2.7.9+ client systems to force verify SSL certificate (does not verify by default since most SSL certs are self-signed)
- Updated default timeout to 60 seconds
- Updated --unit to --units (-u) and --units to --unit-name (-n) to avoid confusion and to match the API
- Updated -s, --super-verbose flag to be -d, --debug so that secure flag can be added
- Fixed issue where connection reset errors were frequently raised with simultaneous checks
- Fixed issue where metrics with spaces in their name were not url encoded

0.3.5
-----
- Added in the 'queryargs' variable to pass in extra arguments to the URL being called
- Fixed missing query_args error

0.3.4
-----
- Added timeout option (-T)

0.3.3
-----
- Fixed issue where --list with no metric would cause an error

0.3.2
-----
- Fixed issue where --unit would change the base unit, not the unit prefix
- Added --units/-n that will change the base unit

0.3.1
-----
- Added quoting to arguments intended to by passed to Nagios plugins, all HTML element given with --arguments, -a will be escaped
- Added --super-verbose flag to aid in debugging. Adds stack track on Exceptional exit
- Moved to Major.Minor.Maintenance versioning scheme to align with NCPA
- Added sanity check so -a/--arguments cannot be called when not calling a plugin

0.3
---
- Moved into main git repository
- Fixed minor bugs

0.2
---
- Fixed Python2 incompatibility.
