# telemetryChecks.py - Functions for checking the telemetry
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later
import datetime


# Check whether unified telemetry is plausible
def check_plausibility(self, unified_telemetry):
    # Go through all unified telemetry parameters
    # 'unified_telemetry' is cast to a list, because the values might be modified during the loop
    for key, value in list(unified_telemetry.items()):
        # Check all unified telemetry parameters that have a plausibility function assigned to them
        if self.shuConfig.telemetry[key]['plausibility_function'] is not None:
            # Check the unified telemetry parameters using the plausibility function
            if self.shuConfig.telemetry[key]['plausibility_function'](value):
                self.loggerObj.debug_detail(f'Parameter "{key}" plausible')
            else:
                # Unified telemetry parameters that are not plausible are removed from 'unified_telemetry'
                unified_telemetry.pop(key)
                self.loggerObj.warning(f'Parameter "{key}" not plausible')
        else:
            self.loggerObj.debug_detail(f'Parameter "{key}" has no plausibility check')
    return unified_telemetry


# Check whether a callsign is plausible
def check_callsign_plausibility(callsign):
    # Allowed characters
    capital_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    numbers = '0123456789'

    # A callsign must be either 8 or 9 characters long (depending on the length of the SSID)
    # A callsign (without SSID) must only include capital letters and numbers
    # Callsign and SSID are separated by a '-' character
    # The SSID must be between 0 and 15
    if len(callsign) in range(8, 10) and\
            all(characters in (capital_letters + numbers) for characters in callsign[0:6]) and\
            callsign[6] == '-' and\
            int(callsign[7:]) in range(0, 16):
        return True
    return False


# Check whether a date is plausible
def check_date_plausibility(date, difference_days):
    # The date must be within a certain range around the current UTC date in order to be deemed plausible
    # Calculate the thresholds
    lower_threshold = datetime.datetime.utcnow().date() - datetime.timedelta(days=difference_days)
    upper_threshold = datetime.datetime.utcnow().date() + datetime.timedelta(days=difference_days)

    if lower_threshold <= date <= upper_threshold:
        return True
    return False


# Check whether a time is plausible
def check_time_plausibility(time, difference_seconds):
    # The time must be within a certain range around the current UTC time in order to be deemed plausible
    # Calculate the thresholds
    lower_threshold = (datetime.datetime.utcnow() - datetime.timedelta(seconds=difference_seconds)).time()
    upper_threshold = (datetime.datetime.utcnow() + datetime.timedelta(seconds=difference_seconds)).time()

    if lower_threshold <= time <= upper_threshold:
        return True
    return False


# Check whether xdata is plausible
def check_xdata_plausibility(xdata):
    # Go through the entire xdata list
    for i in range(0, len(xdata)):
        # The first element in the xdata list is some 8 bit value with unknown meaning
        if i == 0:
            if not 0 <= xdata[i] <= 255:
                return False
        else:
            # All other elements are ASCII-coded hexadecimal characters in integer representation
            # So these values should be in between 48 and 57 (0 to 9) or 65 and 70 (A to F)
            if not (48 <= xdata[i] <= 57 or 65 <= xdata[i] <= 70):
                return False
    return True


# Check whether satellite levels are plausible
def check_satellite_levels_plausibility(satellite_levels):
    # Go through the entire satellite levels list
    for element in satellite_levels:
        # All regular satellite levels should be in between 0 and 100
        # -1 is also valid (not connected)
        if not -1 <= element <= 100:
            return False
    return True


# Check whether unified telemetry contains all mandatory parameters for SondeHub
def check_mandatory(self, unified_telemetry):
    # The check result is initially 'True' and might be set to 'False' by the checks
    result = True
    # At first, all the unified telemetry parameters that are mandatory for all radiosondes are checked
    # Go through all possible unified telemetry parameters
    for parameter in self.shuConfig.telemetry:
        # 'mandatory' is set to true, if the unified telemetry parameter is mandatory for all radiosondes
        if self.shuConfig.telemetry[parameter]['mandatory'] == True:
            # Check whether the parameter exists in 'unified_telemetry'
            if parameter in unified_telemetry:
                self.loggerObj.debug_detail(f'Mandatory parameter "{parameter}" exists')
            else:
                result = False
                self.loggerObj.debug_detail(f'Mandatory parameter "{parameter}" is missing')
    # The radiosonde type needs to be determined in order to check the mandatory unified telemetry parameters for specific radiosondes
    _type = None
    # Go through all possible radiosonde types and compare the type
    for key in self.shuConfig.radiosonde.keys():
        if 'type' in unified_telemetry and unified_telemetry['type'].startswith(key):
            _type = key
    if _type is not None:
        # Go through all possible unified telemetry parameters (again)
        for parameter in self.shuConfig.telemetry:
            # 'mandatory' contains a list of radiosonde types, if the unified telemetry parameter is mandatory for specific radiosondes
            if type(self.shuConfig.telemetry[parameter]['mandatory']) == list and _type in self.shuConfig.telemetry[parameter]['mandatory']:
                # Check whether the parameter exists in 'unified_telemetry'
                if parameter in unified_telemetry:
                    self.loggerObj.debug_detail(f'Mandatory parameter "{parameter}" exists')
                else:
                    result = False
                    self.loggerObj.error(f'Mandatory parameter "{parameter}" is missing')
    else:
        result = False
        self.loggerObj.error('Radiosonde type unknown')
    return result
