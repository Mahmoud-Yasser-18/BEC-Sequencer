import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout, QPushButton, QScrollArea

class EventTimeline(QMainWindow):
    def __init__(self, events, time_range):
        super().__init__()
        self.events = events
        self.time_range = time_range
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Event Timeline with Horizontal Scrolling')
        self.setGeometry(100, 100, 800, 200)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        # Create the scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Container widget for the scroll area
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)

        # Calculate the length of the horizontal widget and the scaling factor
        widget_width = 3000  # Arbitrary large width for demonstration
        scaling_factor = widget_width / self.time_range
        print(scaling_factor)

        # Create the main layout for events
        timeline_layout = QGridLayout()
        container_layout.addLayout(timeline_layout)

        current_position = 0

        # Create the event buttons layout
        for event in self.events:
            start_time, duration = event
            start_position = int(start_time * scaling_factor)
            duration_length = int(duration * scaling_factor)

            # Add empty button for the gap
            if start_position > current_position:
                gap_length = start_position - current_position
                empty_button = QPushButton('')
                empty_button.setFixedWidth(gap_length)
                empty_button.setEnabled(False)
                timeline_layout.addWidget(empty_button, 0, current_position, 1, gap_length)

            # Add event button
            event_button = QPushButton(f'Event {start_time}-{start_time + duration}')
            event_button.setFixedWidth(duration_length)
            event_button.setToolTip(f'Starts at {start_time} units, Duration: {duration} units')
            timeline_layout.addWidget(event_button, 0, start_position, 1, duration_length)

            # Update current position
            current_position = start_position + duration_length

        # Add empty button for the remaining time
        if current_position < widget_width:
            empty_button = QPushButton('')
            empty_button.setFixedWidth(widget_width - current_position)
            empty_button.setEnabled(False)
            timeline_layout.addWidget(empty_button, 0, current_position, 1, widget_width - current_position)

        scroll_area.setWidget(container_widget)
        main_layout.addWidget(scroll_area)
        self.setCentralWidget(main_widget)

def main():
    events = [(2.5, 1.5), (5.2, 2.1), (8.3, 1.2), (10.1, 3.0), (14.4, 2.5)]  # Example events with (start_time, duration) in units
    time_range = 20.0  # Total time range in the specified unit

    app = QApplication(sys.argv)
    timeline = EventTimeline(events, time_range)
    timeline.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

