# paramChecks.py - Functions for checking the configuration parameter
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Modules
import ipaddress
# Own modules
import mainConfig


# Check whether an ip address is valid
def check_address(address):
    try:
        ipaddress.ip_address(address)
        return True
    except ValueError:
        return False


# Check whether a user callsign is valid
def check_user_callsign(user_callsign, min_length, max_length):
    # Allowed characters
    capital_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    lowercase_letters = 'abcdefghijklmnopqrstuvwxyz'
    numbers = '0123456789'
    special_characters = '-_'

    # The user callsign has a minimum and a maximum length (generic definition)
    if min_length <= len(user_callsign) <= max_length:
        # All characters of the user callsign must be in either of the allowed character lists
        if all(c in (capital_letters + lowercase_letters + numbers + special_characters) for c in user_callsign):
            return True
    return False


# Check whether a user position is valid
def check_user_position(user_position, min_altitude, max_altitude):
    try:
        # The user position is split because the individual values are separated by commas
        # The individual values are latitude, longitude and altitude
        user_position = [float(x) for x in user_position.split(',')]
        # The user position must have 3 elements
        # Latitude and longitude must be within a certain range
        # Altitude must be within a certain range (generic definition)
        if len(user_position) == 3 and\
                -90 <= user_position[0] <= 90 and\
                -180 <= user_position[1] <= 180 and\
                min_altitude <= user_position[2] <= max_altitude:
            return True
        return False
    # Checking the user position could throw several exceptions
    # Because of that, they are just handled all
    except Exception:
        return False


def check_required(casted_parameters):
    result = True
    # Go through all configuration parameters
    for parameter, (full_name, _type, default, positional_argument, description, check_function, required) in mainConfig.configuration_parameters.items():
        # Check whether a configuration parameter is required
        if required:
            # Check whether the configuration parameter still has the default value
            if casted_parameters[parameter] == default:
                print(f'Error: The configuration parameter {full_name} that you provided is invalid')
                result = False
    return result
