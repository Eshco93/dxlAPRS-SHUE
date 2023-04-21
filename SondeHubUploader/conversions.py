# conversions.py - Functions for converting units
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


import datetime


# Convert an address to a readable hex string
def address_to_string(address):
    addr_str = '0x'
    for i in range(len(address)):
        addr_str += hex(address[i])[2:]
    return addr_str


# Convert a framenumber to an uptime in hms
def frame_to_hms(frame, framerate):
    hms = str(datetime.timedelta(seconds=frame * framerate)).split(':')
    return {'hour': hms[0], 'minute': hms[1], 'second': hms[2]}


# Convert an uptime in hms to a framenumber
def hms_to_frame(hour, minute, second, framerate):
    return (hour * 3600 + minute * 60 + second) * framerate


# Convert a length in feet to meter
def feet_to_meter(feet, precision):
    return round(feet * 0.3048, precision)


# Convert a length in meter to feet
def meter_to_feet(meters, precision):
    return round(meters * 3.28084, precision)


# Convert a speed in knot to kph
def knot_to_kph(knots, precision):
    return round(knots * 1.852, precision)


# Convert a speed in kph to knot
def kph_to_knot(kph, precision):
    return round(kph * 0.539957, precision)


# Convert a speed in knot to m/s
def knot_to_ms(knots, precision):
    return round(knots * 0.514444, precision)


# Convert a speed in m/s to knot
def ms_to_knot(ms, precision):
    return round(ms * 1.94384, precision)


# Convert a speed in kph to m/s
def kph_to_ms(kph, precision):
    return round(kph * 0.277778, precision)


# Convert a speed in m/s to kph
def ms_to_kph(ms, precision):
    return round(ms * 3.6, precision)


# Convert coordinates in GMS to DG
def gms_to_dg(degree, minute, second, direction, precision):
    dg = round(degree + (minute * 60 + second) / 3600, precision)
    if direction in ['S', 'W']:
        dg *= -1
    return dg


# Convert coordinates in DG to GMS
def dg_to_gms(dg, latlon, precision):
    degree = int(dg)
    minute = int((dg - degree) * 60)
    second = round(round((dg - degree) * 3600) % 60, precision)
    if dg > 0:
        if latlon:
            direction = 'N'
        else:
            direction = 'E'
    else:
        if latlon:
            direction = 'S'
        else:
            direction = 'W'
    return {'degree': degree, 'minute': minute, 'second': second, 'direction': direction}


# Convert coordinates in GMM to DG
def gmm_to_dg(degree, minute, direction, precision):
    dg = round(degree + (minute * 60) / 3600, precision)
    if direction in ['S', 'W']:
        dg *= -1
    return dg


# Convert coordinates in DG to GMM
def dg_to_gmm(dg, latlon, precision):
    degree = int(dg)
    minute = round((dg - degree) * 60, precision)
    if dg > 0:
        if latlon:
            direction = 'N'
        else:
            direction = 'E'
    else:
        if latlon:
            direction = 'S'
        else:
            direction = 'W'
    return {'degree': degree, 'minute': minute, 'direction': direction}

# Convert coordinates in GMS to GMM
def gms_to_gmm(degree, minute, second, direction, precision):
    return {'degree': degree, 'minute': minute + round(second / 60, precision), 'direction': direction}

# Convert coordinates in GMM to GMS
def gmm_to_gms(degree, minute, direction, precision):
    return {'degree': degree, 'minute': int(minute), 'second': round((minute - int(minute)) * 60, precision), 'direction': direction}
