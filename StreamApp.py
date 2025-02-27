import sys
import time
from PyQt5 import QtWidgets, QtCore, uic, QtSvg

import numpy as np

import os
os.environ["QT_QPA_PLATFORM"] = "xcb"

import pyqtgraph as pg
from driver.PS4824A      import PS4000A
from driver.enums        import *
from driver.functions    import unit

from tools import Channel
from gui.costumWidgets import ChannelBtn, WelinqSpinBox
import configparser

from datetime import datetime

# Colors 
AVAILABLE_CHANNELS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
WELINQ_DARK = "#002e21"
WELINQ_LIGHT = "#d9f175"
COLORS = ['#d9f175', '#1abc9c','#e67e22', '#3498db', '#9b59b6', '#e74c3c', '#f1c40f', '#2ecc71',  ]

CONFIG_FILE = "config.ini"




def calculate_sample_interval(sample_frequency):
    """
    Calculate the sample interval from the sample frequency and express it as an integer with a suitable unit.
    """
    # Calculate the sample interval
    sample_interval = 1 / sample_frequency
    
    # Determine the most suitable unit
    if sample_interval >= 1:
        value = int(sample_interval)
        unit = TIME_UNITS.S
    elif sample_interval >= 1e-3:
        value = int(sample_interval * 1e3)
        unit = TIME_UNITS.MS
    elif sample_interval >= 1e-6:
        value = int(sample_interval * 1e6)
        unit = TIME_UNITS.US
    else:
        value = int(sample_interval * 1e9)
        unit = TIME_UNITS.NS
    
    return value, unit

class MainWindow(QtWidgets.QWidget):
    
    def __init__(self):
        super().__init__()
        uic.loadUi("gui/stream_app_gui.ui", self) 
        self.setWindowTitle("Picoscope")
        self.ChannelParametersWidget.hide()
        self.build_scales_layout()
        self.setup_scope_screen()

        self.samplerate_widget = WelinqSpinBox(step=100, min=100, max=4000)
        self.top_widgets.insertWidget(0, self.samplerate_widget)

        self.add_welinq_logo()

        self.picoscope = PS4000A()
        self.picoscope.open_unit()
        variant_info = self.picoscope.get_unit_info(PICO_INFO.PICO_VARIANT_INFO)
        batch_serial = self.picoscope.get_unit_info(PICO_INFO.PICO_BATCH_AND_SERIAL)
        self.setWindowTitle(f"PicoSope {variant_info} [{batch_serial}]")
    
        self.settings: dict[CHANNEL, Channel]= {}
        self.plots = {}
        self.is_recording = False

        # Laod preset parameters
        self.load_config()
        self.directory_label.setText(self.logging_directory)

        # Init the channels
        for i, ch in enumerate(AVAILABLE_CHANNELS):
            channel = Channel.from_dict(name=ch)
            # Settings
            self.settings[ch] = channel
            # UI channel
            widget = ChannelBtn(channel)
            widget.set_color(COLORS[i])
            widget.update_signal.connect(self.refresh_hardware)
            widget.name_label.clicked.connect(self.open_channel_settings)
            setattr(self, f"chan_{ch}_widget", widget)
            self.ChannelsLayout.addWidget(getattr(self, f"chan_{ch}_widget"))
            
            # Initialize the plot
            self.plots[ch] = self.scope_screen.plot( [], [], 
                name=f'{ch}: {channel.scale/10} V/div', 
                pen=pg.mkPen(color=COLORS[i], width=1))
        self.ChannelsLayout.addStretch()

        self.define_actions()

        self.size_one_buffer = 200
        self.max_buffer_size = 2000

        # Set up a timer to collect new incoming data.
        self.timer = QtCore.QTimer()
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.start_acquisition)

        # Equivalent of start the acquisition
        self.refresh_hardware()
        self.show()


    def define_actions(self):
        self.offset_value.valueChanged.connect(self.offset_changed)
        self.record_btn.clicked.connect(self.start_recording)
        self.stop_btn.clicked.connect(self.stop_recording)
        self.change_dir_btn.clicked.connect(self.change_directory)
        self.samplerate_widget.valueChanged.connect(self.refresh_hardware)

    def change_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.logging_directory = directory
            self.directory_label.setText(directory)
        self.save_config()

    def refresh_hardware(self):
        self.timer.stop()
        
        [channel.buffer.clear() for channel in self.settings.values()]

        for ch in AVAILABLE_CHANNELS:
            self.settings[ch].buffer.clear()
        
        self.setup_channels()
        self.setup_trigger()
        self.setup_acquisition()
        self.timer.start()
        self.save_config()

    # CHANNEL SETTOINGS METHODS
    def open_channel_settings(self):
        widget: ChannelBtn = self.sender().parent()
        self.current_channel: ChannelBtn = widget

        # First we will stop the signals of the widget
        is_on: QtWidgets.QRadioButton = self.is_on
        is_off: QtWidgets.QRadioButton = self.is_off

        # is_on.toggled.disconnect()
        is_on.toggle() if widget.channel.active else is_off.toggle()
        is_on.toggled.connect(self.activate_channel)

        parameterWidget = self.ChannelParametersWidget

        new_name = f"Channel {widget.channel.name} settings"

        if self.channel_name.text() == new_name and parameterWidget.isVisible():
            parameterWidget.hide()
            return

        self.channel_name.setText(new_name)
        self.channel_name.setStyleSheet(f"background-color: {widget.active_color}")

        scales_layout: QtWidgets.QGridLayout = self.scales_grid
        for i in range(scales_layout.count()):
            button = scales_layout.itemAt(i).widget()
            if button.text() == f"±{widget.channel.range.name.lower().split('_')[1][:-1]}V":
                button.setStyleSheet(f"background-color: {widget.active_color}")
            else:
                button.setStyleSheet("")


        self.show_offset_values()
        parameterWidget.show()

    def build_scales_layout(self):
        scales_layout: QtWidgets.QGridLayout = self.scales_grid
        for i, range_value in enumerate(RANGE):
            display_text = f"±{range_value.name.lower().split('_')[1][:-1]}V"
            button = QtWidgets.QPushButton(display_text)
            scales_layout.addWidget(button, i // 3, i % 3)
            button.clicked.connect(self.range_changed)

    def activate_channel(self):
        self.current_channel.channel.active = self.is_on.isChecked()
        self.current_channel.set_color()

    def range_changed(self):
        # Reset styling
        scales_layout: QtWidgets.QGridLayout = self.scales_grid

        # Set style for the active channel
        for i in range(scales_layout.count()):
            widget = scales_layout.itemAt(i).widget()
            widget.setStyleSheet("")

        button: ChannelBtn = self.sender()
        range_name:str = button.text()[1:].upper() # 10m for example
        
        active_color = self.current_channel.active_color
        button.setStyleSheet(f"background-color: {active_color}")
        
        self.current_channel.apply_range(getattr(RANGE, f"RANGE_{range_name}"))
        
        self.offset_changed()
        self.show_offset_values()

        self.refresh_hardware()

    def show_offset_values(self):
        if not hasattr(self, "current_channel"): return
        
        max_offset, min_offset = self.picoscope.get_analogue_offset(
            self.current_channel.channel.range, 
            COUPLING.DC
            )
        
        current_offset = self.current_channel.channel.offset

        format_voltage = lambda v: f"{v*1000:.0f} mV" if abs(v) < 1 else f"{v:.0f} V"
        
        self.min_offset.setText(f"-{format_voltage(max_offset)}")
        self.max_offset.setText(f"+{format_voltage(max_offset)}")
    
        offset_value: QtWidgets.QDoubleSpinBox = self.offset_value
        offset_value.setMinimum(min_offset)
        offset_value.setMaximum(max_offset)
        offset_value.setValue(current_offset)
        
        slider: QtWidgets.QSlider = self.offset_slider
        slider.setMinimum(int(min_offset * 1000))
        slider.setMaximum(int(max_offset * 1000))
        slider.setValue(int(current_offset * 1000))

    def offset_changed(self):
        self.current_channel.channel.offset = self.offset_value.value()

        max_offset, min_offset = self.picoscope.get_analogue_offset(
            self.current_channel.channel.range, 
            COUPLING.DC
            )

        current_offset = self.current_channel.channel.offset
        
        if not min_offset <= current_offset <= max_offset:
            if current_offset < min_offset:
                current_offset = min_offset
            elif current_offset > max_offset:
                current_offset = max_offset
            self.current_channel.channel.offset = current_offset

        self.offset_slider.setValue(int(current_offset * 1000))

        self.refresh_hardware()

    # GUI METHODS
    def setup_scope_screen(self):
        self.scope_scale = 10
        self.scope_screen.setBackground(WELINQ_DARK)
        # self.scope_screen.setBackground("k")

        self.scope_screen.showGrid(x = True, y = True, alpha = 0.5)
        self.scope_screen.getPlotItem().hideButtons()
        self.scope_screen.getAxis('bottom').setLabel(text='Time', units='s')
        # self.scope_screen.getAxis('left').setLabel(text='Voltage', units='V')
        self.scope_screen.setMouseEnabled(x=False, y=False)
        self.scope_screen.getAxis('left').setStyle(showValues=False)
        self.scope_screen.setYRange(-self.scope_scale, self.scope_scale)
        # self.scope_screen.setXRange(-self.scope_scale, self.scope_scale)


    def add_welinq_logo(self):
        svg_widget = QtSvg.QSvgWidget("gui/Welinq_Logo_Dark.svg")  # Replace with your SVG file path
        svg_widget.setFixedHeight(25)  # Set the height only
        svg_widget.setFixedWidth(int(2.84*25))  # Set the height only
        self.top_widgets.addWidget(svg_widget)



    def update_data(self, data_chunk: dict[str,np.ndarray]):
        """
        Update the rolling buffer with a new data sample and refresh the plot.
        Parameters:
        data_chunk : dict[str, np.ndarray]
            A dictionary containing the data for each channel.
        """

        for ch in AVAILABLE_CHANNELS:
            channel = self.settings[ch]
            
            if not channel.active:
                self.plots[channel.name].setData([], [])
                continue
    
            data = data_chunk[ch]
            data = data  / channel.max_adc * self.scope_scale
            data = list(data.flatten())
            channel.buffer.extend(data)

            # If new_data is longer than the buffer, only use the last buffer_size elements.
            if len(channel.buffer) > self.max_buffer_size:
                channel.buffer = channel.buffer[-self.max_buffer_size:]

            dt = self.sample_interval*unit(self.time_unit)
            x = np.arange(len(channel.buffer))*dt

            # Update the plot using the current buffer values.
            self.plots[ch].setData(x, channel.buffer)
    
    def start_recording(self):
        """ 
        Start recording data to the file. 
        """
        
        self.record_file = {}
        for ch, channel in self.settings.items():
            if not channel.active: continue

            # Create a filename using the current datetime (up to seconds)
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            # create a folder
            folder = os.path.join(self.logging_directory, date_str)
            os.makedirs(folder, exist_ok=True)
            
            filename =  f"{folder}/picoscope_ch_{ch}.bin"

            header_end = "\n\n"
            header = f""
            header += f"Time Interval: {self.sample_interval*unit(self.time_unit)}\n"
            header += f"Scale: {channel.scale}\n"
            header += f"Offset: {channel.offset}"
            header += header_end
            self.record_file[ch] = open(filename, 'wb')
            self.record_file[ch].write(header.encode('utf-8'))

        self.record_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.is_recording = True

    def stop_recording(self):
        """ Stop recording data to the file. """
        self.is_recording = False
        [record_file.close() for record_file in self.record_file.values()]
        self.record_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def record_data(self, incoming_data):
        if not self.is_recording: return

        for ch in AVAILABLE_CHANNELS:
            if self.settings[ch].active:
                np.array(incoming_data[ch], dtype='int16').tofile(self.record_file[ch])

    def start_acquisition(self):
        try:
            self.picoscope.get_streaming_latest_values(self.streaming_ready_callback, None)
        except RuntimeError:
            pass


    def setup_trigger(self):
        self.picoscope.set_simple_trigger(
            True, 
            CHANNEL.A, 
            0, 
            THRESHOLD_DIRECTION.RISING, 
            delay=0, 
            autoTrigger_ms=False)

    def setup_channels(self):
        for setting in self.settings.values():
            self.picoscope.set_channel(setting.flag, setting.active, COUPLING.DC, setting.range, setting.offset)

    def setup_acquisition(self):
        """ Set up the data acquisition. """
        # Set up the data buffers
        self.buffers = {}
        for ch in AVAILABLE_CHANNELS:
            self.buffers[ch] = np.zeros(self.size_one_buffer, dtype=np.int16)
            self.picoscope.set_data_buffers(
                channel=self.settings[ch].flag,
                buffer_max=self.buffers[ch],
                buffer_min=None,
                segment_index=0,
                down_sample_ratio_mode=RATIO_MODE.NONE
            )

        # Set the sample rate
        sample_rate = self.samplerate_widget.value
        res = calculate_sample_interval(sample_rate)
        self.sample_interval, self.time_unit = res

        # Start the streaming
        _ = self.picoscope.run_streaming(
            sample_interval= self.sample_interval,
            sample_interval_time_units=self.time_unit,
            max_pre_trigger_samples=0,
            max_post_trigger_samples = self.size_one_buffer,
            auto_stop=False, # Continuous
            down_sample_ratio=1,
            down_sample_ratio_mode=RATIO_MODE.NONE,
            overview_buffer_size=self.size_one_buffer
        )
        return 

    def streaming_ready_callback(self,handle, no_of_samples, start_index, overflow, *args):
        """ Callback function for the streaming data collection. """
        data_chunk = {}                                                                                                                                                                   
        for ch in AVAILABLE_CHANNELS:
            if not self.settings[ch].active: continue
            data_chunk[ch] = self.buffers[ch][start_index:(start_index + no_of_samples)]
        
        self.update_data(data_chunk)

        self.record_data(data_chunk)

        self.warning_widget.show() if overflow else self.warning_widget.hide()
        
        return

    def closeEvent(self, event):
        """ Close the application safely. """
        self.timer.stop()
        self.picoscope.stop()
        time.sleep(.2)
        self.picoscope.close_unit()
        event.accept()  # Accept the event to close the window

    def save_config(self):
        """ Save the current configuration to a file. """
        config = configparser.ConfigParser()
        
        # Gether global settings
        config['presets'] = {
            "sampling_frequency": self.samplerate_widget.value,
            "logging_directory": self.logging_directory
        }
        # Collect channels' settings
        for name, channel in self.settings.items():
            config[name] = channel.save_channel()
        
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)

    def load_config(self):
        """ Load the configuration from a file. """
        try:
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)
            self.samplerate_widget.value = int(config['presets']['sampling_frequency'])
            self.logging_directory = config['presets']['logging_directory']
        except Exception:
            print("Configuration file not found. Using default values.")
            self.samplerate_widget.value = 2000
            self.logging_directory = "./data"

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
