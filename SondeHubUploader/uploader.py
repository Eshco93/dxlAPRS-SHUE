# uploader.py - Functions for uploading to SondeHub
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


import time
import requests
import json
import gzip
import email.utils


# Upload station to SondeHub
def upload_station(self):
    # Create a dictionary that holds all the station data
    position = {
        'software_name': self.shuConfig.software_name,
        'software_version': self.shuConfig.software_version,
        'uploader_callsign': self.call,
        'uploader_position': tuple(self.pos),
        'uploader_antenna': self.ant,
        'uploader_contact_email': self.mail,
        # This is only for stationary receivers, therefore mobile is hardcoded to 'False'
        'mobile': False
    }

    retries = 0
    upload_success = False
    start_time = time.time()
    # Retry a few times if the upload failed
    while retries < self.retry:
        # Try uploading
        try:
            headers = {
                'User-Agent': self.shuConfig.software_name + '-' + self.shuConfig.software_version,
                'Content-Type': 'application/json',
                'Date': email.utils.formatdate(timeval=None, localtime=False, usegmt=True)
            }
            req = requests.put(
                self.shuConfig.sondehub_station_url,
                json=position,
                timeout=self.timeout,
                headers=headers
            )
        except Exception:
            self.loggerObj.error('Station upload failed')
            return

        # Status code 200 means that everything was ok
        if req.status_code == self.shuConfig.status_code_ok:
            upload_time = time.time() - start_time
            upload_success = True
            self.loggerObj.info('Station upload successful (Duration: %.2f ms)', upload_time * 1000)
            break
        # All other status codes indicate some kind of error
        elif req.status_code == self.shuConfig.status_code_server_error:
            retries += 1
            self.loggerObj.error('Station upload server error, possbily retry')
            continue
        else:
            self.loggerObj.error('Station upload error')
            break

    if not upload_success:
        self.loggerObj.error('Station upload failed after %d retries', retries)


# Upload telemetry to SondeHub
def upload_telemetry(self, reformatted_telemetry):
    # Compress the telemetry
    try:
        start_time = time.time()
        json_telemetry = json.dumps(reformatted_telemetry).encode('utf-8')
        compressed_payload = gzip.compress(json_telemetry)
    except Exception:
        self.loggerObj.error('Error serialising and compressing telemetry list')
        return
    compression_time = time.time() - start_time
    self.loggerObj.debug('Compressed %d bytes to %d bytes, ratio %.2f %% (Duration: %.2f ms)', len(json_telemetry), len(compressed_payload), (len(compressed_payload) / len(json_telemetry)) * 100, compression_time * 1000)
    
    retries = 0
    upload_success = False
    start_time = time.time()
    # Retry a few times if the upload failed
    while retries < self.retry:
        # Try uploading
        try:
            headers = {
                'User-Agent': self.shuConfig.software_name + '-' + self.shuConfig.software_version,
                'Content-Encoding': 'gzip',
                'Content-Type': 'application/json',
                'Date': email.utils.formatdate(timeval=None, localtime=False, usegmt=True)
            }
            req = requests.put(
                self.shuConfig.sondehub_telemetry_url,
                compressed_payload,
                timeout=self.timeout,
                headers=headers
            )
        except Exception:
            self.loggerObj.error('Telemetry upload failed')
            return
        
        # Status code 200 means that everything was ok
        if req.status_code == self.shuConfig.status_code_ok:
            upload_time = time.time() - start_time
            upload_success = True
            self.loggerObj.info('{:d} telemetry packages successfully uploaded (Duration: {:.2f} ms)'.format(len(reformatted_telemetry), upload_time * 1000))
            break
        # All other status codes indicate some kind of error
        elif req.status_code == self.shuConfig.status_code_server_error:
            retries += 1
            self.loggerObj.error('Telemetry upload server error, possibly retry')
            continue
        elif req.status_code == self.shuConfig.status_code_sondehub_error_1 or req.status_code == self.shuConfig.status_code_sondehub_error_2:
            upload_success = True
            self.loggerObj.error('SondeHub reported issue when adding telemetry to DB')
            break
        else:
            self.loggerObj.error('Telemetry upload error')
            break
        
    if not upload_success:
        self.loggerObj.error('Telemetry upload failed after %d retries', retries)
