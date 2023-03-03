# SondeHubUploader.py - SondeHubUploader class with init and close functions
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Modules
import logging
import threading
import queue


class SondeHubUploader:

    import SondeHubUploader.shuConfig as shuConfig
    import SondeHubUploader.logger as logger
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
        
        # Define a logger object
        self.loggerObj = logging.getLogger('logger')
        # Configure the logger
        self.logger.configure_logger(self, self.loggerObj, self.loglevelp, self.loglevelw, self.writel)
        
        # Used to break out of while-loops when the SondeHubUploader is terminated
        self.running = True
        
        # Queue for storing the received APRS packages after receiving and before parsing
        self.aprs_queue = queue.Queue(self.qaprs)
        # Queue for storing the telemetry packages after parsing and before uploading
        self.upload_queue = queue.Queue(self.qupl)
        
        # Stores the last time the station was uploaded
        self.last_station_upload = 0
        # Stores the last time the telemetry was uploaded
        self.last_telemetry_upload = 0
        
        # Create a thread for receiving the APRS packages
        self.udp_receive_thread = threading.Thread(target=self.threads.udp_receive, args=(self,))
        self.udp_receive_thread.start()
        self.loggerObj.debug('udp_receive thread started')
        
        # Create a thread for processing the received APRS packages
        self.process_aprs_queue_thread = threading.Thread(target=self.threads.process_aprs_queue, args=(self,))
        self.process_aprs_queue_thread.start()
        self.loggerObj.debug('process_aprs_queue thread started')

        # Create a thread for uploading the station
        self.upload_station_thread = threading.Thread(target=self.threads.upload_station, args=(self,))
        self.upload_station_thread.start()
        self.loggerObj.debug('upload_station thread started')
        
        # Create a thread for uploading the telemetry
        self.process_upload_queue_thread = threading.Thread(target=self.threads.process_upload_queue, args=(self,))
        self.process_upload_queue_thread.start()
        self.loggerObj.debug('process_upload_queue thread started')

    # Close function
    def close(self):
        # Setting running to 'False' will cause breaking out of the while-loops in the threads
        self.running = False
        # Join the threads
        self.udp_receive_thread.join()
        self.process_aprs_queue_thread.join()
        self.upload_station_thread.join()
        self.process_upload_queue_thread.join()
