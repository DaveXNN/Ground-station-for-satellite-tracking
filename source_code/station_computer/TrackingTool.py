########################################################################################################################
#                                                                                                                      #
#    Author:         D. Nenicka                                                                                        #
#    Created:        3. 11. 2023                                                                                       #
#    Modified:       19. 10. 2024                                                                                      #
#    Description:    Simple GUI for satellite tracking                                                                 #
#                                                                                                                      #
########################################################################################################################


from datetime import datetime, timedelta, timezone                  # module for operations with date and time
from threading import Thread, Timer                                 # module for running more processes in parallel
from tkinter import *                                               # module for creating GUI
from tkinter import messagebox                                      # module for dialog windows
from time import sleep                                              # module with sleep() function

from BeyondTools import BeyondTools                                 # module for predicting satellite visibility
from Mqtt import Mqtt                                               # module for MQTT communication


class TrackingTool(Tk):                                             # GUI for satellite tracking
    def __init__(self, json_tool, tle_updator) -> None:
        super().__init__()

        # Initialize modules
        self.json_tool = json_tool                                  # module for working with json configuration file
        self.mqtt = Mqtt()                                          # module for MQTT communication
        self.beyond_tools = BeyondTools(json_tool.content)          # module for satellite pass predictions
        self.tle_updator = tle_updator                              # module for updating TLE data

        # Initialize basic GUI variables
        self.program_name = self.json_tool.content['program_name']  # program name
        self.icon = self.json_tool.content['icon']                  # icon file of the program window
        self.iconbitmap(self.icon)                                  # program icon
        w, h = self.maxsize()
        self.minsize(w-100, h-100)
        self.bg_color = '#daa520'                                   # background color #1d1f1b
        self.text_color = 'black'                                   # text color
        self.font0 = 'TkTextFont 12'                                # basic font
        self.font_title = 'Helvetica 20 bold'                       # font used in main title
        self.font_subtitle = 'Helvetica 15 bold'                    # font used in subtitles
        self.configure(bg=self.bg_color)                            # set background color
        self.title(self.program_name)                               # set program title

        # Basic variables
        self.selected_satellites = self.json_tool.content['tracked_satellites'] # list of satellites selected for tracking
        for sat in self.selected_satellites:
            if sat not in self.beyond_tools.satellites:
                self.selected_satellites.remove(sat)
        self.tracked_satellites = []                                # list of currently tracked satellites (names only)
        self.tso = []                                               # list of TrackedSatellite objects
        self.track_button_pressed = False                           # True if Track button has already been pressed
        self.tracking = False                                       # True if rotator is currently tracking a satellite
        self.tracked_satellite = None                               # name of currently tracked satellite
        self.next_satellite = None                                  # name of the first satellite to be tracked

        # Tkinter string variables
        self.ss0 = StringVar()                                      # searching in listbox0
        self.ss1 = StringVar()                                      # searching in listbox1
        self.listbox_title0 = StringVar()                           # title of All satellites listbox
        self.listbox_title1 = StringVar()                           # title of Selected satellites listbox
        self.listbox_title2 = StringVar()                           # title of Tracked satellites listbox
        self.prediction_title = StringVar()                         # title of pass predictions
        self.r_sat_title = StringVar()                              # title of Next/Tracked satellite
        self.r_time_title = StringVar()                             # title of Tracking starts in/Time until LOS
        self.date = StringVar()                                     # date of the pass prediction
        self.aos_time = StringVar()                                 # AOS of the pass prediction
        self.aos_az = StringVar()                                   # AOS azimuth of the pass prediction
        self.max_time = StringVar()                                 # MAX time of the pass prediction
        self.max_az = StringVar()                                   # MAX azimuth of the pass prediction
        self.max_el = StringVar()                                   # MAX elevation of the pass prediction
        self.los_time = StringVar()                                 # LOS time of the pass prediction
        self.los_az = StringVar()                                   # LOS azimuth of the pass prediction
        self.duration = StringVar()                                 # duration of the satellite pass in pass prediction
        self.utctime = StringVar()                                  # UTC
        self.localtime = StringVar()                                # Local time
        self.r_az = StringVar()                                     # current rotator azimuth
        self.r_el = StringVar()                                     # current rotator elevation
        self.az_offset_var = StringVar()                            # azimuth offset
        self.el_offset_var = StringVar()                            # elevation offset
        self.r_satellite = StringVar()                              # Next/Tracked satellite name
        self.r_time_till_los = StringVar()                          # Time until LOS/Tracking starts in
        self.r_pol = StringVar()                                    # current antenna polarization
        self.mqtt_status = StringVar()                              # MQTT status
        self.next_pass_info = StringVar()                           # information about the next pass
        self.tle_info = StringVar()                                 # information about time of the last TLE update

        # Azimuth and elevation offsets
        self.az_offset = Offset(self,'az_offset', self.az_offset_var)   # azimuth offset
        self.el_offset = Offset(self,'el_offset', self.el_offset_var)   # elevation offset

        # Listbox definition
        self.listbox0 = MyListbox(self, self.listbox_title0, 'All satellites', self.beyond_tools.satellites, self.font0, 0.125, 0.3, 0.2, 0.15)
        self.listbox1 = MyListbox(self, self.listbox_title1, 'Selected satellites', self.selected_satellites, self.font0, 0.375,0.3, 0.2, 0.15)
        self.listbox2 = MyListbox(self, self.listbox_title2, 'Tracked satellites', self.tracked_satellites, self.font0, 0.75, 0.75, 0.2, 0.35)

        # Labels definition
        self.main_title = Label(self, text=self.program_name, font=self.font_title, bg=self.bg_color, fg=self.text_color)
        self.main_title.place(relx=0.5, rely=0.05, anchor=CENTER)
        self.left_title = Label(self, text='Predicting satellite visibility', font=self.font_subtitle, bg=self.bg_color, fg=self.text_color)
        self.left_title.place(relx=0.25, rely=0.10, anchor=CENTER)
        self.right_title = Label(self, text='Rotator information', font=self.font_subtitle, bg=self.bg_color, fg=self.text_color)
        self.right_title.place(relx=0.75, rely=0.10, anchor=CENTER)
        self.ll00 = Label(self, text='Select a satellite by double click and click Predict to predict its first pass:', font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.ll00.place(relx=0.25, rely=0.15, anchor=CENTER)
        self.ll01 = Label(self, textvariable=self.listbox_title0, font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.ll01.place(relx=0.125, rely=0.20, anchor=CENTER)
        self.ll02 = Label(self, textvariable=self.listbox_title1, font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.ll02.place(relx=0.375, rely=0.20, anchor=CENTER)
        self.ll03 = Label(self, textvariable=self.prediction_title, font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.ll03.place(relx=0.25, rely=0.50, anchor=CENTER)
        self.ll04 = Label(self, text='Date UTC:', bg=self.bg_color, font=self.font0, fg=self.text_color)
        self.ll04.place(relx=0.05, rely=0.55, anchor=W)
        self.ll05 = Label(self, text='Acquisition of satellite (AOS):', font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.ll05.place(relx=0.05, rely=0.60, anchor=W)
        self.ll06 = Label(self, text='AOS azimuth:', font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.ll06.place(relx=0.05, rely=0.65, anchor=W)
        self.ll07 = Label(self, text='Maximum elevation (MAX):', font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.ll07.place(relx=0.05, rely=0.70, anchor=W)
        self.ll08 = Label(self, text='MAX azimuth:', font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.ll08.place(relx=0.05, rely=0.75, anchor=W)
        self.ll09 = Label(self, text='MAX elevation:', font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.ll09.place(relx=0.05, rely=0.80, anchor=W)
        self.ll10 = Label(self, text='Loss of satellite (LOS):', font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.ll10.place(relx=0.05, rely=0.85, anchor=W)
        self.ll11 = Label(self, text='LOS azimuth:', font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.ll11.place(relx=0.05, rely=0.90, anchor=W)
        self.ll12 = Label(self, text='Duration:', font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.ll12.place(relx=0.05, rely=0.95, anchor=W)
        self.rl00 = Label(self, text='Time UTC:', font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.rl00.place(relx=0.525, rely=0.15, anchor=W)
        self.rl01 = Label(self, text='Local time:', font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.rl01.place(relx=0.775, rely=0.15, anchor=W)
        self.rl02 = Label(self, text='Azimuth (AZ):', font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.rl02.place(relx=0.525, rely=0.20, anchor=W)
        self.rl03 = Label(self, text='Elevation (EL):', font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.rl03.place(relx=0.775, rely=0.20, anchor=W)
        self.rl04 = Label(self, text='AZ offset:', font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.rl04.place(relx=0.525, rely=0.25, anchor=W)
        self.rl05 = Label(self, text='EL offset:', font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.rl05.place(relx=0.775, rely=0.25, anchor=W)
        self.rl06 = Label(self, textvariable=self.r_sat_title, font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.rl06.place(relx=0.525, rely=0.30, anchor=W)
        self.rl07 = Label(self, textvariable=self.r_time_title, font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.rl07.place(relx=0.775, rely=0.30, anchor=W)
        self.rl08 = Label(self, text='Antenna polarization:', font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.rl08.place(relx=0.525, rely=0.35, anchor=W)
        self.rl09 = Label(self, text='MQTT status:', font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.rl09.place(relx=0.525, rely=0.40, anchor=W)
        self.rl10 = Label(self, textvariable=self.next_pass_info, font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.rl10.place(relx=0.750, rely=0.47, anchor=CENTER)
        self.rl11 = Label(self, textvariable=self.listbox_title2, font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.rl11.place(relx=0.750, rely=0.55, anchor=CENTER)
        self.rl12 = Label(self, textvariable=self.tle_info, font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.rl12.place(relx=0.750, rely=0.95, anchor=CENTER)

        # Entries definition
        self.sat_entry0 = Entry(textvariable=self.ss0, font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.sat_entry0.place(relx=0.125, rely=0.40, relwidth=0.2, relheight=0.035, anchor=CENTER)
        self.sat_entry0.bind('<Return>', func=lambda event: self.listbox0.search(event, self.ss0.get()))
        self.sat_entry1 = Entry(textvariable=self.ss1, font=self.font0, bg=self.bg_color, fg=self.text_color)
        self.sat_entry1.place(relx=0.375, rely=0.40, relwidth=0.2, relheight=0.035, anchor=CENTER)
        self.sat_entry1.bind('<Return>', func=lambda event: self.listbox1.search(event, self.ss1.get()))
        self.le0 = Entry(textvariable=self.date, font=self.font0, justify=RIGHT, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.le0.place(relx=0.25, rely=0.55, relwidth=0.2, relheight=0.035, anchor=W)
        self.le1 = Entry(textvariable=self.aos_time, font=self.font0, justify=RIGHT, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.le1.place(relx=0.25, rely=0.60, relwidth=0.2, relheight=0.035, anchor=W)
        self.le2 = Entry(textvariable=self.aos_az, font=self.font0, justify=RIGHT, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.le2.place(relx=0.25, rely=0.65, relwidth=0.2, relheight=0.035, anchor=W)
        self.le3 = Entry(textvariable=self.max_time, font=self.font0, justify=RIGHT, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.le3.place(relx=0.25, rely=0.70, relwidth=0.2, relheight=0.035, anchor=W)
        self.le4 = Entry(textvariable=self.max_az, font=self.font0, justify=RIGHT, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.le4.place(relx=0.25, rely=0.75, relwidth=0.2, relheight=0.035, anchor=W)
        self.le5 = Entry(textvariable=self.max_el, font=self.font0, justify=RIGHT, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.le5.place(relx=0.25, rely=0.80, relwidth=0.2, relheight=0.035, anchor=W)
        self.le6 = Entry(textvariable=self.los_time, font=self.font0, justify=RIGHT, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.le6.place(relx=0.25, rely=0.85, relwidth=0.2, relheight=0.035, anchor=W)
        self.le7 = Entry(textvariable=self.los_az, font=self.font0, justify=RIGHT, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.le7.place(relx=0.25, rely=0.90, relwidth=0.2, relheight=0.035, anchor=W)
        self.le8 = Entry(textvariable=self.duration, font=self.font0, justify=RIGHT, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.le8.place(relx=0.25, rely=0.95, relwidth=0.2, relheight=0.035, anchor=W)
        self.re0 = Entry(textvariable=self.utctime, font=self.font0, justify=CENTER, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.re0.place(relx=0.625, rely=0.15, relwidth=0.1, relheight=0.035, anchor=W)
        self.re1 = Entry(textvariable=self.localtime, font=self.font0, justify=CENTER, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.re1.place(relx=0.875, rely=0.15, relwidth=0.1, relheight=0.035, anchor=W)
        self.re2 = Entry(textvariable=self.r_az, font=self.font0, justify=CENTER, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.re2.place(relx=0.625, rely=0.20, relwidth=0.1, relheight=0.035, anchor=W)
        self.re3 = Entry(textvariable=self.r_el, font=self.font0, justify=CENTER, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.re3.place(relx=0.875, rely=0.20, relwidth=0.1, relheight=0.035, anchor=W)
        self.re4 = Entry(textvariable=self.az_offset_var, font=self.font0, justify=CENTER, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.re4.place(relx=0.650, rely=0.25, relwidth=0.05, relheight=0.035, anchor=W)
        self.re5 = Entry(textvariable=self.el_offset_var, font=self.font0, justify=CENTER, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.re5.place(relx=0.900, rely=0.25, relwidth=0.05, relheight=0.035, anchor=W)
        self.re6 = Entry(textvariable=self.r_satellite, font=self.font0, justify=CENTER, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.re6.place(relx=0.625, rely=0.30, relwidth=0.1, relheight=0.035, anchor=W)
        self.re7 = Entry(textvariable=self.r_time_till_los, font=self.font0, justify=CENTER, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.re7.place(relx=0.875, rely=0.30, relwidth=0.1, relheight=0.035, anchor=W)
        self.re8 = Entry(textvariable=self.r_pol, font=self.font0, justify=CENTER, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.re8.place(relx=0.625, rely=0.35, relwidth=0.1, relheight=0.035, anchor=W)
        self.re9 = Entry(textvariable=self.mqtt_status, font=self.font0, justify=CENTER, state='readonly', readonlybackground=self.bg_color, fg=self.text_color)
        self.re9.place(relx=0.625, rely=0.40, relwidth=0.1, relheight=0.035, anchor=W)

        # Buttons definition
        self.predict_button = Button(self, text='Predict', font=self.font0, command=lambda: self.predict(self.sat_entry0.get()), bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.predict_button.place(relx=0.075, rely=0.45, relwidth=0.1, relheight=0.04, anchor=CENTER)
        self.add_button = Button(self, text='Add to tracking', font=self.font0, command=self.add_to_tracked, bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.add_button.place(relx=0.175, rely=0.45, relwidth=0.1, relheight=0.04, anchor=CENTER)
        self.remove_button = Button(self, text='Remove from tracking', font=self.font0, command=self.remove_from_tracked, bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.remove_button.place(relx=0.325, rely=0.45, relwidth=0.1, relheight=0.04, anchor=CENTER)
        self.track_button = Button(self, text='Track', font=self.font0, command=self.start_tracking, bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.track_button.place(relx=0.425, rely=0.45, relwidth=0.1, relheight=0.04, anchor=CENTER)
        self.ver_pol = Button(self, text='Vertical', font=self.font0, command=lambda: self.set_polarization('Vertical'), bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.ver_pol.place(relx=0.775, rely=0.35, relwidth=0.05, relheight=0.04, anchor=W)
        self.hor_pol = Button(self, text='Horizontal', font=self.font0, command=lambda: self.set_polarization('Horizontal'), bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.hor_pol.place(relx=0.825, rely=0.35, relwidth=0.05, relheight=0.04, anchor=W)
        self.lhcp_pol = Button(self, text='LHCP', font=self.font0, command=lambda: self.set_polarization('LHCP'), bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.lhcp_pol.place(relx=0.875, rely=0.35, relwidth=0.05, relheight=0.04, anchor=W)
        self.rhcp_pol = Button(self, text='RHCP', font=self.font0, command=lambda: self.set_polarization('RHCP'), bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.rhcp_pol.place(relx=0.925, rely=0.35, relwidth=0.05, relheight=0.04, anchor=W)
        self.shutdown_button = Button(self, text='Shut down rotator', font=self.font0, command=self.shutdown_rotator, bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.shutdown_button.place(relx=0.775, rely=0.40, relwidth=0.1, relheight=0.04, anchor=W)
        self.close_button = Button(self, text='Quit', font=self.font0, command=self.close_window, bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.close_button.place(relx=0.875, rely=0.40, relwidth=0.1, relheight=0.04, anchor=W)
        self.az_inc_button = Button(self, text='+', font=self.font0, command=self.az_offset.increase, bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.az_inc_button.place(relx=0.625, rely=0.25, relwidth=0.025, relheight=0.035, anchor=W)
        self.az_dec_button = Button(self, text='-', font=self.font0, command=self.az_offset.decrease, bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.az_dec_button.place(relx=0.700, rely=0.25, relwidth=0.025, relheight=0.035, anchor=W)
        self.el_inc_button = Button(self, text='+', font=self.font0, command=self.el_offset.increase, bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.el_inc_button.place(relx=0.875, rely=0.25, relwidth=0.025, relheight=0.035, anchor=W)
        self.el_dec_button = Button(self, text='-', font=self.font0, command=self.el_offset.decrease, bg=self.bg_color, fg=self.text_color, activebackground=self.bg_color)
        self.el_dec_button.place(relx=0.950, rely=0.25, relwidth=0.025, relheight=0.035, anchor=W)

        # Set text of some of the string variables
        self.prediction_title.set('First pass prediction:')
        self.r_pol.set('Vertical')
        self.tle_info.set(f'Last TLE update: {self.tle_updator.last_update.strftime("%d %B %Y %H:%M:%S UTC")}')

        # run basic functions
        self.update_rotator_info()                                  # display rotator information every 1 second
        self.tracking_thread = None                                 # thread for starting satellite tracking
        self.mainloop()

    @staticmethod
    def timedelta_formatter(td) -> str:                             # function that returns timedelta object in string format %H %M %S
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{hours:02}:{minutes:02}:{seconds:02}'

    def add_to_tracked(self) -> None:                               # add satellite to tracked satellite list
        sat = self.sat_entry0.get()
        if sat in self.beyond_tools.satellites and sat not in self.selected_satellites:
            self.selected_satellites.append(sat)
            self.selected_satellites = sorted(self.selected_satellites)
        self.listbox1.fill(self.selected_satellites)
        self.ss0.set('')

    def remove_from_tracked(self) -> None:                          # remove satellite from tracked satellites list
        sat = self.sat_entry1.get()
        if sat in self.selected_satellites:
            self.selected_satellites.remove(sat)
        self.listbox1.fill(self.selected_satellites)
        self.ss1.set('')

    def start_tracking(self) -> None:                               # start satellite tracking
        self.tracking_thread = Thread(target=self.track_satellites, daemon=True)
        self.tracking_thread.start()

    def track_satellites(self) -> None:                             # track all satellites in track_satellites list
        if not self.track_button_pressed:
            self.track_button_pressed = True
            self.tracked_satellites = self.selected_satellites
            self.listbox2.fill(self.tracked_satellites)
            self.json_tool.overwrite_variable('tracked_satellites', self.tracked_satellites)
            self.tso = [TrackedSatellite(self, satellite) for satellite in self.tracked_satellites]
            self.find_first_pass()
            self.show_prediction(self.next_satellite.data)

    def set_polarization(self, pol: str) -> None:                   # remotely set antenna polarization
        self.r_pol.set(pol)
        self.mqtt.publish_polarization(pol)

    def update_rotator_info(self) -> None:                          # display rotator information every 1 second
        self.utctime.set(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))
        self.localtime.set(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.r_az.set(self.mqtt.az)
        self.r_el.set(self.mqtt.el)
        if self.tracking:
            self.r_sat_title.set('Tracked satellite:')
            self.r_time_title.set('Time until LOS:')
            self.r_satellite.set(self.tracked_satellite.data['name'])
            self.r_time_till_los.set(self.timedelta_formatter(self.tracked_satellite.data['los_time'] - datetime.now(timezone.utc)))
        else:
            self.r_sat_title.set('Next satellite:')
            self.r_time_title.set('Tracking starts in:')
            if self.next_satellite is not None:
                self.r_satellite.set(self.next_satellite.data['name'])
                self.r_time_till_los.set(self.timedelta_formatter(self.next_satellite.data['aos_time'] - datetime.now(timezone.utc)))
        if self.mqtt.connected:
            self.mqtt_status.set('connected')
        else:
            self.mqtt_status.set('disconnected')
        self.after(1000, self.update_rotator_info)

    def predict(self, satellite: str) -> None:                      # create data about the first pass of selected satellite
        if satellite == '':
            return
        if satellite in self.beyond_tools.satellites:
            if satellite in self.tracked_satellites:
                for sat in self.tso:
                    if sat.data['name'] == satellite:
                        self.show_prediction(sat.data)
            else:
                data = self.beyond_tools.predict_first_pass(satellite)
                try:
                    self.show_prediction(data)
                except NameError:
                    self.prediction_title.set(f'Sorry, could not predict {satellite}.')
                    self.empty_prediction()
        else:
            self.prediction_title.set(f'{satellite} is not a satellite in orbit around the Earth.')

    def show_prediction(self, prediction: dict) -> None:            # display satellite prediction data
        self.prediction_title.set(f'First pass prediction for {prediction['name']}: ')
        self.date.set(prediction['aos_time'].strftime('%d %B %Y'))
        self.aos_time.set(prediction['aos_time'].strftime('%H:%M:%S'))
        self.aos_az.set(f'{prediction['aos_az']:.2f}')
        self.max_time.set(prediction['max_time'].strftime('%H:%M:%S'))
        self.max_az.set(f'{prediction['max_az']:.2f}')
        self.max_el.set(f'{prediction['max_el']:.2f}')
        self.los_time.set(prediction['los_time'].strftime('%H:%M:%S'))
        self.los_az.set(f'{prediction['los_az']:.2f}')
        self.duration.set(self.timedelta_formatter(prediction['los_time'] - prediction['aos_time']))

    def empty_prediction(self) -> None:                             # clear satellite prediction data
        self.prediction_title.set('First pass prediction:')
        self.date.set('')
        self.aos_time.set('')
        self.aos_az.set('')
        self.max_time.set('')
        self.max_az.set('')
        self.max_el.set('')
        self.los_time.set('')
        self.los_az.set('')
        self.duration.set('')

    def find_first_pass(self) -> None:                              # find the first satellite in tracked satellites that will appear above the horizont
        tsn = len(self.tso)
        if tsn == 0:
            return
        if tsn == 1:
            self.next_satellite = self.tso[0]
        if tsn > 1:
            new_list = sorted(self.tso, key=lambda p: p.data['aos_time'], reverse=False)
            first_sat = new_list[0]
            if first_sat == self.tracked_satellite:
                first_sat = new_list[1]
            self.next_satellite = first_sat
        self.next_pass_info.set(f'Next pass: {self.next_satellite.data['name']}, AOS: {self.next_satellite.data['aos_time'].strftime('%d %B %Y %H:%M:%S UTC')}')

    def shutdown_rotator(self) -> None:                             # remotely shut down the rotator
        if self.mqtt.connected:
            if self.tracking:
                messagebox.showinfo(title='Information', message='You cannot shut down the rotator while tracking.')
            elif messagebox.askokcancel(title='Information', message='Are you sure to shut down the rotator?'):
                self.mqtt.publish_action('shutdown')

    def close_window(self) -> None:                                 # close Satellite Tracking Software
        if self.tracking:
            messagebox.showinfo(title='Information', message=f'You cannot close {self.program_name} while tracking.')
        elif messagebox.askokcancel(title='Information', message=f'Are you sure to quit {self.program_name}?'):
            try:
                self.mqtt.connect_thread.cancel()
            except AttributeError:
                pass
            try:
                self.tracking_thread.join()
            except AttributeError:
                pass
            self.tle_updator.update_thread.cancel()
            for x in self.tso:
                try:
                    x.tracking_thread.cancel()
                except AttributeError:
                    pass
            self.destroy()


class MyListbox(Listbox):                                           # object for working with listboxes
    def __init__(self, app, title_var, title, content, font, rel_x, rel_y, width: float, height: float) -> None:
        super().__init__(app, font=font, bg=app.bg_color, fg=app.text_color, borderwidth=0, highlightbackground='black')
        self.place(relx=rel_x, rely=rel_y, relwidth=width, relheight=height, anchor=CENTER)
        self.bind('<Double-1>', self.select)                        # bind double click on an item in listbox with select function
        self.app = app
        self.title_var = title_var                                  # variable for listbox title
        self.title = title                                          # listbox title
        self.content = content                                      # listbox content
        self.fill(content)                                          # fill listbox with the content

    def fill(self, content: list, overwrite=True) -> None:          # fill listbox with content
        if overwrite:
            self.content = content
        self.delete(0, END)
        for item in content:
            self.insert(END, item)
        self.title_var.set(''.join([self.title, ' (', str(len(content)), '):']))

    def select(self, event) -> None:                                # when you click on a name in listbox, it will be displayed in ss0 and ss1 entry
        cs = self.get(self.curselection())
        self.app.ss0.set(cs)
        self.app.ss1.set(cs)

    def search(self, event, word: str) -> None:                     # fill listbox with filtered satellite names you search
        word = word.upper()
        self.delete(0, END)
        if word == '':
            self.fill(self.content, overwrite=False)
            return
        filtered_data = list()
        for item in self.content:
            if item.find(word) >= 0:
                filtered_data.append(item)
        self.fill(filtered_data, overwrite=False)


class Offset:                                                       # object to control azimuth and elevation offset
    def __init__(self, app, topic_name: str, string_var: StringVar) -> None:
        self.app = app
        self.topic_name = topic_name                                # MQTT topic name
        self.string_var = string_var                                # variable to display offset value
        self.offset = 0.0                                           # offset value
        self.offset_step = 0.1                                      # step of changing the offset
        self.publish()

    def increase(self) -> None:                                     # increase offset by one step
        if not self.app.tracking and self.app.mqtt.connected:
            self.offset += self.offset_step
            self.publish()

    def decrease(self) -> None:                                     # decrease offset by one step
        if not self.app.tracking and self.app.mqtt.connected:
            self.offset -= self.offset_step
            self.publish()

    def publish(self) -> None:                                      # display and publish offset via MQTT broker
        self.offset = round(self.offset, 2)
        self.string_var.set(f'{self.offset}')
        self.app.mqtt.publish_offset(self.topic_name, self.offset)


class TrackedSatellite:                                             # object for tracked satellites
    def __init__(self, app, name: str) -> None:
        self.tracking_data = []                                     # list of azims and elevs in time during the pass
        self.data = {'name': name}                                  # dictionary with satellite info
        self.start_time_seconds = 0                                 # time in seconds until AOS
        self.delay_before_tracking = timedelta(seconds=10)          # time needed for rotator to turn to AOS azimuth
        self.app = app
        self.tracking_thread = None
        self.create_data()

    def print_info(self, msg: str) -> None:                         # print message with satellite name, timestamp
        print(f'{datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}, {self.data['name']} {msg}')

    def create_data(self) -> None:                                  # create data about the first pass of satellite
        self.tracking_data.clear()
        self.tracking_data = self.app.beyond_tools.create_data(self.data['name'])
        length = len(self.tracking_data[0]) - 1
        self.data['aos_time'] = self.tracking_data[0][0]
        self.data['los_time'] = self.tracking_data[0][length]
        self.data['aos_az'] = self.tracking_data[1][0]
        self.data['los_az'] = self.tracking_data[1][length]
        self.data['max_el'] = max(self.tracking_data[2])
        max_index = self.tracking_data[2].index(self.data['max_el'])
        self.data['max_time'] = self.tracking_data[0][max_index]
        self.data['max_az'] = self.tracking_data[1][max_index]
        self.start_time_seconds = (self.data['aos_time'] - datetime.now(timezone.utc) - self.delay_before_tracking).seconds
        self.tracking_thread = Timer(self.start_time_seconds, self.track)
        self.tracking_thread.start()
        self.app.find_first_pass()
        self.print_info(f'created data, AOS: {self.data['aos_time'].strftime("%Y-%m-%d %H:%M:%S UTC")}, MAX elevation: {self.data['max_el']}')

    def track(self) -> None:                                        # track the satellite
        if self.app.mqtt.connected:
            if not self.app.tracking:
                if self.data['aos_time'] > datetime.now(timezone.utc):
                    self.app.tracking = True
                    self.app.tracked_satellite = self
                    self.app.ts_los_time = self.data['los_time']
                    self.app.mqtt.publish_action('start')
                    self.app.find_first_pass()
                    self.app.show_prediction(self.data)
                    wait_time = (self.data['aos_time'] - datetime.now(timezone.utc)).total_seconds()
                    self.print_info(f'will fly over your head in {int(wait_time)} seconds')
                    self.app.mqtt.publish_aos_azimuth(self.data['aos_az'])
                    sleep(wait_time)
                    self.print_info('tracking started')
                    for x in range(len(self.tracking_data[0]) - 1):
                        delta_t = (self.tracking_data[0][x + 1] - self.tracking_data[0][x]).total_seconds()
                        delta_az = self.tracking_data[1][x + 1] - self.tracking_data[1][x]
                        delta_el = self.tracking_data[2][x + 1] - self.tracking_data[2][x]
                        if delta_az > 180:
                            delta_az -= 360
                        if delta_az < -180:
                            delta_az += 360
                        self.app.mqtt.publish_data(delta_t, delta_az, delta_el)
                        sleep(delta_t)
                    self.app.mqtt.publish_action('stop')
                    self.print_info('tracking ended')
                    self.app.tracking = False
                    self.app.tracked_satellite = None
                    self.app.show_prediction(self.app.next_satellite.data)
                else:
                    self.print_info('tracking passed')
                    self.create_data()
            else:
                self.print_info(f'cannot be tracked now, because {self.app.tracked_satellite.data['name']} is being tracked')
                self.create_data()
        else:
            self.print_info(f'cannot be tracked now, because rotator is not connected')
            self.create_data()
            self.app.show_prediction(self.app.next_satellite.data)
