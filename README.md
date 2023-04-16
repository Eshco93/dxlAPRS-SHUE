# dxlAPRS SondeHub Uploader Extension
This extension for the dxlAPRS software toolchain allows uploading of radiosonde telemetry data to SondeHub.
## Introduction
When operating an amateur radiosonde receiver station, there are a bunch of different software solutions to choose from. Examples would be [radiosonde_auto_rx](https://github.com/projecthorus/radiosonde_auto_rx) by [Mark Jessop (VK5QI)](https://github.com/darksidelemm), [dxlAPRS](https://github.com/oe5hpm/dxlAPRS) by Christian Rabler (OE5DXL) or [rdz_ttgo_sonde](https://github.com/dl9rdz/rdz_ttgo_sonde) by [Hansi Reiser (DL9RDZ)](https://github.com/dl9rdz/). There are certainly also a few other solutions and each of them has their own advantages and disadvantages.

Telemetry data gathered by amateur radiosonde receiver stations is often uploaded to online databases. Live radiosonde tracking websites are built, based on these databases. A few examples are [radiosondy.info](https://radiosondy.info/) by Michał Lewiński (SQ6KXY), [SondeHub](https://sondehub.org/) by [Project Horus](http://www.projecthorus.org/) and [wettersonde.net](https://www.wettersonde.net/) by Jean-Michael Grobel (DO2JMG).

However, as you might expect, not every software allows telemetry data upload to every database. For example, dxlAPRS (as the name suggests) is APRS-based and therefore only allows uploading to APRS databases, like radiosondy.info and wettersonde.net. SondeHub, which is not based on APRS, is therefore not supported by dxlAPRS.

This is where this extension of dxlAPRS comes in to play. It takes the telemetry data provided by dxlAPRS and uploads it to the SondeHub database.
## Theory of Operation
At its core, dxlAPRS is a so-called toolchain, i.e. a collection of independent tools that are chained together. The tools communicate with each other mostly using UDP. The following diagram shows the structure of an exemplary dxlAPRS-based radiosonde receiver station.

<p align="center"><img src="https://user-images.githubusercontent.com/34800304/232325696-dd6da51b-eacd-4cb7-a7a6-a08ba0171446.png" width=70% height=70%></p>

On the hardware side, this fairly simple radiosonde receiver station consists of a Raspberry Pi and an RTL-SDR stick. rtl_tcp, which is not part of dxlAPRS but part of rtl-sdr, provides an SDR server. [sdrtst](http://dxlwiki.dl1nux.de/index.php?title=Sdrtst) taps into this SDR server and creates receivers which send the received signals to an audio pipe. [sondeudp](http://dxlwiki.dl1nux.de/index.php?title=Sondeudp) then decodes those signals and sends the raw data to [sondemod](http://dxlwiki.dl1nux.de/index.php?title=Sondemod). sondemod packs the data into APRS packages and sends them to various instances of [udpgate4](http://dxlwiki.dl1nux.de/index.php?title=Udpgate4). udpgate4 is an APRS gateway that will forward the packages to APRS databases like radiosondy.info and wettersonde.net. If you want to know more about this, I recommend visiting the website of [Attila Kocis (DL1NUX)](https://www.dl1nux.de/). He has great tutorials on dxlAPRS.

The following diagram shows how the dxlAPRS SondeHub Uploader Extension (dxlAPRS-SHUE) is integrated into dxlAPRS.

<p align="center"><img src="https://user-images.githubusercontent.com/34800304/232325822-d8f3066b-735b-4d56-b133-304f941cc153.png" width=70% height=70%></p>

dxlAPRS-SHUE uses the data that is sent out by sondemod via UDP. However, sondemod provides two different UDP streams that dxlAPRS-SHUE can use. On the one hand, dxlAPRS-SHUE can use the APRS packages that sondemod already sends out to various instances of udpgate4 (See above). On the other hand, dxlAPRS-SHUE can use the UDP JSON output that sondemod provides (recommended). Both options are equally easy to implement and only require a small adjustment of the configuration of sondemod (See section [5.](https://github.com/Eshco93/dxlAPRS-SHUE/blob/main/README.md#5-changing-parameters-for-udpbox)).

The internal structure of dxlAPRS-SHUE is fairly simple, which can be seen in the next diagram.

<p align="center"><img src="https://user-images.githubusercontent.com/34800304/232330631-eff289bb-716b-45dc-8790-c19d9d652108.png"></p>

The packages received from sondemod via UDP are stored in a queue. The stored packages are then processed once at a time, which involves parsing the data, checking for possible errors and reformatting the telemetry data to the [SondeHub Telemetry Format](https://github.com/projecthorus/sondehub-infra/wiki/SondeHub-Telemetry-Format). The reformatted telemetry data is again stored in a queue, waiting for upload to the SondeHub database. The upload takes place at fixed time intervals (See section [7.](https://github.com/Eshco93/dxlAPRS-SHUE/blob/main/README.md#7-running-dxlaprs-shue)). When an upload is performed, all the telemetry data currently in the queue is uploaded at once. Another completely independent process handles the upload of the station information, which also takes place at fixed time intervals (See section [7.](https://github.com/Eshco93/dxlAPRS-SHUE/blob/main/README.md#7-running-dxlaprs-shue)). Receiving, processing, telemetry uploading and station information uploading are all performed by concurrently running threads.
## Setup
This section will guide you through the setup of dxlAPRS-SHUE.
### 1. Prerequisites
This guide assumes that you already have your dxlAPRS radiosonde receiver station up and running. If that's not yet the case, I recommend following this [tutorial](https://www.dl1nux.de/wettersonden-rx-mit-dxlaprs/) by Attila Kocis (DL1NUX).
### 2. Installing Python
dxlAPRS-SHUE is based on Python. For this reason it is necessary to have a reasonably current version of Python 3 installed. If you are using a Raspberry Pi with Raspberry Pi OS, you might already have Python 3 installed. If you're using a different system, you may have to install Python 3 yourself.
### 3. Python dependencies
Some of the packages that are used by dxlAPRS-SHUE are not part of the Python Standard Library. The crc package is needed for performing a CRC on incoming APRS packages. The requests package is needed for uploading the telemetry and station information data to the SondeHub database. The python-dateutil package is needed for handling data of the datetime module.

The crc package can be installed from PyPI using pip with the following command.
```
$ python -m pip install crc
```
The requests package can also be installed from PyPI using pip with the following command.
```
$ python -m pip install requests
```
### 4. Cloning the dxlAPRS-SHUE Repository
Cloning the dxlAPRS-SHUE Repository requires git to be installed. Once again, if you are using a Raspberry Pi with Raspberry Pi OS, you might already have git installed. If you're using a different system, you may have to install git yourself.

For cloning the dxlAPRS-SHUE Repository, use the following command.
```
$ git clone https://github.com/Eshco93/dxlAPRS-SHUE.git
```
You can issue this command from any directory of your system. It doesn't really matter where you put dxlAPRS-SHUE. Put it wherever you like.
### 5. Changing parameters for sondemod
As mentioned in the [theory of operation](https://github.com/Eshco93/dxlAPRS-SHUE#theory-of-operation), dxlAPRS-SHUE can either use the APRS packages that sondemod already sends out to various instances of udpgate4 or it can use the UDP JSON output that sondemod provides. The second option is the recommended one. The reason for this lies in a fundamental difference between APRS databases, like radiosondy.info and wettersonde.net, and SondeHub.

For the APRS databases, the telemetry data is encapsulated in APRS packages directly after receipt and immediately transmitted to the respective databases. Each telemetry data package is encapsulated and transmitted individually. This method is very inefficient and leads to large amounts of data to be transmitted. For this reason, usually not every single received telemetry data packet actually transmitted via APRS. Instead, fixed transmission intervals are used. All untransmitted telemetry data is simply discarded. This is done to keep traffic to the APRS databases at a manageable level. For dxlAPRS, the transmission intervals are defined in the sondeconfig.txt file that can be found inside your dxlAPRS folder. If you need more information on how to edit the sondeconfig.txt file, I suggest that you take a look at the [tutorial](https://www.dl1nux.de/wettersonden-rx-mit-dxlaprs/) by Attila Kocis (DL1NUX).

SondeHub, on the other hand, works very different. In the case of SondeHub, the received telemetry data is not transmitted individually immediately after receipt. Instead, received telemetry data is first collected and then transmitted to SondeHub at fixed time intervals. Multiple packages of telemetry data are sent to SondeHub in a single large package. In addition, the data packages are compressed before transmission. This method is very efficient and keeps transmission overhead very low. For this reason, with SondeHub it is possible and desirable that every single received telemetry data package is also uploaded.






As mentioned in the [theory of operation](https://github.com/Eshco93/dxlAPRS-SHUE#theory-of-operation), dxlAPRS-SHUE uses the APRS packages that are forwarded by udpbox. Hence udpbox needs to be configured to forward the APRS packages not only to multiple instances of udpgate4, but also to dxlAPRS-SHUE.

This is done by adding another command line argument to udpbox. Adding the following command line argument will tell udpbox to forward the raw APRS packages to another address and port (note that `<ip>` and `<port>` are just placeholders at this point).
```
-l <ip>:<port>
```
Since you are most likely running dxlAPRS-SHUE on the same system as udpbox, you usually just want to use the localhost. Obviously you could also run both tools on different systems and use the address of the system that's running dxlAPRS-SHUE instead. The used port can be chosen relatively freely within the range of the [registered ports](https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers#Registered_ports). But the default port used by dxlAPRS-SHUE is `18001` (See section [7.](https://github.com/Eshco93/dxlAPRS-SHUE/blob/main/README.md#7-running-dxlaprs-shue)).

So assuming you are just using the defaults, the command line argument that needs to be added to udpbox would look like this.
```
-l 127.0.0.1:18001
```
When you are using dxlAPRS then you are probably using a startup script in order to launch all the individual tools of the dxlAPRS toolchain. Hence that would be the place to add this new udpbox command line argument. More information about those startup scripts can be found in the [tutorial](https://www.dl1nux.de/wettersonden-rx-mit-dxlaprs/) by Attila Kocis (DL1NUX).

With the new udpbox command line argument, the udpbox command in the startup script would look something like this.
```
# Verteilen der AXUDP Daten (UDPBOX)
# 9101 zu radiosondy.info - 9102 zu wettersonde.net - 9999 zu APRSMAP (z.B.)
xfce4-terminal  --minimize --title UDPBOX -e 'bash -c "udpbox -R 127.0.0.1:9001 -l 127.0.0.1:9101 -l 127.0.0.1:9102 -l 127.0.0.1:9999 -l 127.0.0.1:18001 -v"' &
sleep 1
```
### 6. Modifying sondecom.txt
The sondecom.txt file can be found inside your dxlAPRS folder. The file is used by sondemod and defines which telemetry parameters sondemod adds to the comment section of each APRS package. Since dxlAPRS-SHUE uses these packages, the comment section should include all telemetry parameters that are useful to dxlAPRS-SHUE. This includes the following telemetry parameters.

- %F: sdr freq+AFC from sdrtst
- %n: frame number
- %s: gps sat count
- %u: sonde uptime

The order of those telemetry parameters is not relevant to dxlAPRS-SHUE. So the line in sondecom.txt could look like this.
```
%F%n%s%u
```
You can also add more telemetry parameters if you like. dxlAPRS-SHUE doesn't use any additional telemetry parameters but they might be useful for other APRS databases that you are sending your APRS packages to. The total number of telemetry parameters is also not relevant to dxlAPRS-SHUE. If you need more information on how to edit the sondecom.txt file, I suggest that you take a look at [this page](http://dxlwiki.dl1nux.de/index.php?title=Sondecom.txt) of the [DXL-Wiki](http://dxlwiki.dl1nux.de/index.php?title=Hauptseite) or again at the [tutorial](https://www.dl1nux.de/wettersonden-rx-mit-dxlaprs/) by Attila Kocis (DL1NUX).
### 7. Running dxlAPRS-SHUE
When running dxlAPRS-SHUE, it must be configured properly. dxlAPRS-SHUE is configured using command line arguments. The following table gives an overview of all the command line arguments used for configuring dxlAPRS-SHUE.
Argument|Description|Default|Range
-|-|-|-
`-i`|Logging level for the printed log messages.<br /><br />Level 1: Print errors<br />Level 2: Print warnings<br />Level 3: Print processing information<br />Level `4`: Print debug messages<br />Level `5`: Print detailed debug messages<br /><br />Each level also contains the messages of all lower levels.|`3`|`1` - `5`
`-j`|Logging level for the log messages written to the log file.<br /><br />Level 1: Write errors<br />Level 2: Write warnings<br />Level 3: Write processing information<br />Level 4: Write debug messages<br />Level 5: Write detailed debug messages<br /><br />Each level also contains the messages of all lower levels.<br />This argument has no effect if writing the log file is disabled (See argument -k).|`3`|`1` - `5`
`-t`|Runtime of the program in seconds (`0` for infinite runtime).<br />Usually the program runs indefinitely.|`0`|>=`0`
`-a`|Address for the UDP socket (usually `127.0.0.1`).|`127.0.0.1`|-
`-p`|Port for the UDP socket (See section [5.](https://github.com/Eshco93/dxlAPRS-SHUE/blob/main/README.md#5-changing-parameters-for-udpbox)).|`18001`|`1024` - `65353`
`-d`|Path for the files written by the program.|`/dxlAPRS-SHUE/log`|-
`-s`|Write the raw APRS packages to a textfile (`0` = no / `1` = yes).<br />All packages in one file with one line for each package.|`0`|`0` - `1`
`-w`|Write the telemetry data to CSV files (`0` = no / `1` = yes).<br />One CSV file for each radiosonde, named by it's serial with with `t_` as a prefix.|`0`|`0` - `1`
`-z`|Write the reformatted telemetry data to CSV files (`0` = no / `1` = yes).<br />One CSV file for each radiosonde, named by it's serial with `r_` as a prefix.|`0`|`0` - `1`
`-k`|Write the log to a log file (`0` = no / `1` = yes).|`1`|`0` - `1`
`-q`|Size of the queue for storing the received APRS packages before processing.<br />The size needed depends on how many radiosondes you are concurrently receiving and how fast you are able to process their incoming data.<br />Usually the default of 20 should be well suited for all circumstances.<br />(See [theory of operation](https://github.com/Eshco93/dxlAPRS-SHUE#theory-of-operation))|`20`|`1` - `100`
`-f`|Size of the queue for storing the reformatted telemetry data before uploading.<br />The size needed depends on how many radiosondes you are concurrently receiving and how often you are uploading the telemetry data.<br />(See [theory of operation](https://github.com/Eshco93/dxlAPRS-SHUE#theory-of-operation))|`200`|`1` - `600`
`-c`|User callsign for SondeHub.<br />Length: 4 - 15 characters<br />Allowed characters: a-z, A-Z, 0-9, -, _<br />**This argument is required.**|-|-
`-l`|Position for showing your radiosonde receiver station on the SondeHub Map.<br />Format: `lat,lon,alt`<br />With lat and lon in decimal degrees and alt in meters.<br />**This argument is required.**|-|-
`-v`|Antenna name for showing in your radiosonde receiver station information on the SondeHub Map.<br />Length: 4 - 25 characters<br />If your antenna description contains spaces, you need to put it in quotation marks.|`"1/4 wave monopole"`|-
`-u`|Your contact E-Mail address.<br />Only visible for the admins of SondeHub.<br />Will be used to contact you in case there is an obvious issue with your radiosonde receiver station.<br />**This argument is required.**|-|-
`-g`|Update rate for your radiosonde receiver station information on the SondeHub Map in hours.<br />(See [theory of operation](https://github.com/Eshco93/dxlAPRS-SHUE#theory-of-operation))|`6`|`1` - `24`
`-r`|Telemetry data update rate in seconds.<br />(See [theory of operation](https://github.com/Eshco93/dxlAPRS-SHUE#theory-of-operation))|`30`|`1` - `600`
`-o`|Upload timeout for telemetry data and radiosonde receiver station information in seconds.|`20`|`1` - `60`
`-e`|Max. number of upload retries for telemetry data and radiosonde receiver station information.|`5`|`0` - `60`

Here is an example of what your command for launching dxlAPRS-SHUE could look like.
```
python dxlAPRS-SHUE.py -i 3 -j 3 -t 0 -a 127.0.0.1 -p 18001 -d /home/pi/dxlAPRS-SHUE/log -s 0 -w 0 -z 0 -k 1 -q 20 -f 200 -c S0MECALL -l 48.06339,11.52943,5 -v "1/4 wave monopole" -u someones@mail.com -g 6 -r 30 -o 20 -e 5
```
Though, you don't have to configure every single parameter of dxlAPRS-SHUE. If you want to leave certain parameters at their default values, you don't have to specify them explicitly. The default value is loaded for each parameter that is not explicitly specified. The only parameters that are mandatory are `-c`, `-l` and `-u` (See table above).

The default values are also loaded for incorrectly specified parameters. You will be informed about this by a warning message that is shown right after launching dxlAPRS-SHUE. A warning could look like this.
```
Warning: The configuration parameter "runtime" that you provided is invalid. Therefore the default was loaded (127.0.0.1)
```
If dxlAPRS-SHUE is launched with the command line argument `-h`, a help message will be printed that also explains all the available command line arguments.
```
python dxlAPRS-SHUE.py -h
```
### 8. Adding dxlAPRS-SHUE to your startup script
You might want to add dxlAPRS-SHUE to the startup script already mentioned in section [5.](https://github.com/Eshco93/dxlAPRS-SHUE/blob/main/README.md#5-changing-parameters-for-udpbox) in order to launch it together with all the other dxlAPRS tools. Add the following line to the bottom of your startup script in order to launch dxlAPRS-SHUE right after lanuching all the other dxlAPRS tools (note that `<command>` is just a placeholder for the command as described in section [7.](https://github.com/Eshco93/dxlAPRS-SHUE/blob/main/README.md#7-running-dxlaprs-shue))
```
# dxlAPRS SondeHub Uploader Extension
xfce4-terminal --minimize --title dxlAPRS-SHUE -e '<command>' &
```
This is what the entire line for the startup script, including the command described in section [7.](https://github.com/Eshco93/dxlAPRS-SHUE/blob/main/README.md#7-running-dxlaprs-shue), would look like.
```
# dxlAPRS SondeHub Uploader Extension
xfce4-terminal --minimize --title dxlAPRS-SHUE -e 'python dxlAPRS-SHUE.py -i 3 -j 3 -t 0 -a 127.0.0.1 -p 18001 -d /home/pi/dxlAPRS-SHUE/log -s 0 -w 0 -z 0 -k 1 -q 20 -f 200 -c S0MECALL -l 48.06339,11.52943,5 -v "1/4 wave monopole" -u someones@mail.com -g 6 -r 30 -o 20 -e 5' &
```
### 9. Adding dxlAPRS-SHUE to your stop script
If you added dxlAPRS-SHUE to your startup script as explained in section [8.](https://github.com/Eshco93/dxlAPRS-SHUE/blob/main/README.md#8-adding-dxlaprs-shue-to-your-startup-script), you'll also want to add it to your stop script in order to stop it together with all the individual tools of the dxlAPRS toolchain. The stop script goes by the name `sondestop.sh` and can be found inside your dxlAPRS folder.

In order to add dxlAPRS-SHUE to your stop script, just add `dxlAPRS-SHUE` to the end of the line in the stop script. This is what the stop script will look like after adding dxlAPRS-SHUE.
```
#!/bin/bash
# Beenden aller dxlAPRS Tools
killall -9 getalmd rtl_tcp sdrtst sondeudp sondemod udpbox udpgate4 dxlAPRS-SHUE
```
## Additional information
### Supported radiosonde types
Regarding the supported radiosonde types, dxlAPRS-SHUE is obviously limited to all the radiosonde types that are supported by both, dxlAPRS and SondeHub. At the moment this includes the follwing radiosonde types.
- RS41
- RS92 (Usually no longer used)
- IMET
- DFM
- M10
- M20
- MRZ
- MEISEI
### No temperature from DFM radiosondes
While other software solutions for radiosonde receiver stations (like radiosonde_auto_rx and rdz_ttgo_sonde) seem to at least support temperature reading from DFM radiosondes, dxlAPRS doesn't do that at the moment. Therefore telemetry data upload for DFM radiosondes is currently limited to the position data only.
### Not enough frames from DFM radiosondes
SondeHub performs a basic [z-test](https://github.com/projecthorus/sondehub-infra/wiki/Telemetry-check-error-messages) on the telemetry data that is being uploaded. Due to a [quirk of the DFM radiosondes](https://github.com/projecthorus/sondehub-infra/wiki/DFM-radiosonde-above-1000-and-not-enough-data-to-perform-z-check), SondeHub needs at least 10 frames of a DFM radiosonde in every uploaded telemetry package in order to perform this z-test. To ensure that, the telemetry data update rate (See section [7.](https://github.com/Eshco93/dxlAPRS-SHUE/blob/main/README.md#7-running-dxlaprs-shue)) should be 20 or higher. A future version of dxlAPRS-SHUE may address this issue by treating the upload for DFM radiosondes differently than the upload for all other radiosondes.
### No XDATA support
While SondeHub generally works based on decoded telemetry data, the data from external measurement instruments (like ozone probes) is handled differently. The XDATA field, which contains the raw data coming from the external measurement instrument, is directly uploaded to the SondeHub database. The [decoding](https://github.com/projecthorus/sondehub-infra/wiki/XDATA-Decoding) is then done by SondeHub, rather than by the radiosonde receiver station. That poses a problem since the APRS packages that sondemod is providing already contain the decoded telemetry data from external measurement instruments, but not the raw XDATA. Therefore there is currently no XDATA support.
### No meaningful RSSI values
In addition to all the other telemetry data, sondemod also provides RSSI values. And the upload of RSSI values is also supported by SondeHub. But since the values that sondemod provides are usually coming from an uncalibrated RTL-SDR stick, they do not represent anything that is even remotely close to reality. Therefore, the upload of RSSI values is currently not supported.
### Hardcoded leap seconds
Usually radiosondes transmit the [gps time](https://en.wikipedia.org/wiki/Global_Positioning_System#Timekeeping). Since the gps system does not factor in any [leap seconds](https://en.wikipedia.org/wiki/Leap_second), it currently has an offset of +18 seconds compared to UTC. While SondeHub standardised on the convention of using the GPS time, sondemod corrects the GPS time offset by applying a hardcoded offset of -18 seconds. This hardcoded offset is compensated by another hardcoded offset of +18 seconds, applied by dxlAPRS-SHUE. This now gives the GPS time again, which creates compliance to the convention of SondeHub.

While this circumstance does not usually pose a problem, it can become a problem when ([and if](https://engineering.fb.com/2022/07/25/production-engineering/its-time-to-leave-the-leap-second-in-the-past/)) another leap second is inserted. Once another leap second is inserted and considered by a newer version of sondemod and/or dxlAPRS-SHUE, you can get into trouble when updating either tool. A mismatch between the hardcoded leap seconds of sondemod and the hardcoded leap seconds of dxlAPRS-SHUE would result in your telemetry frame being one second off. Frankly, there is no smart solution to this problem. We can only hope that no more leap seconds will be inserted in the future. And otherwise, I hope you remember this section of this document.
