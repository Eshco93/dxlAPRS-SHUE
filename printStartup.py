# printStartup.py - Functions used for printing information at program startup
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Modules
import mainConfig


# Print a prolog message that contains all the configuration parameters
def print_prolog(parameters):
    # Print the headlines
    print('dxlAPRS-SHUE by Eshco93\n')
    print('Program configuration parameters:')
    # The full configuration parameter names are printed at a fixed length
    # This fixed length is based on the length of the longest configuration parameter name
    # This results in a nicely formatted and easily readable output
    parameter_string = '{:<' + str(max(len(mainConfig.configuration_parameters[key]['full_name']) for key in parameters) + 1) + '} {}'
    # Print all the configuration parameters
    for key, value in parameters.items():
        # The 'pos' configuration parameter is somewhat special, since it is composed of 3 individual parameters
        if key == 'pos':
            value = 'Lat: {} / Lon: {} / Alt: {}'.format(*value)
        # All other configuration parameters are just printed with their full name and value
        print(parameter_string.format(mainConfig.configuration_parameters[key]['full_name'] + ':', value))


# Print a warning for all configuration parameters that were deemed invalid
def print_warnings(parameters):
    for key, value in parameters.items():
        # An invalid configuration parameter has 'False' assigned to it by the previous validity checks
        if not value and type(value) == bool:
            print(f'"Warning: The configuration parameter "{mainConfig.configuration_parameters[key]["full_name"]}" that you provided is invalid. Therefore the default was loaded ({str(mainConfig.configuration_parameters[key]["default"])})')
