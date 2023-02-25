# crc.py - Functions for CRC
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


import crc


# Create a crc calculator
def crc_create_calculator(self, width, polynomial, init_value, final_xor_value, reverse_input, reverse_output):
    configuration = crc.Configuration(
        width=width,
        polynomial=polynomial,
        init_value=init_value,
        final_xor_value=final_xor_value,
        reverse_input=reverse_input,
        reverse_output=reverse_output,
    )
    self.crc_calculator = crc.Calculator(configuration)
