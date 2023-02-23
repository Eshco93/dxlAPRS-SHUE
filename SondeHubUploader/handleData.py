# handleData.py - Functions for data handling
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Modules
import datetime


# Parse an APRS package
def parse_aprs_package(self, aprs_package):
    telemetry = {}

    # At first the telemetry parameters with fixed positions inside the APRS package are parsed
    # Go through all possible telemetry parameters with fixed positions
    for parameter, (index, parse_function) in self.shuConfig.parse_fixed_position.items():
        # The actual parsing is done using the parse function
        try:
            # Check whether the APRS package actually contains the indices for the telemetry parameters
            if ((type(index)) == slice and len(aprs_package) >= index.stop) or ((type(index)) == int and len(aprs_package) >= index):
                telemetry[parameter] = parse_function(aprs_package[index])
                self.loggerObj.debug_detail(f'Parameter "{parameter}" parsed ({telemetry[parameter]})')
            else:
                raise Exception
        except Exception:
            self.loggerObj.error(f'Error parsing parameter "{parameter}"')

    # From now on it is easier to work with the APRS package cast to a string
    aprs_package_string = str(aprs_package)

    # Second, the optional telemetry parameters are parsed
    # Go through all possible optional telemetry parameters
    for parameter, (start_string, end_string, parse_function) in self.shuConfig.parse_optional.items():
        # The APRS package string is searched for the key of the optional parameter
        start_index = self.utils.aprs_package_string_find_key(aprs_package_string, start_string)
        # 'aprs_package_string_find_key' will return the first index of the value if the key was found
        if start_index != -1:
            # For parsing, the end index of the value needs to be found as well
            end_index = aprs_package_string[start_index:].find(end_string) + start_index
            # The actual parsing is again done using the parse function
            try:
                telemetry[parameter] = parse_function(aprs_package_string[start_index:end_index])
                self.loggerObj.debug_detail(f'Parameter "{parameter}" parsed ({telemetry[parameter]})')
            except Exception:
                self.loggerObj.error(f'Error parsing parameter "{parameter}"')
        else:
            self.loggerObj.debug_detail(f'Parameter "{parameter}" not found in APRS package')

    # Third, the optional multivalue telemetry parameters are parsed
    # Go through all possible optional multivalue telemetry parameters
    for parameter, (start_string, end_string, parse_function, subparameters, subparameter_parse_function) in self.shuConfig.parse_optional_multivalue.items():
        # Finding the start and end index of the value is not different compared to the optional telemetry parameters
        start_index = self.utils.aprs_package_string_find_key(aprs_package_string, start_string)
        if start_index != -1:
            end_index = aprs_package_string[start_index:].find(end_string) + start_index
            # The actual parsing is different compared to the optional telemetry parameters
            # Optional multivalue telemetry parameters contain a list of subparameters
            # The subparameters are parsed using the subparameter parse function
            try:
                subparameter_list = subparameter_parse_function(parse_function(aprs_package_string[start_index:end_index]))
                for i in range(len(subparameters)):
                    telemetry[subparameters[i]] = subparameter_list[i]
                    self.loggerObj.debug_detail(f'Subparameter "{subparameters[i]}" parsed ({telemetry[subparameters[i]]})')
                self.loggerObj.debug_detail(f'Parameter "{parameter}" parsed')
            except Exception:
                self.loggerObj.error(f'Error parsing parameter "{parameter}"')
        else:
            self.loggerObj.debug_detail(f'Parameter "{parameter}" not found in APRS package')

    # Finally, one last optional special telemetry parameter has to be parsed
    # The frequency telemetry parameter does not have a prefix
    # It only has a unit attached to it (MHz)
    # In order to parse this, the unit is searched first instead of a prefix
    end_index = aprs_package_string.find(list(self.shuConfig.parse_optional_special.values())[0][1])
    if end_index != -1:
        # Then the beginning of the frequency telemetry parameter is searched
        # This is done using a reverse search for the first space character, starting at the unit of the frequency telemetry parameter
        start_index = aprs_package_string[:end_index].rfind(list(self.shuConfig.parse_optional_special.values())[0][0]) + 1
        # The actual parsing is again done using the parse function
        try:
            telemetry[list(self.shuConfig.parse_optional_special.keys())[0]] = list(self.shuConfig.parse_optional_special.values())[0][2](aprs_package_string[start_index:end_index])
            self.loggerObj.debug_detail(f'Parameter "{list(self.shuConfig.parse_optional_special.keys())[0]}" parsed ({telemetry[list(self.shuConfig.parse_optional_special.keys())[0]]})')
        except Exception:
            self.loggerObj.error(f'Error parsing parameter "{list(self.shuConfig.parse_optional_special.keys())[0]}"')
    return telemetry


# Parse the minute string of gmm coordinates of an APRS package
def parse_gmm_minute(minute_string):
    # The minute string of gmm coordinates inside an APRS package has a fixed length
    # But some digits might be replaced with spaces, if only limited precision is available
    # This must be considered
    # If all digits are replaced with spaces, no minute is available
    if minute_string == '  .  ':
        return 0
    # If all digits but the first one are replaced with spaces, only 10 minute precision is available
    elif minute_string[0].isdigit() and minute_string[1:] == ' .  ':
        return int(minute_string[0]) * 10
    # In all other cases, the minute can be cast to float
    else:
        return float(minute_string)


# Parse a timer string of an APRS package
def parse_timer(timer_string):
    # If hour or minute or second might be non-existent in the timer string
    # In that case, these values are considered to be zero
    hour, minute, second = 0, 0, 0
    # hour, minute and second are separated by the characters 'h', 'm' and 's'
    hour_index = timer_string.find('h')
    if hour_index != -1:
        hour = int(timer_string[:hour_index])
    minute_index = timer_string.find('m')
    if minute_index != -1:
        minute = int(timer_string[hour_index+1:minute_index])
    second_index = timer_string.find('s')
    if second_index != -1:
        second = int(timer_string[minute_index+1:second_index])
    return [hour, minute, second]

# Parse the rx string of an APRS package
def parse_rx(rx_string):
    # This example shows the structure of the rx string
    # rx=403900(+2/5)
    rx_f_end_index = rx_string.find('(')
    rx_afc_end_index = rx_string.find('/')
    rx_afc_max_end_index = rx_string.find(')')
    rx_f = int(rx_string[:rx_f_end_index])
    rx_afc = int(rx_string[rx_f_end_index + 1:rx_afc_end_index])
    rx_afc_max = int(rx_string[rx_afc_end_index + 1:rx_afc_max_end_index])
    return [rx_f, rx_afc, rx_afc_max]

# Parse the pump string of an APRS package
def parse_pump(pump_string):
    # This example shows the structure of the pump string
    # Pump=99mA 15.0V
    pump_ma_end_index = pump_string.find('mA')
    pump_v_end_index = pump_string.find('V')
    pump_ma = int(pump_string[:pump_ma_end_index])
    pump_v = float(pump_string[pump_ma_end_index + 3:pump_v_end_index])
    return [pump_ma, pump_v]


# Reformat telemetry to the SondeHub telemetry format
# Source: https://github.com/projecthorus/sondehub-infra/wiki/SondeHub-Telemetry-Format
def reformat_telemetry(self, telemetry):
    # Create a dictionary for the SondeHub telemetry
    # At first, some data that is only station- and software-specific is added
    reformatted_telemetry = {
        'software_name': self.shuConfig.software_name,
        'software_version': self.shuConfig.software_version,
        'uploader_callsign': self.call,
        'uploader_position': [round(self.pos[0], 5), round(self.pos[1], 5), round(self.pos[2], 1)],
        'uploader_antenna': self.ant,
        'time_received': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
    }

    # Second, mandatory radiosonde-specific telemetry parameters are added
    # Go through all possible radiosonde types
    for name, (manufacturer, _type, subtypes, serial, fn, altitude_precision, ref_datetime, ref_position) in self.shuConfig.radiosonde.items():
        # The radiosonde type is compared
        if telemetry['type'].startswith(name):
            # manufacturer and type can be transferred directly
            reformatted_telemetry['manufacturer'] = manufacturer
            reformatted_telemetry['type'] = _type
            # A subtype might be present for some radiosondes
            if subtypes is not None and telemetry['type'] in subtypes:
                reformatted_telemetry['subtype'] = telemetry['type']
            # For IMET radiosondes a unique serial must be calculated (based on the convention of SondeHub)
            if serial == 'IMET':
                reformatted_telemetry['serial'] = self.utils.imet_unique_serial(self, telemetry['hour'], telemetry['minute'], telemetry['second'], telemetry['fn'], telemetry['f']).split('-')[1]

            # For all other radiosondes, the serial can be taken directly from the telemetry
            else:
                reformatted_telemetry['serial'] = telemetry[serial[0]][serial[1]:]
                # For M10 radiosondes, the serial provided by dxlAPRS is missing some dashes
                if reformatted_telemetry['type'] == 'M10':
                    reformatted_telemetry['serial'] = reformatted_telemetry['serial'][0:3] + '-' + reformatted_telemetry['serial'][3] + '-' + reformatted_telemetry['serial'][4:]
            # The datetime is composed of the time provided by dxlAPRS and a date that is added manually
            reformatted_telemetry['datetime'] = self.utils.fix_datetime(self, telemetry['hour'], telemetry['minute'], telemetry['second'], True if ref_datetime == 'GPS' else False).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            # For most radiosondes, the framenumber can be taken directly from the telemetry
            if fn == 'fn':
                reformatted_telemetry['frame'] = telemetry['fn']
            # But some radiosondes do not transmit a framenumber
            # In this case the GPS seconds (Seconds since 01/06/1980) are used as the framenumber
            else:
                reformatted_telemetry['frame'] = int((datetime.datetime.strptime(reformatted_telemetry['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ')-datetime.datetime(1980, 1, 6, 0, 0, 0)).total_seconds())
                # For some radiosondes, leap seconds must also be included
                if fn == 'gpsleap':
                    reformatted_telemetry['frame'] += self.shuConfig.leap_seconds
            # The altitude must be in meters, but can otherwise be taken directly from the telemetry
            reformatted_telemetry['alt'] = float(self.conversions.feet_to_meter(telemetry['altitude'], altitude_precision))
            # ref_datetime and ref_position can be transferred directly
            reformatted_telemetry['ref_datetime'] = ref_datetime
            reformatted_telemetry['ref_position'] = ref_position
            # Break out of the for-loop after the first match of the radiosonde type
            break

    # At this point all mandatory radiosonde-specific telemetry parameters were added
    # latitude and longitude are mandatory as well, but not radiosonde specific
    # latitude and longitude are in decimal degree
    # Additional precision is provided using the APRS precision and datum option
    reformatted_telemetry['lat'] = self.conversions.gmm_to_dg(telemetry['latitude_degree'],
                                                  self.utils.minute_add_precision(self, telemetry['latitude_minute'], telemetry['dao_D'], telemetry['dao_A']),
                                                  telemetry['latitude_ns'],
                                                  self.shuConfig.reformat_position_precision
                                                  )
    reformatted_telemetry['lon'] = self.conversions.gmm_to_dg(telemetry['longitude_degree'],
                                                  self.utils.minute_add_precision(self, telemetry['longitude_minute'], telemetry['dao_D'], telemetry['dao_O']),
                                                  telemetry['longitude_we'],
                                                  self.shuConfig.reformat_position_precision
                                                  )

    # Finally, all optional telemetry parameters are added
    # Go through all telemetry parameters
    for key, value in telemetry.items():
        # Check for optional telemetry parameters
        if self.shuConfig.telemetry[key][2]:
            # Reformat the optional telemetry parameters using the reformat function
            reformatted_telemetry[self.shuConfig.telemetry[key][3]] = self.shuConfig.telemetry[key][4](value)
    return reformatted_telemetry
