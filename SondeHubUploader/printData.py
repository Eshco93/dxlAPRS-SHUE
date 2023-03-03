# printData.py - Functions for printing data
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Print raw data
def print_raw_data(raw_data):
    print('Raw data:')
    print(raw_data)


# Print telemetry
def print_telemetry(self, telemetry):
    print('Telemetry:')
    # The telemetry parameter names are printed at a fixed length
    # This fixed length is based on the length of the longest telemetry parameter name
    # This results in a nicely formatted and easily readable output
    parameter_string = '{:<' + str(len(max(self.shuConfig.print_write_telemetry.keys(), key=len)) + 1) + '} {} {}'
    # Go through all possible telemetry parameters
    for name, (parameter, unit, conversion_function) in self.shuConfig.print_write_telemetry.items():
        # Print all telemetry parameters that are included in 'telemetry'
        if all(item in telemetry.keys() for item in parameter):
            # Some printed parameters are composed or calculated from several telemetry parameters
            # These telemetry parameters must be added to a list in order to be passed to the conversion function
            parameter_list = []
            for element in parameter:
                parameter_list.append(telemetry[element])
            # Print the telemetry parameters with their name, value and unit (optional)
            print(parameter_string.format(name + ':', conversion_function(*parameter_list), '' if unit is None else unit))


# Print reformatted telemetry
def print_reformatted_telemetry(self, reformatted_telemetry):
    print('Reformatted telemetry:')
    # The reformatted telemetry parameter names are printed at a fixed length
    # This fixed length is based on the length of the longest reformatted telemetry parameter name
    # This results in a nicely formatted and easily readable output
    parameter_string = '{:<' + str(len(max(reformatted_telemetry.keys(), key=len)) + 1) + '} {} {}'
    # Go through all reformatted telemetry parameters existing in 'reformatted_telemetry'
    for name, unit in reformatted_telemetry.items():
        # Print the reformatted telemetry parameters with their name, value and unit (optional)
        print(parameter_string.format(name + ':', unit, '' if self.shuConfig.write_reformatted[name] is None else self.shuConfig.write_reformatted[name]))
