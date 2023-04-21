# printData.py - Functions for printing data
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Print raw data
def print_raw_data(raw_data):
    print('Raw data:')
    print(raw_data)


# Print unified telemetry
def print_unified_telemetry(self, unified_telemetry):
    print('Telemetry:')
    # The unified telemetry parameter names are printed at a fixed length
    # This fixed length is based on the length of the longest unified telemetry parameter name
    # This results in a nicely formatted and easily readable output
    # Therefore the longest unified telemetry parameter name must be found in order to compile the parameter string
    names = []
    for parameter in self.shuConfig.telemetry:
        if parameter in unified_telemetry:
            names.append(self.shuConfig.telemetry[parameter]['name'])
    parameter_string = '{:<' + str(len(max(names, key=len)) + 1) + '} {} {}'
    # Go through all possible unified telemetry parameters
    for parameter in self.shuConfig.telemetry:
        # Print all unified telemetry parameters that are included in 'unified_telemetry'
        if parameter in unified_telemetry:
            # Print the unified telemetry parameters with their name, value and unit (optional)
            print(parameter_string.format(self.shuConfig.telemetry[parameter]['name'] + ':', unified_telemetry[parameter], '' if self.shuConfig.telemetry[parameter]['unit'] is None else self.shuConfig.telemetry[parameter]['unit']))


# Print reformatted telemetry
def print_reformatted_telemetry(self, reformatted_telemetry):
    print('Reformatted telemetry:')
    # The reformatted telemetry parameter names are printed at a fixed length
    # This fixed length is based on the length of the longest reformatted telemetry parameter name
    # This results in a nicely formatted and easily readable output
    # Therefore the longest reformatted telemetry parameter name must be found in order to compile the parameter string
    parameter_string = '{:<' + str(len(max(reformatted_telemetry.keys(), key=len)) + 1) + '} {} {}'
    # Go through all reformatted telemetry parameters existing in 'reformatted_telemetry'
    for name, unit in reformatted_telemetry.items():
        # Print the reformatted telemetry parameters with their name, value and unit (optional)
        print(parameter_string.format(name + ':', unit, '' if self.shuConfig.reformatted_telemetry[name] is None else self.shuConfig.reformatted_telemetry[name]))
