from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QScrollArea, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QPainter, QPen

class TimeAxisWidget(QWidget):
    def __init__(self, max_time, scale_factor=10, parent=None):
        super().__init__(parent)
        self.max_time = max_time
        self.scale_factor = scale_factor
        self.initUI()
    
    def initUI(self):
        self.setFixedSize(int(self.max_time * self.scale_factor) + 50, 50)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)
        
        # Draw the main line
        painter.drawLine(0, 25, self.width(), 25)
        
        # Draw ticks and labels
        for time in range(int(self.max_time) + 1):
            x = int(time * self.scale_factor)
            painter.drawLine(x, 20, x, 30)  # Tick
            painter.drawText(QRect(x - 10, 30, 20, 20), Qt.AlignCenter, str(time))  # Label

class CustomWidget(QWidget):
    def __init__(self, events, scale_factor=10, parent=None):
        super().__init__(parent)
        self.events = events
        self.scale_factor = scale_factor
        self.initUI()
    
    def initUI(self):
        # Calculate total width based on events
        max_time = max(event['start_time'] + event['duration'] for event in self.events)
        self.setFixedSize(int(max_time * self.scale_factor) + 50, 200)
        
        # Create a layout for the time axis and event buttons
        layout = QVBoxLayout(self)
        
        # Create the time axis
        time_axis = TimeAxisWidget(max_time, self.scale_factor, self)
        layout.addWidget(time_axis)
        
        # Create a container widget for buttons
        buttons_container = QWidget(self)
        buttons_container.setFixedHeight(50)
        buttons_layout = QVBoxLayout(buttons_container)
        
        # Create buttons for each event, including gaps
        previous_end_time = 0.0
        for event in self.events:
            start_time = event['start_time']
            duration = event['duration']
            
            # Create a gap button if there is a gap between previous event end time and current event start time
            if start_time > previous_end_time:
                gap_duration = start_time - previous_end_time
                gap_button = QPushButton('', buttons_container)
                gap_button.setGeometry(int(previous_end_time * self.scale_factor), 0, int(gap_duration * self.scale_factor), 50)
                gap_button.setEnabled(False)  # Disable the gap button
            
            # Create the event button
            button = QPushButton(event['name'], buttons_container)
            button.setGeometry(int(start_time * self.scale_factor), 0, int(duration * self.scale_factor), 50)
            
            previous_end_time = start_time + duration
        
        layout.addWidget(buttons_container)
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self, events, scale_factor=10):
        super().__init__()
        
        # Set fixed size for the main window
        self.setFixedSize(400, 200)
        
        # Create a scroll area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        
        # Create a custom widget with events
        custom_widget = CustomWidget(events, scale_factor, self)
        
        # Set the custom widget as the widget for the scroll area
        scroll_area.setWidget(custom_widget)
        
        # Set the scroll area as the central widget
        self.setCentralWidget(scroll_area)

# Define events with start time and duration (start time and duration can be floats)
events = [
    {'name': 'Event 1', 'start_time': 1.5, 'duration': 5.2},
    {'name': 'Event 2', 'start_time': 8.0, 'duration': 3.5},
    {'name': 'Event 3', 'start_time': 12.7, 'duration': 4.0},
]

# Run the application
if __name__ == '__main__':
    scale_factor = 50  # This can be adjusted as needed
    app = QApplication([])
    window = MainWindow(events, scale_factor)
    window.show()
    app.exec_()
