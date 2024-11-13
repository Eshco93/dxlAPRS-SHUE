# procName.py - Functions for setting/getting the process name
#
# Copyright (C) Simon Schäfer
#
# Released under GNU GPL v3 or later


# Set a new process name
def set_proc_name(name):
    from ctypes import cdll, byref, create_string_buffer
    libc = cdll.LoadLibrary('libc.so.6')
    buffer = create_string_buffer(len(name) + 1)
    buffer.value = str.encode(name)
    libc.prctl(15, byref(buffer), 0, 0, 0)


# Get the current process name
def get_proc_name():
    from ctypes import cdll, byref, create_string_buffer
    libc = cdll.LoadLibrary('libc.so.6')
    buffer = create_string_buffer(128)
    libc.prctl(16, byref(buffer), 0, 0, 0)
    return buffer.value
