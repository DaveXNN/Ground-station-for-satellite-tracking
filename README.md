# Antenna rotator for satellite tracking
This repository contains Antenna rotator for satellite tracking project description. The goal of this project was to design a homemade antenna rotator for tracking any of the satellites in the Earth orbit. The rotator is controlled from a laptop via WiFi. The rotator controll unit is Raspberry Pi 4 with installed Mosquitto broker for subscribing data about satellites from the laptop. Raspberry Pi then controls stepper motors to turn two Yagi antennas into the right direction to the passing satellite. The source code on laptop and on Raspberry Pi is writen in Python 3.9.

## Introduction

Each satellite has data about its position in the Earth orbit called TLE (Two-Line Element). They are updated every 2 hours on URL: https://celestrak.org/NORAD/elements/gp.php?GROUP=ACTIVE&FORMAT=tle. This rotator uses the latest TLE data to predict satellite visibility in a specific location on the Earth. For satellite visibility prediction is used python beyond library (https://pypi.org/project/beyond/). Here is an example of TLE for International Space Station and satellite Nexus FO-99:

```
ISS (ZARYA)             
1 25544U 98067A   23216.30597424  .00016406  00000+0  29387-3 0  9996
2 25544  51.6415  90.1197 0000976 153.7733 359.7746 15.50094272409258

NEXUS (FO-99)           
1 43937U 19003F   23215.56576503  .00083299  00000+0  10492-2 0  9997
2 43937  97.0807 242.3784 0013069 106.8096 253.4596 15.59254066253410
```

If we have the latest TLE data, we can track each satellite in the Earth orbit. This rotator is designed primarily for tracking satellites in the low Earth orbit (LEO), it means below an altitude of 2 000 km.

For the next sections we need to define two important variables - azimuth and elevation of a satellite. Azimuth and Elevation are measures used to identify the position of a satellite flying overhead. Azimuth tells you what direction to face and elevation tells you how high up in the sky to look. Both are measured in degrees. Azimuth varies from 0° to 360° and elevation from 0° to 90°.

## Hardware

The whole rotator is controlled by computer [Raspberry Pi 4](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/) via digital GPIO pins. Raspberry Pi is connected with two stepper motor drivers, two rotary encoders and a magnetometer.

The rotator has to follow satellite's azimuth and elevation, so we need two stepper motors and two drivers. Here is a list of electronic components:

| Name  | Quantity | Link |
| :--- | :---: | :---: |
| Raspberry Pi 4B  | 1  | https://www.raspberrypi.com/products/raspberry-pi-4-model-b/ |
| Step-Down Voltage Regulator LM2596 | 1 | https://www.laskakit.cz/step-down-menic-s-lm2596/ |
| Stepper motor NEMA23  | 2 | https://www.laskakit.cz/krokovy-motor-nema-23-57hs5630a4d8-1-1nm/ |
| Driver TB6600  | 2 | https://www.laskakit.cz/driver-tb6600--tb67s109aftg--pro-krokove-motory-3a-47v/ |

### Raspberry Pi 4

The next picture depicts Raspberry Pi 4B pinout:

![Raspberry Pi 4 pinout](https://github.com/DaveXNN/Antenna-rotator-for-satellite-tracking/blob/main/images/raspberrypi-pinout.png)

In the next table you can see numbers of connected pins and their usage:

| Name | Pin number | GPIO code | Connected device | Description |
| :---: | :---: | :---: | :---: | :--- |
| VCC | 17 | 3V3 | Drivers | :--- |
| AZ.DRIV.-ENABLE | 19 | GPIO10 | Azimuth driver | :--- |
| AZ.DRIV.-DIR | 21 | GPIO9 | Azimuth driver | :--- |
| AZ.DRIV.-STEP | 23 | GPIO11 | Azimuth driver | :--- |
| EL.DRIV.-ENABLE | 11 | GPIO17 | Elevation driver | :--- |
| EL.DRIV.-DIR | 13 | GPIO27 | Elevation driver | :--- |
| EL.DRIV.-STEP | 15 | GPIO22 | Elevation driver | :--- |
| VCC | 1 | 3V3 | Magnetometer | 3.3 V power supply for magnetometer |

### Driver TB6600

Driver TB6600 is supposed to control a stepper motor with a power supply 20 V. It has three inputs - ENABLE, DIRECTION and STEP and four outputs. Here is a list of outputs' names and colors of connected cables from stepper motor:

| Name | Color |
| :---: | :---: |
| A+ | red |
| A- | blue |
| B+ | green |
| B- | black |

### Stepper motor NEMA23

## Software

## Tracking process
