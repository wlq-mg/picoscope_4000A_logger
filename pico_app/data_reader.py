import numpy as np
import matplotlib.pyplot as plt

import numpy as np
import os

def read_recorded_data(directory):
    """
    Reads the recorded data from multiple binary files in the specified directory.
    Returns a dictionary containing headers and data for each channel.
    """
    data_chunk = {}
    headers = {}
    
    # Iterate over all binary files in the given directory
    for filename in os.listdir(directory):
        if filename.endswith('.bin'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'rb') as f:
                # Read and parse the header
                header_text = ''
                while True:
                    line = f.readline().decode('utf-8')
                    if line.strip() == '':  # End of header
                        break
                    header_text += line
                
                # Extract metadata from the header
                header = {}
                for line in header_text.splitlines():
                    if ':' in line:
                        key, value = line.split(':', 1)
                        header[key.strip()] = float(value.strip())
                
                # Extract channel name from filename
                channel_name = filename.split('_')[-1].replace('.bin', '')
                
                # Read the binary data as int16
                data = np.fromfile(f, dtype=np.int16)
                
                # Store the header and data for the channel
                headers[channel_name] = header
                data_chunk[channel_name] = data
    
    return headers, data_chunk



if __name__ == '__main__':
    header, data = read_recorded_data('./data/20250227_132729')
    
    scale = header['A']['Scale']
    _data = data['A']
    dt = np.round(float(header['A']['Time Interval']), 6)
    
    x = np.arange(0, len(_data))*dt
    plt.plot(x*1e6, _data*scale/32767)

    plt.show()
