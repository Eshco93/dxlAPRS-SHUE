# mainConfig.py - Main configuration parameters
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Third-party modules
import re
import os.path
# Own modules
import parameterChecks


# Definition of configuration parameters
# Values: full name, type, default, positional argument, description, check function, required
configuration_parameters = {
    'loglevelp': ['Print Logging Level', int, 3, 'i', 'Logging level for the printed log (Between 1 and 5)', lambda a: str(a).isdigit() and 1 <= int(a) <= 5, False],
    'loglevelw': ['Write Logging Level', int, 3, 'j', 'Logging level for the written log (Between 1 and 5)', lambda a: str(a).isdigit() and 1 <= int(a) <= 5, False],
    'runtime': ['Runtime', int, 0, 't', 'Runtime in seconds (0 for infinite runtime)', lambda a: str(a).isdigit() and int(a) >= 0, False],
    'addr': ['Address', str, '127.0.0.1', 'a', 'IP address for receiving the APRS packages', lambda a: parameterChecks.check_address(a), False],
    'port': ['Port', int, 18001, 'p', 'Port for receiving the APRS packages', lambda a: str(a).isdigit() and 1024 <= int(a) <= 65353, False],
    'filepath': ['File Path', str, os.getcwd() + '\log', 'd', 'Path for the files written by the program', lambda a: os.path.exists(a), False],
    'writeo': ['Write Raw Data', int, 0, 's', 'Write setting for the raw data (0 = no / 1 = yes)', lambda a: str(a).isdigit() and 0 <= int(a) <= 1, False],
    'writet': ['Write Telemetry', int, 0, 'w', 'Write setting for the telemetry (0 = no / 1 = yes)', lambda a: str(a).isdigit() and 0 <= int(a) <= 1, False],
    'writer': ['Write Reformatted Telemetry', int, 0, 'z', 'Write setting for the reformatted telemetry (0 = no / 1 = yes)', lambda a: str(a).isdigit() and 0 <= int(a) <= 1, False],
    'writel': ['Write Log', int, 1, 'k', 'Write setting for the log (0 = no / 1 = yes)', lambda a: str(a).isdigit() and 0 <= int(a) <= 1, False],
    'qaprs': ['APRS Queue Size', int, 20, 'q', 'Size of the queue for storing the APRS packages after receiving and before parsing', lambda a: str(a).isdigit() and 1 <= int(a) <= 100, False],
    'qupl': ['Upload Queue Size', int, 100, 'f', 'Size of the queue for storing the radiosonde telemetry packages after parsing and before uploading', lambda a: str(a).isdigit() and 1 <= int(a) <= 600, False],
    'call': ['User Callsign', str, None, 'c', 'User callsign for SondeHub', lambda a: parameterChecks.check_user_callsign(a, 4, 15), True],
    'pos': ['User Position', list, None, 'l', 'User position for SondeHub', lambda a: parameterChecks.check_user_position(a, -100, 8000), True],
    'ant': ['User Antenna', str, '1/4 wave monopole', 'v', 'User antenna for SondeHub', lambda a: 4 <= len(a) <= 25, False],
    'mail': ['Contact E-Mail', str, None, 'u', 'User e-mail for SondeHub', lambda a: bool(re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', a)), True],
    'posu': ['User Position Update Rate', int, 6, 'g', 'User position update rate for SondeHub', lambda a: str(a).isdigit() and 1 <= int(a) <= 24, False],
    'telemu': ['Telemetry Update Rate', int, 30, 'r', 'Telemetry update rate for SondeHub', lambda a: str(a).isdigit() and 1 <= int(a) <= 600, False],
    'timeout': ['Upload Timeout', int, 20, 'o', 'Upload timeout for SondeHub', lambda a: str(a).isdigit() and 1 <= int(a) <= 60, False],
    'retry': ['Upload Retries', int, 5, 'e', 'Upload retries for SondeHub', lambda a: str(a).isdigit() and 1 <= int(a) <= 60, False]
}

# Other definitions
closetime_on_error = 5
