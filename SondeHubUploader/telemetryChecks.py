# telemetryChecks.py - Functions for checking the telemetry
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Check whether telemetry is plausible
def check_plausibility(self, telemetry):
    # Go through all telemetry parameters
    # 'telemetry' is cast to a list, because the values might be modified during the loop
    for key, value in list(telemetry.items()):
        # Check all telemetry parameters that have a check function assigned to them
        if self.shuConfig.telemetry[key][0] is not None:
            # Check the telemetry parameters using the check function
            if self.shuConfig.telemetry[key][0](value):
                self.loggerObj.debug_detail(f'Parameter "{key}" plausible')
            else:
                # Telemetry parameters that are not plausible are removed from 'telemetry'
                telemetry.pop(key)
                self.loggerObj.warning(f'Parameter "{key}" not plausible')
        else:
            self.loggerObj.debug_detail(f'Parameter "{key}" has no plausibility check')
    return telemetry


# Check whether telemetry contains all mandatory parameters for SondeHub
def check_mandatory(self, telemetry):
    # The check result is initially 'True' and might be set to 'False' by the checks
    result = True
    # At first, all the telemetry parameters that are mandatory for all radiosondes are checked
    # Go through all possible telemetry parameters
    for parameter, (check_function, mandatory, optional, optional_name, reformat_function) in self.shuConfig.telemetry.items():
        # 'mandatory' is set to true, if the telemetry parameter is mandatory for all radiosondes
        if mandatory == True:
            # Check whether the parameter exists in 'telemetry'
            if parameter in telemetry:
                self.loggerObj.debug_detail(f'Mandatory parameter "{parameter}" exists')
            else:
                result = False
                self.loggerObj.debug_detail(f'Mandatory parameter "{parameter}" is missing')
    # The radiosonde type needs to be determined in order to check the mandatory telemetry parameters for specific radiosondes
    _type = None
    # Go through all possible radiosonde types and compare the type
    for key in self.shuConfig.radiosonde.keys():
        if 'type' in telemetry and telemetry['type'].startswith(key):
            _type = key
    if _type is not None:
        # Go through all possible telemetry parameters (again)
        for parameter, (check_function, mandatory, optional, optional_name, reformat_function) in self.shuConfig.telemetry.items():
            # 'mandatory' contains a list of radiosonde types, if the telemetry parameter is mandatory for specific radiosondes
            if type(mandatory) == list and _type in mandatory:
                # Check whether the parameter exists in 'telemetry'
                if parameter in telemetry:
                    self.loggerObj.debug_detail(f'Mandatory parameter "{parameter}" exists')
                else:
                    result = False
                    self.loggerObj.error(f'Mandatory parameter "{parameter}" is missing')
    else:
        result = False
        self.loggerObj.error('Radiosonde type unknown')
    return result
