# handleData.py - Functions for data handling
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Modules
import datetime


# Parse an APRS package
def parse_aprs(self, aprs_package):
    aprs_telemetry = {}

    # At first the APRS telemetry parameters with fixed positions inside the APRS package are parsed
    # Go through all possible APRS telemetry parameters with fixed positions
    for parameter in self.shuConfig.parse_aprs_fixed_position:
        # The actual parsing is done using the parse function
        try:
            # Check whether the APRS package actually contains the indices for the APRS telemetry parameters
            if ((type(self.shuConfig.parse_aprs_fixed_position[parameter]['range'])) == slice and len(aprs_package) >= self.shuConfig.parse_aprs_fixed_position[parameter]['range'].stop) or\
                    ((type(self.shuConfig.parse_aprs_fixed_position[parameter]['range'])) == int and len(aprs_package) >= self.shuConfig.parse_aprs_fixed_position[parameter]['range']):
                aprs_telemetry[parameter] = self.shuConfig.parse_aprs_fixed_position[parameter]['parse_function'](aprs_package[self.shuConfig.parse_aprs_fixed_position[parameter]['range']])
                self.loggerObj.debug_detail(f'Parameter "{parameter}" parsed ({aprs_telemetry[parameter]})')
            else:
                raise Exception
        except Exception:
            self.loggerObj.error(f'Error parsing parameter "{parameter}"')

    # From now on it is easier to work with the APRS package cast to a string
    aprs_package_string = str(aprs_package)

    # Second, the optional APRS telemetry parameters are parsed
    # Go through all possible optional APRS telemetry parameters
    for parameter in self.shuConfig.parse_aprs_optional:
        # The APRS package string is searched for the key of the optional parameter
        start_index = self.utils.aprs_package_string_find_key(aprs_package_string, self.shuConfig.parse_aprs_optional[parameter]['prefix'])
        # 'aprs_package_string_find_key' will return the first index of the value if the key was found
        if start_index != -1:
            # For parsing, the end index of the value needs to be found as well
            end_index = aprs_package_string[start_index:].find(self.shuConfig.parse_aprs_optional[parameter]['unit_end']) + start_index
            # End index will be start index - 1 if it was not found
            # In that case the APRS telemetry parameter is the last one in the APRS package string
            if end_index < start_index:
                # The end index is therefore set to the last index in the APRS package string
                end_index = len(aprs_package_string)-1
            # The actual parsing is again done using the parse function
            try:
                aprs_telemetry[parameter] = self.shuConfig.parse_aprs_optional[parameter]['parse_function'](aprs_package_string[start_index:end_index])
                self.loggerObj.debug_detail(f'Parameter "{parameter}" parsed ({aprs_telemetry[parameter]})')
            except Exception:
                self.loggerObj.error(f'Error parsing parameter "{parameter}"')
        else:
            self.loggerObj.debug_detail(f'Parameter "{parameter}" not found in APRS package')

    # Third, the optional multivalue APRS telemetry parameters are parsed
    # Go through all possible optional multivalue APRS telemetry parameters
    for parameter in self.shuConfig.parse_aprs_optional_multivalue:
        # Finding the start and end index of the value is not different compared to the optional APRS telemetry parameters
        start_index = self.utils.aprs_package_string_find_key(aprs_package_string, self.shuConfig.parse_aprs_optional_multivalue[parameter]['prefix'])
        if start_index != -1:
            end_index = aprs_package_string[start_index:].find(self.shuConfig.parse_aprs_optional_multivalue[parameter]['unit_end']) + start_index
            # End index will be start index - 1 if it was not found
            # In that case the APRS telemetry parameter is the last one in the APRS package string
            if end_index < start_index:
                # The end index is therefore set to the last index in the APRS package string
                end_index = len(aprs_package_string) - 1
            # The actual parsing is different compared to the optional APRS telemetry parameters
            # Optional multivalue APRS telemetry parameters contain a list of subparameters
            # The subparameters are parsed using the subparameter parse function
            try:
                subparameter_list = self.shuConfig.parse_aprs_optional_multivalue[parameter]['subparameter_parse_function'](self.shuConfig.parse_aprs_optional_multivalue[parameter]['parse_function'](aprs_package_string[start_index:end_index]))
                for i in range(len(self.shuConfig.parse_aprs_optional_multivalue[parameter]['subparameter'])):
                    aprs_telemetry[self.shuConfig.parse_aprs_optional_multivalue[parameter]['subparameter'][i]] = subparameter_list[i]
                    self.loggerObj.debug_detail(f'Subparameter "{self.shuConfig.parse_aprs_optional_multivalue[parameter]["subparameter"][i]}" parsed ({aprs_telemetry[self.shuConfig.parse_aprs_optional_multivalue[parameter]["subparameter"][i]]})')
                self.loggerObj.debug_detail(f'Parameter "{parameter}" parsed')
            except Exception:
                self.loggerObj.error(f'Error parsing parameter "{parameter}"')
        else:
            self.loggerObj.debug_detail(f'Parameter "{parameter}" not found in APRS package')

    # Finally, one last optional special APRS telemetry parameter has to be parsed
    # The frequency APRS telemetry parameter does not have a prefix
    # It only has a unit attached to it (MHz)
    # In order to parse this, the unit is searched first instead of a prefix
    end_index = aprs_package_string.find(self.shuConfig.parse_aprs_optional_special['frequency']['unit_end'])
    if end_index != -1:
        # Then the beginning of the frequency APRS telemetry parameter is searched
        # This is done using a reverse search for the first space character, starting at the unit of the frequency APRS telemetry parameter
        start_index = aprs_package_string[:end_index].rfind(self.shuConfig.parse_aprs_optional_special['frequency']['prefix']) + 1
        # The actual parsing is again done using the parse function
        try:
            aprs_telemetry[list(self.shuConfig.parse_aprs_optional_special.keys())[0]] = self.shuConfig.parse_aprs_optional_special['frequency']['parse_function'](aprs_package_string[start_index:end_index])
            self.loggerObj.debug_detail(f'Parameter "{list(self.shuConfig.parse_aprs_optional_special.keys())[0]}" parsed ({aprs_telemetry[list(self.shuConfig.parse_aprs_optional_special.keys())[0]]})')
        except Exception:
            self.loggerObj.error(f'Error parsing parameter "{list(self.shuConfig.parse_aprs_optional_special.keys())[0]}"')
    return aprs_telemetry


# Parse the destination/source address of an APRS package
def parse_aprs_address(address):
    address_string = ''
    # The address is ASCII-coded and 6 characters long
    # But only MSB to LSB+1 of each byte contains the ASCII character
    # The LSB is the address extension bit, which can be ignored in this case
    for i in range(len(address) - 1):
        address_string += chr(address[i] >> 1)
    # The last byte contains the SSID and a few additional bits
    # The last byte has the following structure: CRRSSSSX
    # C = command/response bit
    # R = reserved bit
    # S = SSID bit
    # X = address extension bit
    # In this case, all bits but the SSID bits can be ignored
    address_string += '-' + str(int(format(address[len(address) - 1], '08b')[3:7], 2))
    return address_string


# Parse the minute string of gmm coordinates of an APRS package
def parse_aprs_gmm_minute(minute_string):
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
def parse_aprs_timer(timer_string):
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
def parse_aprs_rx(rx_string):
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
def parse_aprs_pump(pump_string):
    # This example shows the structure of the pump string
    # Pump=99mA 15.0V
    pump_ma_end_index = pump_string.find('mA')
    pump_v_end_index = pump_string.find('V')
    pump_ma = int(pump_string[:pump_ma_end_index])
    pump_v = float(pump_string[pump_ma_end_index + 3:pump_v_end_index])
    return [pump_ma, pump_v]


# Unify JSON telemetry
def unify_json(self, json_telemetry):
    unified_telemetry = {}

    # Go through all possible telemetry parameters
    for parameter in self.shuConfig.telemetry:
        try:
            # Check whether the telemetry parameter actually exists in JSON telemetry
            if self.shuConfig.telemetry[parameter]['json_source'] is not None:
                # Check whether the data type of the JSON source of the telemetry parameter is string, list or tuple
                if type(self.shuConfig.telemetry[parameter]['json_source']) == str:
                    # Telemetry parameters with a string JSON source can be unified directly using the JSON conversion function
                    unified_telemetry[parameter] = self.shuConfig.telemetry[parameter]['json_conversion_function'](json_telemetry[self.shuConfig.telemetry[parameter]['json_source']])
                elif type(self.shuConfig.telemetry[parameter]['json_source']) == list:
                    # Telemetry parameters with a list JSON source are contained within a sub-dictionary
                    # The list JSON source provides the keys necessary to access the telemetry parameter within the sub-dictionary
                    # Other than that, the telemetry parameters can be unified directly using the JSON conversion function
                    unified_telemetry[parameter] = self.shuConfig.telemetry[parameter]['json_conversion_function'](json_telemetry[self.shuConfig.telemetry[parameter]['json_source'][0]][self.shuConfig.telemetry[parameter]['json_source'][1]])
                elif type(self.shuConfig.telemetry[parameter]['json_source']) == tuple:
                    # Telemetry parameters with a tuple JSON source can be sourced from multiple JSON telemetry parameters
                    # These JSON telemetry parameters are compiled in a parameter list
                    parameter_list = []
                    for element in self.shuConfig.telemetry[parameter]['json_source']:
                        # The individual JSON telemetry parameters of type string or list (see above)
                        if type(element) == str:
                            parameter_list.append(json_telemetry[element] if element in json_telemetry else None)
                        elif type(element) == list:
                            parameter_list.append(
                                json_telemetry[element[0]][element[1]] if element[0] in json_telemetry and element[1] in json_telemetry[element[0]] else None)
                    # Source selection and unification are done by the JSON conversion function
                    # The JSON conversion function will return None in case of an error
                    if self.shuConfig.telemetry[parameter]['json_conversion_function'](*parameter_list) is not None:
                        unified_telemetry[parameter] = self.shuConfig.telemetry[parameter]['json_conversion_function'](*parameter_list)
                    else:
                        # Raise a KeyError in order to get a proper debug message (see below)
                        raise KeyError
                self.loggerObj.debug_detail(f'Parameter "{parameter}" unified')
            else:
                self.loggerObj.debug_detail(f'Parameter "{parameter}" does not exist in JSON telemetry')
        except KeyError:
            self.loggerObj.debug_detail(f'Parameter "{parameter}" not found in JSON telemetry')
    return unified_telemetry


# Unify the type of a JSON telemetry
def unify_json_type(_type, ser):
    # Multiple JSON telemetry parameter sources for the type only exist for RS41 radiosondes
    if _type == 'RS41':
        # The ser JSON telemetry parameter defines the detailed type (if it exists)
        if ser is not None:
            return ser
        else:
            # Otherwise the type JSON telemetry parameter is used
            return _type
    # For all radiosondes but the RS41, the type JSON telemetry parameter is used
    else:
        return _type


# Unify the frequency of a JSON telemetry
def unify_json_frequency(frequency, rx_frequency):
    # Some radiosondes might not provide their transmit frequency in their telemetry
    # In that case the receiver frequency must be used
    if frequency is not None:
        return frequency
    elif rx_frequency is not None:
        return rx_frequency
    else:
        return None


# Unify the burst timer of a JSON telemetry
def unify_json_burst_timer(bursttx, txoff):
    # The burst timer has two different JSON telemetry parameter sources
    # 'bursttx' is the JSON telemetry parameter source before the burst (burst timer not yet counting)
    # 'txoff' is the JSON telemetry parameter source after the burst (burst timer is counting)
    if bursttx is not None:
        return bursttx
    elif txoff is not None:
        return txoff
    else:
        return None


# Unify APRS telemetry
def unify_aprs(self, aprs_telemetry):
    unified_telemetry = {}

    # Go through all possible telemetry parameters
    for parameter in self.shuConfig.telemetry:
        try:
            # Check whether the telemetry parameter actually exists in APRS telemetry
            if self.shuConfig.telemetry[parameter]['aprs_source'] is not None:
                # Check whether the data type of the APRS source of the telemetry parameter is string or tuple
                if type(self.shuConfig.telemetry[parameter]['aprs_source']) == str:
                    # Telemetry parameters with a string APRS source can be unified directly using the APRS conversion function
                    unified_telemetry[parameter] = self.shuConfig.telemetry[parameter]['aprs_conversion_function'](aprs_telemetry[self.shuConfig.telemetry[parameter]['aprs_source']])
                elif type(self.shuConfig.telemetry[parameter]['aprs_source']) == tuple:
                    # Telemetry parameters with a tuple APRS source must be compiled from multiple APRS telemetry parameters
                    # These APRS telemetry parameters are compiled in a parameter list
                    parameter_list = []
                    for element in self.shuConfig.telemetry[parameter]['aprs_source']:
                        parameter_list.append(aprs_telemetry[element] if element in aprs_telemetry else None)
                    # Compiling and unification are done by the APRS conversion function
                    # The APRS conversion function will return None in case of an error
                    if self.shuConfig.telemetry[parameter]['aprs_conversion_function'](*parameter_list) is not None:
                        unified_telemetry[parameter] = self.shuConfig.telemetry[parameter]['aprs_conversion_function'](*parameter_list)
                    else:
                        # Raise a KeyError in order to get a proper debug message (see below)
                        raise KeyError
                self.loggerObj.debug_detail(f'Parameter "{parameter}" unified')
            else:
                self.loggerObj.debug_detail(f'Parameter "{parameter}" does not exist in APRS telemetry')
        except KeyError:
            self.loggerObj.debug_detail(f'Parameter "{parameter}" not found in APRS telemetry')
    return unified_telemetry


# Reformat the unified telemetry to the SondeHub telemetry format
# Source: https://github.com/projecthorus/sondehub-infra/wiki/SondeHub-Telemetry-Format
def reformat_telemetry(self, unified_telemetry):
    # Create a dictionary for the reformatted telemetry
    # At first, some data that is only station- and software-specific is added
    reformatted_telemetry = {
        'software_name': self.shuConfig.software_name,
        'software_version': self.shuConfig.software_version,
        'uploader_callsign': self.call if self.call is not None else unified_telemetry['source_address'],
        'uploader_position': [round(self.pos[0], 5), round(self.pos[1], 5), round(self.pos[2], 1)],
        'uploader_antenna': self.ant,
        'time_received': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
    }

    # Second, mandatory radiosonde-specific reformatted telemetry parameters are added
    # Go through all possible radiosonde types
    for name in self.shuConfig.radiosonde:
        # The radiosonde type is compared
        if unified_telemetry['type'].startswith(name):
            # manufacturer and type can be transferred directly
            reformatted_telemetry['manufacturer'] = self.shuConfig.radiosonde[name]['manufacturer']
            reformatted_telemetry['type'] = self.shuConfig.radiosonde[name]['type']
            # A subtype might be present for some radiosondes
            if self.shuConfig.radiosonde[name]['subtype'] is not None and unified_telemetry['type'] in self.shuConfig.radiosonde[name]['subtype']:
                reformatted_telemetry['subtype'] = unified_telemetry['type']
            # For IMET radiosondes a unique serial must be calculated (based on the convention of SondeHub)
            if self.shuConfig.radiosonde[name]['serial'] == 'IMET':
                # The date provided by the radiosonde is used (if it is available)
                if 'date' in unified_telemetry:
                    # Date and time are combined in a datetime object
                    _datetime = datetime.datetime.combine(unified_telemetry['date'], unified_telemetry['time'])
                # Otherwise the system date is used
                else:
                    _datetime = self.utils.generate_datetime(self, unified_telemetry['time'])
                # The leap seconds need to be factored in
                # The leap seconds provided by the radiosonde are used (if they are available)
                if 'leap_seconds' in unified_telemetry:
                    _datetime += datetime.timedelta(seconds=unified_telemetry['leap_seconds'])
                # Otherwise the hardcoded leap seconds are used
                else:
                    _datetime += datetime.timedelta(seconds=self.shuConfig.leap_seconds)
                # The IMET unique serial is calculated based on the datetime, framenumber and frequency
                reformatted_telemetry['serial'] = self.utils.imet_unique_serial(self, _datetime, unified_telemetry['framenumber'], unified_telemetry['frequency']).split('-')[1]
            # For all other radiosondes, the serial can be transferred directly
            else:
                serial = unified_telemetry[self.shuConfig.radiosonde[name]['serial'][0]][self.shuConfig.radiosonde[name]['serial'][1]:]
                # For M10 radiosondes, the serial provided by dxlAPRS is missing some dashes
                if reformatted_telemetry['type'] == 'M10':
                    reformatted_telemetry['serial'] = serial[0:3] + '-' + serial[3] + '-' + serial[4:]
                # For M20 radiosondes, the serial might have some sort of number in square brackets attached
                # This needs to me removed
                elif reformatted_telemetry['type'] == 'M20':
                    reformatted_telemetry['serial'] = serial.split('[', 1)[0]
                # For all other radiosondes, the serial can be transferred directly
                else:
                    reformatted_telemetry['serial'] = serial
            # The date provided by the radiosonde is used (if it is available)
            if 'date' in unified_telemetry:
                # Date and time are combined in a datetime object
                _datetime = datetime.datetime.combine(unified_telemetry['date'], unified_telemetry['time'])
            # Otherwise the system date is used
            else:
                _datetime = self.utils.generate_datetime(self, unified_telemetry['time'])
            # The leap seconds might need to be factored in
            # The leap seconds provided by the radiosonde are used (if they are available)
            if 'leap_seconds' in unified_telemetry:
                # The leap seconds must only be factored in in some cases
                # This depends on the time reference of the radiosonde and the time reference used by SondeHub (UTC or GPS)
                # Then sometimes the leap seconds provided by the radiosonde can be used
                # While in other cases the hardcoded leap seconds have to be used
                # The reasons for that are perhaps somewhat difficult to fathom
                # The time provided by dxlAPRS is always UTC
                # And the leap seconds provided by dxlAPRS are the leap seconds that were applied in order to get the time in UTC
                # One example: If the radiosonde time reference is GPS, dxlAPRS has to (currently) add 18 leap seconds in order to get UTC
                # That means the leap seconds provided by dxlAPRS will be 18
                # Another example: If the radiosonde time reference is UTC, dxlAPRS must not add any leap seconds
                # That means the leap seconds provided by dxlAPRS will be 0
                # With this background knowledge, you should be able to understand the following lines
                # Take some time to think this through carefully - it's quite a brainfuck
                if self.shuConfig.radiosonde[name]['radiosonde_time_reference'] == self.shuConfig.radiosonde[name]['sondehub_time_reference']:
                    _datetime += datetime.timedelta(seconds=unified_telemetry['leap_seconds'])
                elif self.shuConfig.radiosonde[name]['radiosonde_time_reference'] == 'UTC' and self.shuConfig.radiosonde[name]['sondehub_time_reference'] == 'GPS':
                    _datetime += datetime.timedelta(seconds=self.shuConfig.leap_seconds)
            # Otherwise the hardcoded leap seconds are used
            else:
                # The leap seconds must only be factored in when the SondeHub time reference is GPS
                # This is due to the fast that the time provided by dxlAPRS is always UTC
                if self.shuConfig.radiosonde[name]['sondehub_time_reference'] == 'GPS':
                    _datetime += datetime.timedelta(seconds=self.shuConfig.leap_seconds)
            # A datetime string is generated from the datetime
            reformatted_telemetry['datetime'] = _datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            # For most radiosondes, the framenumber can be transferred directly
            if self.shuConfig.radiosonde[name]['framenumber'] == 'fn':
                reformatted_telemetry['frame'] = unified_telemetry['framenumber']
            # But some radiosondes do not transmit a framenumber
            # In this case the GPS seconds (Seconds since 01/06/1980) are used as the framenumber
            elif self.shuConfig.radiosonde[name]['framenumber'] == 'gps':
                reformatted_telemetry['frame'] = int((datetime.datetime.strptime(reformatted_telemetry['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ') - datetime.datetime(1980, 1, 6, 0, 0, 0)).total_seconds())
                # The leap seconds might need to be factored in here as well
                # This depends on the time reference used by the radiosonde and the time reference used by SondeHub
                # If they both match, nothing needs to be done
                # If they are different, the leap seconds must be either added or subtracted
                if self.shuConfig.radiosonde[name]['radiosonde_time_reference'] == 'GPS' and self.shuConfig.radiosonde[name]['sondehub_time_reference'] == 'UTC':
                    reformatted_telemetry['frame'] += unified_telemetry['leap_seconds'] if 'leap_seconds' in unified_telemetry else self.shuConfig.leap_seconds
                elif self.shuConfig.radiosonde[name]['radiosonde_time_reference'] == 'UTC' and self.shuConfig.radiosonde[name]['sondehub_time_reference'] == 'GPS':
                    reformatted_telemetry['frame'] -= unified_telemetry['leap_seconds'] if 'leap_seconds' in unified_telemetry else self.shuConfig.leap_seconds
            # The altitude is provided with a radiosonde-specific precision
            reformatted_telemetry['alt'] = float(round(unified_telemetry['altitude'], self.shuConfig.radiosonde[name]['altitude_precision']))
            # ref_datetime and ref_position can be transferred directly
            reformatted_telemetry['ref_datetime'] = self.shuConfig.radiosonde[name]['sondehub_time_reference']
            reformatted_telemetry['ref_position'] = self.shuConfig.radiosonde[name]['sondehub_position_reference']
            # Break out of for-loop after the first match because only a single match is expected
            break

    # Thirdly, mandatory non-radiosonde-specific reformatted telemetry parameters are added
    # lat and lon can be transferred directly
    reformatted_telemetry['lat'] = unified_telemetry['latitude']
    reformatted_telemetry['lon'] = unified_telemetry['longitude']
    self.loggerObj.debug_detail(f'All mandatory parameters reformatted')

    # Finally, all optional reformatted telemetry parameters are added
    # Go through all unified telemetry parameters
    for key, value in unified_telemetry.items():
        # Check for optional telemetry parameters
        if self.shuConfig.telemetry[key]['optional'] is not False:
            # Reformat the optional telemetry parameters using the reformat function
            reformatted_telemetry[self.shuConfig.telemetry[key]['optional']] = self.shuConfig.telemetry[key]['reformat_function'](value)
            self.loggerObj.debug_detail(f'Optional parameter "{key}" reformatted')
    return reformatted_telemetry


# Reformat the xdata of a unified telemetry
def reformat_xdata(xdata):
    # xdata is ASCII-coded and provided as a string
    reformatted_xdata = ''
    for element in xdata[1:]:
        reformatted_xdata += chr(element)
    return reformatted_xdata
