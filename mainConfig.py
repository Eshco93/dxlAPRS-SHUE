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
configuration_parameters = {
    'loglevelp':
    {
        'full_name':            'Print Logging Level',
        'type':                 int,
        'default':              3,
        'positional_argument':  'i',
        'description':          'Logging level for the printed log (Between 1 and 5)',
        'check_function':       lambda a: str(a).isdigit() and 1 <= int(a) <= 5,
        'required':             False
    },
    'loglevelw':
    {
        'full_name':            'Write Logging Level',
        'type':                 int,
        'default':              3,
        'positional_argument':  'j',
        'description':          'Logging level for the written log (Between 1 and 5)',
        'check_function':       lambda a: str(a).isdigit() and 1 <= int(a) <= 5,
        'required':             False
    },
    'runtime':
    {
        'full_name':            'Runtime',
        'type':                 int,
        'default':              0,
        'positional_argument':  't',
        'description':          'Runtime in seconds (0 for infinite runtime)',
        'check_function':       lambda a: str(a).isdigit() and int(a) >= 0,
        'required':             False
    },
    'addr':
    {
        'full_name':            'Address',
        'type':                 str,
        'default':              '127.0.0.1',
        'positional_argument':  'a',
        'description':          'Address for the UDP socket',
        'check_function':       lambda a: parameterChecks.check_address(a),
        'required':             False
    },
    'port':
    {
        'full_name':            'Port',
        'type':                 int,
        'default':              18001,
        'positional_argument':  'p',
        'description':          'Port for the UDP socket',
        'check_function':       lambda a: str(a).isdigit() and 1024 <= int(a) <= 65353,
        'required':             False
    },
    'mode':
    {
        'full_name':            'Mode',
        'type':                 int,
        'default':              0,
        'positional_argument':  'y',
        'description':          'Mode (0 = auto-select / 1 = JSON / 2 = APRS)',
        'check_function':       lambda a: str(a).isdigit() and 0 <= int(a) <= 2,
        'required':             False
    },
    'filepath':
    {
        'full_name':            'File Path',
        'type':                 str,
        'default':              os.getcwd() + '\log',
        'positional_argument':  'd',
        'description':          'Path for the files written by the program',
        'check_function':       lambda a: os.path.exists(a),
        'required':             False
    },
    'writeo':
    {
        'full_name':            'Write Raw Data',
        'type':                 int,
        'default':              0,
        'positional_argument':  's',
        'description':          'Write setting for the raw data (0 = no / 1 = yes)',
        'check_function':       lambda a: str(a).isdigit() and 0 <= int(a) <= 1,
        'required':             False
    },
    'writet':
    {
        'full_name':            'Write Telemetry',
        'type':                 int,
        'default':              0,
        'positional_argument':  'w',
        'description':          'Write setting for the telemetry (0 = no / 1 = yes)',
        'check_function':       lambda a: str(a).isdigit() and 0 <= int(a) <= 1,
        'required':             False
    },
    'writer':
    {
        'full_name':            'Write Reformatted Telemetry',
        'type':                 int,
        'default':              0,
        'positional_argument':  'z',
        'description':          'Write setting for the reformatted telemetry (0 = no / 1 = yes)',
        'check_function':       lambda a: str(a).isdigit() and 0 <= int(a) <= 1,
        'required':             False
    },
    'writel':
    {
        'full_name':            'Write Log',
        'type':                 int,
        'default':              1,
        'positional_argument':  'k',
        'description':          'Write setting for the log (0 = no / 1 = yes)',
        'check_function':       lambda a: str(a).isdigit() and 0 <= int(a) <= 1,
        'required':             False
    },
    'qin':
    {
        'full_name':            'Input Queue Size',
        'type':                 int,
        'default':              20,
        'positional_argument':  'q',
        'description':          'Size of the queue for storing the incoming packages before processing',
        'check_function':       lambda a: str(a).isdigit() and 1 <= int(a) <= 100,
        'required':             False
    },
    'qupl':
    {
        'full_name':            'Upload Queue Size',
        'type':                 int,
        'default':              200,
        'positional_argument':  'f',
        'description':          'Size of the queue for storing the telemetry packages before uploading',
        'check_function':       lambda a: str(a).isdigit() and 1 <= int(a) <= 600,
        'required':             False
    },
    'call':
    {
        'full_name':            'User Callsign',
        'type':                 str,
        'default':              None,
        'positional_argument':  'c',
        'description':          'User callsign for SondeHub',
        'check_function':       lambda a: parameterChecks.check_user_callsign(a, 4, 15),
        'required':             False
    },
    'pos':
    {
        'full_name':            'User Position',
        'type':                 list,
        'default':              None,
        'positional_argument':  'l',
        'description':          'User position for SondeHub',
        'check_function':       lambda a: parameterChecks.check_user_position(a, -100, 8000),
        'required':             True
    },
    'ant':
    {
        'full_name':            'User Antenna',
        'type':                 str,
        'default':              '1/4 wave monopole',
        'positional_argument':  'v',
        'description':          'User antenna for SondeHub',
        'check_function':       lambda a: 4 <= len(a) <= 25,
        'required':             False
    },
    'mail':
    {
        'full_name':            'Contact E-Mail',
        'type':                 str,
        'default':              None,
        'positional_argument':  'u',
        'description':          'User e-mail for SondeHub',
        'check_function':       lambda a: bool(re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', a)),
        'required':             True
    },
    'posu':
    {
        'full_name':            'User Position Update Rate',
        'type':                 int,
        'default':              6,
        'positional_argument':  'g',
        'description':          'User position update rate for SondeHub',
        'check_function':       lambda a: str(a).isdigit() and 1 <= int(a) <= 24,
        'required':             False
    },
    'telemu':
    {
        'full_name':            'Telemetry Update Rate',
        'type':                 int,
        'default':              30,
        'positional_argument':  'r',
        'description':          'Telemetry update rate for SondeHub',
        'check_function':       lambda a: str(a).isdigit() and 1 <= int(a) <= 600,
        'required':             False
    },
    'timeout':
    {
        'full_name':            'Upload Timeout',
        'type':                 int,
        'default':              20,
        'positional_argument':  'o',
        'description':          'Upload timeout for SondeHub',
        'check_function':       lambda a: str(a).isdigit() and 1 <= int(a) <= 60,
        'required':             False
    },
    'retry':
    {
        'full_name':            'Upload Retries',
        'type':                 int,
        'default':              5,
        'positional_argument':  'e',
        'description':          'Upload retries for SondeHub',
        'check_function':       lambda a: str(a).isdigit() and 1 <= int(a) <= 60,
        'required':             False
    },
    'sonde':
    {
        'full_name':            'Enabled Radiosondes',
        'type':                 str,
        'default':              'RS41,RS92,DFM,iMET,M10,M20,MRZ,MEISEI',
        'positional_argument':  'b',
        'description':          'Radiosondes enabled for upload',
        'check_function':       lambda a: parameterChecks.check_enabled_radiosondes(a),
        'required':             False
    }
}

# Other definitions
closetime_on_error = 5
