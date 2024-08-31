# Ground station for satellite tracking
This repository contains a description of the project Ground station for satellite tracking. The goal of this project was to build a ground satellite station that is able to receive signals from satellites operating at VHF (Very High Frequency) and UHF (Ultra High Frequency). The ground station constists of rotator, antennas, polarization switcher, receiver and station computer (laptop). Each part is describet in separate chapter.

![](/images/rotator-outside.png)

## Rotator
Unfortunately, a lot of these satellites are situated on the LEO (Low Earth Orbit), in other words below the altitude of 2 000 km. It means that the satellite changes its position very quickly and it's very uncomfortable to change antennas' direction manually, because it may cause a loss of the satellite signal. A rotator is a good solution of this problem, because this device moves the antennas automatically with very high precision.

### Design
Of course there are many proffesional rotators available to buy in the internet e.g. Yaesu, but i decided to build a similar rotator by myself, because it's cheaper option and I really wanted to get into this field of problems. I've got an inspiration from [SatNOGS Rotator v3](https://wiki.satnogs.org/SatNOGS_Rotator_v3).

The rotator frame is made from aluminium and wood and has dimensions of 240x240x305 mm. There are also 4 bearings installed, 2 to hold azimuth rod and 2 to hold elevation rod. It's also designed to mantle and dismantle easily, so each of the rods can be installed or removed quickly. Spur gears are used to make the rods to move. They are available with all 3D-printed parts in [this repository](/stl-files/rotator).

### Electronic components

The device is supplied by 45 W laptop charger providing 20 V voltage. This voltage is used to supply stepper motors, but it's also reduced into 5 V using step-down voltage regulator to supply control unit and polarization switchers. The control unit of the rotator is computer [Raspberry Pi 4](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/) with its digital GPIO pins. Raspberry Pi controls two stepper motor drivers TB6600 and two polarization switchers described in chapter 3. The device is designed to require as few cables as possible so the communication between the rotator and station computer runs through WiFi.

Here is a list of electronic components:

| Name  | Quantity | Link |
| :--- | :---: | :---: |
| Raspberry Pi 4B  | 1  | https://www.raspberrypi.com/products/raspberry-pi-4-model-b/ |
| Step-Down Voltage Regulator LM2596 | 1 | https://www.laskakit.cz/step-down-menic-s-lm2596/ |
| Stepper motor NEMA23  | 2 | https://www.laskakit.cz/krokovy-motor-nema-23-57hs5630a4d8-1-1nm/ |
| Driver TB6600  | 2 | https://www.laskakit.cz/driver-tb6600--tb67s109aftg--pro-krokove-motory-3a-47v/ |
| Laptop charger 45 W | 1  |  |

#### Raspberry Pi 4B
The next picture depicts Raspberry Pi 4B pinout:

![Raspberry Pi 4 pinout (www.theengineeringprojects.com)](/images/raspberrypi-pinout.png)

In the next table you can see Raspberry Pi digital pins and their usage:

| Name | Pin number | GPIO code | Connected device | Description |
| :--- | :---: | :---: | :---: | :---: |
| VCC | 17 | 3V3 | Azimuth/elevation stepper motor driver | provides 3.3 V for controling drivers |
| az.ENA | 19 | GPIO10 | Azimuth stepper motor driver | enables stepper motor to move |
| az.DIR | 21 | GPIO9 | Azimuth stepper motor driver | sets rotation direction |
| az.PUL | 23 | GPIO11 | Azimuth stepper motor driver | used to do 1 single step |
| el.ENA | 11 | GPIO17 | Elevation stepper motor driver | enables stepper motor to move |
| el.DIR | 13 | GPIO27 | Elevation stepper motor driver | sets rotation direction |
| el.PUL | 15 | GPIO22 | Elevation stepper motor driver | used to do 1 single step |
| pol_sw.UHF_REL1 | 27 | GPIO0 | UHF polarization switcher | controls relay 1 |
| pol_sw.UHF_REL2 | 29 | GPIO5 | UHF polarization switcher | controls relay 2 |
| pol_sw.VHF_REL1 | 31 | GPIO6 | VHF polarization switcher | controls relay 1 |
| pol_sw.VHF_REL2 | 33 | GPIO13 | VHF polarization switcher | controls relay 2 |

#### Driver TB6600 (2x)
Driver TB6600 is supposed to control a stepper motor with a power supply 20 V. It has three inputs for controling stepper motor - ENA (enable), DIR (direction) and PUL (pulse) and for outputs A+, A-, B+, B-. Here is a list of all inputs and outputs of one stepper motor driver:

| Name | I/O | Connected device| Cable color | Voltage |
| :--- | :---: | :---: | :---: | :---: |
| ENA- | input | Raspberry Pi | green | 0/3.3 V |
| ENA+ | input | Raspberry Pi | red | 3.3 V |
| DIR- | input | Raspberry Pi | yellow | 0/3.3 V |
| DIR+ | input | Raspberry Pi | red | 3.3 V |
| PUL- | input | Raspberry Pi | orange | 0/3.3 V |
| PUL+ | input | Raspberry Pi | red | 3.3 V |
| B- | output | stepper motor | black | 0-20 V |
| B+ | output | stepper motor | green | 0-20 V |
| A- | output | stepper motor | blue | 0-20 V |
| A+ | output | stepper motor | red | 0-20 V |
| GND | input | Laptop charger | black | 0 V |
| VCC | input | Laptop charger | white | 20 V |

Each of the drivers also has six switches to set up peak current and microstep. Peak current is set to 0,7 V and microstep to level 4, it means that the position of the switches is: S1-ON, S2-OFF, S3-OFF, S4-ON, S5-ON, S6-ON.

![](/images/driver.jpg)

#### Stepper motor NEMA23 (2x)
NEMA23 is a high torque stepper motor with torque over 1,8 Nm and step angle 1,8°. It's connected with 4 wires (black, green, blue, red) to the driver. Stepper motors move the rotator via spur gears. In the next picture you can see spur gears for azimuth and elevation control.

![](/images/spurgear_azimuth.jpg)
![](/images/spurgear_elevation.jpg)

### Software
Rotator receives commands via MQTT client and then moves stepper motors or changes antenna polarization. It's programmed in Python 3.9 and you can find the source code in [this repository](/source_code/rotator).

To install MQTT broker on Raspberry Pi I used a command ```sudo apt install -y mosquitto mosquitto-clients```

and to make Mosquitto auto start when the Raspberry Pi boots I used a command ```sudo systemctl enable mosquitto.service```.

[Rotator.py](/source_code/rotator/Rotator.py) is a main script that is run on boot. It initializes all modules and subscribes topics used to control rotator. There is also module [Stepper.py](/source_code/rotator/Stepper.py) to control stepper motors, module [PolarizationSwitcher.py](/source_code/rotator/PolarizationSwitcher.py) to control polarazation switchers and module [Publisher.py](/source_code/rotator/Publisher.py) to send rotator current azimuth and elevation back to station computer.

Here is a list of used Python packages:
* [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) - controling digital pins
* [paho-mqtt](https://pypi.org/project/paho-mqtt/) - communicating with MQTT broker
* [threading](https://docs.python.org/3/library/threading.html) - running functions in parallel
* [time](https://docs.python.org/3/library/time.html) - time acces and conversions

For running script on boot of Raspberry Pi, I modified file ```/etc/rc.local``` by adding a line ```python3 /home/rotator/Rotator.py```, so the final file looks like this:
```
#!/bin/sh -e
#
# rc.local
#
# This script is executed at the end of each multiuser runlevel.
# Make sure that the script will "exit 0" on success or any other
# value on error.
#
# In order to enable or disable this script just change the execution
# bits.
#
# By default this script does nothing.

# Print the IP address
_IP=$(hostname -I) || true
if [ "$_IP" ]; then
  printf "My IP address is %s\n" "$_IP"
fi

python3 /home/rotator/Rotator.py &

exit 0
```

## Yagi antennas
The rotator has two arms equiped with cross-Yagi antennas for VHF and UHF. The VHF Yagi antenna is designed for frequency 145 MHz and the UHF Yagi antenna is designed for 435 MHz. The antennas are made from aluminium. For boom is made from 20 mm square rod and the elements are made from 6 mm circle rod.

The cross-Yagi antennas consist of two antennas on the same boom. The are rotated by 45 degrees and the shift between them is one fourth of the wavelangth ($\lambda/4$).

### VHF Yagi antenna (145 MHz)
The VHF Yagi antenna has 4 elements - reflector, radiator and 2 directors. The frequency 145 MHz corresponds with the wavelenth 2068 mm. All of the elements are described in the table below:

| Element | Length (mm) | Boom position (mm) | Gain (dBd) | Gain (dBi) |
| :--- | :---: | :---: | :---: | :---: |
| reflector | 1019.4 | 30 | - | - |
| radiator | 983.7 | 444 | - | - |
| director 1 | 946.1 | 598.6 | 4.8 | 6.9 |
| director 2 | 937.9 | 970.7 | 6.5 | 8.6 |

### UHF Yagi antenna (435 MHz)
The UHF Yagi antenna has 9 elements - reflector, radiator and 7 directors. The frequency 435 MHz corresponds with the wavelenth 689 mm. All of the elements are described in the table below:

| Element | Length (mm) | Boom position (mm) | Gain (dBd) | Gain (dBi) |
| :--- | :---: | :---: | :---: | :---: |
| reflector | 348.9 | 30 | - | - |
| radiator | 323.8 | 168 | - | - |
| director 1 | 313.5 | 219.5 | 4.8 | 6.9 |
| director 2 | 310.2 | 343.6 | 6.5 | 8.6 |
| director 3 | 307.1 | 491.7 | 7.8 | 9.9 |
| director 4 | 304.2 | 664.0 | 8.9 | 11.0 |
| director 5 | 301.6 | 857.0 | 9.8 | 11.9 |
| director 6 | 299.1 | 1063.8 | 10.5 | 12.7 |
| director 7 | 296.8 | 1280.9 | 11.2 | 13.3 |

## Polarization switchers
To change antenna polarization I built a polarization switcher. It is a device that is between antenna and receiver and can change the polarization between vertical, horizontal, right-handed circular polarization (RHCP) and left-handed circular polarization (LHCP). The device consists of two relays, that switch between two lenghts of coaxial cable, so they can shift the phase of comming signal from both antennas. VHF and UHF polarization switchers have different lenght of the cables because they are operating on different frequencies. The polarization switcher is inserted into a 3d-printed box and its STL model is located [here](/stl-files/polarization_switcher/polarization_switcher.stl).

## Receiver
Receiver [Airspy Mini](https://airspy.com/airspy-mini/) is used here.

![Airspy Mini](/images/airspy_mini.jpg)

## Station computer software
Station computer (laptop) has a program called Satellite Tracking Software developed in Python 3.10. Source code is available [here](/source_code/station_computer). The program has a graphical user interface (GUI) and is used for predicting satellite visibility and controlling rotator. The program configuration is in a json file [configuration.json](/source_code/station_computer/configuration.json).

Within starting the program, the latest Two-line element (TLE) data are downloaded from [CelesTrak](https://celestrak.org/NORAD/elements/gp.php?GROUP=ACTIVE&FORMAT=tle). The data are updated every 2 hours, because it is the same period as CelesTrak uses for publishing the newest version of TLE. It is necessary to use the latest data for predicting satellite visibility, because when it's too old, the program may calculate the satellite position badly and the rotator won't be able to track the satellite correctly. Here is an example of TLE for the International Space Station or Czech satellite Planetum-1 from 31/8/2024:

```
ISS (ZARYA)             
1 25544U 98067A   24243.69891984  .00053939  00000+0  97276-3 0  9991
2 25544  51.6407 306.1908 0011145 301.8729 210.3060 15.49164437470102

PLANETUM1               
1 52738U 22057G   24244.10463033  .00126959  00000+0  21033-2 0  9999
2 52738  97.5706  13.4568 0006175 242.8845 117.1778 15.51691004126148
```

A text file tle_active.txt contains TLE of all active satellites on the Earth's orbit. The list of all these satellite is displayed in GUI on the left hand side in listbox All satellites. Next to the All satellites listbox there is another listbox called Selected satellites, which shows all satellites selected for tracking using buttons Add to tracking and Remove from tracking. The default screen looks like this:

![](/images/satellite_tracking_software-default.png)

You can select any of the satellites in All satellites listbox and predict its visibility. Information about the pass will be shown below in the table. Here is an example predict for the International Space Station (ISS):

![](/images/satellite_tracking_software-predicting.png)

The pass prediction consists of:
* Aquistition of the satellite (AOS) - time of the beginning of a pass
* AOS azimuth
* Maximum elevation (MAX) - time of the maximum elevation of a pass
* MAX azimuth
* MAX elevation
* Loss of the satellite (LOS) - time of the end of a pass
* LOS azimuth
* Duration - duration of the pass

On the left hand side, there is a rotator information section. When the rotator is turned of, its current azimuth and elevation is displayed here. While tracking, you can see name of tracked satellite and its time until LOS. You can also change antennas polarization by clicking on one of the buttons - Vertical, Horizontal, RHCP or LHCP. The current polarization is also shown here. Below the table, there is information about the next pass and listbox of satellite currently selected for tracking. On to bottom of the column there is a time of the latest TLE update. Here is the GUI while tracking satellite [Planetum-1](https://db.satnogs.org/satellite/CBUM-7092-9005-4302-8636).

![](/images/satellite_tracking_software-screenshot1.png)

Here is a list of used Python packages:
* [beyond](https://pypi.org/project/beyond/) - predicting satellite visibility
* [datetime](https://docs.python.org/3/library/datetime.html) - operations with date and time
* [json](https://docs.python.org/3/library/json.html) - coding and decoding json files
* [numpy](https://numpy.org/) - math operations
* [requests](https://pypi.org/project/requests/) - downloading TLE
* [socket](https://docs.python.org/3/library/socket.html) - MQTT connection errors
* [paho-mqtt](https://pypi.org/project/paho-mqtt/) - communicating with MQTT broker
* [threading](https://docs.python.org/3/library/threading.html) - running functions in parallel
* [tkinter](https://docs.python.org/3/library/tkinter.html) - creating GUI
* [time](https://docs.python.org/3/library/time.html) - time acces and conversions

## Functionality
In the beginning you select all satellites you want to track in the GUI. Then you click on the Predict button and the program calculates the first passes of selected satellites that is above minimum elevation set in [configuration.json](/source_code/station_computer/configuration.json). When any of the selected satellites appears above the horizon, station computer sends AOS azimuth to the rotator and the rotator moves to that azimuth. Then the station computer begins to send azimuth and elevation changes of satellite position in time. When the tracking is finished, the rotator returns to its default position (AZ: 0, EL: 0) and waits for another passing selected satellite to track.

## Experience with satellite tracking

![](/images/sdr_sharp00.png)
![](/images/sdr_sharp01.png)
![](/images/sdr_angel00.png)


