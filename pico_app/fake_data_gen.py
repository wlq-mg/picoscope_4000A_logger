# Adjusted unit function to handle time units properly
import os
import numpy as np
from datetime import datetime

import random

# Function to generate a random time (HHMMSS) for a given date
def get_random_time():
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return f"{hour:02d}{minute:02d}{second:02d}"

# Configuration
logging_directory = "./pico_app/data"
sample_interval = 0.02
time_unit = "s"
channels = {
    'A': {"active": True, "scale": 5.0, "offset": 0.0},
    'B': {"active": True, "scale": 0.5, "offset": 1.0},
    'C': {"active": True, "scale": 2.0, "offset": -1.0},
    'E': {"active": True, "scale": 1.0, "offset": 0.2},
}
num_samples = 500


def unit(time_unit):
    if time_unit == "s":
        return 1  # Keep seconds as is
    elif time_unit == "ms":
        return 1e-3  # Convert milliseconds to seconds
    elif time_unit == "us":
        return 1e-6  # Convert microseconds to seconds
    else:
        return 1  # Default to seconds

specified_date = "20250226"  # Example date (YYYYMMDD)
random_time = get_random_time()

# Combine the specified date with the random time
date_str = f"{specified_date}_{random_time}"

# Create folder with current datetime
# date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
folder = os.path.join(logging_directory, date_str)
os.makedirs(folder, exist_ok=True)

# Record files dictionary
record_file = {}

# Create files and write headers
for ch, channel in channels.items():
    if not channel["active"]:
        continue

    filename = f"{folder}/picoscope_ch_{ch}.bin"
    
    # Create header
    header = (
        f"Time Interval: {sample_interval * unit(time_unit)} {time_unit}\n"
        f"Scale: {channel['scale']}\n"
        f"Offset: {channel['offset']}\n\n"
    )
    
    # Open file and write header
    record_file[ch] = open(filename, 'wb')
    record_file[ch].write(header.encode('utf-8'))
    
    # Generate fake data and write to file
    fake_data = np.random.randint(-32768, 32767, num_samples, dtype='int16')
    fake_data.tofile(record_file[ch])
    
    # Close the file
    record_file[ch].close()

# List generated files
generated_files = os.listdir(folder)
generated_files
