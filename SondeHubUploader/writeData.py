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


# Write unified telemetry
def write_unified_telemetry(self, unified_telemetry):
    # A CSV file is used
    # A prefix indicates that the file contains unified telemetry
    # CSV files are named by the serial of the radiosonde
    filename = self.filepath + '/' + self.shuConfig.filename_prefix_telemetry + unified_telemetry['serial'] + '.csv'
    # It is checked whether the file already exists
    exists = os.path.isfile(filename)
    status = 'File already exists' if exists else 'File does not exist'
    self.loggerObj.debug(status + ' (' + self.shuConfig.filename_prefix_telemetry + unified_telemetry['serial'] + '.csv)')
    try:
        file = open(filename, 'a', newline='', encoding='utf-8')
        writer = csv.writer(file, delimiter=',')
        # If the file does not already exist, a headline has to be written
        if not exists:
            headline_list = []
            # Go through all possible unified telemetry parameters
            for parameter in self.shuConfig.telemetry:
                # Build a headline string, starting with the name of the unified telemetry parameter
                headline_string = self.shuConfig.telemetry[parameter]['name']
                # Optionally the unit is added to the headline string
                if self.shuConfig.telemetry[parameter]['unit'] is not None:
                    headline_string += f' [{self.shuConfig.telemetry[parameter]["unit"]}]'
                headline_list.append(headline_string)
            writer.writerow(headline_list)
            self.loggerObj.debug('Headline written (%s.csv)', self.shuConfig.filename_prefix_telemetry + unified_telemetry['serial'])
        row_list = []
        # Go through all possible unified telemetry parameters
        for parameter in self.shuConfig.telemetry:
            # Write all unified telemetry parameters that are included in 'unified_telemetry'
            if parameter in unified_telemetry:
                row_list.append(unified_telemetry[parameter])
            # Write 'N/A' for all unified telemetry parameters that are not included in 'unified_telemetry'
            else:
                row_list.append('N/A')
        writer.writerow(row_list)
        file.close()
        self.loggerObj.debug('Telemetry written (%s.csv)', self.shuConfig.filename_prefix_telemetry + unified_telemetry['serial'])
    except OSError:
        self.loggerObj.error('Error writing telemetry (%s.csv)', self.shuConfig.filename_prefix_telemetry + unified_telemetry['serial'])


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
        file = open(filename, 'a', newline='', encoding='utf-8')
        writer = csv.writer(file, delimiter=',')
        # If the file does not already exist, a headline has to be written
        if not exists:
            headline_list = []
            # Go through all possible reformatted telemetry parameters
            for name, unit in self.shuConfig.reformatted_telemetry.items():
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
        for name, unit in self.shuConfig.reformatted_telemetry.items():
            # Write all reformatted telemetry parameters that are included in 'reformatted_telemetry'
            if name in reformatted_telemetry.keys():
                row_list.append(reformatted_telemetry[name])
            # Write 'N/A' for all reformatted telemetry parameters that are not included in 'reformatted_telemetry'
            else:
                row_list.append('N/A')
        writer.writerow(row_list)
        file.close()
        self.loggerObj.debug('Reformatted telemetry written (%s.csv)', self.shuConfig.filename_prefix_reformatted_telemetry + reformatted_telemetry['serial'])
    except OSError:
        self.loggerObj.error('Error writing reformatted telemetry (%s.csv)', self.shuConfig.filename_prefix_reformatted_telemetry + reformatted_telemetry['serial'])
