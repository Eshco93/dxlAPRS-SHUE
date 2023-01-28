# dxlAPRS-SHUE - dxlAPRS extension for uploading radiosonde telemetry to the SondeHub Tracker
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


import argparse
import copy
import ipaddress
import re
import time
import datetime
import socket
import threading
import queue
import csv
import os.path
import requests
import hashlib
import json
import gzip
from email.utils import formatdate
from dateutil.parser import parse


default_addr = '127.0.0.1'
default_port = 18001
default_qaprs = 20
default_runtime = 0
default_saver = 1
default_savep = 1
default_filepath = os.getcwd() + '\sondedata'
default_user_callsign = 'N0CALL'
default_user_position = [0.0, 0.0, 0.0]
default_user_antenna = '1/4 wave monopole'
default_contact_email = 'none@none.com'
default_qupl = 20
default_upload_rate = 30
default_upload_timeout = 20
default_upload_retries = 5
default_user_position_update_rate = 6

 
class SondeHubUploader:
    software_name = 'dxlAPRS-SHUE'
    software_version = '1.0.0'

    sondehub_url = 'https://api.v2.sondehub.org/sondes/telemetry'
    sondehub_station_position_url = 'https://api.v2.sondehub.org/listeners'
    
    def __init__(self, args):
        # Save the provided configuration parameters for the SondeHubUploader 
        self.addr = args['addr']
        self.port = args['port']
        self.qaprs = args['qaprs']
        self.saver = args['saver']
        self.savep = args['savep']
        self.filepath = args['filepath']
        self.call = args['call']
        self.pos = args['pos']
        self.ant = args['ant']
        self.mail = args['mail']
        self.qupl = args['qupl']
        self.posu = args['posu']
        self.rate = args['rate']
        self.timeout = args['timeout']
        self.retry = args['retry']
        
        # Used to break out of while-loops when the SondeHubUploader is terminated
        self.running = True
        
        # Queue for storeing the received AXUDP packages before processing them
        self.aprs_queue = queue.Queue(self.qaprs)
        # Queue for storeing the SondeHub telemetry packages before uploading them
        self.upload_queue = queue.Queue(self.qupl)
        
        # Stores the last time the station position was uploaded to SondeHub (seconds since epoch)
        self.last_station_upload = 0
        # Stores the last time the telemetry was uploaded to SondeHub (seconds since epoch)
        self.last_sonde_upload = 0
        
        # Create a thread for receiving the AXUDP packages from dxlAPRS
        self.thread_udp_receive = threading.Thread(target=self.udp_receive)
        self.thread_udp_receive.start()
        
        # Create a thread for processing the received AXUDP packages
        self.thread_process_aprs_queue = threading.Thread(target=self.process_aprs_queue)
        self.thread_process_aprs_queue.start()
        
        # Create a thread for uploading the SondeHub telemetry packages to SondeHub
        self.thread_process_upload_queue = threading.Thread(target=self.process_upload_queue)
        self.thread_process_upload_queue.start()
        
        # Create a thread for uploading the station position to SondeHub
        self.thread_upload_station = threading.Thread(target=self.upload_station)
        self.thread_upload_station.start()

    # Receives the AXUDP packages from dxlAPRS
    def udp_receive(self):
        # Create a socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setblocking(0)
        s.bind((self.addr, self.port))
        
        while(self.running):
            # Receive package
            try:
                data, addr = s.recvfrom(1024)
                # Store package to a queue
                try:
                    self.aprs_queue.put(data, False)
                except queue.Full:
                    pass
            except socket.error:
                pass

    # Process the received AXUDP packages
    def process_aprs_queue(self):
        while(self.running):
            # Get packages, if there are any in the queue
            if(not self.aprs_queue.empty()):
                aprs_packet = self.aprs_queue.get(False)
                # Write the raw AXUDP packet data to a file (if configured)
                if(self.saver):
                    self.write_raw_data_to_file(aprs_packet)
                # Parse the data
                parsed_aprs_packet = self.parse_aprs_packet(aprs_packet)
                print()
                # Print the parsed data
                self.print_parsed_data(parsed_aprs_packet)
                # Write the parsed data to a file (if configured)
                if(self.savep):
                    self.write_parsed_data_to_file(parsed_aprs_packet)
                # Reformat the data to the SondeHub telemetry format and store the packages to a queue for uploading
                try:
                    self.upload_queue.put(self.reformat_data(parsed_aprs_packet), False)
                except queue.Full:
                    pass
                
    # Upload the telemetry packages to SondeHub
    def process_upload_queue(self):
        while(self.running):
            # Check whether it's time for uploading, based on the provided upload rate and the last upload time
            if((time.time() - self.last_sonde_upload) > self.rate):
                # Create an empty list that will hold the SondeHub telemetry packages
                to_upload = []
                # Get all packages that are currently stored in the queue and append them to the previously created list
                while(not self.upload_queue.empty()):
                    to_upload.append(self.upload_queue.get(False))
                # Upload the packages (if there are any)
                if(len(to_upload) > 0):
                    self.upload_sonde(to_upload)
                # Save the upload time in order to determine when it's time for the next upload
                self.last_sonde_upload = time.time()
            # This task is performed every second
            time.sleep(1)
    
    # Upload the station position to SondeHub
    def upload_station(self):
        # Create a dict that will hold all the station data
        position = {
            'software_name': self.software_name,
            'software_version': self.software_version,
            'uploader_callsign': self.call,
            'uploader_position': tuple(self.pos),
            'uploader_antenna': self.ant,
            'uploader_contact_email': self.mail,
            # This is only for stationary receivers, therefore mobile is hardcoded to false
            'mobile': False,
        }
    
        while(self.running):
            retries = 0
            upload_success = False
            
            # Check whether it's time for uploading, based on the provided update rate and the last upload time
            if((time.time() - self.last_station_upload) > (self.posu * 3600)):
                # Retry a few time if the upload failed
                while(retries < self.retry):
                    # Try uploading
                    try:
                        headers = {
                            'User-Agent': self.software_name + '-' + self.software_version,
                            'Content-Type': 'application/json',
                            'Date': formatdate(timeval=None, localtime=False, usegmt=True),
                        }
                        req = requests.put(
                            self.sondehub_station_position_url,
                            json=position,
                            timeout=(self.timeout, 6.1),
                            headers=headers,
                        )
                    except Exception as e:
                        print('Station Upload: Upload failed')
                        print()
                        return

                    # Status code 200 means that everything was ok
                    if(req.status_code == 200):
                        upload_success = True
                        print('Station Upload: Upload successfull')
                        print()
                        break
                    # All other status codes indicate some kind of error
                    elif(req.status_code == 500):
                        retries += 1
                        print('Station Upload: Server error, possibly retry')
                        print()
                        continue
                    else:
                        print('Station Upload: Uploading error, status code: ' + str(req.status_code) + ' ' + req.text)
                        print()
                        break

                if(not upload_success):
                    print('Station Upload: Upload failed after ' + retries + ' retries')
                    
                # Save the upload time in order to determine when it's time for the next upload
                self.last_station_upload = time.time()

            # This task is performed every second   
            time.sleep(1)
    
    # Write the raw data of the AXUDP packages to a file
    def write_raw_data_to_file(self, data):
        # A simple text file is used
        filename = self.filepath + '/' + 'rawdata.txt'
        try:
            f = open(filename, 'a', newline='', encoding='utf-8')
            f.write(str(data))
            # Packages are separated by a new line
            f.write('\n')
            f.close()
        except OSError:
            print('filepath invalid')
            
    # Parse the data of the AXUDP packages
    def parse_aprs_packet(self, aprs_packet):
        # Create a string copy of the AXUDP package - that's sometimes easier to work with
        aprs_packet_str = str(aprs_packet)
        
        # Save all the APRS protocol data
        dest_addr = bytes(aprs_packet[0:7])
        src_addr = bytes(aprs_packet[7:14])
        control = hex(aprs_packet[14])
        protocol_id = hex(aprs_packet[15])
        data_type = chr(aprs_packet[16])
        
        # The serial starts at index 17, but it's end can be individual
        # The serial might end with a space character, so try to search for that
        serial_end_idx = 17+aprs_packet[17:].find(int(0x20))
        # The time starts with a * character, so try to search for that
        time_pos_start = 17+aprs_packet[17:].find(int(0x2A))
        # If the first occurrence of a space character is after the start position of the time, then the serial did not end with a space character
        if(serial_end_idx > time_pos_start):
            # In that case the end position of the serial is equivalent to the start position of the time
            serial_end_idx = time_pos_start
        # Save the serial
        serial = aprs_packet[17:serial_end_idx].decode('utf-8')
        
        # The time comes right after the serial and has a fixed length
        hour = int(aprs_packet[time_pos_start+1:time_pos_start+3])
        minute = int(aprs_packet[time_pos_start+3:time_pos_start+5])
        second = int(aprs_packet[time_pos_start+5:time_pos_start+7])
        time_format = chr(aprs_packet[serial_end_idx+8])
        
        latitude_degree = int(aprs_packet[time_pos_start+8:time_pos_start+10])
        if(aprs_packet[time_pos_start+10] != 0x20):
            if(aprs_packet[time_pos_start+11] != 0x20):
                latitude_minute = float(aprs_packet[time_pos_start+10:time_pos_start+15])
            else:
                latitude_minute = int(aprs_packet[time_pos_start+10:time_pos_start+11]) * 10
        else:
            latitude_minute = 'N/A'
        latitude_ns = chr(aprs_packet[time_pos_start+15])
        
        longitude_degree = int(aprs_packet[time_pos_start+17:time_pos_start+20])
        if(aprs_packet[time_pos_start+20] != 0x20):
            if(aprs_packet[time_pos_start+21] != 0x20):
                longitude_minute = float(aprs_packet[time_pos_start+20:time_pos_start+25])
            else:
                longitude_minute = int(aprs_packet[time_pos_start+20:time_pos_start+21]) * 10
        else:
            longitude_minute = 'N/A'
        longitude_we = chr(aprs_packet[time_pos_start+25])
        
        if(aprs_packet[time_pos_start+27] != 0x20 and aprs_packet[time_pos_start+27] != 0x2E):
            course = int(aprs_packet[time_pos_start+27:time_pos_start+30])
            speed = int(aprs_packet[time_pos_start+31:time_pos_start+34])
        else:
            course = 'N/A'
            speed = 'N/A'
        
        altitude_pos_start = aprs_packet_str.find('/A=') + len('/A=')
        altitude = int(aprs_packet_str[altitude_pos_start:altitude_pos_start+6])
        
        dao_D = aprs_packet_str[altitude_pos_start+7]
        dao_A = aprs_packet_str[altitude_pos_start+8]
        dao_O = aprs_packet_str[altitude_pos_start+9]
        
        clb_pos_start = self.find_param(aprs_packet_str, 'Clb=')
        if(clb_pos_start != -1):
            clb_pos_end = aprs_packet_str[clb_pos_start:].find('m/s') + clb_pos_start
            clb = float(aprs_packet_str[clb_pos_start:clb_pos_end])
        else:
            clb = 'N/A'
        
        p_pos_start = self.find_param(aprs_packet_str, 'p=')
        if(p_pos_start != -1):
            p_pos_end = aprs_packet_str[p_pos_start:].find('hPa') + p_pos_start
            p = float(aprs_packet_str[p_pos_start:p_pos_end])
        else:
            p = 'N/A'
        
        t_pos_start = self.find_param(aprs_packet_str, 't=')
        if(t_pos_start != -1):
            t_pos_end = aprs_packet_str[t_pos_start:].find('C') + t_pos_start
            t = float(aprs_packet_str[t_pos_start:t_pos_end])
        else:
            t = 'N/A'
        
        h_pos_start = self.find_param(aprs_packet_str, 'h=')
        if(h_pos_start != -1):
            h_pos_end = aprs_packet_str[h_pos_start:].find('%') + h_pos_start
            h = float(aprs_packet_str[h_pos_start:h_pos_end])
        else:
            h = 'N/A'
        
        f_pos_end = aprs_packet_str.find('MHz')
        if(f_pos_end != -1):
            f_pos_start = aprs_packet_str[:f_pos_end].rfind(' ') + 1
            f = float(aprs_packet_str[f_pos_start:f_pos_end])
        else:
            f = 'N/A'
        
        type_pos_start = self.find_param(aprs_packet_str, 'Type=')
        if(type_pos_start != -1):
            type_pos_end = aprs_packet_str[type_pos_start:].find(' ') + type_pos_start
            _type = aprs_packet_str[type_pos_start:type_pos_end]
        else:
            _type = 'N/A'

        tx_past_burst_pos_start = self.find_param(aprs_packet_str, 'TxPastBurst=')
        if(tx_past_burst_pos_start != -1):
            tx_past_burst_pos_end = aprs_packet_str[tx_past_burst_pos_start:].find(' ') + tx_past_burst_pos_start
            tx_past_burst_hour_pos_end = aprs_packet_str[tx_past_burst_pos_start:tx_past_burst_pos_end].find('h') + tx_past_burst_pos_start
            tx_past_burst_minute_pos_end = aprs_packet_str[tx_past_burst_pos_start:tx_past_burst_pos_end].find('m') + tx_past_burst_pos_start
            tx_past_burst_second_pos_end = aprs_packet_str[tx_past_burst_pos_start:tx_past_burst_pos_end].find('s') + tx_past_burst_pos_start
            if(tx_past_burst_pos_start < tx_past_burst_hour_pos_end):
                tx_past_burst_hour = int(aprs_packet_str[tx_past_burst_pos_start:tx_past_burst_hour_pos_end])
            else:
                tx_past_burst_hour = 'N/A'
            if(tx_past_burst_hour_pos_end < tx_past_burst_minute_pos_end):
                tx_past_burst_minute = int(aprs_packet_str[tx_past_burst_hour_pos_end+1:tx_past_burst_minute_pos_end])
            else:
                tx_past_burst_minute = 'N/A'
            if(tx_past_burst_minute_pos_end < tx_past_burst_second_pos_end):
                tx_past_burst_second = int(aprs_packet_str[tx_past_burst_minute_pos_end+1:tx_past_burst_second_pos_end])
            else:
                tx_past_burst_second = 'N/A'
        else:
            tx_past_burst_hour = 'N/A'
            tx_past_burst_minute = 'N/A'
            tx_past_burst_second = 'N/A'
        
        batt_pos_start = self.find_param(aprs_packet_str, 'batt=')
        if(batt_pos_start != -1):
            batt_pos_end = aprs_packet_str[batt_pos_start:].find('V') + batt_pos_start
            batt = float(aprs_packet_str[batt_pos_start:batt_pos_end])
        else:
            batt = 'N/A'

        powerup_pos_start = self.find_param(aprs_packet_str, 'powerup=')
        if(powerup_pos_start != -1):
            powerup_pos_end = aprs_packet_str[powerup_pos_start:].find(' ') + powerup_pos_start
            powerup_hour_pos_end = aprs_packet_str[powerup_pos_start:powerup_pos_end].find('h') + powerup_pos_start
            powerup_minute_pos_end = aprs_packet_str[powerup_pos_start:powerup_pos_end].find('m') + powerup_pos_start
            powerup_second_pos_end = aprs_packet_str[powerup_pos_start:powerup_pos_end].find('s') + powerup_pos_start
            if(powerup_pos_start < powerup_hour_pos_end):
                powerup_hour = int(aprs_packet_str[powerup_pos_start:powerup_hour_pos_end])
            else:
                powerup_hour = 'N/A'
            if(powerup_hour_pos_end < powerup_minute_pos_end):
                powerup_minute = int(aprs_packet_str[powerup_hour_pos_end+1:powerup_minute_pos_end])
            else:
                powerup_minute = 'N/A'
            if(powerup_minute_pos_end < powerup_second_pos_end):
                powerup_second = int(aprs_packet_str[powerup_minute_pos_end+1:powerup_second_pos_end])
            else:
                powerup_second = 'N/A'
        else:
            powerup_hour = 'N/A'
            powerup_minute = 'N/A'
            powerup_second = 'N/A'

        calibration_pos_start = self.find_param(aprs_packet_str, 'calibration')
        if(calibration_pos_start != -1):
            calibration_pos_end = aprs_packet_str[calibration_pos_start:].find('%') + calibration_pos_start
            calibration = int(aprs_packet_str[calibration_pos_start:calibration_pos_end])
        else:
            calibration = 'N/A'

        sats_pos_start = self.find_param(aprs_packet_str, 'Sats=')
        if(sats_pos_start != -1):
            sats_pos_end = aprs_packet_str[sats_pos_start:].find(' ') + sats_pos_start
            try:
                sats = int(aprs_packet_str[sats_pos_start:sats_pos_end])
            except ValueError:
                sats = 'N/A'
        else:
            sats = 'N/A'
            
        fp_pos_start = self.find_param(aprs_packet_str, 'fp=')
        if(fp_pos_start != -1):
            fp_pos_end = aprs_packet_str[fp_pos_start:].find('hPa') + fp_pos_start
            fp = float(aprs_packet_str[fp_pos_start:fp_pos_end])
        else:
            fp = 'N/A'
            
        fn_pos_start = self.find_param(aprs_packet_str, 'FN=')
        if(fn_pos_start != -1):
            fn_pos_end = aprs_packet_str[fn_pos_start:].find(' ') + fn_pos_start
            fn = int(aprs_packet_str[fn_pos_start:fn_pos_end])
        else:
            fn = 'N/A'

        og_pos_start = self.find_param(aprs_packet_str, 'OG=')
        if(og_pos_start != -1):
            og_pos_end = aprs_packet_str[og_pos_start:].find('m') + og_pos_start
            og = int(aprs_packet_str[og_pos_start:og_pos_end])
        else:
            og = 'N/A'

        rssi_pos_start = self.find_param(aprs_packet_str, 'rssi=')
        if(rssi_pos_start != -1):
            rssi_pos_end = aprs_packet_str[rssi_pos_start:].find('dB') + rssi_pos_start
            rssi = float(aprs_packet_str[rssi_pos_start:rssi_pos_end])
        else:
            rssi = 'N/A'

        tx_pos_start = self.find_param(aprs_packet_str, 'tx=')
        if(tx_pos_start != -1):
            tx_pos_end = aprs_packet_str[tx_pos_start:].find('dBm') + tx_pos_start
            tx = int(aprs_packet_str[tx_pos_start:tx_pos_end])
        else:
            tx = 'N/A'

        hdil_pos_start = self.find_param(aprs_packet_str, 'hdil=')
        if(hdil_pos_start != -1):
            hdil_pos_end = aprs_packet_str[hdil_pos_start:].find('m') + hdil_pos_start
            hdil = float(aprs_packet_str[hdil_pos_start:hdil_pos_end])
        else:
            hdil = 'N/A'

        azimuth_pos_start = self.find_param(aprs_packet_str, 'azimuth=')
        if(azimuth_pos_start != -1):
            azimuth_pos_end = aprs_packet_str[azimuth_pos_start:].find(' ') + azimuth_pos_start
            azimuth = int(aprs_packet_str[azimuth_pos_start:azimuth_pos_end])
        else:
            azimuth = 'N/A'

        elevation_pos_start = self.find_param(aprs_packet_str, 'elevation=')
        if(elevation_pos_start != -1):
            elevation_pos_end = aprs_packet_str[elevation_pos_start:].find(' ') + elevation_pos_start
            elevation = float(aprs_packet_str[elevation_pos_start:elevation_pos_end])
        else:
            elevation = 'N/A'

        dist_pos_start = self.find_param(aprs_packet_str, 'dist=')
        if(dist_pos_start != -1):
            dist_pos_end = aprs_packet_str[dist_pos_start:].find(' ') + dist_pos_start
            dist = float(aprs_packet_str[dist_pos_start:dist_pos_end])
        else:
            dist = 'N/A'

        dev_pos_start = self.find_param(aprs_packet_str, 'dev=')
        if(dev_pos_start != -1):
            dev_pos_end = aprs_packet_str[dev_pos_start:].find(' ') + dev_pos_start
            dev = aprs_packet_str[dev_pos_start:dev_pos_end]
        else:
            dev = 'N/A'
            
        ser_pos_start = self.find_param(aprs_packet_str, 'ser=')
        if(ser_pos_start != -1):
            ser_pos_end = aprs_packet_str[ser_pos_start:].find(' ') + ser_pos_start
            ser = aprs_packet_str[ser_pos_start:ser_pos_end]
        else:
            ser = 'N/A'
            
        rx_pos_start = self.find_param(aprs_packet_str, 'rx=')
        if(rx_pos_start != -1):
            rx_f_pos_end = aprs_packet_str[rx_pos_start:].find('(') + rx_pos_start
            rx_f = int(aprs_packet_str[rx_pos_start:rx_f_pos_end])
            rx_afc_pos_end = aprs_packet_str[rx_pos_start:].find('/') + rx_pos_start
            rx_afc = int(aprs_packet_str[rx_f_pos_end+1:rx_afc_pos_end])
            rx_afc_max_pos_end = aprs_packet_str[rx_pos_start:].find(')') + rx_pos_start
            rx_afc_max = int(aprs_packet_str[rx_afc_pos_end+1:rx_afc_max_pos_end])
        else:
            rx_f = 'N/A'
            rx_afc = 'N/A'
            rx_afc_max = 'N/A'
            
        o3_pos_start = self.find_param(aprs_packet_str, 'o3=')
        if(o3_pos_start != -1):
            o3_pos_end = aprs_packet_str[o3_pos_start:].find('mPa') + o3_pos_start
            o3 = float(aprs_packet_str[o3_pos_start:o3_pos_end])
        else:
            o3 = 'N/A'
            
        pump_pos_start = self.find_param(aprs_packet_str, 'Pump=')
        if(pump_pos_start != -1):
            pump_ma_pos_end = aprs_packet_str[pump_pos_start:].find('mA') + pump_pos_start
            pump_ma = int(aprs_packet_str[pump_pos_start:pump_ma_pos_end])
            pump_v_pos_end = aprs_packet_str[pump_pos_start:].find('V') + pump_pos_start
            pump_v = float(aprs_packet_str[pump_ma_pos_end+3:pump_v_pos_end])
        else:
            pump_ma = 'N/A'
            pump_v = 'N/A'
            
        parsed_aprs_packet = {
            'dest_addr': dest_addr,
            'src_addr': src_addr,
            'control': control,
            'protocol_id': protocol_id,
            'data_type': data_type,
            'serial': serial,
            'hour': hour,
            'minute': minute,
            'second': second,
            'time_format': time_format,
            'latitude_degree': latitude_degree,
            'latitude_minute': latitude_minute,
            'latitude_ns': latitude_ns,
            'longitude_degree': longitude_degree,
            'longitude_minute': longitude_minute,
            'longitude_we': longitude_we,
            'course': course,
            'speed': speed,
            'altitude': altitude,
            'dao_D': dao_D,
            'dao_A': dao_A,
            'dao_O': dao_O,
            'clb': clb,
            'p': p,
            't': t,
            'h': h,
            'f': f,
            'type': _type,
            'tx_past_burst_hour': tx_past_burst_hour,
            'tx_past_burst_minute': tx_past_burst_minute,
            'tx_past_burst_second': tx_past_burst_second,
            'batt': batt,
            'powerup_hour': powerup_hour,
            'powerup_minute': powerup_minute,
            'powerup_second': powerup_second,
            'calibration': calibration,
            'sats': sats,
            'fp': fp,
            'fn': fn,
            'og': og,
            'rssi': rssi,
            'tx': tx,
            'hdil': hdil,
            'azimuth': azimuth,
            'elevation': elevation,
            'dist': dist,
            'dev': dev,
            'ser': ser,
            'rx_f': rx_f,
            'rx_afc': rx_afc,
            'rx_afc_max': rx_afc_max,
            'o3': o3,
            'pump_ma': pump_ma,
            'pump_v': pump_v
        }
            
        return parsed_aprs_packet
            
    def find_param(self, aprs_packet, param):
        index = aprs_packet.find(' ' + param)
        if(index == -1):
            index = aprs_packet.find('!' + param)
        if(index != -1):
            index += len(param) + 1 
        return index
    
    def print_parsed_data(self, data):
        print('New APRS packet:')
        print('{:<12} {}'.format('Serial:', data['serial']))
        hour_str = str(data['hour'])
        if(data['minute'] < 10):
            minute_str = '0' + str(data['minute'])
        else:
            minute_str = str(data['minute'])
        if(data['second'] < 10):
            second_str = '0' + str(data['second'])
        else:
            second_str = str(data['second'])
        print('{:<12} {}'.format('Time:', hour_str + ':' + minute_str + ':' + second_str))
        dg = self.gmm_to_dg(data['latitude_degree'],
                            self.meters_add_precision(data['latitude_minute'], data['dao_D'], data['dao_A']),
                            data['latitude_ns'],
                            data['longitude_degree'],
                            self.meters_add_precision(data['longitude_minute'], data['dao_D'], data['dao_O']),
                            data['longitude_we'],
                            6)
        print('{:<12} {}'.format('Position:', 'Lat: ' + str(dg['latitude']) + ' / Lon: ' + str(dg['longitude'])))
        print('{:<12} {}'.format('Course:', str(data['course']) + '°'))
        print('{:<12} {}'.format('Speed:', str(self.knots_to_kph(data['speed'], 2)) + ' kph'))
        print('{:<12} {}'.format('Altitude:', str(self.feet_to_meters(data['altitude'], 2)) + ' m'))
        if(data['clb'] != 'N/A'):
            print('{:<12} {}'.format('Climb:', str(data['clb']) + ' m/s'))
        if(data['p'] != 'N/A'):
            print('{:<12} {}'.format('Pressure:', str(data['p']) + ' hPa'))
        if(data['t'] != 'N/A'):
            print('{:<12} {}'.format('Temperature:', str(data['t']) + ' °C'))
        if(data['h'] != 'N/A'):
            print('{:<12} {}'.format('Humidity:', str(data['h']) + ' %'))
        if(data['f'] != 'N/A'):
            print('{:<12} {}'.format('Frequency:', str(data['f']) + ' MHz'))
        if(data['type'] != 'N/A'):
            print('{:<12} {}'.format('Type:', data['type']))
        tx_past_burst_str = ''
        if(data['tx_past_burst_hour'] != 'N/A'):
            tx_past_burst_str += str(data['tx_past_burst_hour']) + 'h'
        if(data['tx_past_burst_minute'] != 'N/A'):
            tx_past_burst_str += str(data['tx_past_burst_minute']) + 'm'
        if(data['tx_past_burst_second'] != 'N/A'):
            tx_past_burst_str += str(data['tx_past_burst_second']) + 's'
        if(tx_past_burst_str != ''):
            print('{:<12} {}'.format('TxPastBurst:', tx_past_burst_str))
        if(data['batt'] != 'N/A'):
            print('{:<12} {}'.format('Battery:', str(data['batt']) + ' V'))
        powerup_str = ''
        if(data['powerup_hour'] != 'N/A'):
            powerup_str += str(data['powerup_hour']) + 'h'
        if(data['powerup_minute'] != 'N/A'):
            powerup_str += str(data['powerup_minute']) + 'm'
        if(data['powerup_second'] != 'N/A'):
            powerup_str += str(data['powerup_second']) + 's'
        if(powerup_str != ''):
            print('{:<12} {}'.format('PowerUp:', powerup_str))
        if(data['calibration'] != 'N/A'):
            print('{:<12} {}'.format('Calibration:', str(data['calibration']) + ' %'))
        if(data['sats'] != 'N/A'):
            print('{:<12} {}'.format('Satellites:', str(data['sats'])))
        if(data['fp'] != 'N/A'):
            print('{:<12} {}'.format('Fakehp:', str(data['fp']) + ' hPa'))
        if(data['fn'] != 'N/A'):
            print('{:<12} {}'.format('Framenumber:', str(data['fn'])))
        if(data['og'] != 'N/A'):
            print('{:<12} {}'.format('OverGround:', str(data['og']) + ' m'))
        if(data['rssi'] != 'N/A'):
            print('{:<12} {}'.format('RSSI:', str(data['rssi']) + ' dB'))
        if(data['tx'] != 'N/A'):
            print('{:<12} {}'.format('TxPower:', str(data['tx']) + ' dBm'))
        if(data['hdil'] != 'N/A'):
            print('{:<12} {}'.format('GPSNoise:', str(data['hdil']) + ' m'))
        if(data['azimuth'] != 'N/A'):
            print('{:<12} {}'.format('Azimuth:', str(data['azimuth'])))
        if(data['elevation'] != 'N/A'):
            print('{:<12} {}'.format('Elevation:', str(data['elevation'])))
        if(data['dist'] != 'N/A'):
            print('{:<12} {}'.format('Distance:', str(data['dist']) + ' km'))
        if(data['dev'] != 'N/A'):
            print('{:<12} {}'.format('Device:', str(data['dev'])))
        if(data['ser'] != 'N/A'):
            print('{:<12} {}'.format('Serial2:', str(data['ser'])))
        if(data['rx_f'] != 'N/A'):
            print('{:<12} {}'.format('RxSetting:', str(data['rx_f']) + ' kHz (' + str(data['rx_afc']) + '/' + str(data['rx_afc_max']) + ')'))
        if(data['o3'] != 'N/A'):
            print('{:<12} {}'.format('o3:', str(data['o3']) + ' mPa'))
        if(data['pump_ma'] != 'N/A' and data['pump_v'] != 'N/A'):
            print('{:<12} {}'.format('Pump:', str(data['pump_ma']) + ' mA / ' + str(data['pump_v']) + ' V'))
            
    def write_parsed_data_to_file(self, data):
        filename = self.filepath + '/' + data['serial'] + '.csv'
        if(os.path.isfile(filename)):
            exists = True
        else:
            exists = False
        try:
            f = open(filename, 'a', newline='', encoding='utf-8')
            writer = csv.writer(f, delimiter=';')
            if(not exists):
                writer.writerow([
                    'Serial',
                    'Time [hh:mm:ss]',
                    'Latitude [°]',
                    'Longitude [°]',
                    'Course [°]',
                    'Speed [kph]',
                    'Altitude [m]',
                    'Climb [m/s]',
                    'Pressure [hPa]',
                    'Temperature [°C]',
                    'Humidity [%]',
                    'Frequency [MHz]',
                    'Type',
                    'TxPastBurst',
                    'Battery [V]',
                    'PowerUp',
                    'Calibration [%]',
                    'Satellites',
                    'Fakehp [hPa]',
                    'Framenumber',
                    'OverGround [m]',
                    'RSSI [dB]',
                    'TxPower [dBm]',
                    'GPSNoise [m]',
                    'Azimuth',
                    'Elevation',
                    'Distance [km]',
                    'Device',
                    'Serial2',
                    'RxSetting',
                    'o3 [mPa]',
                    'Pump [mA]',
                    'Pump [V]'
                ])
            hour_str = str(data['hour'])
            if(data['minute'] < 10):
                minute_str = '0' + str(data['minute'])
            else:
                minute_str = str(data['minute'])
            if(data['second'] < 10):
                second_str = '0' + str(data['second'])
            else:
                second_str = str(data['second'])
            dg = self.gmm_to_dg(data['latitude_degree'],
                                self.meters_add_precision(data['latitude_minute'], data['dao_D'], data['dao_A']),
                                data['latitude_ns'],
                                data['longitude_degree'],
                                self.meters_add_precision(data['longitude_minute'], data['dao_D'], data['dao_O']),
                                data['longitude_we'],
                                6)
            tx_past_burst_str = ''
            if(data['tx_past_burst_hour'] != 'N/A'):
                tx_past_burst_str += str(data['tx_past_burst_hour']) + 'h'
            if(data['tx_past_burst_minute'] != 'N/A'):
                tx_past_burst_str += str(data['tx_past_burst_minute']) + 'm'
            if(data['tx_past_burst_second'] != 'N/A'):
                tx_past_burst_str += str(data['tx_past_burst_second']) + 's'
            if(tx_past_burst_str == ''):
                tx_past_burst_str = 'N/A'
            powerup_str = ''
            if(data['powerup_hour'] != 'N/A'):
                powerup_str += str(data['powerup_hour']) + 'h'
            if(data['powerup_minute'] != 'N/A'):
                powerup_str += str(data['powerup_minute']) + 'm'
            if(data['powerup_second'] != 'N/A'):
                powerup_str += str(data['powerup_second']) + 's'
            if(powerup_str == ''):
                powerup_str = 'N/A'
            if(data['rx_f'] != 'N/A'):
                rx = str(data['rx_f']) + ' kHz (' + str(data['rx_afc']) + '/' + str(data['rx_afc_max']) + ')'
            else:
                rx = 'N/A'
            writer.writerow([
                data['serial'],
                hour_str + ':' + minute_str + ':' + second_str,
                dg['latitude'],
                dg['longitude'],
                data['course'],
                data['speed'],
                self.feet_to_meters(data['altitude'], 2),
                data['clb'],
                data['p'],
                data['t'],
                data['h'],
                data['f'],
                data['type'],
                tx_past_burst_str,
                data['batt'],
                powerup_str,
                data['calibration'],
                data['sats'],
                data['fp'],
                data['fn'],
                data['og'],
                data['rssi'],
                data['tx'],
                data['hdil'],
                data['azimuth'],
                data['elevation'],
                data['dist'],
                data['dev'],
                data['ser'],
                rx,
                data['o3'],
                data['pump_ma'],
                data['pump_v']
            ])
            f.close()
        except OSError:
            print('filepath invalid')
    
    def knots_to_kph(self, knots, precision):
        return round(knots * 1.852, precision)
    
    def kph_to_knots(self, kph, precision):
        return round(kph * 0.539957, precision)
    
    def knots_to_ms(self, knots, precision):
        return round(knots * 0.514444, precision)

    def ms_to_knots(self, ms, precision):
        return round(ms * 1.94384, precision)
    
    def kph_to_ms(self, kph, precision):
        return round(kph * 0.277778, precision)
    
    def ms_to_kph(self, ms, precision):
        return round(ms * 3.6, precision)

    def feet_to_meters(self, feet, precision):
        return round(feet * 0.3048, precision)
        
    def meters_to_feet(self, meters, precision):
        return round(meters * 3.28084, precision)
    
    def meters_add_precision(self, meters, dao_D, precision):
        if(precision == 0x20):
            return meters
        elif(dao_D == 'w' or dao_D == 'W'):
            meters = str(meters)
            if(meters.find('.') == -1):
                meters += '.00'
            else:
                if(meters.find('.') == len(meters) - 2):
                    meters += '0'
            if(dao_D == 'w'):
                precision = round((ord(precision) - 33) * 1.1 * 10)
                meters += str(precision)
            else:
                meters += str(precision)
            return float(meters)
        else:
            return meters
    
    def gms_to_dg(self, latitude_degree, latitude_minute, latitude_second, latitude_ns, longitude_degree, longitude_minute, longitude_second, longitude_we, precision):
        latitude = round(latitude_degree + (latitude_minute * 60 + latitude_second) / 3600, precision)
        if(latitude_ns == 'S'):
            latitude *= -1
        longitude = round(longitude_degree + (longitude_minute * 60 + longitude_second) / 3600, precision)
        if(longitude_we == 'W'):
            longitude *= -1
        dg = {
            'latitude': latitude,
            'longitude': longitude
        }
        return dg
    
    def dg_to_gms(self, latitude, longitude):
        latitude_degree = int(latitude)
        latitude_minute = int((latitude - latitude_degree) * 60)
        latitude_second = round((latitude - latitude_degree) * 3600) % 60
        if(latitude > 0):
            latitude_ns = 'N'
        else:
            latitude_ns = 'S'
        longitude_degree = int(longitude)
        longitude_minute = int((longitude - longitude_degree) * 60)
        longitude_second = round((longitude - longitude_degree) * 3600) % 60
        if(longitude > 0):
            longitude_we = 'E'
        else:
            longitude_we = 'W'
        gms = {
            'latitude_degree': latitude_degree,
            'latitude_minute': latitude_minute,
            'latitude_second': latitude_second,
            'latitude_ns': latitude_ns,
            'longitude_degree': longitude_degree,
            'longitude_minute': longitude_minute,
            'longitude_second': longitude_second,
            'longitude_we': longitude_we
        }
        return gms
    
    def gmm_to_dg(self, latitude_degree, latitude_minute, latitude_ns, longitude_degree, longitude_minute, longitude_we, precision):
        latitude = round(latitude_degree + (latitude_minute * 60) / 3600, precision)
        if(latitude_ns == 'S'):
            latitude *= -1
        longitude = round(longitude_degree + (longitude_minute * 60) / 3600, precision)
        if(longitude_we == 'W'):
            longitude *= -1
        dg = {
            'latitude': latitude,
            'longitude': longitude
        }
        return dg
    
    def dg_to_gmm(self, latitude, longitude, precision):
        latitude_degree = int(latitude)
        latitude_minute = round((latitude - latitude_degree) * 60, precision)
        if(latitude > 0):
            latitude_ns = 'N'
        else:
            latitude_ns = 'S'
        longitude_degree = int(longitude)
        longitude_minute = round((longitude - longitude_degree) * 60, precision)
        if(longitude > 0):
            longitude_we = 'E'
        else:
            longitude_we = 'W'
        gmm = {
            'latitude_degree': latitude_degree,
            'latitude_minute': latitude_minute,
            'latitude_ns': latitude_ns,
            'longitude_degree': longitude_degree,
            'longitude_minute': longitude_minute,
            'longitude_we': longitude_we
        }
        return gmm
    
    def gms_to_gmm(self, latitude_degree, latitude_minute, latitude_second, latitude_ns, longitude_degree, longitude_minute, longitude_second, longitude_we, precision):
        latitude_minute += round(latitude_second / 60, precision)
        longitude_minute += round(longitude_second / 60, precision)
        gmm = {
            'latitude_degree': latitude_degree,
            'latitude_minute': latitude_minute,
            'latitude_ns': latitude_ns,
            'longitude_degree': longitude_degree,
            'longitude_minute': longitude_minute,
            'longitude_we': longitude_we
        }
        return gmm
    
    def gmm_to_gms(self, latitude_degree, latitude_minute, latitude_ns, longitude_degree, longitude_minute, longitude_we, precision):
        latitude_second = round((latitude_minute - int(latitude_minute)) * 60)
        latitude_minute = int(latitude_minute)
        longitude_second = round((longitude_minute - int(longitude_minute)) * 60)
        longitude_minute = int(longitude_minute)
        gms = {
            'latitude_degree': latitude_degree,
            'latitude_minute': latitude_minute,
            'latitude_second': latitude_second,
            'latitude_ns': latitude_ns,
            'longitude_degree': longitude_degree,
            'longitude_minute': longitude_minute,
            'longitude_second': longitude_second,
            'longitude_we': longitude_we
        }
        return gms
    
    def frame_to_hms(self, frame):
        hms = str(datetime.timedelta(seconds=frame)).split(':')
        hms = {
            'hour': hms[0],
            'minute': hms[1],
            'second': hms[2]
        }
        return hms
    
    def hms_to_frame(self, hour, minute, second):
        return hour * 3600 + minute * 60 + second
    
    def addr_to_str(self, addr):
        addr_str = '0x'
        for i in range(len(addr)):
            addr_str += hex(addr[i])[2:]
        return addr_str
    
    def reformat_data(self, parsed_aprs_packet):
        subtypes = ['RS41-SG', 'RS41-SGP', 'RS41-SGM', 'DFM06', 'DFM09', 'DFM09P', 'DFM17', 'M10', 'M20', 'MRZ-H1']
        
        telemetry = {
            'software_name': self.software_name,
            'software_version': self.software_version,
            'uploader_callsign': self.call,
            'uploader_position': list(self.pos),
            'uploader_antenna': self.ant,
            'time_received': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        }
        
        telemetry['datetime'] = self.fix_datetime(parsed_aprs_packet['hour'] , parsed_aprs_packet['minute'], parsed_aprs_packet['second']).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        if(parsed_aprs_packet['type'].startswith('RS41')):
            telemetry['manufacturer'] = 'Vaisala'
            telemetry['type'] = 'RS41'
            telemetry['serial'] = parsed_aprs_packet['serial']
            if(parsed_aprs_packet['type'] in subtypes):
                telemetry['subtype'] = parsed_aprs_packet['type']
        elif(parsed_aprs_packet['type'].startswith('RS92')):
            telemetry['manufacturer'] = 'Vaisala'
            telemetry['type'] = 'RS92'
            telemetry['serial'] = parsed_aprs_packet['serial']
            if(parsed_aprs_packet['type'] in subtypes):
                telemetry['subtype'] = parsed_aprs_packet['type']
        elif(parsed_aprs_packet['type'].startswith('DFM')):
            telemetry['manufacturer'] = 'Graw'
            telemetry['type'] = 'DFM'
            telemetry['subtype'] = parsed_aprs_packet['type'][1:]
        elif(parsed_aprs_packet['type'].startswith('M10')):
            telemetry['manufacturer'] = 'Meteomodem'
            telemetry['type'] = 'M10'
            telemetry['serial'] = parsed_aprs_packet['serial']
        elif(parsed_aprs_packet['type'].startswith('iMET')):
            telemetry['manufacturer'] = 'Intermet Systems'
            telemetry['type'] = 'iMet-4'
            telemetry['serial'] = self.imet_unique_id(parsed_aprs_packet).split('-')[1]
            
        if(parsed_aprs_packet['fn'] != 'N/A'):
            telemetry['frame'] = parsed_aprs_packet['fn']
        else:
            if(parsed_aprs_packet['powerup_hour'] == 'N/A'):
                hour = 0
            else:
                hour = parsed_aprs_packet['powerup_hour']
            if(parsed_aprs_packet['powerup_minute'] == 'N/A'):
                minute = 0
            else:
                minute = parsed_aprs_packet['powerup_minute']
            if(parsed_aprs_packet['powerup_second'] == 'N/A'):
                second = 0
            else:
                second = parsed_aprs_packet['powerup_second']
            telemetry['frame'] = self.hms_to_frame(hour, minute, second)
        
        dg = self.gmm_to_dg(parsed_aprs_packet['latitude_degree'],
                            self.meters_add_precision(parsed_aprs_packet['latitude_minute'], parsed_aprs_packet['dao_D'], parsed_aprs_packet['dao_A']),
                            parsed_aprs_packet['latitude_ns'],
                            parsed_aprs_packet['longitude_degree'],
                            self.meters_add_precision(parsed_aprs_packet['longitude_minute'], parsed_aprs_packet['dao_D'], parsed_aprs_packet['dao_O']),
                            parsed_aprs_packet['longitude_we'],
                            5)
        telemetry['lat'] = float(dg['latitude'])
        telemetry['lon'] = float(dg['longitude'])
        telemetry['alt'] = float(self.feet_to_meters(parsed_aprs_packet['altitude'], 4))
        
        if(parsed_aprs_packet['t'] != 'N/A'):
            if(parsed_aprs_packet['t'] > -273):
                telemetry['temp'] = float(parsed_aprs_packet['t'])
                
        if(parsed_aprs_packet['h'] != 'N/A'):
            if(parsed_aprs_packet['h'] >= 0):
                telemetry['humidity'] = float(parsed_aprs_packet['h'])
                
        if(parsed_aprs_packet['p'] != 'N/A'):
            if(parsed_aprs_packet['p'] >= 0):
                telemetry['pressure'] = float(parsed_aprs_packet['p'])
                
        if(parsed_aprs_packet['clb'] != 'N/A'):
            if(parsed_aprs_packet['clb'] > -9999):
                telemetry['vel_v'] = float(parsed_aprs_packet['clb'])
                
        if(parsed_aprs_packet['speed'] != 'N/A'):
            if(self.knots_to_ms(parsed_aprs_packet['speed'], 1) > -9999):
                telemetry['vel_h'] = float(self.knots_to_ms(parsed_aprs_packet['speed'], 5))
                
        if(parsed_aprs_packet['course'] != 'N/A'):
            if(parsed_aprs_packet['course'] > -9999):
                telemetry['heading'] = float(parsed_aprs_packet['course'])
                
        if(parsed_aprs_packet['sats'] != 'N/A'):
            telemetry['sats'] = parsed_aprs_packet['sats']
            
        if(parsed_aprs_packet['batt'] != 'N/A'):
            if(parsed_aprs_packet['batt'] >= 0):
                telemetry['batt'] = float(parsed_aprs_packet['batt'])
                
        if(parsed_aprs_packet['rx_f'] != 'N/A'):
            telemetry['frequency'] = float(parsed_aprs_packet['rx_f'] / 1000)
            
        if(parsed_aprs_packet['f'] != 'N/A'):
            telemetry['tx_frequency'] = float(parsed_aprs_packet['f'])
            
        #if(parsed_aprs_packet['rssi'] != 'N/A'):
            #telemetry['rssi'] = float(parsed_aprs_packet['rssi'])
                
        return telemetry
    
    def fix_datetime(self, hour, minute, second, local_datetime_str = None):
        if(hour < 10):
            hour_str = '0' + str(hour)
        else:
            hour_str = str(hour)
        if(minute < 10):
            minute_str = '0' + str(minute)
        else:
            minute_str = str(minute)
        if(second < 10):
            second_str = '0' + str(second)
        else:
            second_str = str(second)
            
        time = hour_str + ':' + minute_str + ':' + second_str
        
        if(local_datetime_str is None):
            now = datetime.datetime.utcnow()
        else:
            now = parse(local_datetime_str)
        
        if(now.hour == 23 or now.hour == 0):
            outside_window = False
        else:
            outside_window = True
            
        fixed_datetime = parse(time, default=now)
        
        fixed_datetime += datetime.timedelta(seconds=18)
        
        if(outside_window):
            return fixed_datetime
        else:
            if(fixed_datetime.hour == 23 and now.hour == 0):
                fixed_datetime = fixed_datetime - datetime.timedelta(days=1)
            elif(fixed_datetime.hour == 00 and now.hour == 23):
                fixed_datetime = fixed_datetime + datetime.timedelta(days=1)
                
            return fixed_datetime
    
    def imet_unique_id(self, parsed_aprs_packet):        
        imet_datetime = self.fix_datetime(parsed_aprs_packet['hour'] , parsed_aprs_packet['minute'], parsed_aprs_packet['second'])
        
        if(parsed_aprs_packet['fn'] != 'N/A'):
            power_on_time = imet_datetime - datetime.timedelta(seconds=parsed_aprs_packet['fn'])
        elif(parsed_aprs_packet['powerup_hour'] != 'N/A' or
             parsed_aprs_packet['powerup_minute'] != 'N/A' or
             parsed_aprs_packet['powerup_second'] != 'N/A'):
            if(parsed_aprs_packet['powerup_hour'] == 'N/A'):
                hour = 0
            if(parsed_aprs_packet['powerup_minute'] == 'N/A'):
                minute = 0
            if(parsed_aprs_packet['powerup_second'] == 'N/A'):
                second = 0
            power_on_time = imet_datetime - datetime.timedelta(hours=hour, minutes=minute, seconds=second)
        else:
            return None
        
        if(parsed_aprs_packet['f'] != 'N/A'):
            temp_str = power_on_time.strftime("%Y-%m-%dT%H:%M:%SZ") + '{0:.3f}'.format(parsed_aprs_packet['f']) + ' MHz' + ''
        else:
            return None
        
        serial = hashlib.sha256(temp_str.encode('ascii')).hexdigest().upper()
        
        return 'IMET-' + serial[-8:]
    
    def upload_sonde(self, telemetry):        
        telemetry_len = len(telemetry)
        
        try:
            start_time = time.time()
            telem_json = json.dumps(telemetry).encode('utf-8')
            compressed_payload = gzip.compress(telem_json)
        except Exception as e:
            print('Sonde Upload: Error serialising and compressing telemetry list for upload')
            return
        
        compression_time = time.time() - start_time
        
        retries = 0
        upload_success = False
        
        start_time = time.time()
        
        while(retries < self.retry):
            try:
                headers = {
                    'User-Agent': self.software_name + '-' + self.software_version,
                    'Content-Encoding': 'gzip',
                    'Content-Type': 'application/json',
                    'Date': formatdate(timeval=None, localtime=False, usegmt=True),
                }
                req = requests.put(
                    self.sondehub_url,
                    compressed_payload,
                    timeout=(self.timeout, 6.1),
                    headers=headers,
                    )
            except Exception as e:
                print('Sonde Upload: Upload failed')
                print()
                return
            
            if(req.status_code == 200):
                upload_time = time.time() - start_time
                upload_success = True
                print('Sonde Upload: Upload successfull')
                print()
                break
            elif(req.status_code == 500):
                retries += 1
                print('Sonde Upload: Server error, possibly retry')
                print()
                continue
            elif(req.status_code == 201):
                upload_success = True
                print('Sonde Upload: SondeHub reported issue when adding packets to DB, status code: ' + str(req.status_code) + ' ' + req.text)
                print()
                break
            else:
                print('Sonde Upload: Uploading error, status code: ' + str(req.status_code) + ' ' + req.text)
                print()
                break
            
        if(not upload_success):
            print('Sonde Upload: Upload failed after ' + retries + ' retries')
            
    def close(self):
        self.running = False
        self.thread_udp_receive.join()
        self.thread_process_aprs_queue.join()
        self.thread_process_upload_queue.join()
        self.thread_upload_station.join()
      

def set_proc_name(newname):
    from ctypes import cdll, byref, create_string_buffer
    libc = cdll.LoadLibrary('libc.so.6')
    buff = create_string_buffer(len(newname)+1)
    buff.value = str.encode(newname)
    libc.prctl(15, byref(buff), 0, 0, 0)

def get_proc_name():
    from ctypes import cdll, byref, create_string_buffer
    libc = cdll.LoadLibrary('libc.so.6')
    buff = create_string_buffer(128)
    libc.prctl(16, byref(buff), 0, 0, 0)
    return buff.value

def parse_arguments():
    argParser = argparse.ArgumentParser(description='description: accepts AXUDP packages from udpbox and uploads the data to SondeHub')
    
    argParser.add_argument('-a', '--addr', default=default_addr, help='ip address for receiving the AXUDP packages (default: ' + default_addr + ')')
    argParser.add_argument('-p', '--port', default=default_port, help='port for receiving the AXUDP packages (default: ' + str(default_port) + ')')
    argParser.add_argument('-q', '--qaprs', default=default_qaprs, help='size of the queue for storing the AXUDP packages after receiving and before parsing (default: ' + str(default_qaprs) + ')')
    argParser.add_argument('-t', '--runtime', default=default_runtime, help='runtime of the program in seconds (0 for infinite runtime) (default: ' + str(default_runtime) + ')')
    argParser.add_argument('-s', '--saver', default=default_saver, help='save the raw received radiosonde data to a TXT file (0 = no / 1 = yes) (default: ' + str(default_saver) + ')')
    argParser.add_argument('-w', '--savep', default=default_savep, help='save the parsed received radiosonde data to a CSV file (0 = no / 1 = yes) (default: ' + str(default_savep) + ')')
    argParser.add_argument('-d', '--filepath', default=default_filepath, help='path for the files that will store the received radiosonde data (default: ' + default_filepath + ')')
    argParser.add_argument('-f', '--qupl', default=default_qupl, help='size of the queue for storing the radiosonde data after parsing and before uploading (default: ' + str(default_qupl) + ')')
    argParser.add_argument('-c', '--call', default=default_user_callsign, help='user callsign for SondeHub (default: ' + default_user_callsign + ')')
    argParser.add_argument('-l', '--pos', default=default_user_position, help='user position for SondeHub (default: ' + str(default_user_position) + ')')
    argParser.add_argument('-i', '--ant', default=default_user_antenna, help='user antenna for SondeHub (default: ' + default_user_antenna + ')')
    argParser.add_argument('-u', '--mail', default=default_contact_email, help='contact e-mail for SondeHub (default: ' + default_contact_email + ')')
    argParser.add_argument('-g', '--posu', default=default_user_position_update_rate, help='user position update rate for SondeHub (default: ' + str(default_user_position_update_rate) + ')')
    argParser.add_argument('-r', '--rate', default=default_upload_rate, help='upload rate to SondeHub(default: ' + str(default_upload_rate) + ')')
    argParser.add_argument('-o', '--timeout', default=default_upload_timeout, help='upload timeout for SondeHub (default: ' + str(default_upload_timeout) + ')')
    argParser.add_argument('-e', '--retry', default=default_upload_retries, help='upload retries for SondeHub (default: ' + str(default_upload_retries) + ')')

    args = argParser.parse_args()
    
    args_dict = {
        'addr': args.addr,
        'port': args.port,
        'qaprs': args.qaprs,
        'runtime': args.runtime,
        'saver': args.saver,
        'savep': args.savep,
        'filepath': args.filepath,
        'qupl': args.qupl,
        'call': args.call,
        'pos': args.pos,
        'ant': args.ant,
        'mail': args.mail,
        'posu': args.posu,
        'rate': args.rate,
        'timeout': args.timeout,
        'retry': args.retry
    }
    return args_dict

def perform_checks(args):
    if(args['addr'] != default_addr):
        if(not check_addr(args['addr'])):
            args['addr'] = False
    if(args['port'] != default_port):
        if(not check_port(args['port'])):
            args['port'] = False
    if(args['qaprs'] != default_qaprs):
        if(not check_qaprs(args['qaprs'])):
            args['qaprs'] = False
    if(args['runtime'] != default_runtime):
        if(not check_runtime(args['runtime'])):
            args['runtime'] = False
    if(args['saver'] != default_saver):
        if(not check_saver(args['saver'])):
            args['saver'] = False
    if(args['savep'] != default_savep):
        if(not check_savep(args['savep'])):
            args['savep'] = False
    if(args['filepath'] != default_filepath):
        if(not check_filepath(args['filepath'])):
            args['filepath'] = False
    if(args['qupl'] != default_qupl):
        if(not check_qupl(args['qupl'])):
            args['qupl'] = False
    if(args['call'] != default_user_callsign):
        if(not check_user_callsign(args['call'])):
            args['call'] = False
    if(args['pos'] != default_user_position):
        if(not check_user_position(args['pos'])):
            args['pos'] = False
    if(args['ant'] != default_user_antenna):
        if(not check_user_antenna(args['ant'])):
            args['ant'] = False
    if(args['mail'] != default_contact_email):
        if(not check_contact_email(args['mail'])):
            args['mail'] = False
    if(args['posu'] != default_user_position_update_rate):
        if(not check_user_position_update_rate(args['posu'])):
            args['posu'] = False
    if(args['rate'] != default_upload_rate):
        if(not check_upload_rate(args['rate'])):
            args['rate'] = False
    if(args['timeout'] != default_upload_timeout):
        if(not check_upload_timeout(args['timeout'])):
            args['timeout'] = False
    if(args['retry'] != default_upload_retries):
        if(not check_upload_retries(args['retry'])):
            args['retry'] = False
    return args

def check_addr(addr):
    try:
        ipaddress.ip_address(addr)
        return True
    except ValueError:
        return False
    
def check_port(port):
    try:
        port = int(port)
        if(port in range(1024, 65354)):
            return True
        return False
    except ValueError:
        return False

def check_qaprs(qaprs):
    try:
        qaprs = int(qaprs)
        if(qaprs in range(1, 101)):
            return True
        return False
    except ValueError:
        return False

def check_runtime(runtime):
    try:
        runtime = int(runtime)
        if(runtime >= 0):
            return True
        return False
    except ValueError:
        return False
    
def check_saver(saver):
    try:
        saver = int(saver)
        if(saver in range(0, 2)):
            return True
        return False
    except ValueError:
        return False

def check_savep(savep):
    try:
        savep = int(savep)
        if(savep in range(0, 2)):
            return True
        return False
    except ValueError:
        return False
    
def check_filepath(filepath):
    return os.path.exists(filepath)

def check_qupl(qupl):
    try:
        qupl = int(qupl)
        if(qupl in range(1, 101)):
            return True
        return False
    except ValueError:
        return False

def check_user_callsign(user_callsign):
    capital_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    lowercase_letters = 'abcdefghijklmnopqrstuvwxyz'
    numbers = '0123456789'
    special_characters = '-_'
    
    if(len(user_callsign) <= 15):
        if all(c in (capital_letters + lowercase_letters + numbers + special_characters) for c in user_callsign):
            return True
    return False

def check_user_position(user_position):
    try:
        user_position = user_position.split(',')
        for i in range(len(user_position)):
            user_position[i] = float(user_position[i])
        if(len(user_position) == 3):
            if(user_position[0] >= -180 and user_position[0] <= 180):
                if(user_position[1] >= -90 and user_position[1] <= 90):
                    if(user_position[2] >= -100 and user_position[2] <= 8000):
                        return True
        return False
    except Exception:
        return False
    
def check_user_antenna(user_antenna):
    if(len(user_antenna) <= 25):
        return True
    return False

def check_contact_email(contact_email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    if(re.fullmatch(regex, contact_email)):
        return True
    return False

def check_user_position_update_rate(user_position_update_rate):
    try:
        user_position_update_rate = int(user_position_update_rate)
        if(user_position_update_rate in range(1, 25)):
            return True
        return False
    except ValueError:
        return False

def check_upload_rate(upload_rate):
    try:
        upload_rate = int(upload_rate)
        if(upload_rate in range(1, 601)):
            return True
        return False
    except ValueError:
        return False
    
def check_upload_timeout(upload_timeout):
    try:
        upload_timeout = int(upload_timeout)
        if(upload_timeout in range(1, 61)):
            return True
        return False
    except ValueError:
        return False
    
def check_upload_retries(upload_retries):
    try:
        upload_retries = int(upload_retries)
        if(upload_retries in range(0, 61)):
            return True
        return False
    except ValueError:
        return False

def load_defaults(args):
    if(args['addr'] == False):
        args['addr'] = default_addr
    if(args['port'] == False):
        args['port'] = default_port
    if(args['qaprs'] == False):
        args['qaprs'] = default_qaprs
    if(args['runtime'] == False):
        args['runtime'] = default_runtime
    if(args['saver'] == False):
        args['saver'] = default_saver
    if(args['savep'] == False):
        args['savep'] = default_savep
    if(args['filepath'] == False):
        args['filepath'] = default_filepath
    if(args['qupl'] == False):
        args['qupl'] = default_qupl
    if(args['call'] == False):
        args['call'] = default_user_callsign
    if(args['pos'] == False):
        args['pos'] = default_user_position
    if(args['ant'] == False):
        args['ant'] = default_user_antenna
    if(args['mail'] == False):
        args['mail'] = default_contact_email
    if(args['posu'] == False):
        args['posu'] = default_user_position_update_rate
    if(args['rate'] == False):
        args['rate'] = default_upload_rate
    if(args['timeout'] == False):
        args['timeout'] = default_upload_timeout
    if(args['retry'] == False):
        args['retry'] = default_upload_retries
    return args

def convert(args):
    args['port'] = int(args['port'])
    args['qaprs'] = int(args['qaprs'])
    args['runtime'] = int(args['runtime'])
    if(args['saver'] == '0'):
        args['saver'] = 0
    else:
        args['saver'] = 1
    if(args['savep'] == '0'):
        args['savep'] = 0
    else:
        args['savep'] = 1
    args['qupl'] = int(args['qupl'])
    if(type(args['pos']) != list):
        args['pos'] = args['pos'].split(',')
        for i in range(len(args['pos'])):
            args['pos'][i] = float(args['pos'][i])  
    args['posu'] = int(args['posu'])
    args['rate'] = int(args['rate'])
    args['timeout'] = int(args['timeout'])
    args['retry'] = int(args['retry'])
    return args

def print_prolog(args):
    print('SondeHub Uploader by Eshco93')
    print('')
    print('Program parameters:')
    print('{:<26} {}'.format('Address:', args['addr']))
    print('{:<26} {}'.format('Port:', args['port']))
    print('{:<26} {}'.format('APRS Queue Size:', args['qaprs']))
    print('{:<26} {}'.format('Runtime:', args['runtime']))
    print('{:<26} {}'.format('Save Raw Data:', args['saver']))
    print('{:<26} {}'.format('Save Parsed Data:', args['savep']))
    print('{:<26} {}'.format('File Path:', args['filepath']))
    print('{:<26} {}'.format('Upload Queue Size:', args['qupl']))
    print('{:<26} {}'.format('User Callsign:', args['call']))
    print('{:<26} {}'.format('User Position:', 'Lat: ' + str(args['pos'][0]) + ' / Lon: ' + str(args['pos'][1]) + ' / Alt: ' + str(args['pos'][2])))
    print('{:<26} {}'.format('User Antenna:', args['ant']))
    print('{:<26} {}'.format('Contact E-Mail:', args['mail']))
    print('{:<26} {}'.format('User Position Update Rate:', args['posu']))
    print('{:<26} {}'.format('Upload Rate:', args['rate']))
    print('{:<26} {}'.format('Upload Timeout:', args['timeout']))
    print('{:<26} {}'.format('Upload Retries:', args['retry']))
    

def print_warnings(args):
    if(args['addr'] == False):
        print('Warning: You provided an invalid address. Therefore the default was loaded (' + default_addr + ')')
    if(args['port'] == False):
        print('Warning: You provided an invalid port. Therefore the default was loaded (' + str(default_port) + ')')
    if(args['qaprs'] == False):
        print('Warning: You provided an invalid aprs queue size. Therefore the default was loaded (' + str(default_qaprs) + ')')
    if(args['runtime'] == False):
        print('Warning: You provided an invalid runtime. Therefore the default was loaded (' + str(default_runtime) + ')')
    if(args['saver'] == False):
        print('Warning: You provided an invalid save raw data setting. Therefore the default was loaded (' + str(default_saver) + ')')
    if(args['savep'] == False):
        print('Warning: You provided an invalid save parsed data setting. Therefore the default was loaded (' + str(default_savep) + ')')
    if(args['filepath'] == False):
        print('Warning: You provided an invalid filepath. Therefore the default was loaded (' + default_filepath + ')')
    if(args['qupl'] == False):
        print('Warning: You provided an invalid upload queue size. Therefore the default was loaded (' + str(default_qupl) + ')')
    if(args['call'] == False):
        print('Warning: You provided an invalid user callsign. Therefore the default was loaded (' + default_user_callsign + ')')
    if(args['pos'] == False):
        print('Warning: You provided an invalid user position. Therefore the default was loaded (' + str(default_user_position) + ')')
    if(args['ant'] == False):
        print('Warning: You provided an invalid user antenna. Therefore the default was loaded (' + default_user_antenna + ')')
    if(args['mail'] == False):
        print('Warning: You provided an invalid contact e-mail. Therefore the default was loaded (' + default_contact_email + ')')
    if(args['posu'] == False):
        print('Warning: You provided an invalid user position update rate. Therefore the default was loaded (' + str(default_user_position_update_rate) + ')')
    if(args['rate'] == False):
        print('Warning: You provided an invalid upload rate. Therefore the default was loaded (' + str(default_upload_rate) + ')')
    if(args['timeout'] == False):
        print('Warning: You provided an invalid upload timeout. Therefore the default was loaded (' + str(default_upload_timeout) + ')')
    if(args['retry'] == False):
        print('Warning: You provided invalid upload retries. Therefore the default was loaded (' + str(default_upload_retries) + ')')
        
        
if __name__ == '__main__':
    set_proc_name('SondeHubUploader')
      
    args_raw = parse_arguments()
    args_checked = perform_checks(copy.deepcopy(args_raw))
    args_default = load_defaults(copy.deepcopy(args_checked))
    args_converted = convert(args_default)
    
    print_prolog(args_converted)
    print()
    print_warnings(args_checked)
    
    obj = SondeHubUploader(args_converted)
    
    if(args_converted['runtime'] == 0):
        while True:
            pass
    elif(args_converted['runtime'] > 0):
        time.sleep(args_converted['runtime'])
        obj.close()
        
