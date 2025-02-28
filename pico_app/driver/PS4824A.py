#
# Copyright (C) 2014-2018 Pico Technology Ltd. See LICENSE file for terms.
#
"""
This is a Python module defining the functions from the ps4000aApi.h C header
file for PicoScope 4000 Series oscilloscopes using the ps4000a driver API
functions.
"""
from .enums     import *
from .errors    import CannotOpenPicoSDKError, CannotFindPicoSDKError
from .constants import pico_tag, make_enum

import sys
from ctypes import *
from functools import wraps
from ctypes.util import find_library

import numpy as np

class TRIGGER_INFO(Structure):
    _pack_ = 1
    _fields_ = [("status", c_uint32),
                ("segmentIndex", c_uint32),
                ("triggerIndex", c_uint32),
                ("triggerTime", c_int64),
                ("timeUnits", c_int16),
                ("reserved0", c_int16),
                ("timeStampCounter", c_uint64)]

def block_ready_callback(handle, status, p_parameter):
    """ 
    Signature of a ready callback function.
    
    This callback function is part of your application. You register it with the ps4000a driver using
    'run_block', and the driver calls it back when block-mode data is ready. You can then download the
    data using the 'get_values' function.
    """
    if p_parameter:
        # Parameter extraction (you can pass any python object to this function)
        parameter = cast(p_parameter, POINTER(py_object)).contents.value
    else:
        parameter = None

    return

def streaming_ready_callback(handle, 
                             no_of_samples, 
                             start_index, overflow, 
                             trigger_at, 
                             triggered, 
                             auto_stop, 
                             p_parameter):
    """ 
    Signature of a streaming ready callback function.
    
    This callback function is part of your application. You register it with the driver using
    'get_streaming_latest_values', and the driver calls it back when streaming-mode data is ready. 
    You can then download the data using the 'get_values_async' function.
    
    Your callback function should do nothing more than copy the data to another buffer within your application. 
    To maintain the best application performance, the function should return as quickly as possible without
    attempting to process or display the data.

    - no_of_samples: the number of samples to collect. 
    - start_index: 
        an index to the first valid sample in the buffer. 
        This is the buffer that was previously passed to 'set_data_buffer'. 
    - overflow: 
        returns a set of flags that indicate whether an overvoltage has occurred on any of the
        channels. It is a bit pattern with bit 0 denoting Channel A. 
    - trigger_at,:
        an index to the buffer indicating the location of the trigger point relative to start_index. This
        parameter is valid only when triggered is non-zero. 
    - triggered: 
        a flag indicating whether a trigger occurred. If non-zero, a trigger occurred at the location
        indicated by trigger_at.
    - auto_stop: the flag that was set in the call to 'run_streaming'. 
    - p_parameter: 
        a void pointer passed from 'get_streaming_latest_values'. 
        The callback function can write to this location to send any data, such as a status flag, 
        back to the application.
    """
    if p_parameter:
        # Parameter extraction (you can pass any python object to this function)
        parameter = cast(p_parameter, POINTER(py_object)).contents.value
    else:
        parameter = None

    return

def check_status(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if self.status != 0:
            print(pico_tag(self.status))
            # You can raise a custom exception or RuntimeError, etc.
            # raise RuntimeError(pico_tag(self.status))
        return result
    return wrapper

class PS4000A():

    def __init__(self):
        self.driver = "ps4000a"
        self._clib = self._load()

    def _load(self):
        library_path = find_library(self.driver)

        if not sys.platform == 'cygwin':
            if library_path is None:
                env_var_name = "PATH" if sys.platform == 'win32' else "LD_LIBRARY_PATH"
                raise CannotFindPicoSDKError("PicoSDK (%s) not found, check %s" % (self.driver, env_var_name))

        try:
            if sys.platform == 'win32':
                from ctypes import WinDLL
                result = WinDLL(library_path)
            elif sys.platform == 'cygwin':
                from ctypes import CDLL
                library_path = self.driver
                result = CDLL(library_path + ".dll")
            else:
                result = cdll.LoadLibrary(library_path)
        except OSError as e:
            raise CannotOpenPicoSDKError("PicoSDK (%s) not compatible (check 32 vs 64-bit): %s" % (self.driver, e))
        return result

    def enumerate_units(self) -> str:
        c_function = getattr(self._clib, self.driver + "EnumerateUnits")
        
        count = c_int16()
        serial = create_string_buffer(1024)
        serial_lth = c_int16()

        self.status = c_function(
            byref(count),
            serial,
            byref(serial_lth),
            )
        
        return serial.value.decode("utf-8")

    @check_status
    def close_unit(self):
        """
        This function shuts down the PicoScope 5000 Series oscilloscope.
        """
        c_function = getattr(self._clib, self.driver + "CloseUnit")
        self.status = c_function(c_int16(self.handle))

    @check_status
    def open_unit(self, serial:str=None):
        """
        This function opens a PicoScope 5000A, 5000B or 5000D Series scope attached to the computer. 
        The maximum number of units that can be opened depends on the operating system, 
        the kernel driver and the computer.
        """
        
        c_function = getattr(self._clib, self.driver + "OpenUnit")
        handle = c_int16()

        if serial:
            serial = serial.encode("utf-8")
            serial_c = create_string_buffer(len(serial) + 1)
            serial_c.value = serial

        self.status = c_function(
            byref(handle), 
            serial_c if serial else None, 
            )
        
        self.handle = handle.value

        if self.handle <= 0:
            if self.handle == -1: print("Scope fails to open !")
            if self.handle ==  0: print("No scope is found !")
            exit()

    @check_status
    def open_unit_async(self, serial:str=None, resolution:RESOLUTION=0):
        """
        This function opens a scope without blocking the calling thread. You can find out when it has finished by
        periodically calling 'cpen_unit_progress' until that function returns a non-zero value.


        """
        c_function = getattr(self._clib, self.driver + "OpenUnitAsync")
        self.handle = c_int16()

        if serial:
            serial = serial.encode("utf-8")
            serial_c = create_string_buffer(len(serial) + 1)
            serial_c.value = serial

        self.status = c_function(
            byref(self.handle),
            serial_c if serial else None,
            c_int32(resolution)
            )
        
    @check_status
    def open_unit_progress(self) -> tuple[int, bool]:
        """
        This function checks on the progress of a request made to 'open_unit_async' to open a scope.
        If the function returns PICO_POWER_SUPPLY_NOT_CONNECTED or PICO_USB3_0_DEVICE_NON_USB3_0_PORT, 
        call 'change_power_source' to select a new power source. 
        
        Returns:
        * progressPercent: the percentage progress towards opening the scope. 
                           100% implies that the open operation is complete. 
        * complete: True when the open operation has finished.
        """
        c_function = getattr(self._clib, self.driver + "OpenUnitProgress")
        
        progress_percent = c_int16()
        complete = c_int16()

        self.status = c_function(
            byref(self.handle),
            byref(progress_percent),
            byref(complete)
            )
        
        return progress_percent.value, bool(complete.value)

    @check_status
    def stop(self):
        """
        This function stops the scope device from sampling data
        """
        c_function = getattr(self._clib, self.driver + "Stop")
        self.status = c_function(c_int16(self.handle))

    @check_status
    def get_minimum_value(self) -> int:
        """ This function returns a status code and outputs the minimum ADC count value to a parameter. 
        The output value depends on the currently selected resolution. """
        c_function = getattr(self._clib, self.driver + "MinimumValue")
        self.min_adc = c_int16()
        self.status = c_function(c_int16(self.handle), byref(self.min_adc))
        return self.min_adc.value

    @check_status
    def get_maximum_value(self) -> int:
        """ This function returns a status code and outputs the maximum ADC count value to a parameter. 
        The output value depends on the currently selected resolution. """
        c_function = getattr(self._clib, self.driver + "MaximumValue")
        self.max_adc = c_int16()
        self.status = c_function(c_int16(self.handle), byref(self.max_adc))
        return self.max_adc.value

    @check_status
    def set_channel(self, 
                    channel: CHANNEL, 
                    enabled: bool, 
                    coupling: COUPLING, 
                    channel_range: RANGE, 
                    analog_offset: float):
        """
        This function specifies whether an analog input channel is to be enabled, 
        the input coupling type, voltage range and analog offset.

        analog_offset: a voltage to add to the input channel before digitization. 
        The allowable range of offsets depends on the input range selected for the channel, 
        as obtained from "get_analogue_offset".

        """
        c_function = getattr(self._clib, self.driver + "SetChannel")
        self.status = c_function(
            c_int16(self.handle),
            c_int32(channel),
            c_int16(1 if enabled else 0),
            c_int32(coupling),
            c_int32(channel_range),
            c_float(analog_offset)
        )

    @check_status
    def set_simple_trigger(self, 
                           enable:bool, 
                           source:CHANNEL, 
                           threshold_mu:int, 
                           direction:THRESHOLD_DIRECTION, 
                           delay:int, 
                           autoTrigger_ms:int):
        """
        This function simplifies arming the trigger, removing the need to call 
        the three trigger functions individually.
        It supports only the edge and level trigger types (not window triggers), 
        only the analog and external trigger input channels, and does not allow 
        more than one channel to have a trigger applied to it. 
        Any previous pulse width qualifier is canceled.

        Parameters:
        - enable, False to disable the trigger.
        - source, the channel on which to trigger (CHANNEL_A to CHANNEL_D and EXTERNAL values only).
        - threshold_mu, the ADC count at which the trigger will fire.
        - direction, the direction in which the signal must move to cause a trigger. The following directions are
            supported: ABOVE, BELOW, RISING, FALLING and RISING_OR_FALLING.
        - delay, the time between the trigger occurring and the first sample. For example, if delay = 100, the
            scope would wait 100 sample periods before sampling. At a timebase of 500 MS/s, or 2 ns per sample, the
            total delay would then be 100 x 2 ns = 200 ns. Range: 0 to MAX_DELAY_COUNT.
        - autoTrigger_ms, the number of milliseconds after which the device starts capturing if no trigger occurs.
            If this is set to zero, the scope device waits indefinitely for a trigger. 
            The value passed here overrides any value set by calling 'set_auto_trigger_microseconds'. 
            For greater precision, call 'set_auto_trigger_microseconds' after calling this function.

        """
        c_function = getattr(self._clib, self.driver + "SetSimpleTrigger")
        self.status = c_function(
            c_int16(self.handle), 
            c_int16(1 if enable else 0), 
            source, 
            c_int16(threshold_mu), 
            direction, 
            c_int32(delay), 
            c_int16(autoTrigger_ms)
        )
    
    @check_status
    def get_timebase(self, timebase: int, no_samples: int, segment_index: int = 0) -> tuple[float, int]:
        """
        This function calculates the sampling rate and maximum number of samples for a given timebase under the
        specified conditions. The result will depend on the number of channels enabled by the last call to
        'set_channel'.

        To use this function, first estimate the timebase number that you require using the information in the timebase guide. 
        Next, call this function with the timebase that you have just chosen and verify that the 'time_interval_ns' 
        argument that the function returns is the value that you require. 
        You may need to iterate this process until you obtain the time interval that you need.

        Parameters:
            - timebase: a number in the range 0 to 2^32 - 1. see timebase guide.
            - no_samples: The number of samples required.
            - segment_index: he index of the memory segment to use.

        Returns:
            - time_interval_ns: the time interval between readings at the selected timebase.
            - max_samples: the maximum number of samples available. The scope reserves some memory
                for internal overheads and this may vary depending on the number of segments, 
                number of channels enabled, and the timebase chosen.
        """
        c_function = getattr(self._clib, self.driver + "GetTimebase2")
        
        time_interval_ns = c_float()
        max_samples = c_int32()

        self.status = c_function(
            c_int16(self.handle),                 
            c_uint32(timebase),
            c_int32(no_samples),
            byref(time_interval_ns),
            byref(max_samples),
            c_uint32(segment_index)
        )

        return time_interval_ns.value, max_samples.value

    @check_status
    def memory_segments(self, n_segments: int) -> int:
        """
        This function sets the number of memory segments that the scope will use.
        When the scope is opened, the number of segments defaults to 1, meaning that each capture fills the
        scope's available memory. This function allows you to divide the memory into a number of segments so that
        the scope can store several waveforms sequentially. After capturing multiple segments, you can query their
        relative timings by calling 'get_trigger_info_bulk'.
        
        Parameters:
            - n_segments: the number of segments required. To find the maximum number of memory segments
                allowed, which may depend on the resolution setting, call 'get_max_segments'.
        
        Returns:
            - n_max_samples (int): The number of samples available in each segment. 
                This is the total number over all channels, so if two channels or 8-bit digital ports are in use, 
                the number of samples available to each channel is nMaxSamples divided by 2; 
                for 3 or 4 channels or digital ports divide by 4; and for 5 to 6 channels or digital ports divide by 8.
        """
        c_function = getattr(self._clib, self.driver + "MemorySegments")

        n_max_samples = c_int32()

        self.status = c_function(
            c_int16(self.handle),            
            c_uint32(n_segments),
            byref(n_max_samples)
        )

        return n_max_samples.value

    @check_status
    def set_no_of_captures(self, n_captures: int):
        """ 
        This function sets the number of captures to be collected in one run of rapid block mode. If you do not call
        this function before a run, the driver will capture only one waveform. Once a value has been set, the value
        remains constant unless changed.
        
        n_captures : the number of waveforms to capture in one run."""
        c_function = getattr(self._clib, self.driver + "SetNoOfCaptures")
        self.status = c_function(c_int16(self.handle), c_uint32(n_captures))

    @check_status
    def get_no_of_captures(self) -> int:
        """ 
        This function returns the number of captures the device has made in rapid block mode, since you called
        'run_block'. You can call "get_no_of_captures" during device capture, after collection has
        completed or after interrupting waveform collection by calling 'stop'. The returned value
        (n_captures) can then be used to iterate through the number of segments using 'get_values', or in
        a single call to 'get_values_bulk', where it is used to calculate the toSegmentIndex parameter."""

        c_function = getattr(self._clib, self.driver + "GetNoOfCaptures")
        n_captures = c_uint32()
        self.status = c_function(c_int16(self.handle), byref(n_captures))
        return n_captures.value

    no_of_captures = property(get_no_of_captures, set_no_of_captures)

    @check_status
    def run_block(self,
                pre_trigger_samples: int,
                post_trigger_samples: int,
                timebase: int,
                segment_index: int = 0,
                ready_callback = None,
                parameter: py_object = None) -> int:
        """
        This function starts collecting data in block mode. (step-by-step guide to this process in Using block mode)
        
        The number of samples is determined by 'pre_trigger_samples' and 'post_trigger_samples'. 
        The total number of samples must not be more than the length of the segment referred to by 'segment_index'.

        Parameters:
            - pre_trigger_samples: the number of samples to return before the trigger event. If no trigger has
            been set, then this argument is added to 'post_trigger_samples' to give the maximum number of
            data points (samples) to collect.
            - post_trigger_samples (int): the number of samples to return after the trigger event. If no trigger event
            has been set, then this argument is added to pre_trigger_samples to give the maximum number of
            data points to collect. If a trigger condition has been set, this specifies the number of data points to collect
            after a trigger has fired, and the number of samples to be collected is:
                            
                            pre_trigger_samples + post_trigger_samples
            
            - timebase: a number in the range 0 to 2^32 - 1.
            - segment_index: zero-based, specifies which memory segment to use.
            - ready_callback :a callback function that the driver will call when the data has been collected. 
                To use the "is_ready" polling method instead of a callback function, set this to None.
            - parameter: a pyobject (tuple for example) that is passed to the callback function. 
                The callback can use this pointer to return arbitrary data to the application.

        Returns:
            - time_indisposed_ms: the time, in milliseconds, that the scope will spend collecting samples. 
            This does not include any auto trigger timeout. 
            If this pointer is null, nothing will be written here
        """
        c_function = getattr(self._clib, self.driver + "RunBlock")
        
        BlockReady = CFUNCTYPE(None,c_int16,c_int32,c_void_p)
        block_ready = BlockReady(ready_callback) if ready_callback else None
        
        p_parameter = byref(parameter) if parameter is not None else None

        time_indisposed_ms = c_int32()
        self.status = c_function(
            c_int16(self.handle),
            c_int32(pre_trigger_samples),
            c_int32(post_trigger_samples),
            c_uint32(timebase),            
            byref(time_indisposed_ms),
            c_uint32(segment_index),
            block_ready,                    # lpReady (function pointer)
            cast(p_parameter, c_void_p),        # pParameter (void pointer)
        )
        
        return time_indisposed_ms.value

    @check_status
    def is_ready(self) -> bool:
        """
        This function may be used instead of a callback function to receive data from 'run_block'. 
        To use this method, pass a NULL pointer as the 'ready_callback' argument to 'run_block'. 
        You must then poll the driver to see if it has finished collecting the requested samples.
        """
        c_function = getattr(self._clib, self.driver + "IsReady")
        ready = c_int16()
        self.status = c_function(c_int16(self.handle), byref(ready))
        return bool(ready.value)

    @check_status
    def set_data_buffer(self,
                        channel: CHANNEL,
                        buffer: np.ndarray,
                        segment_index: int,
                        down_sample_ratio_mode: int) -> int:
        """
        This function tells the driver where to store the data, either unprocessed or downsampled, that will be
        returned after the next call to one of the GetValues functions. The function allows you to specify only a
        single buffer, so for aggregation mode, which requires two buffers, call 'set_data_buffers' instead.

        Parameters:
            - channel: The channel identifier.
            - buffer: pointer to the buffer. Each sample written to the buffer will be a 16-bit ADC count scaled
                      according to the selected voltage range
            - buffer_length: the length of the buffer array. 
            - segment_index: The memory segment number to be used.
            - mode: The downsampling ratio mode (RATIO_MODE). This must correspond to
                        the mode used when retrieving values (e.g. via get_values...()).

        """
        c_function = getattr(self._clib, self.driver + "SetDataBuffer")
        
        self.status = c_function(
            c_int16(self.handle),
            c_int32(channel),
            buffer.ctypes.data_as(POINTER(c_int16)),
            c_int32(len(buffer)),
            c_uint32(segment_index),
            c_int32(down_sample_ratio_mode)
        )

    @check_status
    def set_data_buffers(self,
                        channel: CHANNEL,
                        buffer_max: np.ndarray,
                        buffer_min: np.ndarray,
                        segment_index: int,
                        down_sample_ratio_mode: int) -> int:
        """
        This function tells the driver where to store the acquired data. You must allocate the 
        memory for the buffers before calling this function. In aggregation mode, the driver will 
        write the maximum values to buffer_max and the minimum values to buffer_min. In non-aggregated
        modes, only buffer_max is required (or you can use 'set_data_buffer' instead).

        Parameters:
            - channel: The channel identifier.
            - buffer_max: a user-allocated buffer to receive the maximum data values in aggregation mode, 
                or the non-aggregated values otherwise. 
                Each value is a 16-bit ADC count scaled according to the selected voltage range. 
            - buffer_min: a user-allocated buffer to receive the minimum data values in aggregation mode. 
                Not normally used in other modes, but you can direct the driver to write non-aggregated 
                values to this buffer by setting buffer_max to None. 
                To enable aggregation, the downsampling ratio and mode must be set appropriately 
                when calling one of the get_values...() functions.
            - buffer_length: The number of elements in the buffer_max and buffer_min arrays.
            - segment_index: The memory segment number to be used.
            - mode: The downsampling ratio mode. This must correspond to the mode used when retrieving values.

        """
        c_function = getattr(self._clib, self.driver + "SetDataBuffers")

        self.status = c_function(
            c_int16(self.handle),
            c_int32(channel),
            buffer_max.ctypes.data_as(POINTER(c_int16)) if buffer_max is not None else None,
            buffer_min.ctypes.data_as(POINTER(c_int16)) if buffer_min is not None else None,
            c_int32(len(buffer_max)),
            c_uint32(segment_index),
            c_int32(down_sample_ratio_mode)
        )

    @check_status
    def get_values(self, 
                   start_index: int, 
                   n_samples: int,
                   down_sample_ratio: int, 
                   down_sample_ratio_mode: RATIO_MODE,
                   segment_index: int) -> tuple[int,int]:
        """
        This function returns block-mode data from the oscilloscope's buffer memory, with or without
        downsampling, starting at the specified sample number. 
        It is used to get the stored data after data collection has stopped. 
        It blocks the calling function while retrieving data.
        If multiple channels are enabled, a single call to this function is sufficient to retrieve data for all channels.
        Note that if you are using block mode and call this function before the oscilloscope is ready, no capture will
        be available and the driver will return PICO_NO_SAMPLES_AVAILABLE

        Parameters:
            - start_index: a zero-based index that indicates the start point for data collection. 
                It is measured in sample intervals from the start of the buffer.
            - n_samples: on entry, the number of samples required. 
                The number of samples retrieved will not be more than the number requested, 
                and the data retrieved starts at start_index.
            - down_sample_ratio: the downsampling factor that will be applied to the raw data.
            - down_sample_ratio_mode: which downsampling mode to use. See RATIO_MODE. 
                These values are single-bit constants that can be ORed to apply multiple downsampling modes to the data.
            - segment_index: the zero-based number of the memory segment where the data is stored.

        Returns:
            - samples_retrieved: the actual number of samples retrieved
            - overflow: a set of flags that indicate whether an overvoltage has occurred on any of the channels. 
                It is a bit field with bit 0 denoting Channel A
        """
        c_function = getattr(self._clib, self.driver + "GetValues")
        
        samples_retrieved = c_uint32(n_samples)
        overflow = c_int16()
        
        self.status = c_function(
            c_int16(self.handle),
            c_uint32(start_index),
            byref(samples_retrieved),
            c_uint32(down_sample_ratio),
            c_int32(down_sample_ratio_mode),
            c_uint32(segment_index),
            byref(overflow)
        )

        return samples_retrieved.value, overflow.value

    @check_status
    def get_values_bulk(self, 
                        n_samples: int, 
                        from_segment: int, 
                        to_segment: int,
                        down_sample_ratio: int, 
                        down_sample_ratio_mode: RATIO_MODE):
        """
        This function retrieves waveforms captured using rapid block mode. The waveforms must have been
        collected sequentially and in the same run.
        
        Parameters:
            - n_samples: On entry, the number of samples requested;
            - from_segment: The first segment index from which the waveform should be retrieved.
            - to_segment: The last segment index from which the waveform should be retrieved.
            - down_sample_ratio: the downsampling factor that will be applied to the raw data.
            - down_sample_ratio_mode: The downsampling mode.
        
        Returns:
            - no_of_samples: The actual number of samples retrieved.
            - overflow: an array of integers equal to or larger than the number of waveforms to be retrieved. Each
            segment index has a corresponding entry in the overflow array, with overflow[0] containing the flags
            for the segment numbered from_segment and the last element in the array containing the flags for
            the segment numbered to_segment. Each element in the array is a bit field as described under
            get_values. 
        """
        
        c_function = getattr(self._clib, self.driver + "GetValuesBulk")
        
        no_of_samples = c_uint32(n_samples)
        n_segments = to_segment - from_segment + 1
        overflow_array = np.zeros(n_segments, dtype=np.int16)# (c_int16 * n_segments)()
        
        self.status = c_function(
            c_int16(self.handle),
            byref(no_of_samples),
            c_uint32(from_segment),
            c_uint32(to_segment),
            c_uint32(down_sample_ratio),
            c_int32(down_sample_ratio_mode),
            overflow_array.ctypes.data_as(POINTER(c_int16))
        )
        return no_of_samples.value, list(overflow_array)

    @check_status
    def get_values_overlapped(self,
                                start_index: int,
                                no_of_samples: int,
                                down_sample_ratio: int,
                                down_sample_ratio_mode: RATIO_MODE,
                                segment_index: int
                                ) -> tuple[int, list]:
        """
        This function allows you to make a deferred data-collection request in block mode. The request will be
        executed, and the arguments validated, when you call 'run_block'. The advantage of this function is
        that the driver makes contact with the scope only once, when you call 'run_block', compared with
        the two contacts that occur when you use the conventional 'run_block', 'get_values'
        calling sequence. This slightly reduces the dead time between successive captures in block mode.

        After calling 'run_block', you can optionally use 'get_values' to request further copies of
        the data. This might be required if you wish to display the data with different data reduction settings.
        """

        c_function = getattr(self._clib, self.driver + "GetValuesOverlapped")
        
        samples_var = c_uint32(no_of_samples)
    
        overflow = c_int16()
        
        self.handle = c_function(
            c_int16(self.handle),
            c_uint32(start_index),
            byref(samples_var),
            c_uint32(down_sample_ratio),
            c_int32(down_sample_ratio_mode),
            c_uint32(segment_index),
            cast(overflow, c_void_p)
        )
        
        return samples_var.value, list(overflow)

    @check_status
    def get_values_overlapped_bulk(self,
                                start_index: int,
                                no_of_samples: int,
                                from_segment: int,
                                to_segment: int,
                                down_sample_ratio: int,
                                down_sample_ratio_mode: RATIO_MODE) -> tuple[int, list]:
        """
        This function allows you to make a deferred data-collection request in rapid block mode. The request will be
        executed, and the arguments validated, when you call 'run_block'. The advantage of this method is
        that the driver makes contact with the scope only once, when you call 'run_block', compared with
        the two contacts that occur when you use the conventional 'run_block', 'get_values_bulk'
        calling sequence. This slightly reduces the dead time between successive captures in rapid block mode.

        After calling 'run_block', you can optionally use 'get_values' to request further copies of the data. 
        This might be required if you wish to display the data with different data reduction settings.
        For more information, see Using the GetValuesOverlapped functions

        Parameters:
            start_index, no_of_samples, down_sample_ratio, down_sample_ratio_mode, see 'get_values'. 
            from_segment, to_segment, * overflow†, see 'get_values_bulk'
        """
        c_function = getattr(self._clib, self.driver + "GetValuesOverlappedBulk")
        
        samples_var = c_uint32(no_of_samples)
        
        num_segments = to_segment - from_segment + 1
        overflow = (c_int16 * num_segments)()
        
        self.handle = c_function(
            c_int16(self.handle),
            c_uint32(start_index),
            byref(samples_var),
            c_uint32(down_sample_ratio),
            c_int32(down_sample_ratio_mode),
            c_uint32(from_segment),
            c_uint32(to_segment),
            cast(overflow, c_void_p)
        )
        
        return samples_var.value, list(overflow)

    @check_status
    def get_values_async(self,
                        start_index: int,
                        no_of_samples: int,
                        down_sample_ratio: int,
                        down_sample_ratio_mode: RATIO_MODE,
                        segment_index: int,
                        data_ready_callback, 
                        parameter=None) -> int:
        """
        This function returns data either with or without downsampling, starting at the specified sample number. It
        is used to get the stored data from the driver after data collection has stopped. It returns the data using a
        callback. 

        Parameters:
            - start_index, no_of_samples, down_sample_ratio, down_sample_ratio_mode,
                segment_index, see "get_values".

            - data_ready_callback: a pointer to the user-supplied function that will be called when the data is ready. 
                    This will be a 'block_ready_callback' function for block-mode data or a 'streaming_ready_callback' 
                    function for streaming-mode data.
            - parameter: a void pointer that will be passed to the callback function. The data type is determined by
                    the application.
        """
        c_function = getattr(self._clib, self.driver + "GetValuesAsync")
        
        if parameter is None:
            c_p_parameter = None
        else:
            c_p_parameter = cast(parameter, c_void_p)
        
        self.status = c_function(
            c_int16(self.handle),
            c_uint32(start_index),
            c_uint32(no_of_samples),
            c_uint32(down_sample_ratio),
            c_int32(down_sample_ratio_mode),
            c_uint32(segment_index),
            data_ready_callback,
            c_p_parameter
        )

    @check_status
    def get_analogue_offset(self, range_val: RANGE, coupling: COUPLING) -> tuple[float, float]:
        """
        This function is used to get the maximum and minimum allowable analog offset for a specific voltage range.
        """
        maximum_voltage = c_float()
        minimum_voltage = c_float()
        
        c_function = getattr(self._clib, self.driver + "GetAnalogueOffset")
        
        self.status = c_function(
            c_int16(self.handle),                    
            range_val,
            coupling,
            byref(maximum_voltage),
            byref(minimum_voltage)
        )
        return maximum_voltage.value, minimum_voltage.value

    @check_status
    def set_auto_trigger_microseconds(self, microseconds: int):
        """
        This function sets up the auto-trigger function, which starts a capture if no trigger event occurs 
        within a specified time after a Run command has been issued.

        - microseconds: the number of microseconds for which the scope device will wait for a trigger before timing out. 
        If this argument is zero, the scope device will wait indefinitely for a trigger.
        Otherwise, its behavior depends on the sampling mode:
        · In block mode, the capture cannot finish until a trigger event or auto-trigger timeout has occurred.
        · In streaming mode the device always starts collecting data as soon as run_streaming is called
        but does not start counting post-trigger samples until it detects a trigger event or auto-trigger timeout.
        """
        c_function = getattr(self._clib, self.driver + "SetAutoTriggerMicroSeconds")
        self.status = c_function(
            c_int16(self.handle),
            c_uint64(microseconds)
        )

    @check_status
    def get_max_segments(self) -> int:
        """
        This function returns the maximum number of segments allowed for the opened device. 
        Refer to 'memory_segments' for specific figures.
        """
        c_function = getattr(self._clib, self.driver + "GetMaxSegments")

        max_segments = c_uint32()
        self.status = c_function(
            c_int16(self.handle),
            byref(max_segments)
        )
        return max_segments.value

    @check_status
    def get_trigger_info_bulk(self, from_segment_index, to_segment_index):
        """
        Used to retrieve in formation about the trigger point in one or more segments of captured data, 
        in the form of a TRIGGER_INFO structure or array of structures.
        
        This function can retrieve trigger information for more than one segment at once by using
        'from_segment_index' and 'to_segment_index'. These values are both inclusive so, to collect details for a
        single segment, set 'from_segment_index' equal to 'to_segment_index'.
        
        Returns:
            trigger_info: a pointer to one or more TRIGGER_INFO objects. When collecting details for a single segment, 
            this parameter should be a pointer to a single object. When collecting details for more than
            one segment the parameter should be a pointer to an array of objects, of length greater than or equal to the
            number of TRIGGER_INFO elements requested.

        """

        c_function = getattr(self._clib, self.driver + "GetTriggerInfoBulk")

        # Create array of structures
        n = to_segment_index - from_segment_index + 1
        trigger_info_array = (TRIGGER_INFO * n)()  

        self.status = c_function(
            c_int16(self.handle),
            byref(trigger_info_array),
            c_uint32(from_segment_index),
            c_uint32(to_segment_index),
        )
        return list(trigger_info_array) 

    @check_status
    def get_no_of_processed_captures(self) -> int:
        """
        This function gets the number of captures collected and processed in one run of rapid block mode. It
        enables your application to start processing captured data while the driver is still transferring later captures
        from the device to the computer. 

        The function returns the number of captures the driver has processed since you called 'run_block'. 
        It is for use in rapid block mode, alongside the 'get_values_overlapped_bulk' function, when the
        driver is set to transfer data from the device automatically as soon as the 'run_block' function is
        called. You can call 'get_no_of_captures' during device capture, after collection has
        completed or after interrupting waveform collection by calling 'stop'. 

        The returned value (n_processed_captures) can then be used to iterate through the number of segments
        using 'get_values', or in a single call to 'get_values_bulk', where it is used to calculate
        the toSegmentIndex parameter. 

        When capture is stopped
        If n_processed_captures = 0, you will also need to call 'get_no_of_captures', in order to determine
        how many waveform segments were captured, before calling 'get_values' or 'get_values_bulk'.
        
        Returns:
        n_processed_captures : the number of available captures that has been collected from calling 'run_block'. 
        """
        c_function = getattr(self._clib, self.driver + "GetNoOfProcessedCaptures")
        n_processed_captures = c_uint32()
        self.status = c_function(c_int16(self.handle), byref(n_processed_captures))
        return n_processed_captures.value

    @check_status
    def run_streaming(self,
                    sample_interval: int,
                    sample_interval_time_units: TIME_UNITS,
                    max_pre_trigger_samples: int,
                    max_post_trigger_samples: int,
                    auto_stop: bool,
                    down_sample_ratio: int,
                    down_sample_ratio_mode: RATIO_MODE,
                    overview_buffer_size: int) -> int:
        """
        This function tells the oscilloscope to start collecting data in streaming mode. When data has been
        collected from the device it is downsampled if necessary and then delivered to the application. 
        Call 'get_streaming_latest_values' to retrieve the data. See Using streaming mode for a step-by-step
        guide to this process.

        The function always starts collecting data immediately, regardless of the trigger settings. 
        Whether a trigger is set or not, the total number of samples stored in the driver is always: 
        max_pre_trigger_samples + max_post_trigger_samples.

        Parameters:
            - sample_interval: the requested time interval between samples.
            - sample_interval_time_units: the unit of time used for sampleInterval.
            - max_pre_trigger_samples   : the maximum number of raw samples before a trigger event for each enabled channel.
            - max_post_trigger_samples  : the maximum number of raw samples after  a trigger event for each enabled channel.
            - auto_stop:
                a flag that specifies if the streaming should stop when all of max_samples =
                max_pre_trigger_samples + max_post_trigger_samples have been captured and a trigger event has
                occurred.If no trigger event occurs or no trigger is set, streaming will continue until stopped by 'stop'. 
                If auto_stop is False, the scope will collect data continuously using the buffer as a FIFO memory.
            - down_sample_ratio: The down sampling ratio.
            - down_sample_ratio_mode: The down sampling mode.
            - overview_buffer_size:
                the length of the overview buffers. These are temporary buffers used for storing the data before returning 
                it to the application. The length is the same as the 'buffer_length' value passed to 'set_data_buffer'

        Returns:
            - effective_sample_interval: the actual time interval used.
        """
        c_function = getattr(self._clib, self.driver + "RunStreaming")
        
        effective_sample_interval = c_uint32(sample_interval)

        self.status = c_function(
            c_int16(self.handle),
            byref(effective_sample_interval),
            c_int32(sample_interval_time_units),
            c_uint32(max_pre_trigger_samples),
            c_uint32(max_post_trigger_samples),
            c_int16(1 if auto_stop else 0),
            c_uint32(down_sample_ratio),
            c_int32(down_sample_ratio_mode),
            c_uint32(overview_buffer_size)
        )
        
        return effective_sample_interval.value

    @check_status
    def get_streaming_latest_values(self, 
                                    streaming_ready_callback, 
                                    args : py_object = None):
        """
        This function instructs the driver to return the next block of values to your 'streaming_ready'
        callback function. You must have previously called 'run_streaming' beforehand to set up streaming.
        
        In most cases the block of values returned will not be enough to fill the data buffer, so you will 
        need to call 'get_streaming_latest_values' repeatedly until you have obtained the required number of
        samples. 
        The timing between calls to the function depends on your application - it should be fast enough to
        avoid running out data but not so fast that it wastes processor time.
        
        Parameters:
            streaming_ready_callback: a function with 'streaming_ready' signature.
            parameter: The callback function may optionally use this to return information to the application.
        
        """
        c_function = getattr(self._clib, self.driver + "GetStreamingLatestValues")
        
        StreamingReady = CFUNCTYPE(None,
                                    c_int16,
                                    c_int32,
                                    c_uint32,
                                    c_int16,
                                    c_uint32,
                                    c_int16,
                                    c_int16,
                                    c_void_p)
        
        streaming_ready = StreamingReady(streaming_ready_callback) if streaming_ready_callback else None

        p_parameter = byref(args) if args is not None else None

        self.status = c_function(
            c_int16(self.handle),
            streaming_ready,
            cast(p_parameter, c_void_p)
        )

    @check_status
    def no_of_streaming_values(self) -> int:
        """ 
        This function returns the number of samples available after data collection in streaming mode. 
        Call it after calling 'stop'
        """
        c_function = getattr(self._clib, self.driver + "NoOfStreamingValues")
        no_of_values = c_uint32()
        self.status = c_function(c_int16(self.handle), byref(no_of_values))
        return no_of_values.value

    @check_status
    def get_unit_info(self, 
                      info:PICO_INFO, 
                      string_length=256) -> str:
        """
        This function retrieves information about the specified oscilloscope or driver software. 
        If the device fails to open or no device is opened, it is still possible to read the driver version.

        Parameters:
            - info: a number specifying what information is required (PICO_INFO).
            - string_length (int, optional): 
                the maximum number of 8-bit integers (int8_t) that may be written to string.

        Returns:
            info_string: the unit information string selected specified by the info argument.
        """
        c_function = getattr(self._clib, self.driver + "GetUnitInfo")

        string = create_string_buffer(string_length)
        
        required_size = c_int16(0)
        
        self.status = c_function(
            c_int16(self.handle),
            byref(string),
            c_int16(string_length),
            byref(required_size),
            c_uint32(info)
        )

        info_string = string.value.decode("utf-8")
        
        return info_string #, required_size.value

    @check_status
    def flash_led(self, start:int):
        """
        This function flashes the LED on the front of the scope without blocking the calling thread. 
        Calls to 'run_streaming' and 'run_block' cancel any flashing started by this function. 
        It is not possible to set the LED to be constantly illuminated, as this state is used 
        to indicate that the scope has not been initialized

        start, the action required: 
        < 0 : flash the LED indefinitely. 
          0 : stop the LED flashing. 
        > 0 : flash the LED 'start' times. 
        If the LED is already flashing on entry to this function, the flash count will be reset to start.
        """
        c_function = getattr(self._clib, self.driver + "FlashLed")
        self.status = c_function(c_int16(self.handle), c_int16(start))
    
    @check_status
    def is_led_flashing(self) -> bool:
        """ This function reads the status of the front-panel LED. """
        c_function = getattr(self._clib, self.driver + "IsLedFlashing")
        status = c_int16()
        self.status = c_function(
            c_int16(self.handle), 
            byref(status)
            )
        return bool(status.value)

    @check_status
    def get_minimum_timebase_stateless(self,
                                       enabled_channel_or_port_flags,
                                       resolution: RESOLUTION
                                       ) -> int:
        """ 
        This function returns the fastest available timebase for the proposed device configuration. 
        It does not write the proposed configuration to the device. 

        - enabled_channel_or_port_flags: The proposed combination of enabled channels and ports. 
            To specify multiple channels and ports, use the bitwise-OR of the relevant CHANNEL_FLAGS #TODO values.
        - resolution: 
            the resolution mode in which you propose to operate the oscilloscope.

        Returns
        - timebase: the shortest timebase available. 
        - time_interval: the sampling interval, in seconds, corresponding to the stated timebase. 
        """
        c_function = getattr(self._clib, self.driver + "GetMinimumTimebaseStateless")

        timebase = c_uint32()
        time_interval = c_double()

        self.status = c_function(
            c_int16(self.handle), 
            c_uint32(enabled_channel_or_port_flags),
            byref(timebase),
            byref(time_interval),
            c_uint32(resolution)
            )

        return timebase.value, time_interval.value

    @check_status
    def nearest_sample_interval_stateless(self,
                                       enabled_channel_or_port_flags,
                                       time_interval_requested: float,
                                       resolution: RESOLUTION,
                                       use_Ets:bool = False
                                       ) -> int:
        """ 
        This function queries the nearest available sampling interval given a desired sampling interval and a
        device configuration. It does not change the configuration of the device.

        """
        c_function = getattr(self._clib, self.driver + "NearestSampleIntervalStateless")

        time_interval_available = c_double()
        timebase = c_uint32()

        self.status = c_function(
            c_int16(self.handle), 
            c_uint32(enabled_channel_or_port_flags),
            c_double(time_interval_requested),
            c_uint32(resolution),
            c_uint16(1 if use_Ets else 0),
            byref(timebase),
            byref(time_interval_available),
            )

        return time_interval_available.value, timebase.value


    @check_status
    def set_digital_port(self, port: CHANNEL, enabled:bool, logic_level: int):
        """
        This function enables or disables a digital port and sets the logic threshold.
        In order to use the fastest sampling rates with digital inputs, disable all analog channels. 
        When all analog channels are disabled you must also select 8-bit resolution to allow the digital inputs to operate alone.
        
        - port, identifies the port for digital data:
                DIGITAL_PORT0 = 0x80 (digital channels 0-7)
                DIGITAL_PORT1 = 0x81 (digital channels 8-15)
        - enabled, whether or not to enable the port. 
            Enabling a digital port allows the scope to collect data from the port and to trigger on the port.
        - logiclevel, the threshold voltage used to distinguish the 0 and 1 states. 
                Range: -32767 (-5V) to 32767 (+5V). 
        """
        c_function = getattr(self._clib, self.driver + "SetDigitalPort")
        
        self.status = c_function(
            c_int16(self.handle), 
            c_int32(port),
            c_int16(1 if enabled else 0),
            c_int16(logic_level)
            )
        
    @check_status
    def set_bandwidth_filter(self, channel: CHANNEL, bandwidth: BANDWIDTH_LIMITER):
        """
        This function controls the hardware bandwidth limiter fitted to each analog input channel. 
        It does not apply to digital input channels on mixed-signal scopes. 

        - channel, the channel to be configured (analog channel A, B, C or D only)
        - bandwidth, the required bandwidth (full or limited to 20 MHz). 
        """
        c_function = getattr(self._clib, self.driver + "SetBandwidthFilter")
        
        self.status = c_function(
            c_int16(self.handle), 
            c_int32(channel),
            c_int32(bandwidth),
            )
        
    @check_status
    def change_power_source(self, power_state:int):
        """
        This function selects the power supply mode. 
        If USB power is required, you must explicitly allow it by calling this function. 
        You must also call this function if the AC power adapter is connected or disconnected during use. 
        
        If you change the power source to PICO_POWER_SUPPLY_NOT_CONNECTED and either of channels C
        and D is currently enabled, they will be switched off. 
        
        If a trigger is set using channel C or D, the trigger settings for those channels will also be removed.
        
        Input:
        power_state, the required state of the unit; one of the following:
                PICO_POWER_SUPPLY_CONNECTED - to run the device on AC adaptor power
                PICO_POWER_SUPPLY_NOT_CONNECTED - to run the device on USB power
                PICO_USB3_0_DEVICE_NON_USB3_0_PORT - for 2-channel 5000D and 5000D MSO devices
        hint: use PICO_STATUS dictionary in constants.py
        """
        c_function = getattr(self._clib, self.driver + "ChangePowerSource")
        
        self.status = c_function(
            c_int16(self.handle),
            c_uint32(power_state)
        )

    def current_power_source(self):
        """
        This function returns the current power state of the device.

        Returns:
        PICO_INVALID_HANDLE - handle of the device is not recognized. 
        PICO_POWER_SUPPLY_CONNECTED - device is powered by the AC adaptor. 
        PICO_POWER_SUPPLY_NOT_CONNECTED - device is powered by the USB cable. 
        PICO_USB3_0_DEVICE_NON_USB3_0_PORT - a 2-channel 5000D or 5000D MSO model is connected to a USB 2.0 port. 
        PICO_OK - the device has two channels and PICO_USB3_0_DEVICE_NON_USB3_0_PORT does not apply.
        """

        c_function = getattr(self._clib, self.driver + "CurrentPowerSource")
        return pico_tag(c_function(c_int16(self.handle)))

    power_source = property(current_power_source, change_power_source)

    ##################### AWG ###########################
    @check_status
    def set_sig_gen_arbitrary(self,
                            offset_voltage: float,
                            pk_to_pk: float,
                            start_delta_phase: int,
                            stop_delta_phase: int,
                            delta_phase_increment: int,
                            dwell_count: int,
                            arbitrary_waveform,
                            arbitrary_waveform_size: int,
                            sweep_type: SWEEP_TYPE,
                            operation: EXTRA_OPERATIONS,
                            index_mode: INDEX_MODE,
                            shots: int,
                            sweeps: int,
                            trigger_type: SIGGEN_TRIG_TYPE,
                            trigger_source: SIGGEN_TRIG_SOURCE,
                            ext_in_threshold: int) -> int:
        """
        Programs the signal generator to produce an arbitrary waveform.

        The arbitrary waveform generator (AWG) uses direct digital synthesis (DDS). It maintains a 32-bit phase
        accumulator that indicates the present location in the waveform. The top bits of the phase accumulator are
        used as an index into a buffer containing the arbitrary waveform. The remaining bits act as the fractional
        part of the index, enabling high-resolution control of output frequency and allowing the generation of lower
        frequencies. 

        The phase accumulator initially increments by start_delta_phase. If the AWG is set to sweep mode, the
        phase increment is increased or decreased at specified intervals until it reaches stop_delta_phase. 
        
        The easiest way to obtain the values of start_delta_phase and stop_delta_phase necessary to generate the
        desired frequency is to call 'sig_gen_frequency_to_phase'. 
        Alternatively, see Calculating deltaPhase below for more information on how to calculate these values.

        Parameters:
        offset_voltage (int):
            Voltage offset in volts applied to the waveform.
        pk_to_pk (int):
            Peak-to-peak voltage in volts. (Ensure that the combination of offset and pk_to_pk does not exceed
            the generator's voltage range, or the output will be clipped.)
        start_delta_phase (int):
            the initial value added to the phase accumulator as the generator begins to step through the waveform buffer.
        stop_delta_phase (int):
            the final value added to the phase accumulator before the generator restarts or reverses the sweep.
        delta_phase_increment (int):
            the amount added to the delta phase value every time the 'dwell_count' period expires. 
            This determines the amount by which the generator sweeps the output frequency in each dwell period.
        dwell_count (int):
            the time, in 50 ns steps, between successive additions of delta_phase_increment to the delta phase accumulator. 
            This determines the rate at which the generator sweeps the output frequency. Minimum value: MIN_DWELL_COUNT
        arbitrary_waveform:
            a buffer that holds the waveform pattern as a set of samples equally spaced in time. 
            If pk_to_pk is set to its maximum (4V) and offset_voltage is set to 0, the output range will be [-2V,+2 V]. 
            Obtain the maximum and minimum allowed sample values by calling 'sig_gen_arbitrary_min_max_values'. 
        arbitrary_waveform_size (int):
            the length of the arbitrary waveform buffer, in samples. 
            Obtain the minimumand maximum allowed values by calling 'sig_gen_arbitrary_min_max_values'. 
        sweep_type (int):
            determines whether the start_delta_phase is swept up to the stop_delta_phase, down to
            it, or repeatedly up and down.
        operation:
            the type of waveform to be produced.
        index_mode:
            specifies how the signal will be formed from the arbitrary waveform data. 
        shots (int):
            0: sweep the frequency as specified by sweeps
            1...PS4000A_MAX_SWEEPS_SHOTS: the number of cycles of the waveform to be produced after a trigger event. sweeps must be zero.
            SHOT_SWEEP_TRIGGER_CONTINUOUS_RUN: start and run continuously after trigger occurs
        sweeps (int):
            0: produce number of cycles specified by shots
            1..PS4000A_MAX_SWEEPS_SHOTS: the number of times to sweep the frequency after a trigger event, according to sweep_type. shots must be zero
            SHOT_SWEEP_TRIGGER_CONTINUOUS_RUN: start a sweep and continue after trigger occurs
        trigger_type:
            the type of trigger (edge or level) that will be applied to the signal generator . 
            If a gated trigger is used, either shots or sweeps, but not both, must be non-zero.
        trigger_source:
            the source that will trigger the signal generator. 
            If a trigger source other than SIGGEN_TRIG_TYPE.NONE is specified, either shots or sweeps, but not both, must be non-zero.
        ext_in_threshold (int):
            used to set trigger level for external trigger.
        """

        c_function = getattr(self._clib, self.driver + "SetSigGenArbitrary")



        self.status = c_function(
            c_int16(self.handle),
            c_int32(int(round(offset_voltage*1e6))),
            c_uint32(int(round(pk_to_pk*1e6))),
            c_uint32(start_delta_phase),
            c_uint32(stop_delta_phase),
            c_uint32(delta_phase_increment),
            c_uint32(dwell_count),
            cast(arbitrary_waveform, c_void_p),
            c_int32(arbitrary_waveform_size),
            c_int32(sweep_type),
            c_int32(operation),
            c_int32(index_mode),
            c_uint32(shots),
            c_uint32(sweeps),
            c_int32(trigger_type),
            c_int32(trigger_source),
            c_int16(ext_in_threshold)
        )
    
    @check_status
    def set_sig_gen_properties_arbitrary(self,
                            start_delta_phase: int,
                            stop_delta_phase: int,
                            delta_phase_increment: int,
                            dwell_count: int,
                            sweep_type: SWEEP_TYPE,
                            shots: int,
                            sweeps: int,
                            trigger_type: SIGGEN_TRIG_TYPE,
                            trigger_source: SIGGEN_TRIG_SOURCE,
                            ext_in_threshold: int) -> int:
        """
        This function reprograms the arbitrary waveform generator. All values can be reprogrammed while the
        oscilloscope is waiting for a trigger. see 'set_sig_gen_arbitrary'.
        """

        c_function = getattr(self._clib, self.driver + "SetSigGenPropertiesArbitrary")

        self.status = c_function(
            c_int16(self.handle),
            c_uint32(start_delta_phase),
            c_uint32(stop_delta_phase),
            c_uint32(delta_phase_increment),
            c_uint32(dwell_count),
            c_int32(sweep_type),
            c_uint32(shots),
            c_uint32(sweeps),
            c_int32(trigger_type),
            c_int32(trigger_source),
            c_int16(ext_in_threshold)
        )

    @check_status
    def sig_gen_software_control(self, state:bool):
        """ 
        This function causes a trigger event, or starts and stops gating, for the signal generator.
        See API programmers guide for more details.
        """
        c_function = getattr(self._clib, self.driver + "SigGenSoftwareControl")
        self.status = c_function(
            c_int16(self.handle),
            c_int16(1 if state else 0)
        ) 

    @check_status
    def sig_gen_arbitrary_min_max_values(self) -> tuple[int,int,int,int]:
        """ 
        This function returns the range of possible sample values and waveform buffer sizes that can 
        be supplied to 'set_sig_gen_arbitrary' for setting up the arbitrary waveform generator (AWG). 
        """
        c_function = getattr(self._clib, self.driver + "SigGenArbitraryMinMaxValues")

        min_arbitrary_waveform_value = c_int16()
        max_arbitrary_waveform_value = c_int16()
        min_arbitrary_waveform_size = c_uint32()
        max_arbitrary_waveform_size = c_uint32()

        self.status = c_function(
            c_int16(self.handle),
            byref(min_arbitrary_waveform_value),
            byref(max_arbitrary_waveform_value),
            byref(min_arbitrary_waveform_size),
            byref(max_arbitrary_waveform_size),
        )
        return (
            min_arbitrary_waveform_value.value,
            max_arbitrary_waveform_value.value, 
            min_arbitrary_waveform_size.value,
            max_arbitrary_waveform_size.value)

    @check_status
    def sig_gen_frequency_to_phase(self, 
                                   frequency:float, 
                                   index_mode: INDEX_MODE, 
                                   buffer_length:int) -> int:
        """ 
        This function converts a frequency to a phase count for use with the arbitrary waveform generator (AWG). 
        The value returned depends on the length of the buffer, the index mode passed and the device model. 
        The phase count can then be used as one of the deltaPhase arguments for set_sig_gen_arbitrary
        or set_sig_gen_properties_arbitrary.
        """
        c_function = getattr(self._clib, self.driver +"SigGenFrequencyToPhase")
        phase = c_uint32()
        self.status = c_function(
            c_int16(self.handle),
            c_double(frequency),
            c_int32(index_mode),
            c_uint32(buffer_length),
            byref(phase)
        )
        return phase.value

    @check_status
    def set_sig_gen_built_in(self,
                            offset_voltage: float,
                            pk_to_pk: float,
                            wave_type: WAVE_TYPE,
                            start_frequency: float,
                            stop_frequency: float,
                            increment: float,
                            dwell_time: float,
                            sweep_type: SWEEP_TYPE,
                            operation: EXTRA_OPERATIONS,
                            shots: int,
                            sweeps: int,
                            trigger_type: SIGGEN_TRIG_TYPE,
                            trigger_source: SIGGEN_TRIG_SOURCE,
                            ext_in_threshold: int,
                            ) -> int:
        """
        This function sets up the signal generator to produce a signal from a list of built-in waveforms. If different
        start and stop frequencies are specified, the device will sweep either up, down or up and down.

        Arguments
        - start_frequency: MIN_FREQUENCY: 30 mHz
        - stop_frequency: MAX_FREQUENCY: 20 MHz
        - increment: the amount of frequency increase or decrease in sweep mode.
        - dwell_time: the time for which the sweep stays at each frequency, in seconds.

        Other arguments: see 'set_sig_gen_arbitrary'.
        """
        c_function = getattr(self._clib, self.driver +"SetSigGenBuiltInV2")

        self.status = c_function(
            c_int16(self.handle),
            c_int32(int(round(offset_voltage*1e6))),
            c_uint32(int(round(pk_to_pk*1e6))),
            c_int32(wave_type),
            c_double(start_frequency),
            c_double(stop_frequency),
            c_double(increment),
            c_double(dwell_time),
            c_int32(sweep_type),
            c_int32(operation),
            c_uint32(shots),
            c_uint32(sweeps),
            c_int32(trigger_type),
            c_int32(trigger_source),
            c_int16(ext_in_threshold)
        )

    @check_status
    def set_sig_gen_properties_built_in(self,
                            start_frequency: float,
                            stop_frequency: float,
                            increment: float,
                            dwell_time: float,
                            sweep_type: SWEEP_TYPE,
                            shots: int,
                            sweeps: int,
                            trigger_type: SIGGEN_TRIG_TYPE,
                            trigger_source: SIGGEN_TRIG_SOURCE,
                            ext_in_threshold: int,
                            ) -> int:
        """
        This function reprograms the signal generator.
        Values can be changed while the oscilloscope is waiting for a trigger.
        Arguments: see 'set_sig_gen_built_in'
        """
        c_function = getattr(self._clib, self.driver + "SetSigGenPropertiesBuiltIn")

        self.status = c_function(
            c_int16(self.handle),
            c_double(start_frequency),
            c_double(stop_frequency),
            c_double(increment),
            c_double(dwell_time),
            c_int32(sweep_type),
            c_uint32(shots),
            c_uint32(sweeps),
            c_int32(trigger_type),
            c_int32(trigger_source),
            c_int16(ext_in_threshold)
        )
    
    @check_status
    def ping_unit(self):
        """
        This function can be used to check that the already opened device is still 
        connected to the USB port and communication is successful.
        """
        c_function = getattr(self._clib, self.driver + "PingUnit")
        self.status = c_function(c_int16(self.handle),)

    @check_status
    def get_max_down_sample_ratio(self,
                                  no_of_unaggreated_samples:int,
                                  down_sample_ratio_mode: RATIO_MODE,
                                  segment_index:int):
        """
        This function returns the maximum downsampling ratio that can be used for 
        a given number of samples in a given downsampling mode.
        """
        c_function = getattr(self._clib, self.driver + "GetMaxDownSampleRatio")
        
        max_down_sample_ratio = c_uint32()
        self.status = c_function(
            c_int16(self.handle),
            c_uint32(no_of_unaggreated_samples),
            byref(max_down_sample_ratio),
            c_int32(down_sample_ratio_mode),
            c_uint32(segment_index)
            )
        return max_down_sample_ratio.value


    def make_symbol(self, *args):
        #print(args[1][7:], " is not implemented")
        return
