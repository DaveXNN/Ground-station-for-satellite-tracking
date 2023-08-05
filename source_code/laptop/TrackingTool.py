from beyond.dates import Date                                       # for Date object from beyond library
from beyond.io.tle import Tle                                       # for Tle object from beyond library
from beyond.frames import create_station                            # for station object from beyond library
from datetime import datetime, timedelta                            # for operations with date and time
from tkinter import *                                               # tkinter package for GUI
import paho.mqtt.client as paho                                     # for subscribing data from MQTT broker
import numpy as np                                                  # for radian-degree conversion
import requests                                                     # for downloading TLE data


def write_line_into_txt(filename, line, text):
    content = open(filename, 'r').readlines()
    content[line] = text
    out = open(filename, 'w')
    out.writelines(content)
    out.close()


def timedelta_formatter(td):                                        # function that creates td string in format %H %M %S
    td_sec = td.seconds                                             # getting the seconds field of the timedelta
    hour_count, rem = divmod(td_sec, 3600)                          # calculating the total hours
    minute_count, second_count = divmod(rem, 60)                    # distributing the remainders
    if td_sec < 3600:
        msg = "{}:{}".format(minute_count, second_count)
        return msg
    elif td_sec < 86400:
        msg = "{}:{}:{}".format(hour_count, minute_count, second_count)
        return msg
    else:
        msg = "{} days, {}:{}:{}".format(td.days, hour_count, minute_count, second_count)
        return msg


class TrackingTool(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.window = master
        self.conf_file = 'configuration.txt'                        # text file with station configuration
        self.tle_file = 'tle-active.txt'                            # text file with TLE data
        self.satellites = []                                        # list of all satellites on Earth orbit
        self.tracked_satellites = []                                # list of tracked satellites
        self.program_name = 'Satellite tracking software 1.0'       # program name
        self.window.iconbitmap('Satellite.ico')                     # program icon
        self.window.geometry('1200x600')                            # window dimensions
        self.bg_color = 'white'                                     # background color
        self.window.configure(bg=self.bg_color)                     # set window background color
        self.window.title(self.program_name)                        # set program title
        self.search_str0 = StringVar()
        self.search_str1 = StringVar()
        self.search_str2 = StringVar()
        self.rotator_state = 'sleep'
        self.tracked_satellite = ''
        self.rotator_azimuth = ''
        self.rotator_elevation = ''
        self.azimuth_arrived = False
        self.elevation_arrived = False
        self.create_sat_list()
        self.update_tle()
        self.station = self.create_stat()
        self.pack()
        self.main_title = Label(self.window, text=self.program_name, font='Helvetica 20 bold', bg='white')
        self.main_title.place(relx=0.5, rely=0.05, anchor=CENTER)
        self.left_title = Label(self.window, text='Predicting satellite visibility', font='Helvetica 10 bold',
                                bg=self.bg_color)
        self.left_title.place(relx=0.25, rely=0.10, anchor=CENTER)
        self.right_title = Label(self.window, text='Rotator',
                                 font='Helvetica 10 bold', bg=self.bg_color)
        self.right_title.place(relx=0.75, rely=0.10, anchor=CENTER)
        self.left_explanation0 = Label(self.window, text='Select a satellite by double click and click Predict to '
                                                         'predict first pass or Add to tracking to track it:',
                                       bg=self.bg_color)
        self.left_explanation0.place(relx=0.25, rely=0.15, anchor=CENTER)
        self.left_explanation1 = Label(self.window, text='All satellites:', bg=self.bg_color)
        self.left_explanation1.place(relx=0.125, rely=0.20, anchor=CENTER)
        self.left_explanation2 = Label(self.window, text='Selected satellites:', bg=self.bg_color)
        self.left_explanation2.place(relx=0.375, rely=0.20, anchor=CENTER)
        self.left_explanation3 = Label(self.window, text='First pass prediction:', bg=self.bg_color)
        self.left_explanation3.place(relx=0.25, rely=0.50, anchor=CENTER)
        self.right_explanation0 = Label(self.window, text='Information about current rotator status and position:',
                                        bg=self.bg_color)
        self.right_explanation0.place(relx=0.75, rely=0.15, anchor=CENTER)
        self.right_explanation1 = Label(self.window, text='Tracked satellites:', bg=self.bg_color)
        self.right_explanation1.place(relx=0.75, rely=0.45, anchor=CENTER)
        self.ll0 = Label(self.window, text='Date UTC:', bg=self.bg_color)
        self.ll0.place(relx=0.05, rely=0.55, anchor=W)
        self.ll1 = Label(self.window, text='Acquisition of satellite (AOS):', bg=self.bg_color)
        self.ll1.place(relx=0.05, rely=0.60, anchor=W)
        self.ll2 = Label(self.window, text='AOS azimuth:', bg=self.bg_color)
        self.ll2.place(relx=0.05, rely=0.65, anchor=W)
        self.ll3 = Label(self.window, text='Maximum elevation (MAX):', bg=self.bg_color)
        self.ll3.place(relx=0.05, rely=0.70, anchor=W)
        self.ll4 = Label(self.window, text='MAX azimuth:', bg=self.bg_color)
        self.ll4.place(relx=0.05, rely=0.75, anchor=W)
        self.ll5 = Label(self.window, text='MAX elevation:', bg=self.bg_color)
        self.ll5.place(relx=0.05, rely=0.80, anchor=W)
        self.ll6 = Label(self.window, text='Loss of satellite (LOS):', bg=self.bg_color)
        self.ll6.place(relx=0.05, rely=0.85, anchor=W)
        self.ll7 = Label(self.window, text='LOS azimuth:', bg=self.bg_color)
        self.ll7.place(relx=0.05, rely=0.90, anchor=W)
        self.ll8 = Label(self.window, text='Duration:', bg=self.bg_color)
        self.ll8.place(relx=0.05, rely=0.95, anchor=W)
        self.rl0 = Label(self.window, text='Time UTC:', bg=self.bg_color)
        self.rl0.place(relx=0.55, rely=0.20, anchor=W)
        self.rl1 = Label(self.window, text='Status:', bg=self.bg_color)
        self.rl1.place(relx=0.55, rely=0.25, anchor=W)
        self.rl2 = Label(self.window, text='Satellite:', bg=self.bg_color)
        self.rl2.place(relx=0.55, rely=0.30, anchor=W)
        self.rl3 = Label(self.window, text='Azimuth (AZ):', bg=self.bg_color)
        self.rl3.place(relx=0.55, rely=0.35, anchor=W)
        self.rl4 = Label(self.window, text='Elevation (EL):', bg=self.bg_color)
        self.rl4.place(relx=0.55, rely=0.40, anchor=W)

        # Entries definition
        self.sat_entry = Entry(textvariable=self.search_str0)
        self.sat_entry.place(relx=0.125, rely=0.40, relwidth=0.2, anchor=CENTER)
        self.sat_entry.bind('<Return>', self.search0)
        self.tsat_entry = Entry(textvariable=self.search_str1)
        self.tsat_entry.place(relx=0.375, rely=0.40, relwidth=0.2, anchor=CENTER)
        self.tsat_entry.bind('<Return>', self.search1)
        self.le0 = Entry(justify=RIGHT)
        self.le0.place(relx=0.25, rely=0.55, relwidth=0.2, anchor=W)
        self.le1 = Entry(justify=RIGHT)
        self.le1.place(relx=0.25, rely=0.60, relwidth=0.2, anchor=W)
        self.le2 = Entry(justify=RIGHT)
        self.le2.place(relx=0.25, rely=0.65, relwidth=0.2, anchor=W)
        self.le3 = Entry(justify=RIGHT)
        self.le3.place(relx=0.25, rely=0.70, relwidth=0.2, anchor=W)
        self.le4 = Entry(justify=RIGHT)
        self.le4.place(relx=0.25, rely=0.75, relwidth=0.2, anchor=W)
        self.le5 = Entry(justify=RIGHT)
        self.le5.place(relx=0.25, rely=0.80, relwidth=0.2, anchor=W)
        self.le6 = Entry(justify=RIGHT)
        self.le6.place(relx=0.25, rely=0.85, relwidth=0.2, anchor=W)
        self.le7 = Entry(justify=RIGHT)
        self.le7.place(relx=0.25, rely=0.90, relwidth=0.2, anchor=W)
        self.le8 = Entry(justify=RIGHT)
        self.le8.place(relx=0.25, rely=0.95, relwidth=0.2, anchor=W)
        self.re0 = Entry(justify=RIGHT)
        self.re0.place(relx=0.75, rely=0.20, relwidth=0.2, anchor=W)
        self.re1 = Entry(justify=RIGHT)
        self.re1.place(relx=0.75, rely=0.25, relwidth=0.2, anchor=W)
        self.re2 = Entry(justify=RIGHT)
        self.re2.place(relx=0.75, rely=0.30, relwidth=0.2, anchor=W)
        self.re3 = Entry(justify=RIGHT)
        self.re3.place(relx=0.75, rely=0.35, relwidth=0.2, anchor=W)
        self.re4 = Entry(justify=RIGHT)
        self.re4.place(relx=0.75, rely=0.40, relwidth=0.2, anchor=W)

        # Buttons definition
        self.predict_button = Button(self.window, text='Predict', command=lambda: self.predict(self.sat_entry.get()),
                                     bg=self.bg_color)
        self.predict_button.place(relx=0.075, rely=0.45, relwidth=0.1, anchor=CENTER)
        self.add_button = Button(self.window, text='Add to tracking', command=self.add_to_tracked, bg=self.bg_color)
        self.add_button.place(relx=0.175, rely=0.45, relwidth=0.1, anchor=CENTER)
        self.remove_button = Button(self.window, text='Remove from tracking', command=self.remove_from_tracked,
                                    bg=self.bg_color)
        self.remove_button.place(relx=0.325, rely=0.45, relwidth=0.1, anchor=CENTER)
        self.track_button = Button(self.window, text='Track!', command=self.track, bg=self.bg_color)
        self.track_button.place(relx=0.425, rely=0.45, relwidth=0.1, anchor=CENTER)

        # Scrollbar definition
        self.scrollbar0 = Scrollbar(self.window, bg=self.bg_color)
        self.scrollbar0.place(relx=0.225, rely=0.30, relwidth=0.015, relheight=0.15, anchor=W)
        self.scrollbar1 = Scrollbar(self.window, bg=self.bg_color)
        self.scrollbar1.place(relx=0.475, rely=0.30, relwidth=0.015, relheight=0.15, anchor=W)
        self.scrollbar2 = Scrollbar(self.window, bg=self.bg_color)
        self.scrollbar2.place(relx=0.85, rely=0.65, relwidth=0.015, relheight=0.35, anchor=W)

        # Listbox definition
        self.listbox0 = Listbox(self.window, yscrollcommand=self.scrollbar0.set)
        self.listbox0.place(relx=0.125, rely=0.30, relwidth=0.2, relheight=0.15, anchor=CENTER)
        self.listbox0.bind('<Double-1>', self.go0)
        self.scrollbar0.config(command=self.listbox0.yview)
        self.fill_listbox(self.listbox0, self.satellites)
        self.listbox1 = Listbox(self.window, yscrollcommand=self.scrollbar1.set)
        self.listbox1.place(relx=0.375, rely=0.30, relwidth=0.2, relheight=0.15, anchor=CENTER)
        self.listbox1.bind('<Double-1>', self.go1)
        self.scrollbar1.config(command=self.listbox1.yview)
        self.fill_listbox(self.listbox1, self.tracked_satellites)
        self.listbox2 = Listbox(self.window, yscrollcommand=self.scrollbar2.set)
        self.listbox2.place(relx=0.75, rely=0.65, relwidth=0.2, relheight=0.35, anchor=CENTER)
        self.listbox2.bind('<Double-1>', self.go2)
        self.scrollbar2.config(command=self.listbox2.yview)
        self.fill_listbox(self.listbox2, self.tracked_satellites)

        self.utc_clock()

        # create a MQTT client for subscribing data from rotator
        self.client = paho.Client()
        self.client.username_pw_set('rotatorinfo', password='rotatorinfo')
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect('raspberrypi', port=1883)
        self.client.subscribe('state')
        self.client.subscribe('satellite')
        self.client.subscribe('azimuth')
        self.client.subscribe('elevation')
        self.client.loop_start()

    @staticmethod
    def utc():
        return datetime.utcnow()

    @staticmethod
    def fill_entry(entry, value):                                   # write value to entry field
        entry.delete(0, END)
        entry.insert(END, value)

    @staticmethod
    def fill_listbox(listbox, content):                             # fill listbox with all satellite names
        listbox.delete(0, END)
        for item in content:
            listbox.insert(END, item)

    @staticmethod
    def read_line_from_txt(filename, line):
        content = open(filename, 'r').readlines()
        return content[line].strip()

    @staticmethod
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print('MQTT client is connected')
        else:
            print('MQTT client is not connected', rc)

    def on_message(self, client, userdata, message):
        if str(message.topic) == 'state':
            self.rotator_state = str(message.payload.decode('utf-8'))
        if str(message.topic) == 'satellite':
            self.tracked_satellite = str(message.payload.decode('utf-8'))
            self.show_tracked_sat_list()
            self.fill_entry(self.sat_entry, self.tracked_satellite)
            self.predict(self.tracked_satellite)
        if str(message.topic) == 'azimuth':
            self.rotator_azimuth = str(message.payload.decode('utf-8'))
        if str(message.topic) == 'elevation':
            self.rotator_elevation = str(message.payload.decode('utf-8'))

    def utc_clock(self):
        self.fill_entry(self.re0, self.utc().strftime('%Y-%m-%d %H:%M:%S'))
        self.fill_entry(self.re1, self.rotator_state)
        self.fill_entry(self.re2, self.tracked_satellite)
        self.fill_entry(self.re3, self.rotator_azimuth)
        self.fill_entry(self.re4, self.rotator_elevation)
        self.re0.after(1000, self.utc_clock)

    def go0(self, event):
        cs = self.listbox0.curselection()
        self.fill_entry(self.sat_entry, str(self.listbox0.get(cs)))

    def go1(self, event):
        cs = self.listbox1.curselection()
        self.fill_entry(self.tsat_entry, str(self.listbox1.get(cs)))

    def go2(self, event):
        cs = self.listbox2.curselection()
        self.fill_entry(self.tsat_entry, str(self.listbox2.get(cs)))

    def search0(self, event):                                       # fill listbox0 with filtered satellite names
        word = self.search_str0.get()
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
        word = self.search_str1.get()
        self.listbox1.delete(0, END)
        if word == '':
            self.fill_listbox(self.listbox1, self.tracked_satellites)
            return
        filtered_data = list()
        for item in self.tracked_satellites:
            if item.find(word) >= 0:
                filtered_data.append(item)
        self.fill_listbox(self.listbox1, filtered_data)

    def search2(self, event):                                       # fill listbox2 with filtered satellite names
        word = self.search_str2.get()
        self.listbox1.delete(0, END)
        if word == '':
            self.fill_listbox(self.listbox2, self.tracked_satellites)
            return
        filtered_data = list()
        for item in self.tracked_satellites:
            if item.find(word) >= 0:
                filtered_data.append(item)
        self.fill_listbox(self.listbox2, filtered_data)

    def add_to_tracked(self):                                       # add satellite to tracking
        sat = self.sat_entry.get()
        if sat not in self.tracked_satellites and sat in self.satellites:
            self.tracked_satellites.append(sat)
        self.fill_listbox(self.listbox1, self.tracked_satellites)

    def remove_from_tracked(self):                                  # remove satellite from tracking
        sat = self.tsat_entry.get()
        if sat in self.tracked_satellites and sat in self.satellites:
            self.tracked_satellites.remove(sat)
        self.fill_listbox(self.listbox1, self.tracked_satellites)

    def track(self):                                                # track all satellites in track_satellites list
        self.update_tle()
        f = open('tracked_sats.txt', 'w')
        f.writelines('\n'.join(self.tracked_satellites))
        f.close()

    def create_sat_list(self):                                      # create list of all satellite names
        self.satellites.clear()
        with open(self.tle_file, 'r') as file:
            lines = file.readlines()
            for line in lines[::3]:
                self.satellites.append(line.strip())

    def show_tracked_sat_list(self):                                # create list of all satellite names
        f = open('tracked_sats.txt', 'r')
        self.fill_listbox(self.listbox2, f.readlines())

    def create_stat(self):                                          # create station object
        return create_station(str(self.utc()), (float(self.read_line_from_txt(self.conf_file, 0)),
                                                float(self.read_line_from_txt(self.conf_file, 1)),
                                                float(self.read_line_from_txt(self.conf_file, 2))))

    def find_tle(self, name):                                       # create TLE object for a satellite
        with open(self.tle_file, 'r') as file:                      # open TLE text file
            lines = file.readlines()
            for line in lines:
                if line.find(name) != -1:
                    line_number = lines.index(line)
                    return Tle(lines[line_number + 1] + lines[line_number + 2])

    def predict(self, sat):                                         # create data about the pass of selected satellite
        if sat in self.satellites:
            times = []
            azims = []
            elevs = []
            max_el = 0
            max_az = 0
            max_time = self.utc()
            for orb in self.station.visibility(self.find_tle(sat).orbit(), start=Date.now(),
                                               stop=timedelta(hours=24), step=timedelta(seconds=10), events=True):
                times.append(datetime.strptime(str(orb.date), '%Y-%m-%dT%H:%M:%S.%f UTC'))
                azims.append(float('{azim:7f}'.format(azim=(np.degrees(-orb.theta) % 360))))
                elevs.append(float('{elev:7f}'.format(elev=np.degrees(orb.phi))))
                if orb.event and orb.event.info.startswith('MAX'):
                    max_time = times[len(times) - 1].strftime('%H:%M:%S')
                    max_az = str(round(azims[len(azims) - 1], 2))
                    max_el = str(round(elevs[len(elevs) - 1], 2))
                if orb.event and orb.event.info.startswith('LOS'):
                    break
            try:
                x = len(times) - 1
                date = times[0].strftime('%d %B %Y')
                aos_time = times[0].strftime('%H:%M:%S')
                aos_az = str(round(azims[0], 2))
                los_time = times[x].strftime('%H:%M:%S')
                los_az = str(round(azims[x], 2))
                duration = timedelta_formatter(times[x] - times[0])
                self.fill_data(date, aos_time, aos_az, max_time, max_az, max_el, los_time, los_az, duration)
            except IndexError:
                self.fill_data('', '', '', '', '', '', '', '', '')
                print(self.utc(), sat, 'unable to track this satellite', sep=', ')
        else:
            print(self.utc(), sat, 'this is not a satellite', sep=', ')
            self.fill_data('', '', '', '', '', '', '', '', '')

    def fill_data(self, e0, e1, e2, e3, e4, e5, e6, e7, e8):
        self.fill_entry(self.le0, e0)
        self.fill_entry(self.le1, e1)
        self.fill_entry(self.le2, e2)
        self.fill_entry(self.le3, e3)
        self.fill_entry(self.le4, e4)
        self.fill_entry(self.le5, e5)
        self.fill_entry(self.le6, e6)
        self.fill_entry(self.le7, e7)
        self.fill_entry(self.le8, e8)

    def update_tle(self):                                           # update tle data (if it is older than 2 hours)
        if self.utc() > datetime.strptime(self.read_line_from_txt(self.conf_file, 3), '%Y-%m-%d %H:%M:%S.%f') + \
                timedelta(hours=2):
            print(self.utc(), ', updating TLE data...', sep='')
            response = requests.get('https://celestrak.org/NORAD/elements/gp.php?GROUP=ACTIVE&FORMAT=tle')
            f = open(self.tle_file, 'wb')
            f.write(response.content)
            f.close()
            write_line_into_txt(self.conf_file, 3, str(self.utc()))
            self.create_sat_list()
            print(self.utc(), ', TLE data updated successfully', sep='')


if __name__ == '__main__':
    app = TrackingTool(master=Tk())
    app.mainloop()
