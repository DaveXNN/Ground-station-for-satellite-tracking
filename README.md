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

## Hardware

The whole rotator is controlled by compter [Raspberry Pi 4](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/) via digital GPIO pins. Raspberry Pi is connected with two stepper motors, two rotary encoders and a magnetometer.

### Electronic components description

### List of components

| Name  | Quantity | Link |
| :--- | :---: | :---: |
| Raspberry Pi 4B  | 1  | https://www.raspberrypi.com/products/raspberry-pi-4-model-b/ |
| Stepper motor NEMA17  | 1 |

- Raspberry Pi 4B
- 2x stepper motor NEMA17 1,1 Nm
- 2x stepper motor driver TB6600
- 2x rotary encoder
- magnetometer HMC5883L

## Software

## Tracking process
