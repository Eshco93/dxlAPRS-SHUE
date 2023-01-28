# dxlAPRS SondeHub Uploader Extension
This extension for the [dxlAPRS software toolchain](https://github.com/oe5hpm/dxlAPRS) allows uploading of radiosonde telemetry data to the [SondeHub Tracker](https://sondehub.org/).
## Introduction
When operating an amateur radiosonde receiver station, there are a bunch of different software solutions to choose from. Examples would be [radiosonde_auto_rx](https://github.com/projecthorus/radiosonde_auto_rx) by [Mark Jessop (VK5QI)](https://github.com/darksidelemm), [dxlAPRS](https://github.com/oe5hpm/dxlAPRS) by Christian Rabler (OE5DXL) or [rdz_ttgo_sonde](https://github.com/dl9rdz/rdz_ttgo_sonde) by [Hansi Reiser (DL9RDZ)](https://github.com/dl9rdz/). There are certainly also a few other solutions and each of them has their own advantages and disadvantages.

Telemetry data gathered by amateur radiosonde receiver stations is often uploaded to online databases, on which live radiosonde tracking websites are built. A few examples are [radiosondy.info](https://radiosondy.info/) by Michał Lewiński (SQ6KXY), [SondeHub Tracker](https://sondehub.org/) by [Project Horus](http://www.projecthorus.org/) and [wettersonde.net](https://www.wettersonde.net/) by Jean-Michael Grobel (DO2JMG).

However, as you might expect, not every software allows telemetry data upload to every database. For example, dxlAPRS (as the name suggests) is APRS-based and therefore only allows uploading to APRS databases, like [radiosondy.info](https://radiosondy.info/) and [wettersonde.net](https://www.wettersonde.net/). [SondeHub Tracker](https://sondehub.org/), which is not based on APRS, is therefore not supported by dxlAPRS.

This is where this extension of dxlAPRS comes in to play. It takes the telemetry data provided by dxlAPRS and uploads it to the [SondeHub Tracker](https://sondehub.org/) database.
## Theory of Operation
At its core, dxlAPRS is a so-called toolchain, i.e. a collection of independent tools that are chained together. The tools communicate with each other mostly using UDP ports. The following diagram shows the structure of an exemplary dxlAPRS-based radiosonde receiver station.

<p align="center"><img src="https://user-images.githubusercontent.com/34800304/215264049-abb16e7f-edc6-4e68-9141-fb1cc8c4a398.png" width=70% height=70%></p>

On the hardware side, this fairly simple receiver station consists of a [Raspberry Pi](https://www.raspberrypi.com/) and an [RTL-SDR](https://www.rtl-sdr.com/) stick. rtl_tcp, which is not part of dxlAPRS but part of [rtl-sdr](https://github.com/osmocom/rtl-sdr), provides an SDR server. sdrtst taps into this SDR server and creates receivers which send the received signals to an audio pipe. sondeudp then decodes those signals and sends the raw data to sondemod. sondemod packs the data into APRS packets and sends them to udpbox. udpbox multiplies the packets and sends them to various instances of udpgate4. udpgate4 is an APRS gateway that will forward the packets to APRS databases like [radiosondy.info](https://radiosondy.info/) and [wettersonde.net](https://www.wettersonde.net/). If you want to know more about this, I recommend visiting the website of [Attila Kocis (DL1NUX)](https://www.dl1nux.de/). He has great tutorials on dxlAPRS.

The following diagram shows how the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE) is integrated into the dxlAPRS toolchain.

<p align="center"><img src="https://user-images.githubusercontent.com/34800304/215265940-06f17886-d776-405c-9d9e-fd28c45c146d.png" width=70% height=70%></p>

The [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE) uses the APRS packets that are created by sondemod and distributed by udpbox. With a small adjustment of the configuration of udpbox, the packets can not only be forwarded to multiple instances of udpgate4, but also to the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE).

The internal structure of the dxlAPRS SondeHub Uploader is fairly simple, which can be seen in the next diagram.

<p align="center"><img src="https://user-images.githubusercontent.com/34800304/215267742-2082bc5c-1b36-480e-8ccb-8faaecc828cd.png"></p>

The APRS packages received from udpbox via UDP are stored in a queue. The stored packages are then processed once at a time, which involves parsing and reformatting the telemetry data to the [SondeHub Telemetry Format](https://github.com/projecthorus/sondehub-infra/wiki/SondeHub-Telemetry-Format). The reformatted telemetry data is again stored in a queue, waiting for upload to the [SondeHub Tracker](https://sondehub.org/) database. The upload takes place at fixed time intervals. When an upload is performed, all the telemetry data currently in the queue is uploaded at once. Another completely independent process handles the upload of the station data. Receiving, processing, telemetry uploading and station uploading are all performed by concurrently running threads.
## Setup
This section will guide you through the setup of the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE).
### 1. Prerequisites
This guide assumes that you already have your dxlAPRS radiosonde receiver station up and running. If that's not yet the case, I recommend following this [tutorial](https://www.dl1nux.de/wettersonden-rx-mit-dxlaprs/) by [Attila Kocis (DL1NUX)](https://www.dl1nux.de/).
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
You can issue this command from any directory of your system. It doesn't really matter where you put the [dxlAPRS SondeHub Uploader Extension](https://github.com/Eshco93/dxlAPRS-SHUE)
## Known limitations
