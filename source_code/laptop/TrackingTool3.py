import requests                                                     # for downloading TLE data
import sched
import time

from beyond.dates import Date                                       # for Date object from beyond library
from beyond.io.tle import Tle                                       # for Tle object from beyond library
from beyond.frames import create_station                            # for station object from beyond library
from datetime import datetime, timedelta                            # for operations with date and time
from numpy import degrees                                           # for radian-degree conversion
from tkinter import *                                               # tkinter package for GUI
from threading import Thread

from Mqtt import mqtt


def print_info(msg):
    print('{0} UTC, {1}'.format(datetime.utcnow(), msg))


def read_line_from_txt(filename, line):
    with open(filename, 'r') as f:
        content = f.readlines()
    return content[line].strip()


def create_stat():                                                  # create station object
    with open(configuration_file, 'r') as f:
        content = f.readlines()
    return create_station(str(datetime.utcnow()), (float(content[0].strip()), float(content[1].strip()),
                                                   float(content[2].strip())))


def find_tle(sat_name):                                             # create TLE object for a satellite
    with open(tle_file, 'r') as file:                               # open TLE text file
        lines = file.readlines()
        for line in lines:
            if line.find(sat_name) != -1:
                line_number = lines.index(line)
                return Tle(lines[line_number + 1] + lines[line_number + 2])


def convert_to_decimal(var):
    return str(round(var, 2))


class TrackingTool(Tk):
    def __init__(self):
        super().__init__()
        self.program_name = 'Satellite tracking software 1.1'       # program name
        self.iconbitmap('Satellite.ico')                            # program icon
        self.geometry('1200x600')                                   # window dimensions
        self.bg_color = '#1d1f1b'                                   # background color
        self.text_color = 'white'                                   # text color
        self.configure(bg=self.bg_color)                            # set background color
        self.title(self.program_name)                               # set program title

        # List and string variables definition
        self.satellites = []                                        # list of all satellites on Earth orbit
        self.selected_satellites = []                               # list of selected satellites
        self.tracked_satellites = []                                # list of tracked satellites
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
        self.r_stat = StringVar()
        self.r_tracked_satellite = StringVar()
        self.r_az = StringVar()
        self.r_el = StringVar()
        self.r_pol = StringVar()
        self.tle_info = StringVar()
        self.msv3.set('First pass prediction:')
        self.r_stat.set('sleeping')
        self.r_tracked_satellite.set('none')
        self.r_pol.set('Vertical')

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
                                     ' to tracking to track it:', bg=self.bg_color,
                          fg=self.text_color)
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
        self.rl01 = Label(self, text='Time UTC:', bg=self.bg_color, fg=self.text_color)
        self.rl01.place(relx=0.525, rely=0.15, anchor=W)
        self.rl02 = Label(self, text='Local time:', bg=self.bg_color, fg=self.text_color)
        self.rl02.place(relx=0.775, rely=0.15, anchor=W)
        self.rl03 = Label(self, text='Status:', bg=self.bg_color, fg=self.text_color)
        self.rl03.place(relx=0.525, rely=0.20, anchor=W)
        self.rl04 = Label(self, text='Tracked satellite:', bg=self.bg_color, fg=self.text_color)
        self.rl04.place(relx=0.775, rely=0.20, anchor=W)
        self.rl05 = Label(self, text='Azimuth (AZ):', bg=self.bg_color, fg=self.text_color)
        self.rl05.place(relx=0.525, rely=0.25, anchor=W)
        self.rl06 = Label(self, text='Elevation (EL):', bg=self.bg_color, fg=self.text_color)
        self.rl06.place(relx=0.775, rely=0.25, anchor=W)
        self.rl06 = Label(self, text='Antenna polarization:', bg=self.bg_color, fg=self.text_color)
        self.rl06.place(relx=0.525, rely=0.30, anchor=W)
        self.rl11 = Label(self, textvariable=self.msv2, bg=self.bg_color, fg=self.text_color)
        self.rl11.place(relx=0.750, rely=0.40, anchor=CENTER)
        self.rl12 = Label(self, textvariable=self.tle_info, bg=self.bg_color, fg=self.text_color)
        self.rl12.place(relx=0.750, rely=0.95, anchor=CENTER)

        # Entries definition
        self.sat_entry = Entry(textvariable=self.ss0, bg=self.bg_color, fg=self.text_color,
                               highlightbackground='black')
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
        self.re2 = Entry(textvariable=self.r_stat, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re2.place(relx=0.625, rely=0.20, relwidth=0.1, anchor=W)
        self.re3 = Entry(textvariable=self.r_tracked_satellite, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re3.place(relx=0.875, rely=0.20, relwidth=0.1, anchor=W)
        self.re4 = Entry(textvariable=self.r_az, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re4.place(relx=0.625, rely=0.25, relwidth=0.1, anchor=W)
        self.re5 = Entry(textvariable=self.r_el, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re5.place(relx=0.875, rely=0.25, relwidth=0.1, anchor=W)
        self.re5 = Entry(textvariable=self.r_pol, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re5.place(relx=0.625, rely=0.30, relwidth=0.1, anchor=W)

        # Buttons definition
        self.predict_button = Button(self, text='Predict', command=self.start_predicting, bg=self.bg_color,
                                     fg=self.text_color, activebackground=self.bg_color)
        self.predict_button.place(relx=0.075, rely=0.45, relwidth=0.1, anchor=CENTER)
        self.add_button = Button(self, text='Add to tracking', command=self.add_to_tracked, bg=self.bg_color,
                                 fg=self.text_color, activebackground=self.bg_color)
        self.add_button.place(relx=0.175, rely=0.45, relwidth=0.1, anchor=CENTER)
        self.remove_button = Button(self, text='Remove from tracking', command=self.remove_from_tracked,
                                    bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.remove_button.place(relx=0.325, rely=0.45, relwidth=0.1, anchor=CENTER)
        self.track_button = Button(self, text='Track!', command=lambda: Thread(target=self.track_sats).start(),
                                   bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.track_button.place(relx=0.425, rely=0.45, relwidth=0.1, anchor=CENTER)
        self.ver_pol = Button(self, text='Vertical', command=lambda: self.set_polarization('Vertical'),
                              bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.ver_pol.place(relx=0.775, rely=0.30, relwidth=0.05, anchor=W)
        self.hor_pol = Button(self, text='Horizontal', command=lambda: self.set_polarization('Horizontal'),
                              bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.hor_pol.place(relx=0.825, rely=0.30, relwidth=0.05, anchor=W)
        self.lhcp_pol = Button(self, text='LHCP', command=lambda: self.set_polarization('LHCP'),
                               bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.lhcp_pol.place(relx=0.875, rely=0.30, relwidth=0.05, anchor=W)
        self.rhcp_pol = Button(self, text='RHCP', command=lambda: self.set_polarization('RHCP'),
                               bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.rhcp_pol.place(relx=0.925, rely=0.30, relwidth=0.05, anchor=W)
        self.reset_button = Button(self, text='Reset', command=lambda: mqtt.publish_action('reset'),
                                   bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.reset_button.place(relx=0.625, rely=0.35, relwidth=0.1, anchor=CENTER)
        self.reset_button = Button(self, text='Shut down', command=lambda: mqtt.publish_action('shutdown'),
                                   bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.reset_button.place(relx=0.875, rely=0.35, relwidth=0.1, anchor=CENTER)

        # Scrollbar definition
        self.scrollbar0 = Scrollbar(self, bg=self.bg_color)
        self.scrollbar0.place(relx=0.225, rely=0.30, relwidth=0.015, relheight=0.15, anchor=W)
        self.scrollbar1 = Scrollbar(self, bg=self.bg_color)
        self.scrollbar1.place(relx=0.475, rely=0.30, relwidth=0.015, relheight=0.15, anchor=W)
        self.scrollbar2 = Scrollbar(self, bg=self.bg_color)
        self.scrollbar2.place(relx=0.8575, rely=0.45, relwidth=0.015, relheight=0.45, anchor=N)

        # Listbox definition
        self.listbox0 = Listbox(self, yscrollcommand=self.scrollbar0.set, bg=self.bg_color, fg=self.text_color)
        self.listbox0.place(relx=0.125, rely=0.30, relwidth=0.2, relheight=0.15, anchor=CENTER)
        self.listbox0.bind('<Double-1>', self.go0)
        self.scrollbar0.config(command=self.listbox0.yview)
        self.listbox1 = Listbox(self, yscrollcommand=self.scrollbar1.set, bg=self.bg_color, fg=self.text_color)
        self.listbox1.place(relx=0.375, rely=0.30, relwidth=0.2, relheight=0.15, anchor=CENTER)
        self.listbox1.bind('<Double-1>', self.go1)
        self.scrollbar1.config(command=self.listbox1.yview)
        self.listbox2 = Listbox(self, yscrollcommand=self.scrollbar2.set, bg=self.bg_color, fg=self.text_color)
        self.listbox2.place(relx=0.75, rely=0.45, relwidth=0.2, relheight=0.45, anchor=N)
        self.scrollbar2.config(command=self.listbox2.yview)

        # run basic functions
        self.update_tle()
        self.update_r_info()
        self.listbox_init()

    def start_predicting(self):
        Thread(target=self.predict, args=(self.sat_entry.get(),)).start()

    def set_polarization(self, pol):
        self.r_pol.set(pol)
        mqtt.publish_polarization(pol)

    @staticmethod
    def fill_listbox(listbox, content):                             # fill listbox with all satellite names
        listbox.delete(0, END)
        for item in content:
            listbox.insert(END, item)

    @staticmethod
    def timedelta_formatter(td):                        # function that creates td string in format %H %M %S
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))

    def update_r_info(self):
        self.utctime.set(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
        self.localtime.set(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.r_az.set(mqtt.azimuth)
        self.r_el.set(mqtt.elevation)
        self.re0.after(1000, self.update_r_info)

    def listbox_init(self):
        with open(tle_file, 'r') as file:
            self.satellites = sorted(list(map(str.strip, file.readlines()[::3])))
        with open(tracked_file, 'r') as f:
            self.selected_satellites = sorted(list(map(str.strip, f.readlines())))
        self.update_listbox0()
        self.update_listbox1()
        self.update_listbox2()

    def go0(self, event):
        cs = self.listbox0.curselection()
        self.ss0.set(self.listbox0.get(cs))

    def go1(self, event):
        cs = self.listbox1.curselection()
        self.ss1.set(self.listbox1.get(cs))

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
        if sat not in self.selected_satellites:
            self.selected_satellites.append(sat)
        self.update_listbox1()

    def remove_from_tracked(self):                                  # remove satellite from tracking
        sat = self.tsat_entry.get()
        if sat in self.selected_satellites:
            self.selected_satellites.remove(sat)
        self.update_listbox1()

    def track_sats(self):                                           # track all satellites in track_satellites list
        self.tracked_satellites = sorted(self.selected_satellites)
        self.update_listbox2()
        with open(tracked_file, 'w') as f:
            f.writelines('\n'.join(self.tracked_satellites))
        for sat in self.tracked_satellites:
            TrackedSatellite(sat)
        s.run()

    def update_listbox0(self):
        self.fill_listbox(self.listbox0, self.satellites)
        self.msv0.set('All satellites ({0}):'.format(len(self.satellites)))

    def update_listbox1(self):
        self.fill_listbox(self.listbox1, sorted(self.selected_satellites))
        self.msv1.set('Selected satellites ({0}):'.format(len(self.selected_satellites)))

    def update_listbox2(self):
        self.fill_listbox(self.listbox2, self.tracked_satellites)
        self.msv2.set('Tracked satellites ({0}):'.format(len(self.tracked_satellites)))

    def predict(self, sat):                                         # create data about the pass of selected satellite
        self.empty_prediction_data()
        if sat in self.satellites:
            for orb in station.visibility(find_tle(sat).orbit(), start=Date.now(), stop=timedelta(hours=24),
                                          step=timedelta(seconds=100), events=True):
                if orb.event and orb.event.info.startswith('AOS'):
                    self.date.set(orb.date.strftime('%d %B %Y'))
                    self.aos_time.set(orb.date.strftime('%H:%M:%S'))
                    self.aos_az.set(convert_to_decimal(degrees(-orb.theta) % 360))
                if orb.event and orb.event.info.startswith('MAX'):
                    self.max_time.set(orb.date.strftime('%H:%M:%S'))
                    self.max_az.set(convert_to_decimal(degrees(-orb.theta) % 360))
                    self.max_el.set(convert_to_decimal(degrees(orb.phi)))
                if orb.event and orb.event.info.startswith('LOS'):
                    self.los_time.set(orb.date.strftime('%H:%M:%S'))
                    self.los_az.set(convert_to_decimal(degrees(-orb.theta) % 360))
                    break
            if self.aos_time.get() == '':
                self.empty_prediction_data()
                self.msv3.set('Sorry, {0} will not fly over your head in foreseeable future'.format(sat))
            if self.aos_time.get() != '' and self.max_time.get() == '':
                self.msv3.set('First pass prediction for fff {0}:'.format(sat))
            if self.aos_time.get() != '' and self.max_time.get() != '' and self.los_time.get() != '':
                self.duration.set(self.timedelta_formatter(datetime.strptime(self.los_time.get(), '%H:%M:%S') -
                                                           datetime.strptime(self.aos_time.get(), '%H:%M:%S')))
                self.msv3.set('First pass prediction for {0}:'.format(sat))
        else:
            self.msv3.set('Sorry, {0} is not a satellite in orbit.'.format(sat))

    def empty_prediction_data(self):
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
        last_update = datetime.strptime(read_line_from_txt(configuration_file, 3), '%Y-%m-%d %H:%M:%S.%f')
        if datetime.utcnow() > last_update + timedelta(hours=2):
            response = requests.get('https://celestrak.org/NORAD/elements/gp.php?GROUP=ACTIVE&FORMAT=tle')
            with open(tle_file, 'wb') as f:
                f.write(response.content)
            with open(configuration_file, 'r') as g:
                content = g.readlines()
                content[3] = str(datetime.utcnow())
            with open(configuration_file, 'w') as h:
                h.writelines(content)
            print_info('updated TLE data')
        self.tle_info.set('Last TLE update: {0}'.format(datetime.utcnow().strftime('%d %B %Y %H:%M:%S')))


class TrackedSatellite:
    def __init__(self, name):
        self.name = name
        self.times, self.azims, self.elevs = [], [], []
        self.start_time = datetime.now()
        self.start_time_seconds = 0
        self.delay_before_tracking = timedelta(seconds=10)
        self.tle = find_tle(name)
        self.create_data(delay=0)

    def create_data(self, delay):
        self.times.clear()
        self.azims.clear()
        self.elevs.clear()
        for orb in station.visibility(self.tle.orbit(), start=Date.now() + timedelta(seconds=delay),
                                      stop=timedelta(hours=24), step=timedelta(seconds=10), events=True):
            self.times.append(datetime.strptime(str(orb.date), '%Y-%m-%dT%H:%M:%S.%f UTC'))
            self.azims.append(degrees(-orb.theta) % 360)
            self.elevs.append(degrees(orb.phi))
            if orb.event and orb.event.info.startswith('LOS'):
                self.start_time = self.times[0]
                self.start_time_seconds = (self.start_time - datetime.utcnow() - self.delay_before_tracking).seconds
                if self.start_time_seconds > 0:
                    s.enter(self.start_time_seconds, 1, self.start_tracking)
                    print_info('{0} created data, AOS: {1}'.format(self.name,
                                                                   self.start_time.strftime('%Y-%m-%d %H:%M:%S')))
                else:
                    self.create_data(delay=self.start_time_seconds + 1000)
                    print('Next try', self.name)
                break

    def start_tracking(self):
        Thread(target=self.track).start()

    def track(self):
        if app.r_stat.get() == 'sleeping':
            if self.start_time > datetime.utcnow():
                wait_time = (self.start_time - datetime.utcnow()).total_seconds()
                app.r_stat.set('tracking')
                mqtt.publish_action('start')
                mqtt.publish_start_azimuth(self.azims[0])
                app.r_tracked_satellite.set(self.name)
                app.predict(self.name)
                print_info('{0} will fly over your head in {1} seconds'.format(self.name, int(wait_time)))
                time.sleep(wait_time)
                print_info('{0} tracking started'.format(self.name))
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
                app.r_stat.set('sleeping')
                app.r_tracked_satellite.set('none')
                print_info('{0} tracking ended'.format(self.name))
            else:
                print_info('{0} tracking passed'.format(self.name))
        else:
            print_info('{0} cannot be tracked now, because {1} is being tracked'.format(self.name,
                                                                                        app.r_tracked_satellite.get()))
        Thread(self.create_data(delay=2000))


if __name__ == '__main__':
    s = sched.scheduler(time.time)                          # create scheduler object
    minmaxel = 20                                           # minimal possible MAX elevation of all satellites
    tle_file = 'tle-active.txt'                             # text file with TLE data
    configuration_file = 'configuration.txt'                # text file with station configuration
    tracked_file = 'tracked_sats.txt'                       # text file with list of tracked satellites
    station = create_stat()                                 # station object
    app = TrackingTool()                                    # GUI object
    app.mainloop()
