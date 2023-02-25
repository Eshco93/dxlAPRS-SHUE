# threads.py - Threads of the SondeHubUploader
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Modules
import socket
import queue
import time


# Receive APRS packages
def udp_receive(self):
    # Create a socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    sock.bind((self.addr, self.port))
    
    while self.running:
        # Try to receive an APRS package
        try:
            data, addr = sock.recvfrom(self.shuConfig.udp_buffersize)
            self.loggerObj.debug('APRS package received')
            # Store the APRS package to the aprs queue
            try:
                self.aprs_queue.put(data, False)
                self.loggerObj.debug('APRS package put in queue')
            except queue.Full:
                self.loggerObj.warning('APRS package queue full')
        # Nothing received
        except socket.error:
            pass


# Process the received APRS packages
def process_aprs_queue(self):
    while self.running:
        # Get packages, if there are any in the aprs queue
        if not self.aprs_queue.empty():
            aprs_package = self.aprs_queue.get(False)
            self.loggerObj.debug('APRS package taken from queue')
            # Optionally write the raw data
            if self.writeo:
                self.writeData.write_raw_data(self, aprs_package)
            # Perform CRC
            if self.crc_calculator.verify(aprs_package[:-2], aprs_package[-1] << 8 | aprs_package[-2]):
                # Parse the APRS package
                telemetry = self.handleData.parse_aprs_package(self, aprs_package[:-2])
                self.loggerObj.debug('APRS package parsed (Serial: %s)', telemetry['serial'] if 'serial' in telemetry else 'N/A')
                self.loggerObj.info('Telemetry received (Serial: %s)', telemetry['serial'] if 'serial' in telemetry else 'N/A')
                # Check whether the telemetry is plausible
                telemetry = self.telemetryChecks.check_plausibility(self, telemetry)
                self.loggerObj.debug('Plausibility checks performed (Serial: %s)', telemetry['serial'] if 'serial' in telemetry else 'N/A')
                # Optionally write the telemetry
                if self.writet:
                    if 'serial' in telemetry:
                        self.writeData.write_telemetry(self, telemetry)
                    else:
                        self.loggerObj.error('Could not write telemetry (serial missing)')
                # Check whether the mandatory telemetry for SondeHub is included
                if self.telemetryChecks.check_mandatory(self, telemetry):
                    self.loggerObj.debug('Mandatory data check successful (Serial: %s)', telemetry['serial'])
                    # Reformat the telemetry to the SondeHub telemetry format
                    reformatted_telemetry = self.handleData.reformat_telemetry(self, telemetry)
                    self.loggerObj.debug('Telemetry reformatted (Serial: %s)', reformatted_telemetry['serial'])
                    # Optionally write the reformatted telemetry
                    if self.writer:
                        self.writeData.write_reformatted_telemetry(self, reformatted_telemetry)
                    # Store the reformatted telemetry to the upload queue
                    try:
                        self.upload_queue.put(reformatted_telemetry, False)
                        self.loggerObj.debug('Reformatted telemetry put in queue (Serial: %s)', reformatted_telemetry['serial'])
                    except queue.Full:
                        self.loggerObj.warning('Upload queue full')
                else:
                    self.loggerObj.error('Mandatory data check failed (Serial: %s)', telemetry['serial'] if 'serial' in telemetry else 'N/A')
            else:
                self.loggerObj.error('APRS package CRC failed')


# Upload the telemetry packages
def process_upload_queue(self):
    while self.running:
        # Check whether it is time for uploading, based on the configured update rate and the last upload time
        if (time.time() - self.last_telemetry_upload) > self.telemu:
            self.loggerObj.debug('Telemetry upload')
            # Create an empty list that will hold the telemetry packages
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
