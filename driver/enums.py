

from enum import IntEnum

class PICO_INFO():
    PICO_DRIVER_VERSION = 0x00000000
    PICO_USB_VERSION = 0x00000001
    PICO_HARDWARE_VERSION = 0x00000002
    PICO_VARIANT_INFO = 0x00000003
    PICO_BATCH_AND_SERIAL = 0x00000004
    PICO_CAL_DATE = 0x00000005
    PICO_KERNEL_VERSION = 0x00000006
    PICO_DIGITAL_HARDWARE_VERSION = 0x00000007
    PICO_ANALOGUE_HARDWARE_VERSION = 0x00000008
    PICO_FIRMWARE_VERSION_1 = 0x00000009
    PICO_FIRMWARE_VERSION_2 = 0x0000000A
    #PICO_MAC_ADDRESS = 0x0000000B
    PICO_SHADOW_CAL = 0x0000000C
    PICO_IPP_VERSION = 0x0000000D

class SWEEP_TYPE(IntEnum):
    """These values specify the frequency sweep mode of the signal generator or arbitrary waveform generator."""
    UP              = 0 # sweep the frequency from lower limit up to upper limit
    DOWN            = 1 # sweep the frequency from upper limit down to lower limit
    UPDOWN          = 2 # sweep the frequency up and then down
    DOWNUP          = 3 # sweep the frequency down and then up

class EXTRA_OPERATIONS(IntEnum):
    """ These values specify additional signal types for the signal generator. """
    ES_OFF      = 0 # normal signal generator operation specified by wavetype, or normal AWG operation.
    WHITENOISE  = 1 # produces white noise and ignores all settings except pk_to_pk and offset_voltage.
    PRBS        = 2 # produces a pseudorandom binary sequence with a bit rate specified by the start and stop frequencies.

class INDEX_MODE(IntEnum):
    """ 
    The arbitrary waveform generator supports single and dual index modes to help you make the best use of
    the waveform buffer.
    - Single mode. The generator outputs the raw contents of the buffer repeatedly. 
    This mode is the only one that can generate asymmetrical waveforms. 
    You can also use this mode for symmetrical waveforms, but the dual mode
    makes more efficient use of the buffer memory.

    - Dual mode. The generator outputs the contents of the buffer from beginning to end, 
    and then does a second pass in the reverse direction through the buffer. 
    This allows you to specify only the first half of a waveform with twofold symmetry, 
    such as a Gaussian function, and let the generator fill in the other half.

    """
    SINGLE  = 0
    DUAL    = 1
    QUAD    = 2 # No used

class SIGGEN_TRIG_TYPE(IntEnum):
    """
    These values specify how triggering of the signal generator or arbitrary waveform generator works. The
    signal generator can be started by a rising or falling edge on the trigger signal or can be gated to run while
    the trigger signal is high or low. The gated trigger remembers the phase of the waveform when the trigger
    signal goes inactive and resumes the waveform from the same phase when the trigger signal goes active again.
    """
    RISING       = 0 # trigger on rising edge
    FALLING      = 1 # trigger on falling edge
    GATE_HIGH    = 2 # run while trigger is high
    GATE_LOW     = 3 # run while trigger is low

class SIGGEN_TRIG_SOURCE(IntEnum):
    """
    These values specify how triggering of the signal generator or arbitrary waveform generator works. The
    signal generator can be started by a rising or falling edge on the trigger signal or can be gated to run while
    the trigger signal is high or low.
    """
    NONE        = 0 # run without waiting for trigger
    SCOPE_TRIG  = 1 # use scope trigger
    AUX_IN      = 2 # 
    EXT_IN      = 3 # use EXT input
    SOFT_TRIG   = 4 # wait for software trigger provided by 'sig_gen_software_control'

class WAVE_TYPE(IntEnum):
    SINE = 0
    SQUARE = 1
    TRIANGLE = 2
    RAMP_UP = 3
    RAMP_DOWN = 4
    SINC = 5
    GAUSSIAN = 6
    HALF_SINE = 7
    DC_VOLTAGE = 8
    WHITE_NOISE = 9

class BANDWIDTH_LIMITER(IntEnum):
    BW_FULL = 0  # use the scope's full specified bandwidth
    BW_20MHZ = 20000000 # enable the hardware 20 MHz bandwidth limiter

class RATIO_MODE(IntEnum): 
    NONE        = 0 # No downsampling. Returns raw data values
    AGGREGATE   = 1 # Reduces every block of n values to just two values: a minimum and a maximum. The minimum and maximum values are returned in two separate buffers
    DECIMATE    = 2 # Reduces every block of n values to a single value representing the average (arithmetic mean) of all the values.
    AVERAGE     = 4 # Reduces every block of n values to just the first value in the block, discarding all the other values.

class RANGE(IntEnum):
    RANGE_10MV  = 0
    RANGE_20MV  = 1
    RANGE_50MV  = 2
    RANGE_100MV = 3
    RANGE_200MV = 4
    RANGE_500MV = 5
    RANGE_1V    = 6
    RANGE_2V    = 7
    RANGE_5V    = 8
    RANGE_10V   = 9
    RANGE_20V   = 10
    RANGE_50V   = 11

class COUPLING(IntEnum):
    AC = 0 # 1 MOhm impedance, AC coupling. The channel accepts input frequencies from about 1Hz   up to its max -3dB analog bandwidth.
    DC = 1 # 1 MOhm impedance, DC coupling. The scope accepts all input frequencies from zero (DC) up to its max -3dB analog bandwidth.

class RESOLUTION(IntEnum):
    DR_8BIT= 0
    DR_12BIT = 1
    DR_14BIT = 2
    DR_15BIT = 3
    DR_16BIT = 4

class CHANNEL(IntEnum):
    A = 0
    B = 1
    C = 2
    D = 3
    E = 4
    F = 5
    G = 6
    H = 7
    TRIGGER_AUX = 9
    PULSE_WIDTH_SOURCE = 0x10000000

class THRESHOLD_DIRECTION(IntEnum):
    ABOVE = 0
    INSIDE = 0  # alias for ABOVE

    BELOW = 1
    OUTSIDE = 1  # alias for BELOW

    RISING = 2
    ENTER = 2   # alias for RISING
    NONE = 2    # alias for RISING

    FALLING = 3
    EXIT = 3    # alias for FALLING

    RISING_OR_FALLING = 4
    ENTER_OR_EXIT = 4  # alias for RISING_OR_FALLING

    ABOVE_LOWER = 5
    BELOW_LOWER = 6
    RISING_LOWER = 7
    FALLING_LOWER = 8
    POSITIVE_RUNT = 9
    NEGATIVE_RUNT = 10


class TIME_UNITS(IntEnum):
    FS = 0
    PS = 1
    NS = 2
    US = 3
    MS = 4
    S = 5