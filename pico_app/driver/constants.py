#
# Copyright (C) 2014-2018 Pico Technology Ltd. See LICENSE file for terms.
#
"""
Defines python-visible versions of preprocessor-macros from Pico SDK C header files.
All constants in this file are exposed directly on the Library class specific to each driver. That
(rather than importing this file directly) is the supported way of accessing them, since some
older drivers have different names/values for some of the macros.
"""
from .errors import UnknownConstantError


MIN_DWELL_COUNT = 3

SHOT_SWEEP_TRIGGER_CONTINUOUS_RUN = 0xFFFFFFFF

# convenience functions provided in the old python SDK:
def pico_tag(number):
    """Get the macro name for a given PICO_STATUS value."""
    try:
        return PICO_STATUS_LOOKUP[number]
    except KeyError:
        raise UnknownConstantError("%s is not a known PICO_STATUS value." % number)


def pico_num(tag):
    """Resolve the numerical constant associated with a PICO_STATUS macro."""
    try:
        return PICO_STATUS[tag]
    except KeyError:
        raise UnknownConstantError("%s is not a known PICO_STATUS macro." % tag)


def make_enum(members):
    """All C enums with no specific values follow the pattern 0, 1, 2... in the order they are in source."""
    enum = {}
    for i, member in enumerate(members):
        keys = [member]
        if isinstance(member, tuple):
            # this member has multiple names!
            keys = member
        for key in keys:
            enum[key] = i
    return enum


PICO_STATUS = {
    "PICO_OK": 0x00000000,
    "PICO_MAX_UNITS_OPENED": 0x00000001,
    "PICO_MEMORY_FAIL": 0x00000002,
    "PICO_NOT_FOUND": 0x00000003,
    "PICO_FW_FAIL": 0x00000004,
    "PICO_OPEN_OPERATION_IN_PROGRESS": 0x00000005,
    "PICO_OPERATION_FAILED": 0x00000006,
    "PICO_NOT_RESPONDING": 0x00000007,
    "PICO_CONFIG_FAIL": 0x00000008,
    "PICO_KERNEL_DRIVER_TOO_OLD": 0x00000009,
    "PICO_EEPROM_CORRUPT": 0x0000000A,
    "PICO_OS_NOT_SUPPORTED": 0x0000000B,
    "PICO_INVALID_HANDLE": 0x0000000C,
    "PICO_INVALID_PARAMETER": 0x0000000D,
    "PICO_INVALID_TIMEBASE": 0x0000000E,
    "PICO_INVALID_VOLTAGE_RANGE": 0x0000000F,
    "PICO_INVALID_CHANNEL": 0x00000010,
    "PICO_INVALID_TRIGGER_CHANNEL": 0x00000011,
    "PICO_INVALID_CONDITION_CHANNEL": 0x00000012,
    "PICO_NO_SIGNAL_GENERATOR": 0x00000013,
    "PICO_STREAMING_FAILED": 0x00000014,
    "PICO_BLOCK_MODE_FAILED": 0x00000015,
    "PICO_NULL_PARAMETER": 0x00000016,
    "PICO_ETS_MODE_SET": 0x00000017,
    "PICO_DATA_NOT_AVAILABLE": 0x00000018,
    "PICO_STRING_BUFFER_TO_SMALL": 0x00000019,
    "PICO_ETS_NOT_SUPPORTED": 0x0000001A,
    "PICO_AUTO_TRIGGER_TIME_TO_SHORT": 0x0000001B,
    "PICO_BUFFER_STALL": 0x0000001C,
    "PICO_TOO_MANY_SAMPLES": 0x0000001D,
    "PICO_TOO_MANY_SEGMENTS": 0x0000001E,
    "PICO_PULSE_WIDTH_QUALIFIER": 0x0000001F,
    "PICO_DELAY": 0x00000020,
    "PICO_SOURCE_DETAILS": 0x00000021,
    "PICO_CONDITIONS": 0x00000022,
    "PICO_USER_CALLBACK": 0x00000023,
    "PICO_DEVICE_SAMPLING": 0x00000024,
    "PICO_NO_SAMPLES_AVAILABLE": 0x00000025,
    "PICO_SEGMENT_OUT_OF_RANGE": 0x00000026,
    "PICO_BUSY": 0x00000027,
    "PICO_STARTINDEX_INVALID": 0x00000028,
    "PICO_INVALID_INFO": 0x00000029,
    "PICO_INFO_UNAVAILABLE": 0x0000002A,
    "PICO_INVALID_SAMPLE_INTERVAL": 0x0000002B,
    "PICO_TRIGGER_ERROR": 0x0000002C,
    "PICO_MEMORY": 0x0000002D,
    "PICO_SIG_GEN_PARAM": 0x0000002E,
    "PICO_SHOTS_SWEEPS_WARNING": 0x0000002F,
    "PICO_SIGGEN_TRIGGER_SOURCE": 0x00000030,
    "PICO_AUX_OUTPUT_CONFLICT": 0x00000031,
    "PICO_AUX_OUTPUT_ETS_CONFLICT": 0x00000032,
    "PICO_WARNING_EXT_THRESHOLD_CONFLICT": 0x00000033,
    "PICO_WARNING_AUX_OUTPUT_CONFLICT": 0x00000034,
    "PICO_SIGGEN_OUTPUT_OVER_VOLTAGE": 0x00000035,
    "PICO_DELAY_NULL": 0x00000036,
    "PICO_INVALID_BUFFER": 0x00000037,
    "PICO_SIGGEN_OFFSET_VOLTAGE": 0x00000038,
    "PICO_SIGGEN_PK_TO_PK": 0x00000039,
    "PICO_CANCELLED": 0x0000003A,
    "PICO_SEGMENT_NOT_USED": 0x0000003B,
    "PICO_INVALID_CALL": 0x0000003C,
    "PICO_GET_VALUES_INTERRUPTED": 0x0000003D,
    "PICO_NOT_USED": 0x0000003F,
    "PICO_INVALID_SAMPLERATIO": 0x00000040,
    "PICO_INVALID_STATE": 0x00000041,
    "PICO_NOT_ENOUGH_SEGMENTS": 0x00000042,
    "PICO_DRIVER_FUNCTION": 0x00000043,
    "PICO_RESERVED": 0x00000044,
    "PICO_INVALID_COUPLING": 0x00000045,
    "PICO_BUFFERS_NOT_SET": 0x00000046,
    "PICO_RATIO_MODE_NOT_SUPPORTED": 0x00000047,
    "PICO_RAPID_NOT_SUPPORT_AGGREGATION": 0x00000048,
    "PICO_INVALID_TRIGGER_PROPERTY": 0x00000049,
    "PICO_INTERFACE_NOT_CONNECTED": 0x0000004A,
    "PICO_RESISTANCE_AND_PROBE_NOT_ALLOWED": 0x0000004B,
    "PICO_POWER_FAILED": 0x0000004C,
    "PICO_SIGGEN_WAVEFORM_SETUP_FAILED": 0x0000004D,
    "PICO_FPGA_FAIL": 0x0000004E,
    "PICO_POWER_MANAGER": 0x0000004F,
    "PICO_INVALID_ANALOGUE_OFFSET": 0x00000050,
    "PICO_PLL_LOCK_FAILED": 0x00000051,
    "PICO_ANALOG_BOARD": 0x00000052,
    "PICO_CONFIG_FAIL_AWG": 0x00000053,
    "PICO_INITIALISE_FPGA": 0x00000054,
    "PICO_EXTERNAL_FREQUENCY_INVALID": 0x00000056,
    "PICO_CLOCK_CHANGE_ERROR": 0x00000057,
    "PICO_TRIGGER_AND_EXTERNAL_CLOCK_CLASH": 0x00000058,
    "PICO_PWQ_AND_EXTERNAL_CLOCK_CLASH": 0x00000059,
    "PICO_UNABLE_TO_OPEN_SCALING_FILE": 0x0000005A,
    "PICO_MEMORY_CLOCK_FREQUENCY": 0x0000005B,
    "PICO_I2C_NOT_RESPONDING": 0x0000005C,
    "PICO_NO_CAPTURES_AVAILABLE": 0x0000005D,
    "PICO_NOT_USED_IN_THIS_CAPTURE_MODE": 0x0000005E,
    "PICO_TOO_MANY_TRIGGER_CHANNELS_IN_USE": 0x0000005F,
    "PICO_INVALID_TRIGGER_DIRECTION": 0x00000060,
    "PICO_INVALID_TRIGGER_STATES": 0x00000061,
    "PICO_GET_DATA_ACTIVE": 0x00000103,
    "PICO_IP_NETWORKED": 0x00000104,
    "PICO_INVALID_IP_ADDRESS": 0x00000105,
    "PICO_IPSOCKET_FAILED": 0x00000106,
    "PICO_IPSOCKET_TIMEDOUT": 0x00000107,
    "PICO_SETTINGS_FAILED": 0x00000108,
    "PICO_NETWORK_FAILED": 0x00000109,
    "PICO_WS2_32_DLL_NOT_LOADED": 0x0000010A,
    "PICO_INVALID_IP_PORT": 0x0000010B,
    "PICO_COUPLING_NOT_SUPPORTED": 0x0000010C,
    "PICO_BANDWIDTH_NOT_SUPPORTED": 0x0000010D,
    "PICO_INVALID_BANDWIDTH": 0x0000010E,
    "PICO_AWG_NOT_SUPPORTED": 0x0000010F,
    "PICO_ETS_NOT_RUNNING": 0x00000110,
    "PICO_SIG_GEN_WHITENOISE_NOT_SUPPORTED": 0x00000111,
    "PICO_SIG_GEN_WAVETYPE_NOT_SUPPORTED": 0x00000112,
    "PICO_INVALID_DIGITAL_PORT": 0x00000113,
    "PICO_INVALID_DIGITAL_CHANNEL": 0x00000114,
    "PICO_INVALID_DIGITAL_TRIGGER_DIRECTION": 0x00000115,
    "PICO_SIG_GEN_PRBS_NOT_SUPPORTED": 0x00000116,
    "PICO_ETS_NOT_AVAILABLE_WITH_LOGIC_CHANNELS": 0x00000117,
    "PICO_WARNING_REPEAT_VALUE": 0x00000118,
    "PICO_POWER_SUPPLY_CONNECTED": 0x00000119,
    "PICO_POWER_SUPPLY_NOT_CONNECTED": 0x0000011A,
    "PICO_POWER_SUPPLY_REQUEST_INVALID": 0x0000011B,
    "PICO_POWER_SUPPLY_UNDERVOLTAGE": 0x0000011C,
    "PICO_CAPTURING_DATA": 0x0000011D,
    "PICO_USB3_0_DEVICE_NON_USB3_0_PORT": 0x0000011E,
    "PICO_NOT_SUPPORTED_BY_THIS_DEVICE": 0x0000011F,
    "PICO_INVALID_DEVICE_RESOLUTION": 0x00000120,
    "PICO_INVALID_NUMBER_CHANNELS_FOR_RESOLUTION": 0x00000121,
    "PICO_CHANNEL_DISABLED_DUE_TO_USB_POWERED": 0x00000122,
    "PICO_SIGGEN_DC_VOLTAGE_NOT_CONFIGURABLE": 0x00000123,
    "PICO_NO_TRIGGER_ENABLED_FOR_TRIGGER_IN_PRE_TRIG": 0x00000124,
    "PICO_TRIGGER_WITHIN_PRE_TRIG_NOT_ARMED": 0x00000125,
    "PICO_TRIGGER_WITHIN_PRE_NOT_ALLOWED_WITH_DELAY": 0x00000126,
    "PICO_TRIGGER_INDEX_UNAVAILABLE": 0x00000127,
    "PICO_AWG_CLOCK_FREQUENCY": 0x00000128,
    "PICO_TOO_MANY_CHANNELS_IN_USE": 0x00000129,
    "PICO_NULL_CONDITIONS": 0x0000012A,
    "PICO_DUPLICATE_CONDITION_SOURCE": 0x0000012B,
    "PICO_INVALID_CONDITION_INFO": 0x0000012C,
    "PICO_SETTINGS_READ_FAILED": 0x0000012D,
    "PICO_SETTINGS_WRITE_FAILED": 0x0000012E,
    "PICO_ARGUMENT_OUT_OF_RANGE": 0x0000012F,
    "PICO_HARDWARE_VERSION_NOT_SUPPORTED": 0x00000130,
    "PICO_DIGITAL_HARDWARE_VERSION_NOT_SUPPORTED": 0x00000131,
    "PICO_ANALOGUE_HARDWARE_VERSION_NOT_SUPPORTED": 0x00000132,
    "PICO_UNABLE_TO_CONVERT_TO_RESISTANCE": 0x00000133,
    "PICO_DUPLICATED_CHANNEL": 0x00000134,
    "PICO_INVALID_RESISTANCE_CONVERSION": 0x00000135,
    "PICO_INVALID_VALUE_IN_MAX_BUFFER": 0x00000136,
    "PICO_INVALID_VALUE_IN_MIN_BUFFER": 0x00000137,
    "PICO_SIGGEN_FREQUENCY_OUT_OF_RANGE": 0x00000138,
    "PICO_EEPROM2_CORRUPT": 0x00000139,
    "PICO_EEPROM2_FAIL": 0x0000013A,
    "PICO_SERIAL_BUFFER_TOO_SMALL": 0x0000013B,
    "PICO_SIGGEN_TRIGGER_AND_EXTERNAL_CLOCK_CLASH": 0x0000013C,
    "PICO_WARNING_SIGGEN_AUXIO_TRIGGER_DISABLED": 0x0000013D,
    "PICO_SIGGEN_GATING_AUXIO_NOT_AVAILABLE": 0x00000013E,
    "PICO_SIGGEN_GATING_AUXIO_ENABLED": 0x00000013F,
    "PICO_RESOURCE_ERROR": 0x00000140,
    "PICO_TEMPERATURE_TYPE_INVALID": 0x00000141,
    "PICO_TEMPERATURE_TYPE_NOT_SUPPORTED": 0x00000142,
    "PICO_TIMEOUT": 0x00000143,
    "PICO_DEVICE_NOT_FUNCTIONING": 0x00000144,
    "PICO_INTERNAL_ERROR": 0x00000145,
    "PICO_MULTIPLE_DEVICES_FOUND": 0x00000146,
    "PICO_WARNING_NUMBER_OF_SEGMENTS_REDUCED": 0x00000147,
    "PICO_CAL_PINS_STATES": 0x00000148,
    "PICO_CAL_PINS_FREQUENCY": 0x00000149,
    "PICO_CAL_PINS_AMPLITUDE": 0x0000014A,
    "PICO_CAL_PINS_WAVETYPE": 0x0000014B,
    "PICO_CAL_PINS_OFFSET": 0x0000014C,
    "PICO_PROBE_FAULT": 0x0000014D,
    "PICO_PROBE_IDENTITY_UNKNOWN": 0x0000014E,
    "PICO_PROBE_POWER_DC_POWER_SUPPLE_REQUIRED": 0x0000014F,
    "PICO_PROBE_NOT_POWERED_THROUGH_DC_POWER_SUPPLY": 0x00000150,
    "PICO_PROBE_CONFIG_FAILURE": 0x00000151,
    "PICO_PROBE_INTERACTION_CALLBACK": 0x00000152,
    "PICO_UNKNOWN_INTELLIGENT_PROBE": 0x00000153,
    "PICO_INTELLIGENT_PROBE_CORRUPT": 0x00000154,
    "PICO_PROBE_COLLECTION_NOT_STARTED": 0x00000155,
    "PICO_PROBE_POWER_CONSUMPTION_EXCEEDED": 0x00000156,
    "PICO_WARNING_PROBE_CHANNEL_OUT_OF_SYNC": 0x00000157,
    "PICO_ENDPOINT_MISSING": 0x00000158,
    "PICO_UNKNOWN_ENDPOINT_REQUEST": 0x00000159,
    "PICO_ADC_TYPE_ERROR": 0x0000015A,
    "PICO_FPGA2_FAILED": 0x0000015B,
    "PICO_FPGA2_DEVICE_STATUS": 0x0000015C,
    "PICO_ENABLED_PROGRAM_FPGA2_FAILED": 0x0000015D,
    "PICO_NO_CANNELS_OR_PORTS_ENABLED": 0x0000015E,
    "PICO_INVALID_RATIO_MODE": 0x0000015F,
    "PICO_READS_NOT_SUPPORTED_IN_CURRENT_CAPTURE_MODE": 0x00000160,
    "PICO_TRIGGER_READ_SELECTION_CHECK_FAILED": 0x00000161,
    "PICO_DATA_READ1_SELECTION_CHECK_FAILED": 0x00000162,
    "PICO_DATA_READ2_SELECTION_CHECK_FAILED": 0x00000164,
    "PICO_DATA_READ3_SELECTION_CHECK_FAILED": 0x00000168,
    "PICO_READ_SELECTION_OUT_OF_RANGE": 0x00000170,
    "PICO_MULTIPLE_RATIO_MODES": 0x00000171,
    "PICO_NO_SAMPLES_READ": 0x00000172,
    "PICO_RATIO_MODE_NOT_REQUESTED": 0x00000173,
    "PICO_NO_USER_READ_REQUESTS": 0x00000174,
    "PICO_ZERO_SAMPLES_INVALID": 0x00000175,
    "PICO_ANALOGUE_HARDWARE_MISSING": 0x00000176,
    "PICO_ANALOGUE_HARDWARE_PINS": 0x00000177,
    "PICO_ANALOGUE_SMPS_FAULT": 0x00000178,
    "PICO_DIGITAL_ANALOGUE_HARDWARE_CONFLICT": 0x00000179,
    "PICO_RATIO_MODE_BUFFER_NOT_SET": 0x0000017A,
    "PICO_RESOLUTION_NOT_SUPPORTED_BY_VARIENT": 0x0000017B,
    "PICO_THRESHOLD_OUT_OF_RANGE": 0x0000017C,
    "PICO_INVALID_SIMPLE_TRIGGER_DIRECTION": 0x0000017D,
    "PICO_AUX_NOT_SUPPORTED": 0x0000017E,
    "PICO_NULL_DIRECTIONS": 0x0000017F,
    "PICO_NULL_CHANNEL_PROPERTIES": 0x00000180,
    "PICO_TRIGGER_CHANNEL_NOT_ENABLED": 0x00000181,
    "PICO_CONDITION_HAS_NO_TRIGGER_PROPERTY": 0x00000182,
    "PICO_RATIO_MODE_TRIGGER_MASKING_INVALID": 0x00000183,
    "PICO_TRIGGER_DATA_REQUIRES_MIN_BUFFER_SIZE_OF_40_SAMPLES": 0x00000184,
    "PICO_NO_OF_CAPTURES_OUT_OF_RANGE": 0x00000185,
    "PICO_RATIO_MODE_SEGMENT_HEADER_DOES_NOT_REQUIRE_BUFFERS": 0x00000186,
    "PICO_FOR_SEGMENT_HEADER_USE_GETTRIGGERINFO": 0x00000187,
    "PICO_READ_NOT_SET": 0x00000188,
    "PICO_ADC_SETTING_MISMATCH": 0x00000189,
    "PICO_DATATYPE_INVALID": 0x0000018A,
    "PICO_RATIO_MODE_DOES_NOT_SUPPORT_DATATYPE": 0x0000018B,
    "PICO_CHANNEL_COMBINATION_NOT_VALID_IN_THIS_RESOLUTION": 0x0000018C,
    "PICO_USE_8BIT_RESOLUTION": 0x0000018D,
    "PICO_AGGREGATE_BUFFERS_SAME_POINTER": 0x0000018E,
    "PICO_OVERLAPPED_READ_VALUES_OUT_OF_RANGE": 0x0000018F,
    "PICO_OVERLAPPED_READ_SEGMENTS_OUT_OF_RANGE": 0x00000190,
    "PICO_CHANNELFLAGSCOMBINATIONS_ARRAY_SIZE_TOO_SMALL": 0x00000191,
    "PICO_CAPTURES_EXCEEDS_NO_OF_SUPPORTED_SEGMENTS": 0x00000192,
    "PICO_TIME_UNITS_OUT_OF_RANGE": 0x00000193,
    "PICO_NO_SAMPLES_REQUESTED": 0x00000194,
    "PICO_INVALID_ACTION": 0x00000195,
    "PICO_NO_OF_SAMPLES_NEED_TO_BE_EQUAL_WHEN_ADDING_BUFFERS": 0x00000196,
    "PICO_WAITING_FOR_DATA_BUFFERS": 0x00000197,
    "PICO_STREAMING_ONLY_SUPPORTS_ONE_READ": 0x00000198,
    "PICO_CLEAR_DATA_BUFFER_INVALID": 0x00000199,
    "PICO_INVALID_ACTION_FLAGS_COMBINATION": 0x0000019A,
    "PICO_PICO_MOTH_MIN_AND_MAX_NULL_BUFFERS_CANNOT_BE_ADDED": 0x0000019B,
    "PICO_CONFLICT_IN_SET_DATA_BUFFERS_CALL_REMOVE_DATA_BUFFER_TO_RESET": 0x0000019C,
    "PICO_REMOVING_DATA_BUFFER_ENTRIES_NOT_ALLOWED_WHILE_DATA_PROCESSING": 0x0000019D,
    "PICO_CYUSB_REQUEST_FAILED": 0x00000200,
    "PICO_STREAMING_DATA_REQUIRED": 0x00000201,
    "PICO_INVALID_NUMBER_OF_SAMPLES": 0x00000202,
    "PICO_INALID_DISTRIBUTION": 0x00000203,
    "PICO_BUFFER_LENGTH_GREATER_THAN_INT32_T": 0x00000204,
    "PICO_PLL_MUX_OUT_FAILED": 0x00000209,
    "PICO_ONE_PULSE_WIDTH_DIRECTION_ALLOWED": 0x0000020A,
    "PICO_EXTERNAL_TRIGGER_NOT_SUPPORTED": 0x0000020B,
    "PICO_NO_TRIGGER_CONDITIONS_SET": 0x0000020C,
    "PICO_NO_OF_CHANNEL_TRIGGER_PROPERTIES_OUT_OF_RANGE": 0x0000020D,
    "PICO_PROBE_COMPNENT_ERROR": 0x0000020E,
    "PICO_INVALID_TRIGGER_CHANNELS_FOR_ETS": 0x00000210,
    "PICO_NOT_AVALIABLE_WHEN_STREAMING_IS_RUNNING": 0x00000211,
    "PICO_INVALID_TRIGGER_WITHIN_PRE_TRIGGER_STATE": 0x00000212,
    "PICO_ZERO_NUMBER_OF_CAPTURES_INVALID": 0x00000213,
    "PICO_TRIGGER_DELAY_OUT_OF_RANGE": 0x00000300,
    "PICO_INVALID_THRESHOLD_DIRECTION": 0x00000301,
    "PICO_INVALID_THRESGOLD_MODE": 0x00000302,
    "PICO_DEVICE_TIME_STAMP_RESET": 0x01000000,
    "PICO_WATCHDOGTIMER": 0x10000000,
    "PICO_IPP_NOT_FOUND": 0x10000001,
    "PICO_IPP_NO_FUNCTION": 0x10000002,
    "PICO_IPP_ERROR": 0x10000003,
    "PICO_SHADOW_CAL_NOT_AVAILABLE": 0x10000004,
    "PICO_SHADOW_CAL_DISABLED": 0x10000005,
    "PICO_SHADOW_CAL_ERROR": 0x10000006,
    "PICO_SHADOW_CAL_CORRUPT": 0x10000007,
}

PICO_STATUS_LOOKUP = {v: k for k, v in PICO_STATUS.items()}

PICO_INFO = {
    "PICO_DRIVER_VERSION": 0x00000000,
    "PICO_USB_VERSION": 0x00000001,
    "PICO_HARDWARE_VERSION": 0x00000002,
    "PICO_VARIANT_INFO": 0x00000003,
    "PICO_BATCH_AND_SERIAL": 0x00000004,
    "PICO_CAL_DATE": 0x00000005,
    "PICO_KERNEL_VERSION": 0x00000006,
    "PICO_DIGITAL_HARDWARE_VERSION": 0x00000007,
    "PICO_ANALOGUE_HARDWARE_VERSION": 0x00000008,
    "PICO_FIRMWARE_VERSION_1": 0x00000009,
    "PICO_FIRMWARE_VERSION_2": 0x0000000A,
    "PICO_MAC_ADDRESS": 0x0000000B,
    "PICO_SHADOW_CAL": 0x0000000C,
    "PICO_IPP_VERSION": 0x0000000D,
}
