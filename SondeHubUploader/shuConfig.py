# shuConfig.py - SondeHubUploader configuration parameters
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Third-party modules
import logging
import datetime
# Own modules
import SondeHubUploader.conversions as conversions
import SondeHubUploader.handleData as handleData
import SondeHubUploader.telemetryChecks as telemetryChecks
import SondeHubUploader.utils as utils


# Logger definitions
loglevel = {
    1: logging.ERROR,
    2: logging.WARNING,
    3: logging.INFO,
    4: logging.DEBUG,
    5: logging.DEBUG - 1
}

# URL definitions
sondehub_telemetry_url = 'https://api.v2.sondehub.org/sondes/telemetry'
sondehub_station_url = 'https://api.v2.sondehub.org/listeners'

# Software definitions
software_name = 'dxlAPRS-SHUE'
software_version = '1.1.2'

# Status code definitions
status_code_ok = 200
status_code_sondehub_error_1 = 201
status_code_sondehub_error_2 = 202
status_code_server_error = 500

# Other definitions
udp_buffersize = 1024
thread_sleep = 1
filename_raw_data = 'rawdata'
filename_prefix_telemetry = 't_'
filename_prefix_reformatted_telemetry = 'r_'
leap_seconds = 18
rs41_burst_timer_inactive_value = 65535

# APRS Parser definitions
# Fixed position parameter definitions
parse_aprs_fixed_position = {
    'destination_address':
    {
        'range':            slice(0, 7),
        'parse_function':   lambda a: handleData.parse_aprs_address(a)
    },
    'source_address':
    {
        'range':            slice(7, 14),
        'parse_function':   lambda a: handleData.parse_aprs_address(a)
    },
    'control_field':
    {
        'range':            14,
        'parse_function':   lambda a: hex(a)
    },
    'protocol_id':
    {
        'range':            15,
        'parse_function':   lambda a: hex(a)
    },
    'data_type':
    {
        'range':            16,
        'parse_function':   lambda a: chr(a)
    },
    'serial':
    {
        'range':            slice(17, 26),
        'parse_function':   lambda a: a.decode('utf-8').split(' ', 1)[0]
    },
    'hour':
    {
        'range':            slice(27, 29),
        'parse_function':   lambda a: int(a)
    },
    'minute':
    {
        'range':            slice(29, 31),
        'parse_function':   lambda a: int(a)
    },
    'second':
    {
        'range':            slice(31, 33),
        'parse_function':   lambda a: int(a)
    },
    'time_format':
    {
        'range':            33,
        'parse_function':   lambda a: chr(a)
    },
    'latitude_degree':
    {
        'range':            slice(34, 36),
        'parse_function':   lambda a: int(a)
    },
    'latitude_minute':
    {
        'range':            slice(36, 41),
        'parse_function':   lambda a: handleData.parse_aprs_gmm_minute(a.decode('utf-8'))
    },
    'latitude_ns':
    {
        'range':            41,
        'parse_function':   lambda a: chr(a)
    },
    'longitude_degree':
    {
        'range':            slice(43, 46),
        'parse_function':   lambda a: int(a)
    },
    'longitude_minute':
    {
        'range':            slice(46, 51),
        'parse_function':   lambda a: handleData.parse_aprs_gmm_minute(a.decode('utf-8'))
    },
    'longitude_we':
    {
        'range':            51,
        'parse_function':   lambda a: chr(a)
    },
    'course':
    {
        'range':            slice(53, 56),
        'parse_function':   lambda a: int(a)
    },
    'speed':
    {
        'range':            slice(57, 60),
        'parse_function':   lambda a: int(a)
    },
    'altitude':
    {
        'range':            slice(63, 69),
        'parse_function':   lambda a: int(a)
    },
    'dao_D':
    {
        'range':            70,
        'parse_function':   lambda a: a
    },
    'dao_A':
    {
        'range':            71,
        'parse_function':   lambda a: a
    },
    'dao_O':
    {
        'range':            72,
        'parse_function':   lambda a: a
    }
}
# Optional parameter definitions
parse_aprs_optional = {
    'type':
    {
        'prefix':           'Type=',
        'unit_end':         ' ',
        'parse_function':   lambda a: a
    },
    'serial_2':
    {
        'prefix':           'ser=',
        'unit_end':         ' ',
        'parse_function':   lambda a: a
    },
    'gps_noise':
    {
        'prefix':           'hdil=',
        'unit_end':         'm',
        'parse_function':   lambda a: float(a)
    },
    'over_ground':
    {
        'prefix':           'OG=',
        'unit_end':         'm',
        'parse_function':   lambda a: int(a)
    },
    'azimuth':
    {
        'prefix':           'azimuth=',
        'unit_end':         ' ',
        'parse_function':   lambda a: int(a)
    },
    'elevation':
    {
        'prefix':           'elevation=',
        'unit_end':         ' ',
        'parse_function':   lambda a: float(a)
    },
    'distance':
    {
        'prefix':           'dist=',
        'unit_end':         ' ',
        'parse_function':   lambda a: float(a)
    },
    'climb':
    {
        'prefix':           'Clb=',
        'unit_end':         'm/s',
        'parse_function':   lambda a: float(a)
    },
    'temperature':
    {
        'prefix':           't=',
        'unit_end':         'C',
        'parse_function':   lambda a: float(a)
    },
    'pressure':
    {
        'prefix':           'p=',
        'unit_end':         'hPa',
        'parse_function':   lambda a: float(a)
    },
    'fake_pressure':
    {
        'prefix':           'fp=',
        'unit_end':         'hPa',
        'parse_function':   lambda a: float(a)
    },
    'humidity':
    {
        'prefix':           'h=',
        'unit_end':         '%',
        'parse_function':   lambda a: float(a)
    },
    'o3':
    {
        'prefix':           'o3=',
        'unit_end':         'mPa',
        'parse_function':   lambda a: float(a)
    },
    'o3_temperature':
    {
        'prefix':           'ti=',
        'unit_end':         'C',
        'parse_function':   lambda a: float(a)
    },
    'calibration':
    {
        'prefix':           'calibration',
        'unit_end':         '%',
        'parse_function':   lambda a: int(a)
    },
    'tx_power':
    {
        'prefix':           'tx=',
        'unit_end':         'dBm',
        'parse_function':   lambda a: int(a)
    },
    'framenumber':
    {
        'prefix':           'FN=',
        'unit_end':         ' ',
        'parse_function':   lambda a: int(a)
    },
    'battery':
    {
        'prefix':           'batt=',
        'unit_end':         'V',
        'parse_function':   lambda a: float(a)
    },
    'satellites':
    {
        'prefix':           'Sats=',
        'unit_end':         ' ',
        'parse_function':   lambda a: int(a)
    },
    'device':
    {
        'prefix':           'dev=',
        'unit_end':         ' ',
        'parse_function':   lambda a: a
    },
    'rssi':
    {
        'prefix':           'rssi=',
        'unit_end':         'dB',
        'parse_function':   lambda a: float(a)
    }
}
# Optional multivalue parameter definitions
parse_aprs_optional_multivalue = {
    'pump':
    {
        'prefix':                       'Pump=',
        'unit_end':                     'V',
        'parse_function':               lambda a: a,
        'subparameter':                 ['pump_current', 'pump_voltage'],
        'subparameter_parse_function':  lambda a: handleData.parse_aprs_pump(a)
    },
    'powerup':
    {
        'prefix':                       'powerup=',
        'unit_end':                     ' ',
        'parse_function':               lambda a: a,
        'subparameter':                 ['powerup_hour', 'powerup_minute', 'powerup_second'],
        'subparameter_parse_function':  lambda a: handleData.parse_aprs_timer(a)
    },
    'tx_past_burst':
    {
        'prefix':                       'TxPastBurst=',
        'unit_end':                     ' ',
        'parse_function':               lambda a: a,
        'subparameter':                 ['tx_past_burst_hour', 'tx_past_burst_minute', 'tx_past_burst_second'],
        'subparameter_parse_function':  lambda a: handleData.parse_aprs_timer(a)
    },
    'rx':
    {
        'prefix':                       'rx=',
        'unit_end':                     ' ',
        'parse_function':               lambda a: a,
        'subparameter':                 ['rx_frequency', 'rx_afc', 'rx_max_afc'],
        'subparameter_parse_function':  lambda a: handleData.parse_aprs_rx(a)
    }
}
# Optional special parameter definitions
parse_aprs_optional_special = {
    'frequency':
    {
        'prefix':           ' ',
        'unit_end':         'MHz',
        'parse_function':   lambda a: float(a)
    }
}

# Telemetry definitions
telemetry = {
    'destination_address':
    {
        'json_source':              None,
        'json_conversion_function': None,
        'aprs_source':              'destination_address',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: telemetryChecks.check_callsign_plausibility(a),
        'name':                     'DestinationAddress',
        'unit':                     None,
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'source_address':
    {
        'json_source':              'uid',
        'json_conversion_function': lambda a: a,
        'aprs_source':              'source_address',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: telemetryChecks.check_callsign_plausibility(a),
        'name':                     'SourceAddress',
        'unit':                     None,
        'mandatory':                True,
        'optional':                 False,
        'reformat_function':        None
    },
    'type':
    {
        'json_source':              ('type', 'ser'),
        'json_conversion_function': lambda a, b: handleData.unify_json_type(a, b),
        'aprs_source':              'type',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: telemetryChecks.check_type_plausibility(a, radiosonde),
        'name':                     'Type',
        'unit':                     None,
        'mandatory':                True,
        'optional':                 False,
        'reformat_function':        None
    },
    'serial':
    {
        'json_source':              'id',
        'json_conversion_function': lambda a: a,
        'aprs_source':              'serial',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if len(a) >= 4 else False,
        'name':                     'Serial',
        'unit':                     None,
        'mandatory':                ['RS41', 'RS92', 'DFM', 'M10'],
        'optional':                 False,
        'reformat_function':        None
    },
    'serial_2':
    {
        'json_source':              'ser',
        'json_conversion_function': lambda a: a,
        'aprs_source':              'serial_2',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if len(a) >= 4 else False,
        'name':                     'Serial2',
        'unit':                     None,
        'mandatory':                ['M20', 'MRZ', 'MEISEI'],
        'optional':                 False,
        'reformat_function':        None
    },
    'date':
    {
        'json_source':              'date',
        'json_conversion_function': lambda a: datetime.date(int(a[0:4]), int(a[5:7]), int(a[8:10])),
        'aprs_source':              None,
        'aprs_conversion_function': None,
        'plausibility_function':    lambda a: telemetryChecks.check_date_plausibility(a, 1),
        'name':                     'Date',
        'unit':                     None,
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'time':
    {
        'json_source':              'time',
        'json_conversion_function': lambda a: datetime.time(int(a[0:2]), int(a[3:5]), int(a[6:8])),
        'aprs_source':              ('hour', 'minute', 'second'),
        'aprs_conversion_function': lambda a, b, c: datetime.time(a, b, c),
        'plausibility_function':    lambda a: telemetryChecks.check_time_plausibility(a, 60),
        'name':                     'Time',
        'unit':                     None,
        'mandatory':                True,
        'optional':                 False,
        'reformat_function':        None
    },
    'leap_seconds':
    {
        'json_source':              'leaps',
        'json_conversion_function': lambda a: a,
        'aprs_source':              None,
        'aprs_conversion_function': None,
        'plausibility_function':    lambda a: True if 0 <= a <= 50 else False,
        'name':                     'LeapSeconds',
        'unit':                     's',
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'latitude':
    {
        'json_source':              'lat',
        'json_conversion_function': lambda a: a,
        'aprs_source':              ('latitude_degree', 'latitude_minute', 'latitude_ns', 'dao_D', 'dao_A'),
        'aprs_conversion_function': lambda a, b, c, d, e: conversions.gmm_to_dg(a, utils.minute_add_precision(None, b, d, e), c, 6),
        'plausibility_function':    lambda a: True if -90 <= a <= 90 else False,
        'name':                     'Latitude',
        'unit':                     '°',
        'mandatory':                True,
        'optional':                 False,
        'reformat_function':        lambda a: round(a, 5)
    },
    'longitude':
    {
        'json_source':              'long',
        'json_conversion_function': lambda a: a,
        'aprs_source':              ('longitude_degree', 'longitude_minute', 'longitude_we', 'dao_D', 'dao_O'),
        'aprs_conversion_function': lambda a, b, c, d, e: conversions.gmm_to_dg(a, utils.minute_add_precision(None, b, d, e), c, 5),
        'plausibility_function':    lambda a: True if -180 <= a <= 180 else False,
        'name':                     'Longitude',
        'unit':                     '°',
        'mandatory':                True,
        'optional':                 False,
        'reformat_function':        lambda a: round(a, 5)
    },
    'gps_noise':
    {
        'json_source':              None,
        'json_conversion_function': None,
        'aprs_source':              'gps_noise',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if 0 <= a <= 100 else False,
        'name':                     'GPSNoise',
        'unit':                     'm',
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'altitude':
    {
        'json_source':              'alt',
        'json_conversion_function': lambda a: a,
        'aprs_source':              'altitude',
        'aprs_conversion_function': lambda a: conversions.feet_to_meter(a, 5),
        'plausibility_function':    lambda a: True if a <= 50000 else False,
        'name':                     'Altitude',
        'unit':                     'm',
        'mandatory':                True,
        'optional':                 False,
        'reformat_function':        None
    },
    'egm_altitude':
    {
        'json_source':              'egmalt',
        'json_conversion_function': lambda a: a,
        'aprs_source':              None,
        'aprs_conversion_function': None,
        'plausibility_function':    lambda a: True if a <= 50000 else False,
        'name':                     'EGMAltitude',
        'unit':                     'm',
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'over_ground':
    {
        'json_source':              'og',
        'json_conversion_function': lambda a: a,
        'aprs_source':              'over_ground',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if a <= 50000 else False,
        'name':                     'OverGround',
        'unit':                     'm',
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'azimuth':
    {
        'json_source':              ['ant', 'az'],
        'json_conversion_function': lambda a: a,
        'aprs_source':              'azimuth',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if 0 <= a < 360 else False,
        'name':                     'Azimuth',
        'unit':                     '°',
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'elevation':
    {
        'json_source':              ['ant', 'el'],
        'json_conversion_function': lambda a: a,
        'aprs_source':              'elevation',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if 0 <= a <= 90 else False,
        'name':                     'Elevation',
        'unit':                     '°',
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'distance':
    {
        'json_source':              ['ant', 'd'],
        'json_conversion_function': lambda a: a,
        'aprs_source':              'distance',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if 0 <= a <= 1500 else False,
        'name':                     'Distance',
        'unit':                     'km',
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'climb':
    {
        'json_source':              'clb',
        'json_conversion_function': lambda a: a,
        'aprs_source':              'climb',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if -100 <= a <= 100 else False,
        'name':                     'Climb',
        'unit':                     'm/s',
        'mandatory':                False,
        'optional':                 'vel_v',
        'reformat_function':        lambda a: float(a)
    },
    'speed':
    {
        'json_source':              'spd',
        'json_conversion_function': lambda a: a,
        'aprs_source':              'speed',
        'aprs_conversion_function': lambda a: conversions.knot_to_kph(a, 5),
        'plausibility_function':    lambda a: True if a <= 1000 else False,
        'name':                     'Speed',
        'unit':                     'kph',
        'mandatory':                False,
        'optional':                 'vel_h',
        'reformat_function':        lambda a: conversions.kph_to_ms(a, 1)
    },
    'course':
    {
        'json_source':              'dir',
        'json_conversion_function': lambda a: a,
        'aprs_source':              'course',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if a < 360 else False,
        'name':                     'Course',
        'unit':                     '°',
        'mandatory':                False,
        'optional':                 'heading',
        'reformat_function':        lambda a: float(a)
    },
    'temperature':
    {
        'json_source':              ['ptu', 't'],
        'json_conversion_function': lambda a: a,
        'aprs_source':              'temperature',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if -100 <= a <= 100 else False,
        'name':                     'Temperature',
        'unit':                     '°C',
        'mandatory':                False,
        'optional':                 'temp',
        'reformat_function':        lambda a: float(a)
    },
    'pressure':
    {
        'json_source':              ['ptu', 'p'],
        'json_conversion_function': lambda a: a,
        'aprs_source':              'pressure',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if 0 <= a <= 2000 else False,
        'name':                     'Pressure',
        'unit':                     'hPa',
        'mandatory':                False,
        'optional':                 'pressure',
        'reformat_function':        lambda a: float(a)
    },
    'fake_pressure':
    {
        'json_source':              None,
        'json_conversion_function': None,
        'aprs_source':              'fake_pressure',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if 0 <= a <= 2000 else False,
        'name':                     'FakePressure',
        'unit':                     'hPa',
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'humidity':
    {
        'json_source':              ['ptu', 'h'],
        'json_conversion_function': lambda a: a,
        'aprs_source':              'humidity',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if 0 <= a <= 100 else False,
        'name':                     'Humidity',
        'unit':                     '%',
        'mandatory':                False,
        'optional':                 'humidity',
        'reformat_function':        lambda a: float(a)
    },
    'xdata':
    {
        'json_source':              'xdata',
        'json_conversion_function': lambda a: a,
        'aprs_source':              None,
        'aprs_conversion_function': None,
        'plausibility_function':    lambda a: telemetryChecks.check_xdata_plausibility(a),
        'name':                     'XDATA',
        'unit':                     None,
        'mandatory':                False,
        'optional':                 'xdata',
        'reformat_function':        lambda a: handleData.reformat_xdata(a)
    },
    'o3':
    {
        'json_source':              ['aux', 'o3'],
        'json_conversion_function': lambda a: a,
        'aprs_source':              'o3',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if 0 <= a <= 100 else False,
        'name':                     'o3',
        'unit':                     'mPa',
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'o3_temperature':
    {
        'json_source':              ['aux', 'o3tmp'],
        'json_conversion_function': lambda a: a,
        'aprs_source':              'o3_temperature',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if -100 <= a <= 100 else False,
        'name':                     'o3Temperature',
        'unit':                     '°C',
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'pump_voltage':
    {
        'json_source':              ['aux', 'pumpv'],
        'json_conversion_function': lambda a: a,
        'aprs_source':              'pump_voltage',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if 0 <= a <= 100 else False,
        'name':                     'PumpVoltage',
        'unit':                     'V',
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'pump_current':
    {
        'json_source':              ['aux', 'pumpma'],
        'json_conversion_function': lambda a: a,
        'aprs_source':              'pump_current',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if 0 <= a <= 10000 else False,
        'name':                     'PumpCurrent',
        'unit':                     'mA',
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'calibration':
    {
        'json_source':              None,
        'json_conversion_function': None,
        'aprs_source':              'calibration',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if 0 <= a <= 100 else False,
        'name':                     'Calibration',
        'unit':                     '%',
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'frequency':
    {
        'json_source':              ('mhz', ['sdr', 'rx']),
        'json_conversion_function': lambda a, b: handleData.unify_json_frequency(a, b),
        'aprs_source':              'frequency',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if 400 <= a <= 406 else False,
        'name':                     'Frequency',
        'unit':                     'MHz',
        'mandatory':                ['iMET'],
        'optional':                 'tx_frequency',
        'reformat_function':        lambda a: float(a)
    },
    'tx_power':
    {
        'json_source':              'txpo',
        'json_conversion_function': lambda a: a,
        'aprs_source':              'tx_power',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if 0 <= a <= 200 else False,
        'name':                     'TxPower',
        'unit':                     'dBm',
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'framenumber':
    {
        'json_source':              'up',
        'json_conversion_function': lambda a: a,
        'aprs_source':              'framenumber',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if 0 <= a <= 86400 else False,
        'name':                     'Framenumber',
        'unit':                     None,
        'mandatory':                ['RS41', 'RS92', 'iMET', 'MEISEI'],
        'optional':                 False,
        'reformat_function':        None
    },
    'powerup':
    {
        'json_source':              None,
        'json_conversion_function': None,
        'aprs_source':              'powerup',
        'aprs_conversion_function': lambda a: conversions.hms_to_frame(a[0], a[1], a[2], 1),
        'plausibility_function':    lambda a: True if 0 <= a <= 86400 else False,
        'name':                     'Powerup',
        'unit':                     's',
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'burst_timer':
    {
        'json_source':              ('bursttx', 'txoff'),
        'json_conversion_function': lambda a, b: handleData.unify_json_burst_timer(a, b),
        'aprs_source':              'tx_past_burst',
        'aprs_conversion_function': lambda a: conversions.hms_to_frame(a[0], a[1], a[2], 1),
        'plausibility_function':    lambda a: True if 0 <= a <= 86400 else False,
        'name':                     'BurstTimer',
        'unit':                     's',
        'mandatory':                False,
        'optional':                 'burst_timer',
        'reformat_function':        lambda a: 65535 if a == 30600 else a
    },
    'battery':
    {
        'json_source':              'ub',
        'json_conversion_function': lambda a: a,
        'aprs_source':              'battery',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if 0 <= a <= 20 else False,
        'name':                     'Battery',
        'unit':                     'V',
        'mandatory':                False,
        'optional':                 'batt',
        'reformat_function':        lambda a: float(a)
    },
    'satellites':
    {
        'json_source':              'sat',
        'json_conversion_function': lambda a: a,
        'aprs_source':              'satellites',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if 0 <= a <= 30 else False,
        'name':                     'Satellites',
        'unit':                     None,
        'mandatory':                False,
        'optional':                 'sats',
        'reformat_function':        lambda a: a
    },
    'satellite_levels':
    {
        'json_source':              'satdb',
        'json_conversion_function': lambda a: a,
        'aprs_source':              None,
        'aprs_conversion_function': None,
        'plausibility_function':    lambda a: telemetryChecks.check_satellite_levels_plausibility(a),
        'name':                     'SatelliteLevels',
        'unit':                     None,
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'device':
    {
        'json_source':              'rxid',
        'json_conversion_function': lambda a: a,
        'aprs_source':              'device',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    None,
        'name':                     'Device',
        'unit':                     None,
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'rx_frequency':
    {
        'json_source':              ['sdr', 'rx'],
        'json_conversion_function': lambda a: a,
        'aprs_source':              'rx',
        'aprs_conversion_function': lambda a: a[0] / 1000,
        'plausibility_function':    lambda a: True if 400 <= a <= 406 else False,
        'name':                     'RxFrequency',
        'unit':                     'MHz',
        'mandatory':                False,
        'optional':                 'frequency',
        'reformat_function':        lambda a: float(a)
    },
    'rx_afc':
    {
        'json_source':              ['sdr', 'afc'],
        'json_conversion_function': lambda a: a,
        'aprs_source':              'rx',
        'aprs_conversion_function': lambda a: a[1],
        'plausibility_function':    None,
        'name':                     'RxAFC',
        'unit':                     None,
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'rx_max_afc':
    {
        'json_source':              ['sdr', 'mafc'],
        'json_conversion_function': lambda a: a,
        'aprs_source':              'rx',
        'aprs_conversion_function': lambda a: a[2],
        'plausibility_function':    None,
        'name':                     'RxAFCMax',
        'unit':                     None,
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        None
    },
    'rssi':
    {
        'json_source':              ['sdr', 'rssi'],
        'json_conversion_function': lambda a: a,
        'aprs_source':              'rssi',
        'aprs_conversion_function': lambda a: a,
        'plausibility_function':    lambda a: True if 0 <= a <= 200 else False,
        'name':                     'RSSI',
        'unit':                     'dB',
        'mandatory':                False,
        'optional':                 False,
        'reformat_function':        lambda a: a
    }
}

# Reformatted telemetry definitions
# Value: unit
reformatted_telemetry = {
    'software_name': None,
    'software_version': None,
    'uploader_callsign': None,
    'uploader_position': None,
    'uploader_antenna': None,
    'time_received': None,
    'manufacturer': None,
    'type': None,
    'subtype': None,
    'serial': None,
    'datetime': None,
    'frame': None,
    'lat': '°',
    'lon': '°',
    'alt': 'm',
    'temp': '°C',
    'pressure': 'hPa',
    'humidity': '%',
    'vel_v': 'm/s',
    'vel_h': 'm/s',
    'heading': '°',
    'sats': None,
    'batt': 'V',
    'burst_timer': 's',
    'xdata': None,
    'frequency': 'MHz',
    'tx_frequency': 'MHz',
    'snr': 'dB',
    'rssi': 'dBm',
    'ref_datetime': None,
    'ref_position': None
}

# Radiosonde definitions
radiosonde = {
    'RS41':
    {
        'manufacturer':                 'Vaisala',
        'type':                         'RS41',
        'subtype':                      ['RS41-SG', 'RS41-SGP', 'RS41-SGM'],
        'serial':                       ['serial', 0],
        'framenumber':                  'fn',
        'altitude_precision':           5,
        'radiosonde_time_reference':    'GPS',
        'sondehub_time_reference':      'GPS',
        'sondehub_position_reference':  'GPS',
        'enabled':                      True
    },
    'RS92':
    {
        'manufacturer':                 'Vaisala',
        'type':                         'RS92',
        'subtype':                      None,
        'serial':                       ['serial', 0],
        'framenumber':                  'fn',
        'altitude_precision':           5,
        'radiosonde_time_reference':    'GPS',
        'sondehub_time_reference':      'GPS',
        'sondehub_position_reference':  'GPS',
        'enabled':                      True
    },
    'DFM':
    {
        'manufacturer':                 'Graw',
        'type':                         'DFM',
        'subtype':                      ['DFM06', 'DFM09', 'DFM09P', 'DFM17', 'PS-15'],
        'serial':                       ['serial', 1],
        'framenumber':                  'gps',
        'altitude_precision':           2,
        'radiosonde_time_reference':    'UTC',
        'sondehub_time_reference':      'UTC',
        'sondehub_position_reference':  'GPS',
        'enabled':                      True
    },
    'iMET':
    {
        'manufacturer':                 'Intermet Systems',
        'type':                         'iMet-4',
        'subtype':                      None,
        'serial':                       'IMET',
        'framenumber':                  'fn',
        'altitude_precision':           0,
        'radiosonde_time_reference':    'GPS',
        'sondehub_time_reference':      'GPS',
        'sondehub_position_reference':  'MSI',
        'enabled':                      True
    },
    'M10':
    {
        'manufacturer':                 'Meteomodem',
        'type':                         'M10',
        'subtype':                      None,
        'serial':                       ['serial', 0],
        'framenumber':                  'gps',
        'altitude_precision':           2,
        'radiosonde_time_reference':    'GPS',
        'sondehub_time_reference':      'UTC',
        'sondehub_position_reference':  'GPS',
        'enabled':                      True
    },
    'M20':
    {
        'manufacturer':                 'Meteomodem',
        'type':                         'M20',
        'subtype':                      None,
        'serial':                       ['serial_2', 0],
        'framenumber':                  'gps',
        'altitude_precision':           2,
        'radiosonde_time_reference':    'GPS',
        'sondehub_time_reference':      'GPS',
        'sondehub_position_reference':  'GPS',
        'enabled':                      True
    },
    'MRZ':
    {
        'manufacturer':                 'Meteo-Radiy',
        'type':                         'MRZ',
        'subtype':                      None,
        'serial':                       ['serial_2', 0],
        'framenumber':                  'gps',
        'altitude_precision':           5,
        'radiosonde_time_reference':    'UTC',
        'sondehub_time_reference':      'UTC',
        'sondehub_position_reference':  'GPS',
        'enabled':                      True
    },
    'MEISEI':
    {
        'manufacturer':                 'Meisei',
        'type':                         'IMS100',
        'subtype':                      None,
        'serial':                       ['serial_2', 7],
        'framenumber':                  'fn',
        'altitude_precision':           1,
        'radiosonde_time_reference':    'UTC',
        'sondehub_time_reference':      'UTC',
        'sondehub_position_reference':  'GPS',
        'enabled':                      True
    }
}
