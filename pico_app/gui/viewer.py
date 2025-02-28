import os
import sys
from PyQt5 import QtWidgets, uic
import re
import pyqtgraph as pg
from datetime import datetime
import numpy as np
pg.setConfigOptions(antialias=True)

COLORS = ['#d9f175', '#1abc9c','#e67e22', '#3498db', '#9b59b6', '#e74c3c', '#f1c40f', '#2ecc71',  ]
NAMES = [f"{chr(65+i)}" for i in range(8)]

def list_folders_by_date(directory):
    """ Function to list folders by date and time in the given directory. 
    How it works:
    - Extracts date and time from the folder name
    - Creates a dictionary with date as key and list of times as value
    - Returns the dictionary
    """
    date_dict = {}
    pattern = re.compile(r"(\d{8})_(\d{6})")  # Pattern to extract date and time from folder name

    for root, dirs, files in os.walk(directory):
        for folder in dirs:
            folder_path = os.path.join(root, folder)
            if any(file.endswith('.bin') for file in os.listdir(folder_path)):
                match = pattern.match(folder)
                if not match: continue
                date_str, time_str = match.groups()
                date_formatted = f"{date_str[2:4]}-{date_str[4:6]}-{date_str[6:8]}"
                time_formatted = f"{time_str[0:2]}:{time_str[2:4]}:{time_str[4:6]}"
                
                if date_formatted not in date_dict:
                    date_dict[date_formatted] = []
                date_dict[date_formatted].append((time_formatted, folder_path))

    return date_dict

class PicoViewer(QtWidgets.QWidget):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(os.path.join(os.path.dirname(__file__), "gui", "viewer_widget.ui"), self) 
        
        # graph: pg.PlotWidget = self.graph
        self.graph.getAxis('bottom').setLabel(text='Time', units='s')
        self.graph.getAxis('left').setLabel(text='Voltage', units='V')
        self.graph.showGrid(x = True, y = True, alpha = 0.5)
        self.graph.addLegend()

        self.define_actions()
        
        # TODO not solid
        self.directory = self.directory_label.text()

        self.create_measurements_tree()

        self.show()

    def define_actions(self):
        self.is_live_btn.clicked.connect(self.is_live_mode)
        self.plot_btn.clicked.connect(self.display_data)
        self.save_note_btn.clicked.connect(self.save_note)
        self.refresh_btn.clicked.connect(self.create_measurements_tree)
        for ch in NAMES:
            check_btn: QtWidgets.QCheckBox = getattr(self, f"channel_{ch}")
            check_btn.stateChanged.connect(self.change_active_channels)
        self.change_dir_btn.clicked.connect(self.change_directory)
        self.notes.textChanged.connect(self.note_changed)
        self.delete_btn.clicked.connect(self.delete_data)

    def init_user_interface(self):
        self.graph.clear()
        self.notes.setEnabled(False)
        self.save_note_btn.setEnabled(False)
        if hasattr(self, 'selected_item'):
            self.selected_item.setBackground(0, pg.mkColor('w'))

    def read_recorded_data(self):
        """
        Reads the recorded data from multiple binary files in the current directory.
        Returns a dictionary containing headers and data for each channel.
        """
        if not self.data_folder: return None
        
        directory = self.data_folder

        data_chunk = {}
        headers = {}
        
        # Iterate over all binary files in the given directory
        for filename in os.listdir(directory):
            if not filename.endswith('.bin'): continue
            
            filepath = os.path.join(directory, filename)

            with open(filepath, 'rb') as f:
                # Read and parse the header
                header_text = ''
                while True:
                    line = f.readline().decode('utf-8')
                    if line.strip() == '': break # End of header
                    header_text += line
                
                # Extract metadata from the header
                header = {}
                for line in header_text.splitlines():
                    if ':' in line:
                        key, value = line.split(':', 1)
                        header[key.strip()] = float(value.split()[0].strip())
                
                # Extract channel name from filename
                channel_name = filename.split('_')[-1].replace('.bin', '')
                
                # Read the binary data as int16
                data = np.fromfile(f, dtype=np.int16)
                
                # Store the header and data for the channel
                headers[channel_name] = header
                data_chunk[channel_name] = data
        
        return headers, data_chunk
  
    def create_measurements_tree(self):
        if hasattr(self, 'selected_item'):
            del self.selected_item

        self.init_user_interface()
        
        tree: QtWidgets.QTreeWidget = self.measurements_tree

        tree.clear()

        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath(self.directory)

        tree.setHeaderHidden(True)
        tree.setDragEnabled(False)
    
        # Root node
        root_item = pg.TreeWidgetItem(["Measurements"])
        tree.addTopLevelItem(root_item)

        # Get folders organized by date
        folders_by_date = list_folders_by_date(self.directory)

        # Add date nodes and corresponding times to the tree view (reverse sorted)
        for date in sorted(folders_by_date.keys(), reverse=True):
            date_item = pg.TreeWidgetItem([date])
            root_item.addChild(date_item)
            
            # Reverse sort times as well
            for time, _ in sorted(folders_by_date[date]):
                time_item = pg.TreeWidgetItem([time])
                date_item.addChild(time_item)

    
        tree.expandAll()

    def delete_data(self):

        try: 
            item = self.measurements_tree.currentItem()
            time_str = item.text(0)
            date_str = item.parent().text(0)
            date_time_obj = datetime.strptime(f"{date_str} {time_str}", '%y-%m-%d %H:%M:%S')
            folder_name = date_time_obj.strftime('%Y%m%d_%H%M%S')
            data_folder = os.path.join(self.directory, folder_name)
        
            if QtWidgets.QMessageBox.question(self, 'Delete Data', f'Are you sure you want to delete this data? {data_folder}', 
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
                for file in os.listdir(data_folder):
                    os.remove(os.path.join(data_folder, file))
                os.rmdir(data_folder)
                self.create_measurements_tree()
                self.init_user_interface()
        
        except Exception as e:
            return

    def display_data(self):
        
        # Get the selected folder path
        try: 
            item = self.measurements_tree.currentItem()
            time_str = item.text(0)
            date_str = item.parent().text(0)
            date_time_obj = datetime.strptime(f"{date_str} {time_str}", '%y-%m-%d %H:%M:%S')
            folder_name = date_time_obj.strftime('%Y%m%d_%H%M%S')
            self.data_folder = os.path.join(self.directory, folder_name)
        except Exception as e:
            # self.data_folder = None
            return

        self.init_user_interface()


        # Highlight the selected item
        self.selected_item: QtWidgets.QTreeWidgetItem = item
        self.selected_item.setBackground(0, pg.mkColor(COLORS[0]))

        self.notes.setEnabled(True)
        # self.save_note_btn.setEnabled(True)

        # Extract headers and data from the recorded data
        headers, data = self.read_recorded_data()
        
        # Update UI with the loaded data
        for ch in NAMES:
            channel_btn = getattr(self, f"channel_{ch}")
            channel_btn.blockSignals(True)
            channel_btn.setChecked(channel_btn.text() in headers.keys())
            channel_btn.setEnabled(channel_btn.text() in headers.keys())
            channel_btn.blockSignals(False)

        # Plot the data
        self.plots = {}
        for i, ch in enumerate(headers.keys()):
            scale = headers[ch]['Scale']
            _data = data[ch] + headers[ch]['Offset']
            dt = np.round(float(headers[ch]['Time Interval']), 6)
            self.plots[ch] = self.graph.plot(
                x=np.arange(0, len(_data))*dt, 
                y=_data*scale/32767, 
                pen=pg.mkPen(COLORS[NAMES.index(ch)]), 
                name=ch)

        # Show the user notes
        if "notes.txt" in os.listdir(self.data_folder):
            with open(os.path.join(self.data_folder, 'notes.txt'), 'r') as f:
                self.notes.setPlainText(f.read())
        else:
            self.notes.setPlainText("")

    @property
    def notes_from_file(self) -> str:
        if not "notes.txt" in os.listdir(self.data_folder):
            return 
        with open(os.path.join(self.data_folder, 'notes.txt'), 'r') as f:
            return f.read()

    def save_note(self):
        """ Save the notes to a text file in the data folder. 
        If the notes are empty, the file is deleted. """
        if not self.data_folder: return
        
        notes = self.notes.toPlainText()
        if notes:
            with open(os.path.join(self.data_folder, 'notes.txt'), 'w') as f:
                f.write(notes)
        else:
            if "notes.txt" in os.listdir(self.data_folder):
                os.remove(os.path.join(self.data_folder, 'notes.txt'))
        
        self.save_note_btn.setEnabled(False)
        
    def change_active_channels(self):
        """ Show/hide the selected channels on the graph. """
        if not hasattr(self, 'plots'): return
        for ch, plot in self.plots.items():
            if getattr(self, f"channel_{ch}").isChecked():
                plot.show()
            else:
                plot.hide()

    def change_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.directory = directory
            self.directory_label.setText(directory)
            self.create_measurements_tree()

    def is_live_mode(self):
        state = self.is_live_btn.isChecked()
        self.measurements_tree.setEnabled(not state)
        self.plot_btn.setEnabled(not state)
        self.save_note_btn.setEnabled(not state)
        self.notes.setEnabled(not state)

    def note_changed(self):
        if self.notes_from_file != self.notes.toPlainText():
            self.save_note_btn.setEnabled(True)
        else:
            self.save_note_btn.setEnabled(False)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = PicoViewer()
    window.setWindowTitle("PicoViewer")
    sys.exit(app.exec_())
