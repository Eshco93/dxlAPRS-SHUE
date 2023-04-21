# utils.py - Utils
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


import json
import datetime
import hashlib


# Check whether data is valid JSON data
def check_json(self, data):
    # Checking whether JSON data is valid is relatively easy by just trying to decode it
    try:
        json.loads(data.decode())
    except ValueError:
        return False
    return True


# Search for a key inside an aprs package string
def aprs_package_string_find_key(aprs_string, key):
    # There might be a space or an exclamation mark before the key
    for prefix in [' ', '!']:
        index = aprs_string.find(prefix + key)
        # Calculate the first index of the value
        if index != -1:
            return index + len(key) + 1
    return -1


# Add precision to the minutes of latitude or longitude, using the APRS precision and datum option
# Source: http://www.aprs.org/aprs12/datum.txt
def minute_add_precision(self, minute, dao_D, precision):
    # There is no additional precision that can be added, if the precision character is space
    if precision == ord(' '):
        if self is not None:
            self.loggerObj.warning('No additional precision')
        return minute
    # The 'D' character has to be 'w' or 'W' for double or single digit precision
    # All other characters are invalid
    if dao_D not in [ord('w'), ord('W')]:
        if self is not None: self.loggerObj.error('Invalid dao_D character')
        return minute
    else:
        # Precision is added in the form of additional digits for the minute decimal part
        # By default the minute contains up to two decimal digits
        # In order to add the additional digits properly, the minute is cast to a string with exactly two decimal digits
        minute = format(minute, '.2f')
        # Two digit precision is used, when the 'D' character is 'w'
        if dao_D == ord('w'):
            # The two decimal digits are calculated as per the definition of the APRS precision and datum option
            minute += '{:03d}'.format(round((precision - 33) * 1.1 * 10))
            if self is not None:
                self.loggerObj.debug('Two digit precision added')
        # Single digit precision is used, when the 'D' character is 'W'
        else:
            # Single digit precision can be added to the minute string directly without any additional calculation
            minute += str(precision)
            if self is not None:
                self.loggerObj.debug('Single digit precision added')
        # The minute string must be cast back to float before returning
        return float(minute)


# Generates a datetime object from a time object by adding the current system date
def generate_datetime(self, time):
    # Get the current system datetime (UTC)
    now = datetime.datetime.utcnow()
    # A datetime string is generated, using the time and the current system date
    _datetime = datetime.datetime.combine(now.date(), time)

    # Everything is fine, if the time is outside the rollover window
    if now.hour in [23, 0]:
        self.loggerObj.debug('Time is within rollover window')
        # There was a rollover according to the system time, but the radiosonde time is still from the last day
        # This might happen, since there is a minor time difference between the frame being sent out by the radiosonde and the processing at this point
        if _datetime.hour == 23 and now.hour == 0:
            # In that case, one day needs to be subtracted from the current date in order to have the correct date for the given radiosonde frame
            fixed_datetime = _datetime - datetime.timedelta(days=1)
            self.loggerObj.debug('One day was subtracted due to a rollover issue (%s)', fixed_datetime)
        # There was a rollover according to the radiosonde time, but the system time is still from the last day
        # This might happen if the system clock is running slow
        elif _datetime.hour == 0 and now.hour == 23:
            # In that case, one day needs to be added to the current date in order to have the correct date for the given radiosonde frame
            fixed_datetime = _datetime + datetime.timedelta(days=1)
            self.loggerObj.debug('One day was added due to a rollover issue (%s)', fixed_datetime)
        else:
            self.loggerObj.debug('No rollover issue detected')
    else:
        self.loggerObj.debug('Time is outside rollover window')
    return _datetime


# Calculate a unique serial for an IMET radiosonde (based on the convention of SondeHub)
# Source: https://github.com/projecthorus/radiosonde_auto_rx/blob/master/auto_rx/autorx/sonde_specific.py
def imet_unique_serial(self, _datetime, framenumber, frequency):
    # The power on time is calculated using the time and framenumber provided by the IMET radiosonde
    # Because IMET radiosondes send one frame per second, the framenumber can be understood as the time since power on in seconds
    # time - framenumber = power on time
    power_on_time = _datetime - datetime.timedelta(seconds=framenumber)
    # A datetime string is generated from the power on time
    # The frequency that the IMET radiosonde transmits on is added to the string
    # The frequency is rounded to the nearest 100 kHz in order to avoid issues due to frequency drift
    # Finally, the string 'SONDE' is added
    temp_str = power_on_time.strftime("%Y-%m-%dT%H:%M:%SZ") + '{0:.3f}'.format(round(frequency, 1)) + ' MHz' + 'SONDE'
    # Calculate a SHA256 hash of the string
    serial = 'IMET-' + hashlib.sha256(temp_str.encode('ascii')).hexdigest().upper()[-8:]
    self.loggerObj.debug('Calculated IMET unique serial (%s)', serial)
    # The hash is used as the unique serial
    return serial
