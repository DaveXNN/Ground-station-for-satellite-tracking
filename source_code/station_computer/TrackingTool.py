import json                                                         # for working with json files
import requests                                                     # for downloading TLE data
import time

from beyond.dates import Date                                       # for Date object from beyond library
from beyond.io.tle import Tle                                       # for Tle object from beyond library
from beyond.frames import create_station                            # for station object from beyond library
from datetime import datetime, timedelta                            # for operations with date and time
from numpy import degrees                                           # for radian-degree conversion
from tkinter import *                                               # tkinter package for GUI
from threading import Thread, Timer                                 # for running more processes in parallel

from Mqtt import Mqtt                                               # for communication with MQTT server


class TrackingTool(Tk):
    def __init__(self, configuration_file):
        super().__init__()
        self.configuration_file = configuration_file                # json configuration file

        # Load program variables from json configuration file
        with open(self.configuration_file) as json_file:            # open configuration file
            conf = json.load(json_file)                             # load content of configuration file
            self.program_name = conf['program_name']                # program name
            self.icon = conf['icon']                                # icon file of the program window
            self.tle_file = conf['tle_file']                        # text file with TLE data
            self.tle_source = conf['tle_source']                    # source of TLE data
            self.station_latitude = conf['station_latitude']        # station latitude
            self.station_longitude = conf['station_longitude']      # station longitude
            self.station_altitude = conf['station_altitude']        # station altitude
            self.last_tle_update = datetime.strptime(conf['last_tle_update'], '%Y-%m-%d %H:%M:%S.%f')  # TLE update
            self.tle_update_period = timedelta(hours=conf['tle_update_period'])     # TLE data update period
            self.min_max = conf['min_max']                          # minimal MAX elevation of a satellite pass
            self.selected_satellites = conf['tracked_satellites']   # list of tracked satellites

        # Initialize basic GUI variables
        self.iconbitmap(self.icon)                                  # program icon
        self.geometry('1200x600')                                   # window dimensions
        self.bg_color = '#daa520'                                   # background color #1d1f1b
        self.text_color = 'black'                                   # text color
        self.configure(bg=self.bg_color)                            # set background color
        self.title(self.program_name)                               # set program title

        # List and string variables definition
        self.satellites = []                                        # list of all satellites on Earth orbit
        self.tracked_satellites = []                                # list of selected satellites
        self.tso = []                                               # list of TrackedSatellite objects
        self.ss0 = StringVar()                                      # text variable for searching in listbox0
        self.ss1 = StringVar()                                      # text variable for searching in listbox1
        self.msv0 = StringVar()                                     # text variable for showing number of all satellites
        self.msv1 = StringVar()                                     # text variable for showing number of s. satellites
        self.msv2 = StringVar()                                     # text variable for showing number of t. satellites
        self.msv3 = StringVar()                                     # text variable for pass predictions
        self.date = StringVar()
        self.aos_time = StringVar()
        self.aos_az = StringVar()
        self.max_time = StringVar()
        self.max_az = StringVar()
        self.max_el = StringVar()
        self.los_time = StringVar()
        self.los_az = StringVar()
        self.duration = StringVar()
        self.utctime = StringVar()
        self.localtime = StringVar()
        self.r_az = StringVar()
        self.r_el = StringVar()
        self.az_offset_var = StringVar()
        self.el_offset_var = StringVar()
        self.r_tracked_satellite = StringVar()
        self.r_time_till_los = StringVar()
        self.r_pol = StringVar()
        self.mqtt_status = StringVar()
        self.first_pass_info = StringVar()
        self.tle_info = StringVar()
        self.msv3.set('First pass prediction:')
        self.r_tracked_satellite.set('none')
        self.r_pol.set('Vertical')
        self.az_offset = Offset(self.az_offset_var)
        self.el_offset = Offset(self.el_offset_var)
        self.track_button_pressed = False                           # True if track button has already been pressed
        self.tracking = False                                       # True if rotator is currently tracking a sat
        self.ts_los_time = datetime.now()

        # Labels definition
        self.main_title = Label(self, text=self.program_name, font='Helvetica 20 bold', bg=self.bg_color,
                                fg=self.text_color)
        self.main_title.place(relx=0.5, rely=0.05, anchor=CENTER)
        self.left_title = Label(self, text='Predicting satellite visibility', font='Helvetica 10 bold',
                                bg=self.bg_color, fg=self.text_color)
        self.left_title.place(relx=0.25, rely=0.10, anchor=CENTER)
        self.right_title = Label(self, text='Rotator information', font='Helvetica 10 bold', bg=self.bg_color,
                                 fg=self.text_color)
        self.right_title.place(relx=0.75, rely=0.10, anchor=CENTER)
        self.ll00 = Label(self, text='Select a satellite by double click and click Predict to predict first pass or Add'
                                     ' to tracking to track it:', bg=self.bg_color, fg=self.text_color)
        self.ll00.place(relx=0.25, rely=0.15, anchor=CENTER)
        self.ll01 = Label(self, textvariable=self.msv0, bg=self.bg_color, fg=self.text_color)
        self.ll01.place(relx=0.125, rely=0.20, anchor=CENTER)
        self.ll02 = Label(self, textvariable=self.msv1, bg=self.bg_color, fg=self.text_color)
        self.ll02.place(relx=0.375, rely=0.20, anchor=CENTER)
        self.ll03 = Label(self, textvariable=self.msv3, bg=self.bg_color, fg=self.text_color)
        self.ll03.place(relx=0.25, rely=0.50, anchor=CENTER)
        self.ll04 = Label(self, text='Date UTC:', bg=self.bg_color, fg=self.text_color)
        self.ll04.place(relx=0.05, rely=0.55, anchor=W)
        self.ll05 = Label(self, text='Acquisition of satellite (AOS):', bg=self.bg_color, fg=self.text_color)
        self.ll05.place(relx=0.05, rely=0.60, anchor=W)
        self.ll06 = Label(self, text='AOS azimuth:', bg=self.bg_color, fg=self.text_color)
        self.ll06.place(relx=0.05, rely=0.65, anchor=W)
        self.ll07 = Label(self, text='Maximum elevation (MAX):', bg=self.bg_color, fg=self.text_color)
        self.ll07.place(relx=0.05, rely=0.70, anchor=W)
        self.ll08 = Label(self, text='MAX azimuth:', bg=self.bg_color, fg=self.text_color)
        self.ll08.place(relx=0.05, rely=0.75, anchor=W)
        self.ll09 = Label(self, text='MAX elevation:', bg=self.bg_color, fg=self.text_color)
        self.ll09.place(relx=0.05, rely=0.80, anchor=W)
        self.ll10 = Label(self, text='Loss of satellite (LOS):', bg=self.bg_color, fg=self.text_color)
        self.ll10.place(relx=0.05, rely=0.85, anchor=W)
        self.ll11 = Label(self, text='LOS azimuth:', bg=self.bg_color, fg=self.text_color)
        self.ll11.place(relx=0.05, rely=0.90, anchor=W)
        self.ll12 = Label(self, text='Duration:', bg=self.bg_color, fg=self.text_color)
        self.ll12.place(relx=0.05, rely=0.95, anchor=W)
        self.rl00 = Label(self, text='Time UTC:', bg=self.bg_color, fg=self.text_color)
        self.rl00.place(relx=0.525, rely=0.15, anchor=W)
        self.rl01 = Label(self, text='Local time:', bg=self.bg_color, fg=self.text_color)
        self.rl01.place(relx=0.775, rely=0.15, anchor=W)
        self.rl02 = Label(self, text='Azimuth (AZ):', bg=self.bg_color, fg=self.text_color)
        self.rl02.place(relx=0.525, rely=0.20, anchor=W)
        self.rl03 = Label(self, text='Elevation (EL):', bg=self.bg_color, fg=self.text_color)
        self.rl03.place(relx=0.775, rely=0.20, anchor=W)
        self.rl04 = Label(self, text='AZ offset:', bg=self.bg_color, fg=self.text_color)
        self.rl04.place(relx=0.525, rely=0.25, anchor=W)
        self.rl05 = Label(self, text='EL offset:', bg=self.bg_color, fg=self.text_color)
        self.rl05.place(relx=0.775, rely=0.25, anchor=W)
        self.rl06 = Label(self, text='Tracked satellite:', bg=self.bg_color, fg=self.text_color)
        self.rl06.place(relx=0.525, rely=0.30, anchor=W)
        self.rl07 = Label(self, text='Time until LOS:', bg=self.bg_color, fg=self.text_color)
        self.rl07.place(relx=0.775, rely=0.30, anchor=W)
        self.rl08 = Label(self, text='Antenna polarization:', bg=self.bg_color, fg=self.text_color)
        self.rl08.place(relx=0.525, rely=0.35, anchor=W)
        self.rl09 = Label(self, text='MQTT status:', bg=self.bg_color, fg=self.text_color)
        self.rl09.place(relx=0.525, rely=0.40, anchor=W)
        self.rl10 = Label(self, textvariable=self.first_pass_info, bg=self.bg_color, fg=self.text_color)
        self.rl10.place(relx=0.750, rely=0.47, anchor=CENTER)
        self.rl11 = Label(self, textvariable=self.msv2, bg=self.bg_color, fg=self.text_color)
        self.rl11.place(relx=0.750, rely=0.52, anchor=CENTER)
        self.rl12 = Label(self, textvariable=self.tle_info, bg=self.bg_color, fg=self.text_color)
        self.rl12.place(relx=0.750, rely=0.95, anchor=CENTER)

        # Entries definition
        self.sat_entry = Entry(textvariable=self.ss0, bg=self.bg_color, fg=self.text_color)
        self.sat_entry.place(relx=0.125, rely=0.40, relwidth=0.2, anchor=CENTER)
        self.sat_entry.bind('<Return>', self.search0)
        self.tsat_entry = Entry(textvariable=self.ss1, bg=self.bg_color, fg=self.text_color)
        self.tsat_entry.place(relx=0.375, rely=0.40, relwidth=0.2, anchor=CENTER)
        self.tsat_entry.bind('<Return>', self.search1)
        self.le0 = Entry(textvariable=self.date, justify=RIGHT, bg=self.bg_color, fg=self.text_color)
        self.le0.place(relx=0.25, rely=0.55, relwidth=0.2, anchor=W)
        self.le1 = Entry(textvariable=self.aos_time, justify=RIGHT, bg=self.bg_color, fg=self.text_color)
        self.le1.place(relx=0.25, rely=0.60, relwidth=0.2, anchor=W)
        self.le2 = Entry(textvariable=self.aos_az, justify=RIGHT, bg=self.bg_color, fg=self.text_color)
        self.le2.place(relx=0.25, rely=0.65, relwidth=0.2, anchor=W)
        self.le3 = Entry(textvariable=self.max_time, justify=RIGHT, bg=self.bg_color, fg=self.text_color)
        self.le3.place(relx=0.25, rely=0.70, relwidth=0.2, anchor=W)
        self.le4 = Entry(textvariable=self.max_az, justify=RIGHT, bg=self.bg_color, fg=self.text_color)
        self.le4.place(relx=0.25, rely=0.75, relwidth=0.2, anchor=W)
        self.le5 = Entry(textvariable=self.max_el, justify=RIGHT, bg=self.bg_color, fg=self.text_color)
        self.le5.place(relx=0.25, rely=0.80, relwidth=0.2, anchor=W)
        self.le6 = Entry(textvariable=self.los_time, justify=RIGHT, bg=self.bg_color, fg=self.text_color)
        self.le6.place(relx=0.25, rely=0.85, relwidth=0.2, anchor=W)
        self.le7 = Entry(textvariable=self.los_az, justify=RIGHT, bg=self.bg_color, fg=self.text_color)
        self.le7.place(relx=0.25, rely=0.90, relwidth=0.2, anchor=W)
        self.le8 = Entry(textvariable=self.duration, justify=RIGHT, bg=self.bg_color, fg=self.text_color)
        self.le8.place(relx=0.25, rely=0.95, relwidth=0.2, anchor=W)
        self.re0 = Entry(textvariable=self.utctime, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re0.place(relx=0.625, rely=0.15, relwidth=0.1, anchor=W)
        self.re1 = Entry(textvariable=self.localtime, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re1.place(relx=0.875, rely=0.15, relwidth=0.1, anchor=W)
        self.re2 = Entry(textvariable=self.r_az, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re2.place(relx=0.625, rely=0.20, relwidth=0.1, anchor=W)
        self.re3 = Entry(textvariable=self.r_el, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re3.place(relx=0.875, rely=0.20, relwidth=0.1, anchor=W)
        self.re4 = Entry(textvariable=self.az_offset_var, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re4.place(relx=0.650, rely=0.25, relwidth=0.05, anchor=W)
        self.re5 = Entry(textvariable=self.el_offset_var, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re5.place(relx=0.900, rely=0.25, relwidth=0.05, anchor=W)
        self.re6 = Entry(textvariable=self.r_tracked_satellite, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re6.place(relx=0.625, rely=0.30, relwidth=0.1, anchor=W)
        self.re7 = Entry(textvariable=self.r_time_till_los, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re7.place(relx=0.875, rely=0.30, relwidth=0.1, anchor=W)
        self.re8 = Entry(textvariable=self.r_pol, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re8.place(relx=0.625, rely=0.35, relwidth=0.1, anchor=W)
        self.re9 = Entry(textvariable=self.mqtt_status, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re9.place(relx=0.625, rely=0.40, relwidth=0.1, anchor=W)

        # Buttons definition
        self.predict_button = Button(self, text='Predict', command=lambda: self.predict(self.sat_entry.get()),
                                     bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.predict_button.place(relx=0.075, rely=0.45, relwidth=0.1, anchor=CENTER)
        self.add_button = Button(self, text='Add to tracking', command=self.add_to_tracked, bg=self.bg_color,
                                 fg=self.text_color, activebackground=self.bg_color)
        self.add_button.place(relx=0.175, rely=0.45, relwidth=0.1, anchor=CENTER)
        self.remove_button = Button(self, text='Remove from tracking', command=self.remove_from_tracked,
                                    bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.remove_button.place(relx=0.325, rely=0.45, relwidth=0.1, anchor=CENTER)
        self.track_button = Button(self, text='Track', command=self.start_tracking,
                                   bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.track_button.place(relx=0.425, rely=0.45, relwidth=0.1, anchor=CENTER)
        self.ver_pol = Button(self, text='Vertical', command=lambda: self.set_polarization('Vertical'),
                              bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.ver_pol.place(relx=0.775, rely=0.35, relwidth=0.05, anchor=W)
        self.hor_pol = Button(self, text='Horizontal', command=lambda: self.set_polarization('Horizontal'),
                              bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.hor_pol.place(relx=0.825, rely=0.35, relwidth=0.05, anchor=W)
        self.lhcp_pol = Button(self, text='LHCP', command=lambda: self.set_polarization('LHCP'),
                               bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.lhcp_pol.place(relx=0.875, rely=0.35, relwidth=0.05, anchor=W)
        self.rhcp_pol = Button(self, text='RHCP', command=lambda: self.set_polarization('RHCP'),
                               bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.rhcp_pol.place(relx=0.925, rely=0.35, relwidth=0.05, anchor=W)
        self.shutdown_button = Button(self, text='Shut down rotator',
                                      command=lambda: mqtt.publish_action('shutdown'), bg=self.bg_color,
                                      fg=self.text_color, activebackground=self.bg_color)
        self.shutdown_button.place(relx=0.775, rely=0.40, relwidth=0.1, anchor=W)
        self.close_button = Button(self, text='Close program', command=self.close_window,
                                   bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.close_button.place(relx=0.875, rely=0.40, relwidth=0.1, anchor=W)
        self.az_inc_button = Button(self, text='+', command=self.az_increase_offset,
                                    bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.az_inc_button.place(relx=0.625, rely=0.25, relwidth=0.025, anchor=W)
        self.az_dec_button = Button(self, text='-', command=self.az_decrease_offset,
                                    bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.az_dec_button.place(relx=0.700, rely=0.25, relwidth=0.025, anchor=W)
        self.el_inc_button = Button(self, text='+', command=self.el_increase_offset,
                                    bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.el_inc_button.place(relx=0.875, rely=0.25, relwidth=0.025, anchor=W)
        self.el_dec_button = Button(self, text='-', command=self.el_decrease_offset,
                                    bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.el_dec_button.place(relx=0.950, rely=0.25, relwidth=0.025, anchor=W)

        # Listbox definition
        self.listbox0 = Listbox(self, bg=self.bg_color, fg=self.text_color, borderwidth=0, highlightbackground='black')
        self.listbox0.place(relx=0.125, rely=0.30, relwidth=0.2, relheight=0.15, anchor=CENTER)
        self.listbox0.bind('<Double-1>', self.go0)
        self.listbox1 = Listbox(self, bg=self.bg_color, fg=self.text_color, borderwidth=0, highlightbackground='black')
        self.listbox1.place(relx=0.375, rely=0.30, relwidth=0.2, relheight=0.15, anchor=CENTER)
        self.listbox1.bind('<Double-1>', self.go1)
        self.listbox2 = Listbox(self, bg=self.bg_color, fg=self.text_color, borderwidth=0, highlightbackground='black')
        self.listbox2.place(relx=0.75, rely=0.55, relwidth=0.2, relheight=0.35, anchor=N)
        self.listbox2.bind('<Double-1>', self.go2)

        # run basic functions
        self.update_r_info()
        self.listbox_init()
        update_time = datetime.utcnow() - self.last_tle_update
        if update_time > self.tle_update_period:
            self.update_tle()
        else:
            self.tle_info.set(f'Last TLE update: {self.last_tle_update.strftime("%d %B %Y %H:%M:%S UTC")}')
            self.t_update = Timer(update_time.total_seconds(), self.update_tle)
            self.t_update.start()

    @staticmethod
    def fill_listbox(listbox, content):                             # fill listbox with all satellite names
        listbox.delete(0, END)
        for item in content:
            listbox.insert(END, item)

    @staticmethod
    def timedelta_formatter(td):                                    # function that returns timedelta in format %H %M %S
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))

    def create_stat(self):                                          # create station object
        return create_station(str(datetime.utcnow()),
                              (self.station_latitude, self.station_longitude, self.station_altitude))

    def find_tle(self, sat_name):                                   # create TLE object for a satellite
        with open(self.tle_file, 'r') as file:                      # open TLE text file
            lines = file.readlines()
            for line in lines:
                if sat_name in line:
                    line_number = lines.index(line)
                    return Tle(lines[line_number + 1] + lines[line_number + 2])

    def az_increase_offset(self):
        self.az_offset.increase()
        mqtt.publish_az_offset(f'{self.az_offset.offset}')

    def az_decrease_offset(self):
        self.az_offset.decrease()
        mqtt.publish_az_offset(f'{self.az_offset.offset}')

    def el_increase_offset(self):
        self.el_offset.increase()
        mqtt.publish_el_offset(f'{self.el_offset.offset}')

    def el_decrease_offset(self):
        self.el_offset.decrease()
        mqtt.publish_el_offset(f'{self.el_offset.offset}')

    def set_polarization(self, pol):                                # sets antenna polarization
        self.r_pol.set(pol)
        mqtt.publish_polarization(pol)

    def start_tracking(self):
        self.tracking_thread = Thread(target=self.track_sats)
        self.tracking_thread.start()

    def update_r_info(self):                                        # display rotator information
        self.utctime.set(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
        self.localtime.set(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.r_az.set(mqtt.az)
        self.r_el.set(mqtt.el)
        if self.tracking:
            self.r_time_till_los.set(self.timedelta_formatter(self.ts_los_time - datetime.utcnow()))
        else:
            self.r_time_till_los.set('')
        if mqtt.connected:
            self.mqtt_status.set('connected')
        else:
            self.mqtt_status.set('disconnected')
        self.after(1000, self.update_r_info)

    def listbox_init(self):
        with open(self.tle_file, 'r') as file:
            self.satellites = sorted(list(map(str.strip, file.readlines()[::3])))
        self.update_listbox0()
        self.update_listbox1()
        self.update_listbox2()

    def go0(self, event):
        cs = self.listbox0.curselection()
        self.ss0.set(self.listbox0.get(cs))
        self.ss1.set('')

    def go1(self, event):
        cs = self.listbox1.curselection()
        self.ss0.set(self.listbox1.get(cs))
        self.ss1.set(self.listbox1.get(cs))

    def go2(self, event):
        cs = self.listbox2.curselection()
        self.ss0.set(self.listbox2.get(cs))
        self.ss1.set(self.listbox2.get(cs))

    def search0(self, event):                                       # fill listbox0 with filtered satellite names
        word = self.ss0.get()
        self.listbox0.delete(0, END)
        if word == '':
            self.fill_listbox(self.listbox0, self.satellites)
            return
        filtered_data = list()
        for item in self.satellites:
            if item.find(word) >= 0:
                filtered_data.append(item)
        self.fill_listbox(self.listbox0, filtered_data)

    def search1(self, event):                                       # fill listbox1 with filtered satellite names
        word = self.ss1.get()
        self.listbox1.delete(0, END)
        if word == '':
            self.fill_listbox(self.listbox1, self.selected_satellites)
            return
        filtered_data = list()
        for item in self.selected_satellites:
            if item.find(word) >= 0:
                filtered_data.append(item)
        self.fill_listbox(self.listbox1, filtered_data)

    def add_to_tracked(self):                                       # add satellite to tracking
        sat = self.sat_entry.get()
        if sat in self.satellites and sat not in self.selected_satellites:
            self.selected_satellites.append(sat)
        self.update_listbox1()
        self.ss0.set('')

    def remove_from_tracked(self):                                  # remove satellite from tracking
        sat = self.tsat_entry.get()
        if sat in self.selected_satellites:
            self.selected_satellites.remove(sat)
        self.update_listbox1()
        self.ss1.set('')

    def track_sats(self):                                           # track all satellites in track_satellites list
        if not self.track_button_pressed:
            self.track_button_pressed = True
            self.tracked_satellites = sorted(self.selected_satellites)
            self.update_listbox2()
            with open(self.configuration_file, 'r') as g:
                content = json.load(g)
                content['tracked_satellites'] = self.tracked_satellites
            with open(self.configuration_file, 'w') as h:
                json.dump(content, h, indent=4)
            self.tso = [TrackedSatellite(sat) for sat in self.tracked_satellites]
            self.find_first_pass()

    def find_first_pass(self):
        if len(self.tso) > 1:
            my_dict = {}
            for x in self.tso:
                my_dict[x.name] = x.aos_time
            sorted_list = sorted(my_dict.items(), key=lambda p: p[1], reverse=False)
            first_pass = list(sorted_list[0])
            first_sat = first_pass[0]
            if first_sat == self.r_tracked_satellite.get():
                first_pass = list(sorted_list[1])
                first_sat = first_pass[0]
            first_pass_time = first_pass[1].strftime('%d %B %Y %H:%M:%S UTC')
            for x in self.tso:
                if x.name == first_sat:
                    self.first_pass_info.set(f'Next pass: {first_sat}, AOS: {first_pass_time}, MAX: {x.max_el}')
                    self.predict(first_sat)

    def update_listbox0(self):
        self.fill_listbox(self.listbox0, self.satellites)
        self.msv0.set(f'All satellites ({len(self.satellites)}): ')

    def update_listbox1(self):
        self.fill_listbox(self.listbox1, sorted(self.selected_satellites))
        self.msv1.set(f'Selected satellites ({len(self.selected_satellites)}): ')

    def update_listbox2(self):
        self.fill_listbox(self.listbox2, self.tracked_satellites)
        self.msv2.set(f'Tracked satellites ({len(self.tracked_satellites)}): ')

    def predict(self, sat):                                         # create data about the pass of selected satellite
        if sat in self.satellites:
            if sat in self.tracked_satellites:
                for x in self.tso:
                    if x.name == sat:
                        self.show_pred_data(x.name, x.aos_time, x.max_time, x.los_time, x.aos_az, x.max_az, x.los_az,
                                            x.max_el)
            else:
                for orb in station.visibility(self.find_tle(sat).orbit(), start=Date.now(), stop=timedelta(hours=24),
                                              step=timedelta(seconds=100), events=True):
                    if orb.event and orb.event.info.startswith('AOS'):
                        aos_time = orb.date
                        aos_az = degrees(-orb.theta) % 360
                    if orb.event and orb.event.info.startswith('MAX'):
                        max_time = orb.date
                        max_az = degrees(-orb.theta) % 360
                        max_el = degrees(orb.phi)
                    if orb.event and orb.event.info.startswith('LOS'):
                        los_time = orb.date
                        los_az = degrees(-orb.theta) % 360
                        break
                try:
                    self.show_pred_data(sat, aos_time, max_time, los_time, aos_az, max_az, los_az, max_el)
                except NameError:
                    self.msv3.set(f'Sorry, could not predict {sat}.')
                    self.empty_pred_data()
        else:
            self.msv3.set(f'Sorry, {sat} is not a satellite in orbit.')

    def show_pred_data(self, sat, aos_time, max_time, los_time, aos_az, max_az, los_az, max_el):
        self.msv3.set(f'First pass prediction for {sat}: ')
        self.date.set(aos_time.strftime('%d %B %Y'))
        self.aos_time.set(aos_time.strftime('%H:%M:%S'))
        self.aos_az.set(f'{aos_az:.2f}')
        self.max_time.set(max_time.strftime('%H:%M:%S'))
        self.max_az.set(f'{max_az:.2f}')
        self.max_el.set(f'{max_el:.2f}')
        self.los_time.set(los_time.strftime('%H:%M:%S'))
        self.los_az.set(f'{los_az:.2f}')
        self.duration.set(self.timedelta_formatter(los_time - aos_time))

    def empty_pred_data(self):
        self.msv3.set('First pass prediction')
        self.date.set('')
        self.aos_time.set('')
        self.aos_az.set('')
        self.max_time.set('')
        self.max_az.set('')
        self.max_el.set('')
        self.los_time.set('')
        self.los_az.set('')
        self.duration.set('')

    def update_tle(self):                                           # update tle data (if it is older than 2 hours)
        try:
            response = requests.get(self.tle_source)
            if response.ok:
                self.last_tle_update = datetime.utcnow()
                with open(self.tle_file, 'wb') as f:
                    f.write(response.content)
                with open(self.configuration_file, 'r') as g:
                    content = json.load(g)
                    content['last_tle_update'] = str(self.last_tle_update)
                with open(self.configuration_file, 'w') as h:
                    json.dump(content, h, indent=4)
                self.tle_info.set(f'Last TLE update: {self.last_tle_update.strftime("%d %B %Y %H:%M:%S UTC")}')
        except requests.exceptions.ConnectionError:
            self.tle_info.set(f'Last TLE update: {self.last_tle_update.strftime("%d %B %Y %H:%M:%S UTC")} '
                              f'(Could not download the newest version)')
        self.t_update = Timer(self.tle_update_period.total_seconds(), self.update_tle)
        self.t_update.start()

    def close_window(self):
        mqtt.enabled = False
        try:
            mqtt.connect_thread.cancel()
        except AttributeError:
            pass
        try:
            self.tracking_thread.join()
        except AttributeError:
            pass
        self.t_update.cancel()
        for x in self.tso:
            try:
                x.create_data_thread.join()
            except AttributeError:
                pass
            try:
                x.tracking_thread.cancel()
            except AttributeError:
                pass
        self.destroy()


class Offset:
    def __init__(self, string_var):
        self.string_var = string_var
        self.offset = 0.0
        self.offset_step = 0.2
        self.publish()

    def increase(self):
        if mqtt.connected:
            self.offset += self.offset_step
            self.publish()

    def decrease(self):
        if mqtt.connected:
            self.offset -= self.offset_step
            self.publish()

    def publish(self):
        self.offset = round(self.offset, 2)
        self.string_var.set(f'{self.offset}')


class TrackedSatellite:
    def __init__(self, name):
        self.name = name                                            # satellite name
        self.times, self.azims, self.elevs = [], [], []             # list of azims and elevs in time during the pass
        self.aos_time = datetime.now()                              # AOS time of the first pass
        self.max_time = datetime.now()                              # MAX time of the first pass
        self.los_time = datetime.now()                              # LOS time of the first pass
        self.aos_az = 0                                             # AOS azimuth
        self.max_az = 0                                             # MAX azimuth
        self.los_az = 0                                             # LOS azimuth
        self.max_el = 0                                             # MAX elevation
        self.delay = 0                                              # delay for creating data
        self.start_time_seconds = 0                                 # time in seconds until AOS
        self.delay_before_tracking = timedelta(seconds=10)          # time needed for rotator to turn to AOS azimuth
        self.tle = app.find_tle(name)                               # TLE data of the satellite
        self.create_data_thread = Thread(self.create_data(delay=0))     # thread for creating data
        self.create_data_thread.start()                             # start create data thread

    def print_info(self, msg):                                      # print info with satellite name and timestamp
        print(f'{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}, {self.name} {msg}')

    def create_data(self, delay):                                   # create data about the first pass of satellite
        self.delay = delay
        self.times.clear()                                          # clear the previous data
        self.azims.clear()
        self.elevs.clear()
        for orb in station.visibility(self.tle.orbit(), start=Date.now() + timedelta(seconds=delay),
                                      stop=timedelta(hours=24), step=timedelta(seconds=10), events=True):
            self.times.append(datetime.strptime(str(orb.date), '%Y-%m-%dT%H:%M:%S.%f UTC'))
            self.azims.append(degrees(-orb.theta) % 360)
            self.elevs.append(degrees(orb.phi))
            if orb.event and orb.event.info.startswith('AOS'):
                self.aos_time = datetime.strptime(str(orb.date), '%Y-%m-%dT%H:%M:%S.%f UTC')
                self.aos_az = degrees(-orb.theta) % 360
            if orb.event and orb.event.info.startswith('MAX'):
                self.max_time = datetime.strptime(str(orb.date), '%Y-%m-%dT%H:%M:%S.%f UTC')
                self.max_az = degrees(-orb.theta) % 360
                self.max_el = degrees(orb.phi)
            if orb.event and orb.event.info.startswith('LOS'):
                self.los_time = datetime.strptime(str(orb.date), '%Y-%m-%dT%H:%M:%S.%f UTC')
                self.los_az = degrees(-orb.theta) % 360
                self.start_time_seconds = (self.aos_time-datetime.utcnow()-self.delay_before_tracking).seconds
                if self.max_el > app.min_max and self.elevs[0] < 0.1:
                    self.delay = 0
                    self.tracking_thread = Timer(self.start_time_seconds, self.track)
                    self.tracking_thread.start()
                    self.print_info(f'created data, AOS: {self.aos_time}, MAX elevation: {self.max_el}')
                else:
                    self.create_data_thread = Thread(self.create_data(delay=self.delay + 20000))
                    self.create_data_thread.start()
                break

    def track(self):                                                # track the satellite when crossing the sky
        if not app.tracking:                                        # if any other satellite is not tracked right now
            if self.aos_time > datetime.utcnow():
                app.tracking = True
                app.r_tracked_satellite.set(self.name)
                app.ts_los_time = self.los_time
                mqtt.publish_action('start')
                app.predict(self.name)
                time.sleep(0.1)
                wait_time = (self.aos_time - datetime.utcnow()).total_seconds()
                self.print_info(f'will fly over your head in {int(wait_time)} seconds')
                mqtt.publish_start_azimuth(self.aos_az)
                time.sleep(wait_time)
                self.print_info('tracking started')
                for x in range(len(self.times) - 1):
                    delta_t = (self.times[x + 1] - self.times[x]).total_seconds()
                    delta_az = self.azims[x + 1] - self.azims[x]
                    delta_el = self.elevs[x + 1] - self.elevs[x]
                    if delta_az > 180:
                        delta_az -= 360
                    if delta_az < -180:
                        delta_az += 360
                    mqtt.publish_data(delta_t, delta_az, delta_el)
                    time.sleep(delta_t)
                mqtt.publish_action('stop')
                self.print_info('tracking ended')
                app.r_tracked_satellite.set('none')
                app.find_first_pass()
                app.tracking = False
            else:
                self.print_info('tracking passed')
        else:
            self.print_info(f'cannot be tracked now, because {app.r_tracked_satellite.get()} is being tracked')
        self.create_data_thread = Thread(self.create_data(delay=2000))
        self.create_data_thread.start()


if __name__ == '__main__':
    mqtt = Mqtt()                                                   # Mqtt object for communicating with rotator
    app = TrackingTool('configuration.json')                        # GUI object
    station = app.create_stat()                                     # ground station object
    app.mainloop()
