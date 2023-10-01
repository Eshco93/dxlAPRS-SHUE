# threads.py - Threads of the SondeHubUploader
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Modules
import socket
import queue
import json
import time


# Receive packages
def receive(self):
    # Create a socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((self.addr, self.port))

    while self.running:
        # Try to receive a package
        data, addr = sock.recvfrom(self.shuConfig.udp_buffersize)
        self.loggerObj.debug('Package received')
        # Store the package to the input queue
        try:
            self.input_queue.put(data, False)
            self.loggerObj.debug('Package put in input queue')
        except queue.Full:
            self.loggerObj.warning('Input queue full')


# Process packages
def process_input_queue(self):
    while self.running:
        # Get package, if there are any in the input queue
        package = self.input_queue.get()
        self.loggerObj.debug('Package taken from input queue')
        # Optionally write the raw data
        if self.writeo:
            self.writeData.write_raw_data(self, package)
        # Mode is set to JSON or package was determined to be JSON
        if (self.mode == 0 or self.mode == 1) and self.utils.check_json(package):
            # Package is valid JSON
            valid = True
            self.loggerObj.debug('Package is JSON')
            # Parse the JSON package
            json_telemetry = json.loads(package.decode())
            self.loggerObj.debug('JSON package parsed (Serial: %s)', json_telemetry['id'] if 'id' in json_telemetry else 'N/A')
            # Unify the JSON package
            unified_telemetry = self.handleData.unify_json(self, json_telemetry)
            self.loggerObj.debug('JSON package unified (Serial: %s)', unified_telemetry['serial'] if 'serial' in unified_telemetry else 'N/A')
        # Mode is set to APRS or package was determined to be APRS
        elif (self.mode == 0 or self.mode == 2) and self.crc_calculator.verify(package[:-2], package[-1] << 8 | package[-2]):
            # Package is valid APRS
            valid = True
            self.loggerObj.debug('Package is APRS')
            # Parse the APRS package
            aprs_telemetry = self.handleData.parse_aprs(self, package[:-2])
            self.loggerObj.debug('APRS package parsed (Serial: %s)', aprs_telemetry['serial'] if 'serial' in aprs_telemetry else 'N/A')
            # Unify the APRS package
            unified_telemetry = self.handleData.unify_aprs(self, aprs_telemetry)
            self.loggerObj.debug('APRS package unified (Serial: %s)', unified_telemetry['serial'] if 'serial' in unified_telemetry else 'N/A')
        # Mode is incorrectly selected or data is invalid
        else:
            valid = False
            if self.mode == 0:
                self.loggerObj.error('Package is neither valid JSON nor valid APRS')
            elif self.mode == 1:
                self.loggerObj.error('Package is not valid JSON')
            elif self.mode == 2:
                self.loggerObj.error('Package is not valid APRS')
        if valid:
            self.loggerObj.info('Telemetry received (Serial: %s)', unified_telemetry['serial'] if 'serial' in unified_telemetry else 'N/A')
            # Check whether the telemetry is plausible
            unified_telemetry = self.telemetryChecks.check_plausibility(self, unified_telemetry)
            self.loggerObj.debug('Plausibility checks performed (Serial: %s)', unified_telemetry['serial'] if 'serial' in unified_telemetry else 'N/A')
            # Optionally write the telemetry
            if self.writet:
                if 'serial' in unified_telemetry:
                    self.writeData.write_unified_telemetry(self, unified_telemetry)
                else:
                    self.loggerObj.error('Could not write telemetry (serial missing)')
            # Check whether the mandatory telemetry for SondeHub is included
            if self.telemetryChecks.check_mandatory(self, unified_telemetry):
                self.loggerObj.debug('Mandatory data check successful (Serial: %s)', unified_telemetry['serial'])
                # Reformat the telemetry to the SondeHub telemetry format
                reformatted_telemetry = self.handleData.reformat_telemetry(self, unified_telemetry)
                self.loggerObj.debug('Telemetry reformatted (Serial: %s)', reformatted_telemetry['serial'])
                # Optionally write the reformatted telemetry
                if self.writer:
                    self.writeData.write_reformatted_telemetry(self, reformatted_telemetry)
                # Go through all possible radiosonde types
                for name in self.shuConfig.radiosonde:
                    # The radiosonde type/subtype is compared in order to find a match
                    if unified_telemetry['type'] == name or\
                            (self.shuConfig.radiosonde[name]['subtype'] is not None and unified_telemetry['type'] in self.shuConfig.radiosonde[name]['subtype']):
                        # Check whether uploading for this radiosonde is enabled
                        if self.shuConfig.radiosonde[name]['enabled']:
                            self.loggerObj.debug('Uploading for radiosonde type %s is enabled', name)
                            # Store the reformatted telemetry to the upload queue
                            try:
                                self.upload_queue.put(reformatted_telemetry, False)
                                self.loggerObj.debug('Reformatted telemetry put in queue (Serial: %s)', reformatted_telemetry['serial'])
                            except queue.Full:
                                self.loggerObj.warning('Upload queue full')
                        else:
                            self.loggerObj.warning('Uploading for radiosonde type %s is disabled', name)
                        # Break out of for-loop after the first match because only a single match is expected
                        break
            else:
                self.loggerObj.error('Mandatory data check failed (Serial: %s)', unified_telemetry['serial'] if 'serial' in unified_telemetry else 'N/A')


# Upload the reformatted telemetry packages
def process_upload_queue(self):
    while self.running:
        # Check whether it is time for uploading, based on the configured update rate and the last upload time
        if (time.time() - self.last_telemetry_upload) > self.telemu:
            self.loggerObj.debug('Telemetry upload')
            # Create an empty list that will hold the reformatted telemetry packages
            to_upload = []
            # Get all packages that are currently stored in the upload queue and append them to the previously created list
            while not self.upload_queue.empty():
                to_upload.append(self.upload_queue.get(False))
            # Upload the packages (if there are any)
            if len(to_upload) > 0:
                self.uploader.upload_telemetry(self, to_upload)
            else:
                self.loggerObj.debug('No telemetry for uploading')
            # Save the upload time in order to determine when it is time for the next upload
            self.last_telemetry_upload = time.time()
        # This task is performed every second
        time.sleep(self.shuConfig.thread_sleep)


# Upload the station
def upload_station(self):
    while self.running:
        # Check whether it is time for uploading, based on the configured update rate and the last upload time
        if (time.time() - self.last_station_upload) > (self.posu * 3600):
            self.loggerObj.debug('Station upload')
            self.uploader.upload_station(self)
            # Save the upload time in order to determine when it is time for the next upload
            self.last_station_upload = time.time()
        # This task is performed every second   
        time.sleep(self.shuConfig.thread_sleep)
