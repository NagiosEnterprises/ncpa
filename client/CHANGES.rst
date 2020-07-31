Changelog
+++++++++

1.2.2
-----
- Fixed error output text giving no check output, now errors show CRITICAL with error message when encountered
- Fixed output of UTF-8 characters that are passed back by the agent

1.2.1
-----
- Fixed an issue throwing an attribute error in case of an http error with python 2.6. (Christian Zettel)

1.2.0
-----
- Added detailed information in case of connection errors, http errors and errors thrown by the agent (Christian Zettel)
- Fixed incompatibility with Python 3.7 and 3.8 (Christian Zettel)
- Fixed Option: --performance is incompatible with Python 2.6.6 (Christian Zettel)

1.1.6
-----
- Fixed list api tree only possible with activated verbose mode (Christian Zettel)

1.1.5
-----
- Fixed incompatability with Python 3 when using certain options

1.1.4
-----
- Fixed issue with older NCPA < 2 with reversed stdout and returncode sections

1.1.3
-----
- Fixed splitting of commas in query params so that if a comma is in quotes it will pass it

1.1.2
-----
- Fixed issue with long output being passed as args through query parameters

1.1.1
-----
- Fixed sending multiple query arguments not being sent to the API

1.1.0
-----
- Added performance data option (-p) for checks that do not return performance data (gregwalters)
- Fixed issue where arguments were being passed without breaking on whitespace
- Reverted change for "unitprefix" back to just "units" to match the API calls (-u is still the same, units)

1.0.2
-----
- Fixed issue where arguments check was checking for "agent/plugin" only

1.0.1
-----
- Fixed units to be named "unitprefix" for less confusion

1.0.0
-----
- Added backwards compatability for 1.7.x and 1.8.x
- Added -s, --secure flag on Python 2.7.9+ client systems to force verify SSL certificate (does not verify by default since most SSL certs are self-signed)
- Updated default timeout to 60 seconds
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
