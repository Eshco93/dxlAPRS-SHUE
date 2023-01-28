# dxlAPRS SondeHub Uploader Extension
This extension for the [dxlAPRS software toolchain](https://github.com/oe5hpm/dxlAPRS) allows uploading of radiosonde telemetry data to the [SondeHub Tracker](https://sondehub.org/).
## Introduction
When operating an amateur radiosonde receiver station, there are a bunch of different software solutions to choose from. Examples would be [radiosonde_auto_rx](https://github.com/projecthorus/radiosonde_auto_rx) by [Mark Jessop (VK5QI)](https://github.com/darksidelemm), [dxlAPRS](https://github.com/oe5hpm/dxlAPRS) by Christian Rabler (OE5DXL) or [rdz_ttgo_sonde](https://github.com/dl9rdz/rdz_ttgo_sonde) by [Hansi Reiser (DL9RDZ)](https://github.com/dl9rdz/). There are certainly also a few other solutions and each of them has their own advantages and disadvantages.

Telemetry data gathered by amateur radiosonde receiver stations is often uploaded to online databases, on which live radiosonde tracking websites are built. A few examples are [radiosondy.info](https://radiosondy.info/) by Michał Lewiński (SQ6KXY), [SondeHub Tracker](https://sondehub.org/) by [Project Horus](http://www.projecthorus.org/) and [wettersonde.net](https://www.wettersonde.net/) by Jean-Michael Grobel (DO2JMG).

However, as you might expect, not every software allows telemetry data upload to every database. For example, dxlAPRS (as the name suggests) is APRS-based and therefore only allows uploading to APRS databases, like [radiosondy.info](https://radiosondy.info/) and [wettersonde.net](https://www.wettersonde.net/). [SondeHub Tracker](https://sondehub.org/), which is not based on APRS, is therefore not supported.

This is where this extension of dxlAPRS comes in to play. It takes the telemetry data provided by dxlAPRS and uploads it to the [SondeHub Tracker](https://sondehub.org/) database.
## Theory of Operation
At its core, dxlAPRS is a so-called toolchain, i.e. a collection of independent tools that are chained together. The tools communicate with each other mostly using UDP ports. The following diagram shows the structure of an exemplary dxlAPRS-based radiosonde receiver station.

<p align="center"><img src="https://user-images.githubusercontent.com/34800304/215233027-d883527e-3c72-4d19-a35f-24ec19f22adc.png" width=70% height=70%></p>

On the hardware side, this fairly simple receiver station consists of a Raspberry Pi and an RTL-SDR stick. rtl_tcp, which is not part of dxlAPRS but part of [rtl-sdr](https://github.com/osmocom/rtl-sdr), provides an SDR server. sdrtst taps into this SDR server and creates receivers which send the received signals to an audio pipe. sondeudp then decodes those signals and sends the raw data to sondemod. sondemod packs the data into APRS packets and sends them to udpbox. udpbox multiplies the packets and sends them to various instances of udpgate4. udpgate4 is an APRS gateway that will forward the packets to APRS databases like [radiosondy.info](https://radiosondy.info/) and [wettersonde.net](https://www.wettersonde.net/). If you want to know more about this, I recommend visiting the website of [Attila Kocis (DL1NUX)](https://www.dl1nux.de/). He has great tutorials on dxlAPRS.

The dxlAPRS SondeHub Uploader Extension uses the APRS packets that are created by sondemod and distributed by udpbox. With a small adjustment of the configuration of udpbox, the packets can not only be forwarded to multiple instances of udpgate4, but also to the dxlAPRS SondeHub Uploader Extension. This results in the structure shown in the diagram below.


## Setup
## Known limitations
