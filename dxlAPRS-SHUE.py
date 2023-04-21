# dxlAPRS-SHUE - dxlAPRS extension for uploading radiosonde telemetry to SondeHub
#
# Copyright (C) Simon Schäfer <simon.gsa@web.de>
#
# Released under GNU GPL v3 or later


# Third-party modules
import copy
import time

# Own modules
import parameterChecks
import mainConfig
import procName
import parameterHandling
import printStartup
import SondeHubUploader.SondeHubUploader as SondeHubUploader


# Main Function
if __name__ == '__main__':
    # Change the process name, so it can be easily identified within all other processes
    procName.set_proc_name('dxlAPRS-SHUE')

    # Parse the command line arguments
    raw_parameters = parameterHandling.parse_arguments()
    # Perform validity checks on the configuration parameters provided through the command line arguments
    checked_parameters = parameterHandling.perform_checks(copy.deepcopy(raw_parameters))
    # Load the defaults for all configuration parameters that were deemed invalid by the validity checks
    defaulted_parameters = parameterHandling.load_defaults(copy.deepcopy(checked_parameters))
    # Cast all the configuration parameters to the needed datatypes
    casted_parameters = parameterHandling.cast(copy.deepcopy(defaulted_parameters))

    # Check if all required configuration parameters were provided
    if parameterChecks.check_required(casted_parameters):
        # Print a prolog message
        printStartup.print_prolog(casted_parameters)
        # Print an empty line for better readability
        print()
        # Print warnings for all invalid parameters
        printStartup.print_warnings(checked_parameters)
        # Check whether any parameter was invalid
        if raw_parameters != checked_parameters:
            # Print an empty line for better readability
            print()

        print('Running...')

        # Create a 'SondeHubUploader' object
        shu = SondeHubUploader.SondeHubUploader(casted_parameters)

        # Run forever if the configured 'runtime' is 0
        if casted_parameters['runtime'] == 0:
            while True:
                # Nothing needs to be done here, since all the processing is handled by the threads of the 'SondeHubUploader'
                time.sleep(1)
        # Sleep for the configured 'runtime' and close afterwards
        elif casted_parameters['runtime'] > 0:
            time.sleep(casted_parameters['runtime'])
            shu.close()
    else:
        print('Error: At least one of the required configuration parameters that you provided is invalid')
        print(f'The program will close in {mainConfig.closetime_on_error} seconds')
        time.sleep(mainConfig.closetime_on_error)
