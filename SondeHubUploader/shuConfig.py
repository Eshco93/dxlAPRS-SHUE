# shuConfig.py - SondeHubUploader configuration parameters
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Third-party modules
import logging
# Own modules
import SondeHubUploader.conversions as conversions
import SondeHubUploader.handleData as handleData
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
software_version = '1.0.0'

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
reformat_position_precision = 5


# Parser definitions
# Fixed position parameter definitions
# Values: range, parse function
parse_fixed_position = {
    'destination_address': [slice(0, 7), lambda a: bytes(a)],
    'source_address': [slice(7, 14), lambda a: bytes(a)],
    'control': [14, lambda a: hex(a)],
    'protocol_id': [15, lambda a: hex(a)],
    'data_type': [16, lambda a: chr(a)],
    'serial': [slice(17, 26), lambda a: a.decode('utf-8').split(' ', 1)[0]],
    'hour': [slice(27, 29), lambda a: int(a)],
    'minute': [slice(29, 31), lambda a: int(a)],
    'second': [slice(31, 33), lambda a: int(a)],
    'time_format': [33, lambda a: chr(a)],
    'latitude_degree': [slice(34, 36), lambda a: int(a)],
    'latitude_minute': [slice(36, 41), lambda a: handleData.parse_gmm_minute(a.decode('utf-8'))],
    'latitude_ns': [41, lambda a: chr(a)],
    'longitude_degree': [slice(43, 46), lambda a: int(a)],
    'longitude_minute': [slice(46, 51), lambda a: handleData.parse_gmm_minute(a.decode('utf-8'))],
    'longitude_we': [51, lambda a: chr(a)],
    'course': [slice(53, 56), lambda a: int(a)],
    'speed': [slice(57, 60), lambda a: int(a)],
    'altitude': [slice(63, 69), lambda a: int(a)],
    'dao_D': [70, lambda a: a],
    'dao_A': [71, lambda a: a],
    'dao_O': [72, lambda a: a]
}
# Optional parameter definitions
# Values: prefix, unit/end, parse function
parse_optional = {
    'clb': ['Clb=', 'm/s', lambda a: float(a)],
    'p': ['p=', 'hPa', lambda a: float(a)],
    't': ['t=', 'C', lambda a: float(a)],
    'h': ['h=', '%', lambda a: float(a)],
    'batt': ['batt=', 'V', lambda a: float(a)],
    'calibration': ['calibration', '%', lambda a: int(a)],
    'fp': ['fp=', 'hPa', lambda a: float(a)],
    'og': ['OG=', 'm', lambda a: int(a)],
    'rssi': ['rssi=', 'dB', lambda a: float(a)],
    'tx': ['tx=', 'dBm', lambda a: int(a)],
    'hdil': ['hdil=', 'm', lambda a: float(a)],
    'o3': ['o3=', 'mPa', lambda a: float(a)],
    'type': ['Type=', ' ', lambda a: a],
    'sats': ['Sats=', ' ', lambda a: int(a)],
    'fn': ['FN=', ' ', lambda a: int(a)],
    'azimuth': ['azimuth=', ' ', lambda a: int(a)],
    'elevation': ['elevation=', ' ', lambda a: float(a)],
    'dist': ['dist=', ' ', lambda a: float(a)],
    'dev': ['dev=', ' ', lambda a: a],
    'ser': ['ser=', ' ', lambda a: a]
}
# Optional multivalue parameter definitions
# Values: prefix, unit/end, parse function, subparameter, subparameter parse function
parse_optional_multivalue = {
    'tx_past_burst': ['TxPastBurst=', ' ', lambda a: a, ['tx_past_burst_hour', 'tx_past_burst_minute', 'tx_past_burst_second'], lambda a: handleData.parse_timer(a)],
    'powerup': ['powerup=', ' ', lambda a: a, ['powerup_hour', 'powerup_minute', 'powerup_second'], lambda a: handleData.parse_timer(a)],
    'rx': ['rx=', ' ', lambda a: a, ['rx_f', 'rx_afc', 'rx_afc_max'], lambda a: handleData.parse_rx(a)],
    'pump': ['Pump=', 'V', lambda a: a, ['pump_ma', 'pump_v'], lambda a: handleData.parse_pump(a)],
}
# Optional special parameter definitions
# Values: prefix, unit/end, parse function
parse_optional_special = {
    'f': [' ', 'MHz', lambda a: float(a)]
}

# Telemetry definitions
# Values: check function, mandatory, optional, optional name, reformat function
telemetry = {
    'destination_address': [None, False, False, None, None],
    'source_address': [None, False, False, None, None],
    'control': [lambda a: True if a == hex(0x3) else False, False, False, None, None],
    'protocol_id': [lambda a: True if a == hex(0xF0) else False, False, False, None, None],
    'data_type': [lambda a: True if a == ';' else False, False, False, None, None],
    'serial': [None, ['RS41', 'RS92', 'DFM'], False, None, None],
    'hour': [lambda a: True if a <= 23 else False, True, False, None, None],
    'minute': [lambda a: True if a <= 59 else False, True, False, None, None],
    'second': [lambda a: True if a <= 59 else False, True, False, None, None],
    'time_format': [lambda a: True if a in ['z', '/', 'h'] else False, False, False, None, None],
    'latitude_degree': [lambda a: True if a <= 180 else False, True, False, None, None],
    'latitude_minute': [lambda a: True if a < 60 else False, True, False, None, None],
    'latitude_ns': [lambda a: True if a in ['N', 'S'] else False, True, False, None, None],
    'longitude_degree': [lambda a: True if a <= 180 else False, True, False, None, None],
    'longitude_minute': [lambda a: True if a < 60 else False, True, False, None, None],
    'longitude_we': [lambda a: True if a in ['W', 'E'] else False, True, False, None, None],
    'course': [lambda a: True if a < 360 else False, False, True, 'heading', lambda a: float(a)],
    'speed': [lambda a: True if conversions.knot_to_kph(a, 0) < 1000 else False, False, True, 'vel_h', lambda a: conversions.knot_to_ms(a, 1)],
    'altitude': [lambda a: True if conversions.feet_to_meter(a, 0) < 50000 else False, True, False, None, None],
    'dao_D': [lambda a: True if a in [ord(' '), ord('w'), ord('W')] else False, True, False, None, None],
    'dao_A': [lambda a: True if 33 <= a <= 123 else False, True, False, None, None],
    'dao_O': [lambda a: True if 33 <= a <= 123 else False, True, False, None, None],
    'clb': [lambda a: True if -100 <= a <= 100 else False, False, True, 'vel_v', lambda a: float(a)],
    'p': [lambda a: True if 0 <= a <= 2000 else False, False, True, 'pressure', lambda a: float(a)],
    't': [lambda a: True if -100 <= a <= 100 else False, False, True, 'temp', lambda a: float(a)],
    'h': [lambda a: True if 0 <= a <= 100 else False, False, True, 'humidity', lambda a: float(a)],
    'batt': [lambda a: True if 0 <= a <= 20 else False, False, True, 'batt', lambda a: float(a)],
    'calibration': [lambda a: True if 0 <= a <= 100 else False, False, False, None, None],
    'fp': [lambda a: True if 0 <= a <= 2000 else False, False, False, None, None],
    'og': [lambda a: True if 0 <= a <= 50000 else False, False, False, None, None],
    'rssi': [lambda a: True if 0 <= a <= 200 else False, False, False, 'rssi', lambda a: float(a)],
    'tx': [lambda a: True if 0 <= a <= 200 else False, False, False, None, None],
    'hdil': [lambda a: True if 0 <= a <= 100 else False, False, False, None, None],
    'o3': [lambda a: True if 0 <= a <= 100 else False, False, False, None, None],
    'type': [lambda a: True if a.startswith(tuple(radiosonde.keys())) else False, True, False, None, None],
    'sats': [lambda a: True if 0 <= a <= 30 else False, False, True, 'sats', lambda a: a],
    'fn': [lambda a: True if 0 <= a <= 86400 else False, ['RS41', 'RS92', 'iMET', 'MEISEI'], False, None, None],
    'azimuth': [lambda a: True if 0 <= a < 360 else False, False, False, None, None],
    'elevation': [lambda a: True if 0 <= a <= 90 else False, False, False, None, None],
    'dist': [lambda a: True if 0 <= a <= 1500 else False, False, False, None, None],
    'dev': [None, False, False, None, None],
    'ser': [None, ['M10', 'M20', 'MRZ', 'MEISEI'], False, None, None],
    'tx_past_burst_hour': [lambda a: True if a <= 23 else False, False, False, None, None],
    'tx_past_burst_minute': [lambda a: True if a <= 59 else False, False, False, None, None],
    'tx_past_burst_second': [lambda a: True if a <= 59 else False, False, False, None, None],
    'powerup_hour': [lambda a: True if a <= 23 else False, False, False, None, None],
    'powerup_minute': [lambda a: True if a <= 59 else False, False, False, None, None],
    'powerup_second': [lambda a: True if a <= 59 else False, False, False, None, None],
    'rx_f': [lambda a: True if 400000 <= a <= 406000 else False, False, True, 'frequency', lambda a: float(a / 1000)],
    'rx_afc': [None, False, False, None, None],
    'rx_afc_max': [None, False, False, None, None],
    'pump_ma': [lambda a: True if 0 <= a <= 10000 else False, False, False, None, None],
    'pump_v': [lambda a: True if 0 <= a <= 100 else False, False, False, None, None],
    'f': [lambda a: True if 400 <= a <= 406 else False, ['iMET'], True, 'tx_frequency', lambda a: float(a)]
}

# Print/Write telemetry definitions
# Values: parameter, unit, conversion function
print_write_telemetry = {
    'Serial': [['serial'], None, lambda a: a],
    'Time': [['hour', 'minute', 'second'], None, lambda a, b, c: '{:02d}:{:02d}:{:02d}'.format(a, b, c)],
    'Latitude': [['latitude_degree', 'latitude_minute', 'latitude_ns', 'dao_D', 'dao_A'], '°', lambda a, b, c, d, e: conversions.gmm_to_dg(a, utils.minute_add_precision(None, b, d, e), c, 5)],
    'Longitude': [['longitude_degree', 'longitude_minute', 'longitude_we', 'dao_D', 'dao_O'], '°', lambda a, b, c, d, e: conversions.gmm_to_dg(a, utils.minute_add_precision(None, b, d, e), c, 5)],
    'Course': [['course'], '°', lambda a: a],
    'Speed': [['speed'], 'kph', lambda a: conversions.knot_to_kph(a, 2)],
    'Altitude': [['altitude'], 'm', lambda a: conversions.feet_to_meter(a, 2)],
    'Climb': [['clb'], 'm/s', lambda a: a],
    'Pressure': [['p'], 'hPa', lambda a: a],
    'Temperature': [['t'], '°C', lambda a: a],
    'Humidity': [['h'], '%', lambda a: a],
    'Frequency': [['f'], 'MHz', lambda a: a],
    'Type': [['type'], None, lambda a: a],
    'TxPastBurst': [['tx_past_burst_hour', 'tx_past_burst_minute', 'tx_past_burst_second'], None, lambda a, b, c: '{:02d}:{:02d}:{:02d}'.format(a, b, c)],
    'Battery': [['batt'], 'V', lambda a: a],
    'PowerUp': [['powerup_hour', 'powerup_minute', 'powerup_second'], None, lambda a, b, c: '{:02d}:{:02d}:{:02d}'.format(a, b, c)],
    'Calibration': [['calibration'], '%', lambda a: a],
    'Satellites': [['sats'], None, lambda a: a],
    'Fakehp': [['fp'], 'hPa', lambda a: a],
    'Framenumber': [['fn'], None, lambda a: a],
    'OverGround': [['og'], 'm', lambda a: a],
    'RSSI': [['rssi'], 'dB', lambda a: a],
    'TxPower': [['tx'], 'dBm', lambda a: a],
    'GPSNoise': [['hdil'], 'm', lambda a: a],
    'Azimuth': [['azimuth'], '°', lambda a: a],
    'Elevation': [['elevation'], '°', lambda a: a],
    'Distance:': [['dist'], 'km', lambda a: a],
    'Device': [['dev'], None, lambda a: a],
    'Serial2': [['ser'], None, lambda a: a],
    'RxSetting': [['rx_f', 'rx_afc', 'rx_afc_max'], None, lambda a, b, c: f'{a} kHz ({b}/{c})'],
    'o3': [['o3'], 'mPa', lambda a: a],
    'PumpVoltage': [['pump_v'], 'V', lambda a: a],
    'PumpCurrent': [['pump_ma'], 'mA', lambda a: a]
}

# Write reformatted telemetry definitions
# Values: unit
write_reformatted_telemetry = {
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
# Values: manufacturer, type, subtype, serial, framenumber, altitude precision, ref_datetime, ref_position
radiosonde = {
    'RS41': ['Vaisala', 'RS41', ['RS41-SG', 'RS41-SGP', 'RS41-SGM'], ['serial', 0], 'fn', 5, 'GPS', 'GPS'],
    'RS92': ['Vaisala', 'RS92', None, ['serial', 0], 'fn', 5, 'GPS', 'GPS'],
    'DFM': ['Graw', 'DFM', ['DFM06', 'DFM09', 'DFM09P', 'DFM17'], ['serial', 1], 'gps', 2, 'UTC', 'GPS'],
    'iMET': ['Intermet Systems', 'iMet-4', None, 'IMET', 'fn', 0, 'GPS', 'MSL'],
    #'M10': ['Meteomodem', 'M10', None, ['ser', 0], 'gpsleap', 2, 'UTC', 'GPS'],
    #'M20': ['Meteomodem', 'M20', None, ['ser', 0], 'gps', 2, 'GPS', 'GPS'],
    'MRZ': ['Meteo-Radiy', 'MRZ', None, ['ser', 0], 'gps', 5, 'UTC', 'GPS'],
    'MEISEI': ['Meisei', 'IMS100', None, ['ser', 7], 'fn', 1, 'UTC', 'GPS']
}
