# SondeHubUploader.py - SondeHubUploader class with init and close functions
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Modules
import threading
import queue


class SondeHubUploader:

    import SondeHubUploader.shuConfig as shuConfig
    import SondeHubUploader.logger as logger
    import SondeHubUploader.crc as crc
    import SondeHubUploader.threads as threads
    import SondeHubUploader.handleData as handleData
    import SondeHubUploader.conversions as conversions
    import SondeHubUploader.printData as printData
    import SondeHubUploader.writeData as writeData
    import SondeHubUploader.telemetryChecks as telemetryChecks
    import SondeHubUploader.uploader as uploader
    import SondeHubUploader.utils as utils

    # Init function
    def __init__(self, args):
        # Save the provided configuration parameters
        self.__dict__.update(args)

        # Create a logger
        self.logger.create_logger(self, self.loglevelp, self.loglevelw, self.writel)

        # Create a crc calculator
        self.crc.crc_create_calculator(self, 16, 0x1021, 0xFFFF, 0xFFFF, True, True)
        
        # Used to break out of while-loops when the SondeHubUploader is terminated
        self.running = True
        
        # Queue for storing the incoming packages before processing
        self.input_queue = queue.Queue(self.qin)
        # Queue for storing telemetry packages before uploading
        self.upload_queue = queue.Queue(self.qupl)

        # Set the source address to not mandatory if a user callsign was provided
        self.shuConfig.telemetry['source_address']['mandatory'] = False
        
        # Stores the last time the station was uploaded
        self.last_station_upload = 0
        # Stores the last time telemetry was uploaded
        self.last_telemetry_upload = 0

        # Disable upload for all radiosondes that were not enabled
        self.utils.disable_radiosondes(self, self.sonde)
        
        # Create a thread for receiving packages
        self.receive_thread = threading.Thread(target=self.threads.receive, args=(self,))
        self.receive_thread.start()
        self.loggerObj.debug('udp_receive thread started')
        
        # Create a thread for processing packages
        self.process_input_queue_thread = threading.Thread(target=self.threads.process_input_queue, args=(self,))
        self.process_input_queue_thread.start()
        self.loggerObj.debug('process_input_queue thread started')

        # Create a thread for uploading the station
        self.upload_station_thread = threading.Thread(target=self.threads.upload_station, args=(self,))
        self.upload_station_thread.start()
        self.loggerObj.debug('upload_station thread started')
        
        # Create a thread for uploading telemetry
        self.process_upload_queue_thread = threading.Thread(target=self.threads.process_upload_queue, args=(self,))
        self.process_upload_queue_thread.start()
        self.loggerObj.debug('process_upload_queue thread started')

    # Close function
    def close(self):
        # Setting running to 'False' will cause breaking out of the while-loops in the threads
        self.running = False
        # Join the threads
        self.receive_thread.join()
        self.process_input_queue_thread.join()
        self.upload_station_thread.join()
        self.process_upload_queue_thread.join()
