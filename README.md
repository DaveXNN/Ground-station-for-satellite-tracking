# Ground station for satellite tracking
This repository contains a description of the project Ground station for satellite tracking. The goal of this project was to build a ground satellite station that is able to receive signals from satellites operating at VHF (Very High Frequency) and UHF (Ultra High Frequency). The ground station constists of rotator, antennas, polarization switcher, receiver and station computer (laptop). Each part is describet in separate chapter.

## Rotator
Unfortunately, a lot of these satellites are situated on the LEO (Low Earth Orbit), in other words below the altitude of 2 000 km. It means that the satellite changes its position very quickly and it's very uncomfortable to change antennas' direction manually, because it may cause a loss of the satellite signal. A rotator is a good solution of this problem, because this device moves the antennas automatically with very high precision.

Of course there are many proffesional rotators available to buy in the internet e.g. Yaesu, but i decided to build a similar rotator by myself, because it's cheaper option and I really wanted to get into this field of problems.

Each satellite has data about its position in the Earth orbit called TLE (Two-Line Element). They are updated every 2 hours from URL: https://celestrak.org/NORAD/elements/gp.php?GROUP=ACTIVE&FORMAT=tle. This rotator uses the latest TLE data to predict satellite visibility in a specific location on the Earth. For satellite visibility prediction is used python beyond library (https://pypi.org/project/beyond/). Here is an example of TLE for the International Space Station or Czech satellite Planetum-1:

```
ISS (ZARYA)             
1 25544U 98067A   23216.30597424  .00016406  00000+0  29387-3 0  9996
2 25544  51.6415  90.1197 0000976 153.7733 359.7746 15.50094272409258

PLANETUM1               
1 52738U 22057G   24218.26634944  .00072435  00000+0  14435-2 0  9995
2 52738  97.5700 346.3663 0004271 318.8227  41.2700 15.46625200122146
```

If we have the latest TLE data, we can track each satellite in the Earth orbit. This rotator is designed primarily for tracking satellites in the low Earth orbit (LEO), it means below an altitude of 2 000 km.

For the next sections we need to define two important variables - azimuth and elevation of a satellite. Azimuth and Elevation are measures used to identify the position of a satellite flying overhead. Azimuth tells you what direction to face and elevation tells you how high up in the sky to look. Both are measured in degrees. Azimuth varies from 0° to 360° and elevation from 0° to 90°.

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

## Antennas

## Polarization switchers

## Receiver and station computer
