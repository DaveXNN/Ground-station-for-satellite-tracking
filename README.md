# Antenna rotator for satellite tracking
This repository contains Antenna rotator for satellite tracking project description. The goal of this project was to design a homemade antenna rotator for tracking any of the satellites in the Earth orbit. The rotator is controlled from a laptop via WiFi. The rotator controll unit is Raspberry Pi 4B with installed Mosquitto broker for subscribing data about satellites from the laptop. Raspberry Pi then controls stepper motors to turn two Yagi antennas into the right direction to the passing satellite. The source code on laptop and on Raspberry Pi is writen in Python 3.9.

## Introduction

Each satellite has data about its position in the Earth orbit called TLE (Two-Line Element). They are updated every 2 hours on URL: https://celestrak.org/NORAD/elements/gp.php?GROUP=ACTIVE&FORMAT=tle. This rotator uses the latest TLE data to predict satellite visibility in a specific location on the Earth. For satellite visibility prediction is used python beyond library (https://pypi.org/project/beyond/). 

## Hardware

## Software

## Tracking process
