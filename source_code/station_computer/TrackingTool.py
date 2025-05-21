########################################################################################################################
#                                                                                                                      #
#    Author:         D. Nenicka                                                                                        #
#    Created:        3. 11. 2023                                                                                       #
#    Modified:       19. 10. 2024                                                                                      #
#    Description:    Simple GUI for satellite tracking                                                                 #
#                                                                                                                      #
########################################################################################################################


from datetime import datetime, timedelta, timezone                  # module for operations with date and time
from threading import Timer                                         # module for running more processes in parallel
from tkinter import *
from tkinter import messagebox, ttk                                 # module for dialog windows
from time import sleep                                              # module with sleep() function

from BeyondTools import BeyondTools                                 # module for predicting satellite visibility
from JsonTools import JsonTools                                     # module for operations with json files
from Mqtt import Mqtt                                               # module for MQTT communication
from SatnogsTools import SatnogsTools, Satellite                    # module for downloading data from Satnogs


class SatelliteList(list):
    def __init__(self, treeview, content):
        super().__init__()
        for x in content:
            self.append(x)
        self.treeview = treeview
        self.on_change()

    def append_sat(self, obj):
        if obj not in self and obj is not None:
            self.append(obj)
            self.on_change()

    def remove_sat(self, obj):
        if obj in self and obj is not None:
            self.remove(obj)
            self.on_change()

    def on_change(self):
        self.sort(key=lambda x: x.norad_id, reverse=False)
        self.treeview.fill(self)
        self.treeview.search_var.set('')


class TrackingTool(Tk):                                             # GUI for satellite tracking
    def __init__(self, configuration_json) -> None:
        super().__init__()

        # Modules
        self.json_tool = JsonTools(configuration_json)              # module for working with json configuration file
        self.satnogs_tools = SatnogsTools()                         # module for updating TLE data
        self.mqtt = Mqtt()                                          # module for MQTT communication
        self.beyond_tools = BeyondTools(self.json_tool.content)     # module for satellite pass predictions

        # Basic variables
        self.program_name = self.json_tool.content['program_name']  # program name
        self.icon = self.json_tool.content['icon']                  # icon file of the program window
        self.iconbitmap(self.icon)                                  # program icon
        self.state('zoomed')                                        # maximize the window
        self.title(self.program_name)                               # set program title
        self.font0 = ('Aerial', 11)                                 # basic font
        self.tracked_satellites = list()                            # list of currently tracked Satellite objects
        self.tracked_satellite = None                               # currently tracked TrackedSatellite object
        self.next_satellite = None                                  # first TrackedSatellite to be tracked

        # Treeview
        self.listbox0 = SatTreeview(self, 'All satellites', 0.125, 0.3, 0.2, 0.15, 'Treeview')
        self.listbox1 = SatTreeview(self, 'Selected satellites', 0.375, 0.3, 0.2, 0.15, 'Treeview')
        self.listbox2 = TSTreeview(self, 'Tracked satellites (sorted by AOS)', 0.75, 0.82, 0.45, 0.2, 'Treeview')
        self.transmitters_treeview = TransmittersTreeview(self, 0.75, 0.57, 0.45, 0.2, 'Treeview')

        # Satellite object lists
        satellites = self.satnogs_tools.get_satellites()
        self.satellites = SatelliteList(self.listbox0, satellites)  # list of all Satellite objects
        selected_satellites = [self.satellite_from_name(sat) for sat in self.json_tool.content['tracked_satellites'] if self.satellite_from_name(sat) in satellites]
        self.selected_satellites = SatelliteList(self.listbox1, selected_satellites)  # list of selected Satellite objects

        # String variables                                          Usage/meaning:
        self.prediction_title = StringVar(value='First pass prediction:')   # title of pass predictions
        self.satellite_title = StringVar(value='Tracked satellite:')# title of Next/Tracked satellite
        self.time_title = StringVar(value='Time until LOS:')        # title of Tracking starts in/Time until LOS
        self.date = StringVar()                                     # date of the pass prediction
        self.aos_time = StringVar()                                 # AOS of the pass prediction
        self.aos_azimuth = StringVar()                              # AOS azimuth of the pass prediction
        self.max_time = StringVar()                                 # MAX time of the pass prediction
        self.max_azimuth = StringVar()                              # MAX azimuth of the pass prediction
        self.max_elevation = StringVar()                            # MAX elevation of the pass prediction
        self.los_time = StringVar()                                 # LOS time of the pass prediction
        self.los_azimuth = StringVar()                              # LOS azimuth of the pass prediction
        self.duration = StringVar()                                 # duration of the satellite pass in pass prediction
        self.utctime = StringVar()                                  # UTC
        self.localtime = StringVar()                                # Local time
        self.rotator_azimuth = StringVar()                          # current rotator azimuth
        self.rotator_elevation = StringVar()                        # current rotator elevation
        self.r_satellite = StringVar()                              # Next/Tracked satellite name
        self.r_time_till_los = StringVar()                          # Time until LOS/Tracking starts in
        self.received_frequency = StringVar()                       # received frequency
        self.doppler_shift = StringVar()                            # doppler shift for received frequency
        self.antenna_polarization = StringVar()                     # current antenna polarization
        self.mqtt_status = StringVar()                              # MQTT status

        # Styles and fonts
        self.background_color = '#daa520'                           # background color
        self.text_color = 'black'                                   # text color
        self.configure(bg=self.background_color)                    # configure background color
        self.style = ttk.Style(self)                                # style
        self.style.theme_use('clam')                                # theme
        self.style.configure( 'TLabel', foreground='black', background=self.background_color, font=('Aerial', 12))
        self.style.configure('Heading0.TLabel', foreground='black', background=self.background_color, font=('Helvetica', 20, 'bold'))
        self.style.configure('Heading1.TLabel', foreground='black', background=self.background_color, font=('Helvetica', 15, 'bold'))
        self.style.configure('TEntry', foreground='black', fieldbackground=self.background_color)
        self.style.map('TEntry', fieldbackground=[('readonly', self.background_color)])
        self.style.configure('TButton', foreground='black', background=self.background_color, font=('Aerial', 11))
        self.style.map('TButton', background=[('pressed', self.background_color)])
        self.style.configure("Treeview", foreground='black', background=self.background_color, backgroundfield=self.background_color, font=('Aerial', 10))
        self.style.configure("Treeview.Heading", foreground='black', background=self.background_color, font=('Aerial', 10))
        self.style.map("Treeview.Heading", background=[('pressed', self.background_color)])

        # Labels
        ttk.Label(self, text=self.program_name, style='Heading0.TLabel').place(relx=0.5, rely=0.05, anchor=CENTER)
        ttk.Label(self, text='Satellite visibility prediction', style='Heading1.TLabel').place(relx=0.25, rely=0.10, anchor=CENTER)
        ttk.Label(self, text='Rotator information', style='Heading1.TLabel').place(relx=0.75, rely=0.10, anchor=CENTER)
        ttk.Label(self, text='Select a satellite by double click and click Predict to predict its first pass:', style='TLabel').place(relx=0.25, rely=0.15, anchor=CENTER)
        ttk.Label(self, textvariable=self.prediction_title, style='TLabel').place(relx=0.25, rely=0.50, anchor=CENTER)
        ttk.Label(self, text='Date UTC:', style='TLabel').place(relx=0.05, rely=0.55, anchor=W)
        ttk.Label(self, text='Acquisition of satellite (AOS):', style='TLabel').place(relx=0.05, rely=0.60, anchor=W)
        ttk.Label(self, text='AOS azimuth:', style='TLabel').place(relx=0.05, rely=0.65, anchor=W)
        ttk.Label(self, text='Maximum elevation (MAX):', style='TLabel').place(relx=0.05, rely=0.70, anchor=W)
        ttk.Label(self, text='MAX azimuth:', style='TLabel').place(relx=0.05, rely=0.75, anchor=W)
        ttk.Label(self, text='MAX elevation:', style='TLabel').place(relx=0.05, rely=0.80, anchor=W)
        ttk.Label(self, text='Loss of satellite (LOS):', style='TLabel').place(relx=0.05, rely=0.85, anchor=W)
        ttk.Label(self, text='LOS azimuth:', style='TLabel').place(relx=0.05, rely=0.90, anchor=W)
        ttk.Label(self, text='Duration:', style='TLabel').place(relx=0.05, rely=0.95, anchor=W)
        ttk.Label(self, text='Time UTC:', style='TLabel').place(relx=0.525, rely=0.15, anchor=W)
        ttk.Label(self, text='Local time:', style='TLabel').place(relx=0.775, rely=0.15, anchor=W)
        ttk.Label(self, text='Azimuth (AZ):', style='TLabel').place(relx=0.525, rely=0.20, anchor=W)
        ttk.Label(self, text='Elevation (EL):', style='TLabel').place(relx=0.775, rely=0.20, anchor=W)
        ttk.Label(self, textvariable=self.satellite_title, style='TLabel').place(relx=0.525, rely=0.30, anchor=W)
        ttk.Label(self, textvariable=self.time_title, style='TLabel').place(relx=0.775, rely=0.30, anchor=W)
        ttk.Label(self, text='Frequency (MHz):', style='TLabel').place(relx=0.525, rely=0.35, anchor=W)
        ttk.Label(self, text='Doppler shift (kHz):', style='TLabel').place(relx=0.775, rely=0.35, anchor=W)
        ttk.Label(self, text='Antenna polarization:', style='TLabel').place(relx=0.525, rely=0.40, anchor=W)
        ttk.Label(self, text='MQTT status:', style='TLabel').place(relx=0.525, rely=0.95, anchor=W)

        # Entries
        ttk.Entry(textvariable=self.date, justify=RIGHT, state='readonly', font=self.font0, style='TEntry').place(relx=0.25, rely=0.55, relwidth=0.2, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.aos_time, justify=RIGHT, state='readonly', font=self.font0, style='TEntry').place(relx=0.25, rely=0.60, relwidth=0.2, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.aos_azimuth, justify=RIGHT, state='readonly', font=self.font0, style='TEntry').place(relx=0.25, rely=0.65, relwidth=0.2, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.max_time, justify=RIGHT, state='readonly', font=self.font0, style='TEntry').place(relx=0.25, rely=0.70, relwidth=0.2, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.max_azimuth, justify=RIGHT, state='readonly', font=self.font0, style='TEntry').place(relx=0.25, rely=0.75, relwidth=0.2, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.max_elevation, justify=RIGHT, state='readonly', font=self.font0, style='TEntry').place(relx=0.25, rely=0.80, relwidth=0.2, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.los_time, justify=RIGHT, state='readonly', font=self.font0, style='TEntry').place(relx=0.25, rely=0.85, relwidth=0.2, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.los_azimuth, justify=RIGHT, state='readonly', font=self.font0, style='TEntry').place(relx=0.25, rely=0.90, relwidth=0.2, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.duration, justify=RIGHT, state='readonly', font=self.font0, style='TEntry').place(relx=0.25, rely=0.95, relwidth=0.2, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.utctime, justify=CENTER, state='readonly', font=self.font0, style='TEntry').place(relx=0.625, rely=0.15, relwidth=0.1, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.localtime, justify=CENTER, state='readonly', font=self.font0, style='TEntry').place(relx=0.875, rely=0.15, relwidth=0.1, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.rotator_azimuth, justify=CENTER, state='readonly', font=self.font0, style='TEntry').place(relx=0.625, rely=0.20, relwidth=0.1, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.rotator_elevation, justify=CENTER, state='readonly', font=self.font0, style='TEntry').place(relx=0.875, rely=0.20, relwidth=0.1, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.r_satellite, justify=CENTER, state='readonly', font=self.font0, style='TEntry').place(relx=0.625, rely=0.30, relwidth=0.1, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.r_time_till_los, justify=CENTER, state='readonly', font=self.font0, style='TEntry').place(relx=0.875, rely=0.30, relwidth=0.1, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.received_frequency, justify=CENTER, state='readonly', font=self.font0, style='TEntry').place(relx=0.625, rely=0.35, relwidth=0.1, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.doppler_shift, justify=CENTER, state='readonly', font=self.font0, style='TEntry').place(relx=0.875, rely=0.35, relwidth=0.1, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.antenna_polarization, justify=CENTER, state='readonly', font=self.font0, style='TEntry').place(relx=0.625, rely=0.40, relwidth=0.1, relheight=0.035, anchor=W)
        ttk.Entry(textvariable=self.mqtt_status, justify=CENTER, state='readonly', font=self.font0, style='TEntry').place(relx=0.625, rely=0.95, relwidth=0.1, relheight=0.035, anchor=W)

        # Buttons
        ttk.Button(self, text='Predict', command=lambda: self.predict(self.listbox0.entry.get()), style='TButton').place(relx=0.075, rely=0.45, relwidth=0.1, relheight=0.04, anchor=CENTER)
        ttk.Button(self, text='Add', command=self.add_to_selected, style='TButton').place(relx=0.175, rely=0.45, relwidth=0.1, relheight=0.04, anchor=CENTER)
        ttk.Button(self, text='Remove', command=self.remove_from_selected, style='TButton').place(relx=0.325, rely=0.45, relwidth=0.1, relheight=0.04, anchor=CENTER)
        ttk.Button(self, text='Track', command=self.track, style='TButton').place(relx=0.425, rely=0.45, relwidth=0.1, relheight=0.04, anchor=CENTER)
        ttk.Button(self, text='Vertical', command=lambda: self.set_polarization('Vertical'), style='TButton').place(relx=0.775, rely=0.40, relwidth=0.05, relheight=0.04, anchor=W)
        ttk.Button(self, text='Horizontal', command=lambda: self.set_polarization('Horizontal'), style='TButton').place(relx=0.825, rely=0.40, relwidth=0.05, relheight=0.04, anchor=W)
        ttk.Button(self, text='LHCP', command=lambda: self.set_polarization('LHCP'), style='TButton').place(relx=0.875, rely=0.40, relwidth=0.05, relheight=0.04, anchor=W)
        ttk.Button(self, text='RHCP', command=lambda: self.set_polarization('RHCP'), style='TButton').place(relx=0.925, rely=0.40, relwidth=0.05, relheight=0.04, anchor=W)
        ttk.Button(self, text='Shut down rotator', command=self.shutdown_rotator, style='TButton').place(relx=0.775, rely=0.95, relwidth=0.1, relheight=0.04, anchor=W)
        ttk.Button(self, text='Quit', command=self.close_window, style='TButton').place(relx=0.875, rely=0.95, relwidth=0.1, relheight=0.04, anchor=W)

        # Azimuth and elevation offsets
        self.az_offset = Offset(self, 'AZ offset:', 'az_offset', 0.625, 0.25)  # azimuth offset
        self.el_offset = Offset(self, 'EL offset:', 'el_offset', 0.875, 0.25)  # elevation offset

        # run basic functions
        self.set_polarization('Vertical')                           # set polarization to Vertical
        self.update_rotator_info()                                  # display rotator information every 1 second

    @staticmethod
    def timedelta_formatter(td: timedelta) -> str:                  # function that returns timedelta object in string format %H %M %S
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{hours:02}:{minutes:02}:{seconds:02}'

    def satellite_from_name(self, name: str) -> Satellite:
        for sat in self.satellites:
            if name == sat.name:
                return sat

    def tracked_satellite_from_name(self, name: str):
        for sat in self.tracked_satellites:
            if name == sat.name:
                return sat

    def get_type(self, name: str):
        result1 = self.tracked_satellite_from_name(name)
        if result1 is not None:
            return result1
        result2 = self.satellite_from_name(name)
        if result2 is not None:
            return result2
        else:
            return None

    def predict(self, name: str) -> None:                           # create data about the first pass of selected satellite
        satellite = self.get_type(name)
        if isinstance(satellite, TrackedSatellite):
            self.show_prediction(satellite)
        elif isinstance(satellite, Satellite):
            tle = self.satnogs_tools.find_tle(satellite.norad_id)
            satellite.prediction = self.beyond_tools.predict_first_pass(tle)
            if not self.show_prediction(satellite):
                self.empty_prediction(f'There is no pass of {name} within next {self.beyond_tools.max_pred_time.days} days.')
        else:
            self.prediction_title.set(f'{name} is not a satellite in orbit around the Earth.')

    def add_to_selected(self) -> None:                               # add satellite to tracked satellite list
        sat = self.satellite_from_name(self.listbox0.entry.get())
        self.selected_satellites.append_sat(sat)

    def remove_from_selected(self) -> None:                          # remove satellite from tracked satellites list
        sat = self.satellite_from_name(self.listbox1.entry.get())
        self.selected_satellites.remove_sat(sat)

    def track(self) -> None:                                        # track all satellites in track_satellites list
        self.tracked_satellites.extend([TrackedSatellite(self, satellite.name, satellite.norad_id) for satellite in self.selected_satellites if not isinstance(self.get_type(satellite.name), TrackedSatellite)])
        for satellite in self.tracked_satellites:
            if self.satellite_from_name(satellite.name) not in self.selected_satellites or len(satellite.transmitters) == 0:
                satellite.tracking_thread.cancel()
                self.tracked_satellites.remove(satellite)
        track_sats_names = [satellite.name for satellite in self.tracked_satellites]
        self.json_tool.overwrite_variable('tracked_satellites', track_sats_names)
        self.find_first_pass()

    def update_rotator_info(self) -> None:                          # display rotator information every 1 second
        self.utctime.set(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))
        self.localtime.set(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        self.rotator_azimuth.set(self.mqtt.az)
        self.rotator_elevation.set(self.mqtt.el)
        if self.tracked_satellite is None and self.next_satellite is not None:
            self.r_time_till_los.set(self.timedelta_formatter(self.next_satellite.prediction['aos_time'] - datetime.now(timezone.utc)))
        elif self.tracked_satellite is not None:
            self.r_time_till_los.set(self.timedelta_formatter(self.tracked_satellite.prediction['los_time'] - datetime.now(timezone.utc)))
        if self.mqtt.connected:
            self.mqtt_status.set('connected')
        else:
            self.mqtt_status.set('disconnected')
        self.after(1000, self.update_rotator_info)

    def set_polarization(self, pol: str) -> None:                   # remotely set antenna polarization
        self.antenna_polarization.set(pol)
        self.mqtt.publish_polarization(pol)

    def show_prediction(self, satellite: Satellite) -> bool:        # display satellite prediction data
        try:
            self.prediction_title.set(f'First pass prediction for {satellite.name}: ')
            self.date.set(satellite.prediction['aos_time'].strftime('%d %B %Y'))
            self.aos_time.set(satellite.prediction['aos_time'].strftime('%H:%M:%S'))
            self.aos_azimuth.set(f'{satellite.prediction['aos_az']:.2f}')
            self.max_time.set(satellite.prediction['max_time'].strftime('%H:%M:%S'))
            self.max_azimuth.set(f'{satellite.prediction['max_az']:.2f}')
            self.max_elevation.set(f'{satellite.prediction['max_el']:.2f}')
            self.los_time.set(satellite.prediction['los_time'].strftime('%H:%M:%S'))
            self.los_azimuth.set(f'{satellite.prediction['los_az']:.2f}')
            self.duration.set(self.timedelta_formatter(satellite.prediction['los_time'] - satellite.prediction['aos_time']))
            return True
        except KeyError:
            return False

    def empty_prediction(self, title: str) -> None:                 # clear satellite prediction data
        self.prediction_title.set(title)
        self.date.set('')
        self.aos_time.set('')
        self.aos_azimuth.set('')
        self.max_time.set('')
        self.max_azimuth.set('')
        self.max_elevation.set('')
        self.los_time.set('')
        self.los_azimuth.set('')
        self.duration.set('')

    def find_first_pass(self) -> None:                              # find the first satellite in tracked satellites that will appear above the horizont
        tsn = len(self.tracked_satellites)
        if tsn == 0:
            return
        if tsn == 1:
            self.next_satellite = self.tracked_satellites[0]
        if tsn > 1:
            self.tracked_satellites.sort(key=lambda x: x.prediction['aos_time'], reverse=False)
            self.listbox2.fill()
            if self.tracked_satellite is None:
                self.next_satellite = self.tracked_satellites[0]
                self.satellite_title.set('Next satellite:')
                self.time_title.set('AOS in:')
                self.r_satellite.set(self.next_satellite.name)
                self.show_prediction(self.next_satellite)
                self.transmitters_treeview.fill(self.next_satellite)
            else:
                self.next_satellite = self.tracked_satellites[1]
                self.satellite_title.set('Tracked satellite:')
                self.time_title.set('LOS in:')
                self.r_satellite.set(self.tracked_satellite.name)
                self.show_prediction(self.tracked_satellite)

    def shutdown_rotator(self) -> None:                             # remotely shut down the rotator
        if self.mqtt.connected:
            if self.tracked_satellite is not None:
                messagebox.showinfo(title='Information', message='You cannot shut down the rotator while tracking.')
            elif messagebox.askokcancel(title='Information', message='Are you sure to shut down the rotator?'):
                self.mqtt.publish_action('shutdown')
        else:
            messagebox.showinfo(title='Information', message='Rotator is not connected')

    def close_window(self) -> None:                                 # close Satellite Tracking Software
        if self.tracked_satellite is not None:
            messagebox.showinfo(title='Information', message=f'You cannot close {self.program_name} while tracking.')
        elif messagebox.askokcancel(title='Information', message=f'Are you sure to quit {self.program_name}?'):
            self.mqtt.stop_thread = True
            for satellite in self.tracked_satellites:
                satellite.tracking_thread.cancel()
            self.destroy()


class Offset:                                                       # object to control azimuth and elevation offset
    offset_step = 0.1                                               # step of changing the offset
    def __init__(self, app: TrackingTool, offset_name: str, topic_name: str, rel_x: float, rel_y) -> None:
        self.app = app
        self.topic_name = topic_name                                # MQTT topic name
        self.string_var = StringVar()                               # variable to display offset value
        ttk.Label(self.app, text=offset_name, style='TLabel').place(relx=rel_x - 0.1, rely=rel_y, anchor=W)
        ttk.Entry(self.app, textvariable=self.string_var, justify=CENTER, state='readonly', font=self.app.font0, style='TEntry').place(relx=rel_x+0.025, rely=rel_y, relwidth=0.05, relheight=0.035, anchor=W)
        ttk.Button(self.app, text='+', command=self.increase, style='TButton').place(relx=rel_x, rely=rel_y, relwidth=0.025, relheight=0.035, anchor=W)
        ttk.Button(self.app, text='-', command=self.decrease, style='TButton').place(relx=rel_x + 0.075, rely=rel_y, relwidth=0.025, relheight=0.035, anchor=W)
        self.offset = 0.0                                           # offset value
        self.publish()

    def increase(self) -> None:                                     # increase offset by one step
        if self.app.tracked_satellite is None and self.app.mqtt.connected:
            self.offset += self.offset_step
            self.publish()

    def decrease(self) -> None:                                     # decrease offset by one step
        if self.app.tracked_satellite is None and self.app.mqtt.connected:
            self.offset -= self.offset_step
            self.publish()

    def publish(self) -> None:                                      # display and publish offset via MQTT broker
        self.offset = round(self.offset, 2)
        self.string_var.set(f'{self.offset}')
        self.app.mqtt.publish_offset(self.topic_name, self.offset)


class SatTreeview(ttk.Treeview):                                    # List of satellites in GUI
    def __init__(self, app: TrackingTool, title: str, rel_x: float, rel_y: float, width: float, height: float, style: str) -> None:
        self.app = app
        super().__init__(app, selectmode='browse', style=style)
        self['columns'] = ('Satellite', 'NORAD')
        self.column('#0', width=0, stretch=NO)
        self.column('Satellite', anchor=W, width=180)
        self.column('NORAD', anchor=CENTER, width=20)
        self.heading('#0', text='', anchor=W)
        self.heading('Satellite', text='Satellite', anchor=W)
        self.heading('NORAD', text='NORAD', anchor=CENTER)
        self.place(relx=rel_x, rely=rel_y, relwidth=width, relheight=height, anchor=CENTER)
        self.bind('<Double-1>', self.select)                        # bind double click on an item in listbox with select function
        self.title_text = StringVar()
        self.search_var = StringVar()
        ttk.Label(self.app, textvariable=self.title_text, style='TLabel').place(relx=rel_x, rely=rel_y - (0.5 * height) - 0.025, anchor=CENTER)
        self.entry = ttk.Entry(textvariable=self.search_var, font=self.app.font0, style='TEntry')
        self.entry.place(relx=rel_x, rely=rel_y + (0.5 * height) + 0.025, relwidth=0.2, relheight=0.035, anchor=CENTER)
        self.entry.bind('<Return>', func=lambda event: self.search(event, self.search_var.get()))
        self.title_name = title                                     # listbox title
        self.content = list()

    def fill(self, content: list, overwrite: bool = True) -> None:  # fill listbox with content
        if overwrite:
            self.content = content
        self.delete(*self.get_children())
        for item in content:
            self.insert(parent='', values=(item.name, item.norad_id), index='end')
        self.title_text.set(f'{self.title_name} ({len(content)}):')

    def select(self, event) -> None:                                # when you click on a name in listbox, it will be displayed in ss0 and ss1 entry
        self.search_var.set(self.item(self.focus())['values'][0])

    def search(self, event, word: str) -> None:                     # fill listbox with filtered satellite names you search
        if word == '':
            self.fill(self.content, overwrite=False)
            return
        filtered_data = list()
        for item in self.content:
            if word.lower() in item.name.lower() or word in str(item.norad_id):
                filtered_data.append(item)
        self.fill(filtered_data, overwrite=False)


class TransmittersTreeview(ttk.Treeview):
    def __init__(self, app: TrackingTool, rel_x: float, rel_y: float, width: float, height: float, style: str) -> None:
        self.app = app
        super().__init__(app, selectmode='browse', style=style)
        self['columns'] = ('Name', 'Frequency', 'Type', 'Mode')
        self.column('#0', width=0, stretch=NO)
        self.column('Name', anchor=W, width=180)
        self.column('Frequency', anchor=CENTER, width=20)
        self.column('Type', anchor=CENTER, width=20)
        self.column('Mode', anchor=CENTER, width=20)
        self.heading('#0', text='', anchor=W)
        self.heading('Name', text='Name', anchor=W)
        self.heading('Frequency', text='Frequency (MHz)', anchor=CENTER)
        self.heading('Type', text='Type', anchor=CENTER)
        self.heading('Mode', text='Mode', anchor=CENTER)
        self.place(relx=rel_x, rely=rel_y, relwidth=width, relheight=height, anchor=CENTER)
        self.bind('<Double-1>', self.select)                        # bind double click on an item in listbox with select function
        self.title_text = StringVar(value='Active transmitters:')
        ttk.Label(self.app, textvariable=self.title_text, style='TLabel').place(relx=rel_x, rely=rel_y - (0.5 * height) - 0.025, anchor=CENTER)
        self.satellite = None

    def fill(self, satellite) -> None:                              # fill listbox with content
        self.satellite = satellite
        self.delete(*self.get_children())
        for item in satellite.transmitters:
            if item['alive'] == True and item['status'] == 'active':
                self.insert(parent='', values=(item['description'], f'{float((item['downlink_low'])/1000000):.3f}', item['type'], item['mode']), index='end')
        self.title_text.set(f'{satellite.name} - active transmitters ({len(satellite.transmitters)}):')
        self.app.received_frequency.set(f'{float((satellite.transmitters[0]['downlink_low'])/1000000):.3f}')
        self.app.frequency = float(satellite.transmitters[0]['downlink_low'])

    def select(self, event) -> None:                                # when you click on a name in listbox, it will be displayed in ss0 and ss1 entry
        if self.satellite.name == self.app.r_satellite.get():
            cs = self.focus()
            self.app.received_frequency.set(self.item(cs)['values'][1])
            self.app.frequency = int(float(self.item(cs)['values'][1]) * 1000000)

class TSTreeview(ttk.Treeview):
    def __init__(self, app: TrackingTool, title: str, rel_x: float, rel_y: float, width: float, height: float, style: str) -> None:
        self.app = app
        super().__init__(app, selectmode='browse', style=style)
        self['columns'] = ('Satellite', 'NORAD', 'Date', 'AOS', 'MAX', 'LOS', 'Duration')
        self.column('#0', width=0, stretch=NO)
        self.column('Satellite', anchor=W, width=100)
        self.column('NORAD', anchor=CENTER, width=20)
        self.column('Date', anchor=CENTER, width=20)
        self.column('AOS', anchor=CENTER, width=20)
        self.column('MAX', anchor=CENTER, width=20)
        self.column('LOS', anchor=CENTER, width=20)
        self.column('Duration', anchor=CENTER, width=20)
        self.heading('#0', text='', anchor=W)
        self.heading('Satellite', text='Satellite', anchor=W)
        self.heading('NORAD', text='NORAD', anchor=CENTER)
        self.heading('Date', text='Date UTC', anchor=CENTER)
        self.heading('AOS', text='AOS', anchor=CENTER)
        self.heading('MAX', text='MAX', anchor=CENTER)
        self.heading('LOS', text='LOS', anchor=CENTER)
        self.heading('Duration', text='Duration', anchor=CENTER)
        self.place(relx=rel_x, rely=rel_y, relwidth=width, relheight=height, anchor=CENTER)
        self.title_text = StringVar()
        ttk.Label(self.app, textvariable=self.title_text, style='TLabel').place(relx=rel_x, rely=rel_y - (0.5 * height) - 0.025, anchor=CENTER)
        self.title_name = title                                     # listbox title
        self.bind('<Double-1>', self.select)                        # bind double click on an item in listbox with select function
        self.fill()

    def fill(self) -> None:                                         # fill listbox with content
        self.delete(*self.get_children())
        for item in self.app.tracked_satellites:
            self.insert(parent='', values=(item.name, item.norad_id, item.prediction['aos_time'].strftime('%d %B %Y'), item.prediction['aos_time'].strftime('%H:%M:%S'), item.prediction['max_time'].strftime('%H:%M:%S'), item.prediction['los_time'].strftime('%H:%M:%S'), self.app.timedelta_formatter(item.prediction['los_time'] - item.prediction['aos_time'])), index='end')
        self.title_text.set(f'{self.title_name} ({len(self.app.tracked_satellites)}):')

    def select(self, event) -> None:                                # when you click on a name in listbox, it will be displayed in ss0 and ss1 entry
        self.app.show_prediction(self.app.tracked_satellite_from_name(self.item(self.focus())['values'][0]))
        self.app.transmitters_treeview.fill(self.app.tracked_satellite_from_name(self.item(self.focus())['values'][0]))


class TrackedSatellite(Satellite):                                  # object for tracked satellites
    delay_before_tracking = timedelta(seconds=15)                   # time needed for rotator to turn to AOS azimuth

    def __init__(self, app: TrackingTool, *args) -> None:
        super().__init__(*args)
        self.app = app
        self.transmitters = self.app.satnogs_tools.get_transmitters(self.norad_id)
        self.tle = self.app.satnogs_tools.find_tle(self.norad_id)
        self.tracking_data = list()                                 # list of azims and elevs in time during the pass
        self.rotator_data = []
        self.start_time = float()                                   # time until AOS in seconds
        self.tracking_thread = None
        self.create_data()

    def create_data(self, delay: float = 0) -> None:                # create data about the first pass of satellite
        self.tracking_data.clear()
        self.tracking_data, self.prediction = self.app.beyond_tools.create_data(self.tle, delay=delay)
        if len(self.tracking_data) > 0:
            self.start_time = (self.prediction['aos_time'] - datetime.now(timezone.utc) - self.delay_before_tracking).total_seconds()
            self.tracking_thread = Timer(self.start_time, self.track)
            self.tracking_thread.start()
        else:
            self.app.tracked_satellites.remove(self)

    def track(self) -> None:                                        # track the satellite
        if self.app.mqtt.connected and self.app.tracked_satellite is None:
            if (self.prediction['aos_time'] - self.delay_before_tracking + timedelta(seconds=5)) >= datetime.now(timezone.utc):
                self.app.tracked_satellite = self
                self.app.find_first_pass()
                self.app.mqtt.publish_action('start')
                wait_time = (self.prediction['aos_time'] - datetime.now(timezone.utc)).total_seconds()
                self.app.mqtt.publish_aos_data(self.prediction['aos_az'])
                sleep(wait_time)
                a = 0
                for utc_time, azimuth, elevation, distance in self.tracking_data:
                    if a == 0:
                        a += 1
                        continue
                    self.app.mqtt.publish_position(utc_time.strftime('%Y-%m-%dT%H:%M:%S.%f%z'), azimuth, elevation)
                    delta_t = (utc_time - self.tracking_data[a - 1][0]).total_seconds()
                    delta_s = self.tracking_data[a + 1][3] - distance
                    doppler = self.calculate_doppler(float(self.app.received_frequency.get()) * 1000000, delta_s, delta_t)
                    self.app.doppler_shift.set(f'{(doppler/1000):.3f}')
                    if a >= 2:
                        sleep(delta_t)
                    a += 1
                self.app.mqtt.publish_action('stop')
                self.app.received_frequency.set('')
                self.app.doppler_shift.set('')
                self.app.tracked_satellite = None
        self.create_data(delay=1)
        self.app.find_first_pass()

    @staticmethod
    def calculate_doppler(fc: float, ds: float, dt: float) -> float:
        c = 299792458                                               # speed of light in vacuum
        return -(fc * ds)/(c * dt)
