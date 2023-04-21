# paramHandling.py - Functions for handling the command line arguments
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Third-party modules
import argparse
# Own modules
import mainConfig


# Parse the provided command line arguments
def parse_arguments():
    # Create an 'ArgumentParser' object
    # The 'HelpFormatter' of the 'ArgumentParser' is modified using another function
    argumentParser = argparse.ArgumentParser(
        description='description: Accepts APRS packages from dxlAPRS and uploads the radiosonde telemetry to SondeHub',
        formatter_class=make_wide(argparse.HelpFormatter, 1000, 1000))
    # Add all arguments based on the configuration parameters
    for parameter in mainConfig.configuration_parameters:
        argumentParser.add_argument('-' + mainConfig.configuration_parameters[parameter]['positional_argument'],
                                    '--' + parameter,
                                    default=mainConfig.configuration_parameters[parameter]['default'],
                                    help=mainConfig.configuration_parameters[parameter]['description'] + ' (Default: ' + str(mainConfig.configuration_parameters[parameter]['default']) + ')',
                                    required=mainConfig.configuration_parameters[parameter]['required']
                                    )
    return vars(argumentParser.parse_args())


# Modify the width and height of a 'HelpFormatter' object
def make_wide(formatter, width, height):
    # The 'HelpFormatter' class is private
    # This means that this modification might stop working with future versions of 'argparse'
    # This is why this exception needs to be handled
    try:
        kwargs = {'width': width, 'max_help_position': height}
        formatter(None, **kwargs)
        return lambda prog: formatter(prog, **kwargs)
    except TypeError:
        return formatter


# Perform validity checks on all configuration parameters
def perform_checks(parameters):
    for key, value in parameters.items():
        # Validity checks are only carried out on configuration parameters that are different from the default
        if parameters[key] != mainConfig.configuration_parameters[key]['default']:
            # The validity check functions are saved as lambda functions in the 'configuration_parameters' dictionary
            if not mainConfig.configuration_parameters[key]['check_function'](parameters[key]):
                # If a configuration parameter was deemed invalid, it is set to 'False'
                parameters[key] = False
    return parameters


# Load the default for all configuration parameters that were deemed invalid
def load_defaults(parameters):
    for key, value in parameters.items():
        # An invalid configuration parameter has 'False' assigned to it by the previous validity checks
        if not parameters[key]:
            parameters[key] = mainConfig.configuration_parameters[key]['default']
    return parameters


# Cast all configuration parameters from 'str' to the needed datatypes
def cast(parameters):
    for key, value in parameters.items():
        # The configuration parameter 'pos' is somewhat special since it is a list of floats
        if key == 'pos' and parameters[key] is not None:
            parameters[key] = [float(element) for element in value.split(',')]
        else:
            # All integer configuration parameters are cast to 'int'
            if mainConfig.configuration_parameters[key]['type'] == int and type(parameters[key]) != mainConfig.configuration_parameters[key]['type']:
                parameters[key] = int(value)
    return parameters
