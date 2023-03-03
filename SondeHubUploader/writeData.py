# writeData.py - Functions for writing data
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Modules
import csv
import datetime
import os.path


# Print raw data
def write_raw_data(self, raw_data):
    # A simple text file is used
    # The name of the file is hardcoded
    filename = self.filepath + '/' + self.shuConfig.filename_raw_data + '.txt'
    try:
        f = open(filename, 'a', newline='', encoding='utf-8')
        f.write('[' + str(datetime.datetime.now()) + '] ' + str(raw_data))
        # All entries are separated by a new line
        f.write('\n')
        f.close()
        self.loggerObj.debug('Raw data written (%s.txt)', self.shuConfig.filename_raw_data)
    except OSError:
        self.loggerObj.error('Error writing raw data (%s.txt)', self.shuConfig.filename_raw_data)


# Write telemetry
def write_telemetry(self, telemetry):
    # A CSV file is used
    # A prefix indicates that the file contains telemetry
    # CSV files are named by the serial of the radiosonde
    filename = self.filepath + '/' + self.shuConfig.filename_prefix_telemetry + telemetry['serial'] + '.csv'
    # It is checked whether the file already exists
    exists = os.path.isfile(filename)
    status = 'File already exists' if exists else 'File does not exist'
    self.loggerObj.debug(status + ' (' + self.shuConfig.filename_prefix_telemetry + telemetry['serial'] + '.csv)')
    try:
        f = open(filename, 'a', newline='', encoding='utf-8')
        writer = csv.writer(f, delimiter=',')
        # If the file does not already exist, a headline has to be written
        if not exists:
            headline_list = []
            # Go through all possible telemetry parameters
            for name, (parameter, unit, function) in self.shuConfig.print_write_telemetry.items():
                # Build a headline string, starting with the name of the telemetry parameter
                headline_string = name
                # Optionally the unit is added to the headline string
                if unit is not None:
                    headline_string += f' [{unit}]'
                headline_list.append(headline_string)
            writer.writerow(headline_list)
            self.loggerObj.debug('Headline written (%s.csv)', self.shuConfig.filename_prefix_telemetry + telemetry['serial'])
        row_list = []
        # Go through all possible telemetry parameters
        for name, (parameter, unit, conversion_function) in self.shuConfig.print_write_telemetry.items():
            # Write all telemetry parameters that are included in 'telemetry'
            if all(item in telemetry.keys() for item in parameter):
                # Some written parameters are composed or calculated from several telemetry parameters
                # These telemetry parameters must be added to a list in order to be passed to the conversion function
                parameter_list = []
                for element in parameter:
                    parameter_list.append(telemetry[element])
                row_list.append(conversion_function(*parameter_list))
            # Write 'N/A' for all telemetry parameters that are not included in 'telemetry'
            else:
                row_list.append('N/A')
        writer.writerow(row_list)
        f.close()
        self.loggerObj.debug('Telemetry written (%s.csv)', self.shuConfig.filename_prefix_telemetry + telemetry['serial'])
    except OSError:
        self.loggerObj.error('Error writing telemetry (%s.csv)', self.shuConfig.filename_prefix_telemetry + telemetry['serial'])


# Write reformatted telemetry
def write_reformatted_telemetry(self, reformatted_telemetry):
    # A CSV file is used
    # A prefix indicates that the file contains reformatted telemetry
    # CSV files are named by the serial of the radiosonde
    filename = self.filepath + '/' + self.shuConfig.filename_prefix_reformatted_telemetry + reformatted_telemetry['serial'] + '.csv'
    # It is checked whether the file already exists
    exists = os.path.isfile(filename)
    status = 'File already exists' if exists else 'File does not exist'
    self.loggerObj.debug(status + ' (' + self.shuConfig.filename_prefix_reformatted_telemetry + reformatted_telemetry['serial'] + '.csv)')
    try:
        f = open(filename, 'a', newline='', encoding='utf-8')
        writer = csv.writer(f, delimiter=',')
        # If the file does not already exist, a headline has to be written
        if not exists:
            headline_list = []
            # Go through all possible reformatted telemetry parameters
            for name, unit in self.shuConfig.write_reformatted_telemetry.items():
                # Build a headline string, starting with the name of the reformatted telemetry parameter
                headline_string = name
                # Optionally the unit is added to the headline string
                if unit is not None:
                    headline_string += f' [{unit}]'
                headline_list.append(headline_string)
            writer.writerow(headline_list)
            self.loggerObj.debug('Headline written (%s.csv)', self.shuConfig.filename_prefix_reformatted_telemetry + reformatted_telemetry['serial'])
        row_list = []
        # Go through all possible reformatted telemetry parameters
        for name, unit in self.shuConfig.write_reformatted_telemetry.items():
            # Write all reformatted telemetry parameters that are included in 'reformatted_telemetry'
            if name in reformatted_telemetry.keys():
                row_list.append(reformatted_telemetry[name])
            # Write 'N/A' for all telemetry parameters that are not included in 'reformatted_telemetry'
            else:
                row_list.append('N/A')
        writer.writerow(row_list)
        f.close()
        self.loggerObj.debug('Reformatted telemetry written (%s.csv)', self.shuConfig.filename_prefix_reformatted_telemetry + reformatted_telemetry['serial'])
    except OSError:
        self.loggerObj.error('Error writing reformatted telemetry (%s.csv)', self.shuConfig.filename_prefix_reformatted_telemetry + reformatted_telemetry['serial'])
