# dxlAPRS SondeHub Uploader Extension
This extension for the [dxlAPRS software toolchain](https://github.com/oe5hpm/dxlAPRS) allows uploading of radiosonde telemetry data to the [SondeHub Tracker](https://sondehub.org/).
## Introduction
When operating an amateur radiosonde receiver station, there are a bunch of different software solutions to choose from. Examples would be [radiosonde_auto_rx](https://github.com/projecthorus/radiosonde_auto_rx) by [Mark Jessop (VK5QI)](https://github.com/darksidelemm), [dxlAPRS](https://github.com/oe5hpm/dxlAPRS) by Christian Rabler (OE5DXL) or [rdz_ttgo_sonde](https://github.com/dl9rdz/rdz_ttgo_sonde) by [Hansi Reiser (DL9RDZ)](https://github.com/dl9rdz/). There are certainly also a few other solutions and each of them has their own advantages and disadvantages.

Telemetry data gathered by amateur radiosonde receiver stations is often uploaded to online databases, on which live radiosonde tracking websites are built. A few examples are [radiosondy.info](https://radiosondy.info/) by Michał Lewiński (SQ6KXY), [SondeHub Tracker](https://sondehub.org/) by [Project Horus](http://www.projecthorus.org/) and [wettersonde.net](https://www.wettersonde.net/) by Jean-Michael Grobel (DO2JMG).

However, as you might expect, not every software allows telemetry data upload to every database. For example, [dxlAPRS](https://github.com/oe5hpm/dxlAPRS) (as the name suggests) is APRS-based and therefore only allows uploading to APRS databases, like [radiosondy.info](https://radiosondy.info/) and [wettersonde.net](https://www.wettersonde.net/). [SondeHub Tracker](https://sondehub.org/), which is not based on APRS, is therefore not supported by [dxlAPRS](https://github.com/oe5hpm/dxlAPRS).

This is where this extension of [dxlAPRS](https://github.com/oe5hpm/dxlAPRS) comes in to play. It takes the telemetry data provided by [dxlAPRS](https://github.com/oe5hpm/dxlAPRS) and uploads it to the [SondeHub Tracker](https://sondehub.org/) database.
## Theory of Operation
At its core, [dxlAPRS](https://github.com/oe5hpm/dxlAPRS) is a so-called toolchain, i.e. a collection of independent tools that are chained together. The tools communicate with each other mostly using UDP ports. The following diagram shows the structure of an exemplary dxlAPRS-based radiosonde receiver station.

<p align="center"><img src="https://user-images.githubusercontent.com/34800304/215264049-abb16e7f-edc6-4e68-9141-fb1cc8c4a398.png" width=70% height=70%></p>

On the hardware side, this fairly simple receiver station consists of a [Raspberry Pi](https://www.raspberrypi.com/) and an [RTL-SDR](https://www.rtl-sdr.com/) stick. rtl_tcp, which is not part of [dxlAPRS](https://github.com/oe5hpm/dxlAPRS) but part of [rtl-sdr](https://github.com/osmocom/rtl-sdr), provides an SDR server. [sdrtst](http://dxlwiki.dl1nux.de/index.php?title=Sdrtst) taps into this SDR server and creates receivers which send the received signals to an audio pipe. [sondeudp](http://dxlwiki.dl1nux.de/index.php?title=Sondeudp) then decodes those signals and sends the raw data to [sondemod](http://dxlwiki.dl1nux.de/index.php?title=Sondemod). [sondemod](http://dxlwiki.dl1nux.de/index.php?title=Sondemod) packs the data into APRS packets and sends them to [udpbox](http://dxlwiki.dl1nux.de/index.php?title=Udpbox). [udpbox](http://dxlwiki.dl1nux.de/index.php?title=Udpbox) multiplies the packets and sends them to various instances of [udpgate4](http://dxlwiki.dl1nux.de/index.php?title=Udpgate4). [udpgate4](http://dxlwiki.dl1nux.de/index.php?title=Udpgate4) is an APRS gateway that will forward the packets to APRS databases like [radiosondy.info](https://radiosondy.info/) and [wettersonde.net](https://www.wettersonde.net/). If you want to know more about this, I recommend visiting the website of [Attila Kocis (DL1NUX)](https://www.dl1nux.de/). He has great tutorials on dxlAPRS.

The following diagram shows how the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE) is integrated into the [dxlAPRS toolchain](https://github.com/oe5hpm/dxlAPRS).

<p align="center"><img src="https://user-images.githubusercontent.com/34800304/215265940-06f17886-d776-405c-9d9e-fd28c45c146d.png" width=70% height=70%></p>

The [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE) uses the APRS packets that are created by [sondemod](http://dxlwiki.dl1nux.de/index.php?title=Sondemod) and distributed by [udpbox](http://dxlwiki.dl1nux.de/index.php?title=Udpbox). With a small adjustment of the configuration of [udpbox](http://dxlwiki.dl1nux.de/index.php?title=Udpbox), the packets can not only be forwarded to multiple instances of [udpgate4](http://dxlwiki.dl1nux.de/index.php?title=Udpgate4), but also to the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE).

The internal structure of the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE) is fairly simple, which can be seen in the next diagram.

<p align="center"><img src="https://user-images.githubusercontent.com/34800304/215267742-2082bc5c-1b36-480e-8ccb-8faaecc828cd.png"></p>

The APRS packages received from udpbox via UDP are stored in a queue. The stored packages are then processed once at a time, which involves parsing and reformatting the telemetry data to the [SondeHub Telemetry Format](https://github.com/projecthorus/sondehub-infra/wiki/SondeHub-Telemetry-Format). The reformatted telemetry data is again stored in a queue, waiting for upload to the [SondeHub Tracker](https://sondehub.org/) database. The upload takes place at fixed time intervals. When an upload is performed, all the telemetry data currently in the queue is uploaded at once. Another completely independent process handles the upload of the station data. Receiving, processing, telemetry uploading and station uploading are all performed by concurrently running threads.
## Setup
This section will guide you through the setup of the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE).
### 1. Prerequisites
This guide assumes that you already have your [dxlAPRS](https://github.com/oe5hpm/dxlAPRS) radiosonde receiver station up and running. If that's not yet the case, I recommend following this [tutorial](https://www.dl1nux.de/wettersonden-rx-mit-dxlaprs/) by [Attila Kocis (DL1NUX)](https://www.dl1nux.de/).
### 2. Installing Python
The [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE) is based on [Python](https://www.python.org/). For this reason it is necessary to have a reasonably current version of [Python 3](https://www.python.org/) installed. If you are using a [Raspberry Pi](https://www.raspberrypi.com/) with [Raspberry Pi OS](https://www.raspberrypi.com/software/), you might already have [Python 3](https://www.python.org/) installed. If you're using a different system, you may have to install [Python 3](https://www.python.org/) yourself.
### 3. Python dependencies
Some of the packages that are used by the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE) are not part of the [Python Standard Library](https://docs.python.org/3/library/). The [requests package](https://pypi.org/project/requests/) is needed for uploading the telemetry and station data to the [SondeHub Tracker](https://sondehub.org/) database. The [python-dateutil package](https://pypi.org/project/python-dateutil/) is needed for handling data of the [datetime module](https://docs.python.org/3/library/datetime.html).

The [requests package](https://pypi.org/project/requests/) can be installed from [PyPI](https://pypi.org/) using [pip](https://pypi.org/project/pip/) with the following command.
```
$ python -m pip install requests
```
The [python-dateutil package](https://pypi.org/project/python-dateutil/) can also be installed from [PyPI](https://pypi.org/) using [pip](https://pypi.org/project/pip/) with the following command.
```
$ python -m pip install python-dateutil
```
### 4. Cloning the dxlAPRS_SHUE Repository
Cloning the [dxlAPRS_SHUE Repository](https://github.com/Eshco93/dxlAPRS-SHUE) requires [git](https://git-scm.com/) to be installed on your system. Once again if you are using a [Raspberry Pi](https://www.raspberrypi.com/) with [Raspberry Pi OS](https://www.raspberrypi.com/software/), you might already have [git](https://git-scm.com/) installed. If you're using a different system, you may have to install [git](https://git-scm.com/) yourself.

For cloning the [dxlAPRS_SHUE Repository](https://github.com/Eshco93/dxlAPRS-SHUE), use the following command.
```
$ git clone https://github.com/Eshco93/dxlAPRS-SHUE.git
```
You can issue this command from any directory of your system. It doesn't really matter where you put the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE). Put it wherever you like.
### 4. Changing parameters for [udpbox](http://dxlwiki.dl1nux.de/index.php?title=Udpbox)
As mentioned before, the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE) uses the APRS packages that are forwarded by [udpbox](http://dxlwiki.dl1nux.de/index.php?title=Udpbox). Hence [udpbox](http://dxlwiki.dl1nux.de/index.php?title=Udpbox) needs to be configured to forward the APRS packages not only to multiple instances of [udpgate4](http://dxlwiki.dl1nux.de/index.php?title=Udpgate4), but also to the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE).

This is done by adding another command line argument to [udpbox](http://dxlwiki.dl1nux.de/index.php?title=Udpbox). Adding the following command line argument will tell udpbox to forward the raw APRS packets to another address and port (note that `<ip>` and `<port>` are just placeholders at this point).
```
-l <ip>:<port>
```
Since you are most likely running the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE) on the same system as [udpbox](http://dxlwiki.dl1nux.de/index.php?title=Udpbox), you usually just want to use the localhost. Obviously you could also run both tools on different systems and use the address of the system that's running the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE) instead. The used port can be chosen relatively freely within the range of the [registered ports](https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers#Registered_ports). But the default port used by the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE) is `18001`.

So assuming you are just using the defaults, the command line argument that needs to be added to [udpbox](http://dxlwiki.dl1nux.de/index.php?title=Udpbox) would look like this.
```
-l 127.0.0.1:18001
```
When you are using [dxlAPRS](https://github.com/oe5hpm/dxlAPRS) then you are probably using a startup script in order to launch all the individual tools of the [dxlAPRS toolchain](https://github.com/oe5hpm/dxlAPRS). Hence that would be the place to add this new [udpbox](http://dxlwiki.dl1nux.de/index.php?title=Udpbox) command line argument. More information about those startup scripts can be found in the [tutorial](https://www.dl1nux.de/wettersonden-rx-mit-dxlaprs/) by [Attila Kocis (DL1NUX)](https://www.dl1nux.de/).

With the new [udpbox](http://dxlwiki.dl1nux.de/index.php?title=Udpbox) command line argument, the [udpbox](http://dxlwiki.dl1nux.de/index.php?title=Udpbox) command in the startup script would look something like this.
```
# Verteilen der AXUDP Daten (UDPBOX)
# 9101 zu radiosondy.info - 9102 zu wettersonde.net - 9999 zu APRSMAP (z.B.)
xfce4-terminal  --minimize --title UDPBOX -e 'bash -c "udpbox -R 127.0.0.1:9001 -l 127.0.0.1:9101 -l 127.0.0.1:9102 -l 127.0.0.1:9999 -l 127.0.0.1:18001 -v"' &
sleep 1
```
### 5. Modifying [sondecom.txt](http://dxlwiki.dl1nux.de/index.php?title=Sondecom.txt)
The [sondecom.txt](http://dxlwiki.dl1nux.de/index.php?title=Sondecom.txt) file can be found inside your [dxlAPRS](https://github.com/oe5hpm/dxlAPRS) folder. The file is used by [sondemod](http://dxlwiki.dl1nux.de/index.php?title=Sondemod) and defines which parameters [sondemod](http://dxlwiki.dl1nux.de/index.php?title=Sondemod) adds to the comment section of each APRS package. Since the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE) works on the basis of these packages, the comment section should include all data that is useful for the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE). This includes the following data.

- %F: sdr freq+AFC from [sdrtst](http://dxlwiki.dl1nux.de/index.php?title=Sdrtst)
- %n: frame number
- %s: gps sat count
- %u: sonde uptime

The order of those parameters is not relevant to the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE). So the line in [sondecom.txt](http://dxlwiki.dl1nux.de/index.php?title=Sondecom.txt) could look like this.
```
%F%n%s%u
```
You can also add more parameters if you like. The [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE) doesn't use any additional parameters but they might be useful for other APRS databases that you are sending your telemetry data to. The total number of parameters is also not relevant to the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE). If you need more information on how to edit the [sondecom.txt](http://dxlwiki.dl1nux.de/index.php?title=Sondecom.txt) file, I suggest that you take a look at [this page](http://dxlwiki.dl1nux.de/index.php?title=Sondecom.txt) of the [DXL-Wiki](http://dxlwiki.dl1nux.de/index.php?title=Hauptseite) or again at the [tutorial](https://www.dl1nux.de/wettersonden-rx-mit-dxlaprs/) by [Attila Kocis (DL1NUX)](https://www.dl1nux.de/).
### 6. Running the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE)
When running the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE), it must be configured properly. The [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE) is configured using command line arguments. The following table gives an overview of all the command line arguments used for configuring the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE).
Argument|Description|Default|Range
-|-|-|-
-a|Address for the UDP socket (usually 127.0.0.1)|127.0.0.1|-
-p|Port for the UDP socket|18001|1024 - 65353
-q|Size of the queue for storeing the received APRS packages before processing<br />The size needed depends on how many radiosondes you are concurrently receiving and how fast you are able to process their incoming data<br />Usually the default of 20 should be well suited for all circumstances|20|1 - 100
-t|Runtime of the program in seconds (0 for infinite runtime)<br />Usually the program runs indefinitely|0|0 - inf.
-s|Save the raw APRS packages to a textfile (0 = no / 1 = yes)<br />All packages in one file with one line for each package|1|0 - 1
-w|Save the parsed telemetry data to CSV files (0 = no / 1 = yes)<br />One CSV file for each radiosonde, named by it's serial|1|0 - 1
-d|Path for the files to be saved by the program|Current directory|-
-f|Size of the queue for storeing the processed telemetry data before uploading|50|1 - 100
-c|User callsign for the [SondeHub Tracker](https://sondehub.org/)<br />Max. length: 15 characters<br />Allowed characters: a-z, A-Z, 0-9, -, _|N0CALL|-
-l|User position for showing the station on the [SondeHub Tracker](https://sondehub.org/) Map<br />Format: [lat, lon, alt]<br />With lat and lon in decimal degrees and alt in meters|[0.0, 0.0, 0.0]|-
-i|Test|127.0.0.1|-
-u|Test|127.0.0.1|-
-g|Test|127.0.0.1|-
-r|Test|127.0.0.1|-
-o|Test|127.0.0.1|-
-e|Test|127.0.0.1|-
### 7. Adding the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE) to your start script
### 8. Adding the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE) to your stop script
## Known limitations
