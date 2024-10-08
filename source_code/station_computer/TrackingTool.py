########################################################################################################################
#                                                                                                                      #
#    Author:         D. Nenicka                                                                                        #
#    Created:        3. 11. 2023                                                                                       #
#    Modified:       30. 8. 2024                                                                                       #
#    Description:    Simple GUI for satellite tracking                                                                 #
#                                                                                                                      #
########################################################################################################################


from datetime import datetime, timedelta, timezone                  # module for operations with date and time
from threading import Thread, Timer                                 # module for running more processes in parallel
from tkinter import *                                               # tkinter package for creating GUI
from time import sleep                                              # module with sleep() function


class TrackingTool(Tk):
    def __init__(self, json_tool, beyond_tools, mqt, tle_updator):
        super().__init__()
        self.json_tool = json_tool                                  # json configuration file
        self.mqtt = mqt                                             # object for MQTT communication
        self.beyond_tools = beyond_tools                            # object for satellite pass predictions
        self.tle_updator = tle_updator                              # object for updating TLE data

        # Load program variables from json configuration file
        self.program_name = self.json_tool.content['program_name']                # program name
        self.icon = self.json_tool.content['icon']                                # icon file of the program window
        self.selected_satellites = self.json_tool.content['tracked_satellites']   # list of tracked satellites

        # Initialize basic GUI variables
        self.iconbitmap(self.icon)                                  # program icon
        self.geometry('1200x600')                                   # window dimensions
        self.bg_color = '#daa520'                                   # background color #1d1f1b
        self.text_color = 'black'                                   # text color
        self.configure(bg=self.bg_color)                            # set background color
        self.title(self.program_name)                               # set program title

        self.tracking_thread = Thread(target=self.track_satellites)

        # Variables
        self.tracked_satellites = []                                # list of selected satellites
        self.tso = []                                               # list of TrackedSatellite objects
        self.track_button_pressed = False                           # True if track button has already been pressed
        self.tracking = False                                       # True if rotator is currently tracking a sat
        self.ts_los_time = None
        self.first_pass_time = None
        self.tracked_satellite = 'none'
        self.next_satellite = 'none'

        # Tkinter variables
        self.ss0 = StringVar()                                      # text variable for searching in listbox0
        self.ss1 = StringVar()                                      # text variable for searching in listbox1
        self.msv0 = StringVar()                                     # text variable for showing number of all satellites
        self.msv1 = StringVar()                                     # text variable for showing number of s. satellites
        self.msv2 = StringVar()                                     # text variable for showing number of t. satellites
        self.msv3 = StringVar()                                     # text variable for pass predictions
        self.msv4 = StringVar()
        self.msv5 = StringVar()
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
        self.r_satellite = StringVar()
        self.r_time_till_los = StringVar()
        self.r_pol = StringVar()
        self.mqtt_status = StringVar()
        self.first_pass_info = StringVar()
        self.tle_info = StringVar()
        self.msv3.set('First pass prediction:')
        self.msv4.set('Next satellite:')
        self.msv5.set('Tracking starts in:')
        self.r_satellite.set(self.next_satellite)
        self.r_time_till_los.set('')
        self.r_pol.set('Vertical')
        self.tle_info.set(f'Last TLE update: {self.tle_updator.last_update.strftime("%d %B %Y %H:%M:%S UTC")}')


        # Azimuth and elevation offsets
        self.az_offset = Offset(self, self.az_offset_var)
        self.el_offset = Offset(self, self.el_offset_var)

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
        self.rl06 = Label(self, textvariable=self.msv4, bg=self.bg_color, fg=self.text_color)
        self.rl06.place(relx=0.525, rely=0.30, anchor=W)
        self.rl07 = Label(self, textvariable=self.msv5, bg=self.bg_color, fg=self.text_color)
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
        self.sat_entry0 = Entry(textvariable=self.ss0, bg=self.bg_color, fg=self.text_color)
        self.sat_entry0.place(relx=0.125, rely=0.40, relwidth=0.2, anchor=CENTER)
        self.sat_entry0.bind('<Return>', self.search0)
        self.sat_entry1 = Entry(textvariable=self.ss1, bg=self.bg_color, fg=self.text_color)
        self.sat_entry1.place(relx=0.375, rely=0.40, relwidth=0.2, anchor=CENTER)
        self.sat_entry1.bind('<Return>', self.search1)
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
        self.re6 = Entry(textvariable=self.r_satellite, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re6.place(relx=0.625, rely=0.30, relwidth=0.1, anchor=W)
        self.re7 = Entry(textvariable=self.r_time_till_los, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re7.place(relx=0.875, rely=0.30, relwidth=0.1, anchor=W)
        self.re8 = Entry(textvariable=self.r_pol, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re8.place(relx=0.625, rely=0.35, relwidth=0.1, anchor=W)
        self.re9 = Entry(textvariable=self.mqtt_status, justify=CENTER, bg=self.bg_color, fg=self.text_color)
        self.re9.place(relx=0.625, rely=0.40, relwidth=0.1, anchor=W)

        # Buttons definition
        self.predict_button = Button(self, text='Predict', command=lambda: self.predict(self.sat_entry0.get()),
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
                                      command=lambda: self.mqtt.publish_action('shutdown'), bg=self.bg_color,
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

    def start_tracking(self):
        self.tracking_thread.start()

    def listbox_init(self):
        self.update_listbox0()
        self.update_listbox1()
        self.update_listbox2()

    def update_r_info(self):                                        # display rotator information
        self.utctime.set(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))
        self.localtime.set(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.r_az.set(self.mqtt.az)
        self.r_el.set(self.mqtt.el)
        if self.tracking:
            self.msv4.set('Tracked satellite:')
            self.msv5.set('Time until LOS:')
            self.r_satellite.set(self.tracked_satellite)
            self.r_time_till_los.set(self.timedelta_formatter(self.ts_los_time - datetime.now(timezone.utc)))
        else:
            self.msv4.set('Next satellite:')
            self.msv5.set('Tracking starts in:')
            if self.first_pass_time is not None:
                self.r_satellite.set(self.next_satellite)
                self.r_time_till_los.set(self.timedelta_formatter(self.first_pass_time - datetime.now(timezone.utc)))
        if self.mqtt.connected:
            self.mqtt_status.set('connected')
        else:
            self.mqtt_status.set('disconnected')
        self.after(1000, self.update_r_info)

    def update_listbox0(self):
        self.fill_listbox(self.listbox0, self.beyond_tools.satellites)
        self.msv0.set(f'All satellites ({self.beyond_tools.satellites_count}): ')

    def update_listbox1(self):
        self.fill_listbox(self.listbox1, sorted(self.selected_satellites))
        self.msv1.set(f'Selected satellites ({len(self.selected_satellites)}): ')

    def update_listbox2(self):
        self.fill_listbox(self.listbox2, self.tracked_satellites)
        self.msv2.set(f'Tracked satellites ({len(self.tracked_satellites)}): ')

    def az_increase_offset(self):
        self.az_offset.increase()
        self.mqtt.publish_az_offset(f'{self.az_offset.offset}')

    def az_decrease_offset(self):
        self.az_offset.decrease()
        self.mqtt.publish_az_offset(f'{self.az_offset.offset}')

    def el_increase_offset(self):
        self.el_offset.increase()
        self.mqtt.publish_el_offset(f'{self.el_offset.offset}')

    def el_decrease_offset(self):
        self.el_offset.decrease()
        self.mqtt.publish_el_offset(f'{self.el_offset.offset}')

    def set_polarization(self, pol):                                # sets antenna polarization
        self.r_pol.set(pol)
        self.mqtt.publish_polarization(pol)

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
        word = self.ss0.get().upper()
        self.listbox0.delete(0, END)
        if word == '':
            self.update_listbox0()
            return
        filtered_data = list()
        for item in self.beyond_tools.satellites:
            if item.find(word) >= 0:
                filtered_data.append(item)
        self.fill_listbox(self.listbox0, filtered_data)
        self.msv0.set(f'All satellites ({len(filtered_data)}): ')

    def search1(self, event):                                       # fill listbox1 with filtered satellite names
        word = self.ss1.get().upper()
        self.listbox1.delete(0, END)
        if word == '':
            self.fill_listbox(self.listbox1, self.selected_satellites)
            self.msv1.set(f'Selected satellites ({len(self.selected_satellites)}): ')
            return
        filtered_data = list()
        for item in self.selected_satellites:
            if item.find(word) >= 0:
                filtered_data.append(item)
        self.fill_listbox(self.listbox1, filtered_data)
        self.msv1.set(f'Selected satellites ({len(filtered_data)}): ')

    def add_to_tracked(self):                                       # add satellite to tracking
        sat = self.sat_entry0.get()
        if sat in self.beyond_tools.satellites and sat not in self.selected_satellites:
            self.selected_satellites.append(sat)
        self.update_listbox1()
        self.ss0.set('')

    def remove_from_tracked(self):                                  # remove satellite from tracking
        sat = self.sat_entry1.get()
        if sat in self.selected_satellites:
            self.selected_satellites.remove(sat)
        self.update_listbox1()
        self.ss1.set('')

    def track_satellites(self):                                     # track all satellites in track_satellites list
        if not self.track_button_pressed:
            self.track_button_pressed = True
            self.tracked_satellites = sorted(self.selected_satellites)
            self.update_listbox2()
            self.json_tool.overwrite_variable('tracked_satellites', self.tracked_satellites)
            self.tso = [TrackedSatellite(self, sat) for sat in self.tracked_satellites]
            self.find_first_pass()

    def find_first_pass(self):
        if len(self.tso) == 0:
            return
        if len(self.tso) == 1:
            sat = self.tso[0]
            self.first_pass_time = sat.aos_time
            self.next_satellite = sat.name
        if len(self.tso) > 1:
            my_dict = {}
            for x in self.tso:
                my_dict[x.name] = x.aos_time
            sorted_list = sorted(my_dict.items(), key=lambda p: p[1], reverse=False)
            first_pass = list(sorted_list[0])
            first_sat = first_pass[0]
            if first_sat == self.tracked_satellite:
                first_pass = list(sorted_list[1])
                first_sat = first_pass[0]
            self.first_pass_time = first_pass[1]
            self.next_satellite = first_sat
        self.first_pass_info.set(f'Next pass: {self.next_satellite}, AOS: {self.first_pass_time.strftime('%d %B %Y %H:%M:%S UTC')}')

    def predict(self, sat):                                         # create data about the first pass of selected satellite
        if sat == '':
            return
        if sat in self.beyond_tools.satellites:
            if sat in self.tracked_satellites:
                for x in self.tso:
                    if x.name == sat:
                        self.show_prediction(x.name, x.aos_time, x.max_time, x.los_time, x.aos_az, x.max_az, x.los_az, x.max_el)
                        break
            else:
                aos_time, max_time, los_time, aos_az, max_az, los_az, max_el = self.beyond_tools.predict_first_pass(sat)
                try:
                    self.show_prediction(sat, aos_time, max_time, los_time, aos_az, max_az, los_az, max_el)
                except NameError:
                    self.msv3.set(f'Sorry, could not predict {sat}.')
                    self.empty_prediction()
        else:
            self.msv3.set(f'Sorry, {sat} is not a satellite in orbit.')

    def show_prediction(self, sat, aos_time, max_time, los_time, aos_az, max_az, los_az, max_el):
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

    def empty_prediction(self):
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

    def close_window(self):
        if not self.tracking or not self.mqtt.connected:
            try:
                self.mqtt.connect_thread.cancel()
            except AttributeError:
                pass
            if self.tracking_thread.is_alive():
                self.tracking_thread.join()
            self.tle_updator.update_thread.cancel()
            for x in self.tso:
                try:
                    x.tracking_thread.cancel()
                except AttributeError:
                    pass
            self.destroy()


class Offset:
    def __init__(self, app, string_var):
        self.string_var = string_var
        self.offset = 0.0
        self.offset_step = 0.2
        self.app = app
        self.publish()

    def increase(self):
        if not self.app.tracking:
            self.offset += self.offset_step
            self.publish()

    def decrease(self):
        if not self.app.tracking:
            self.offset -= self.offset_step
            self.publish()

    def publish(self):
        self.offset = round(self.offset, 2)
        self.string_var.set(f'{self.offset}')


class TrackedSatellite:
    def __init__(self, app, name):
        self.name = name                                            # satellite name
        self.times, self.azims, self.elevs = [], [], []             # list of azims and elevs in time during the pass
        self.aos_time = datetime.now(timezone.utc)                              # AOS time of the first pass
        self.max_time = datetime.now(timezone.utc)                              # MAX time of the first pass
        self.los_time = datetime.now(timezone.utc)                              # LOS time of the first pass
        self.aos_az = 0                                             # AOS azimuth
        self.max_az = 0                                             # MAX azimuth
        self.los_az = 0                                             # LOS azimuth
        self.max_el = 0                                             # MAX elevation
        self.start_time_seconds = 0                                 # time in seconds until AOS
        self.delay_before_tracking = timedelta(seconds=10)          # time needed for rotator to turn to AOS azimuth
        self.app = app
        self.tracking_thread = None
        self.create_data()

    def print_info(self, msg):                                      # print info with satellite name and timestamp
        print(f'{datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}, {self.name} {msg}')

    def create_data(self, init_delay=0):                                          # create data about the first pass of satellite
        self.times.clear()                                          # clear the previous data
        self.azims.clear()
        self.elevs.clear()
        (self.times, self.azims, self.elevs, self.aos_time, self.max_time, self.los_time, self.aos_az, self.max_az,
         self.los_az, self.max_el) = self.app.beyond_tools.create_data(self.name, init_delay=init_delay)
        self.start_time_seconds = (self.aos_time - datetime.now(timezone.utc) - self.delay_before_tracking).seconds
        self.tracking_thread = Timer(self.start_time_seconds, self.track)
        self.tracking_thread.start()
        self.app.find_first_pass()
        self.print_info(f'created data, AOS: {self.aos_time.strftime("%Y-%m-%d %H:%M:%S UTC")}, MAX elevation: {self.max_el}')

    def track(self):                                                # track the satellite when crossing the sky
        if not self.app.tracking:                                        # if any other satellite is not tracked right now
            if self.aos_time > datetime.now(timezone.utc):
                self.app.tracking = True
                self.app.tracked_satellite = self.name
                self.app.ts_los_time = self.los_time
                self.app.mqtt.publish_action('start')
                self.app.find_first_pass()
                self.app.predict(self.name)
                wait_time = (self.aos_time - datetime.now(timezone.utc)).total_seconds()
                self.print_info(f'will fly over your head in {int(wait_time)} seconds')
                self.app.mqtt.publish_start_azimuth(self.aos_az)
                sleep(wait_time)
                self.print_info('tracking started')
                for x in range(len(self.times) - 1):
                    delta_t = (self.times[x + 1] - self.times[x]).total_seconds()
                    delta_az = self.azims[x + 1] - self.azims[x]
                    delta_el = self.elevs[x + 1] - self.elevs[x]
                    if delta_az > 180:
                        delta_az -= 360
                    if delta_az < -180:
                        delta_az += 360
                    self.app.mqtt.publish_data(delta_t, delta_az, delta_el)
                    sleep(delta_t)
                self.app.mqtt.publish_action('stop')
                self.print_info('tracking ended')
                self.app.tracking = False
                self.app.predict(self.app.next_satellite)
            else:
                self.print_info('tracking passed')
        else:
            self.print_info(f'cannot be tracked now, because {self.app.tracked_satellite} is being tracked')
        self.create_data(init_delay=1)
