# logging.py - Functions for logger creation
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Modules
import logging


# Configure logger
def create_logger(self, loglevelp, loglevelw, savel):
    # Define a logger
    self.loggerObj = logging.getLogger('logger')

    # Add a custom logging level for detailed debugging
    add_logging_level('DEBUG_DETAIL', self.shuConfig.loglevel[5])

    # A 'StreamHandler' iss added to the logger
    c_format = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s')
    c_handler = logging.StreamHandler()
    c_handler.setFormatter(c_format)
    c_handler.setLevel(self.shuConfig.loglevel[loglevelp])
    self.loggerObj.addHandler(c_handler)
    # A optional 'FileHandler' might be added to the logger
    if savel:
        f_format = logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s')
        f_handler = logging.FileHandler(self.filepath + '/' + 'log.log')
        f_handler.setFormatter(f_format)
        f_handler.setLevel(self.shuConfig.loglevel[loglevelw])
        self.loggerObj.addHandler(f_handler)
    # A level must also be set for the logger itself, not only for the handlers
    self.loggerObj.setLevel(self.shuConfig.loglevel[5])


# Add a custom logging level
def add_logging_level(level_name, level_number):
    def log_for_level(self, message, *args, **kwargs):
        if self.isEnabledFor(level_number):
            self._log(level_number, message, args, **kwargs)

    def log_to_root(message, *args, **kwargs):
        logging.log(level_number, message, *args, **kwargs)

    logging.addLevelName(level_number, level_name)
    setattr(logging, level_name, level_number)
    setattr(logging.getLoggerClass(), level_name.lower(), log_for_level)
    setattr(logging, level_name.lower(), log_to_root)
