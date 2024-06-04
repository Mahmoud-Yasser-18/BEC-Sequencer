from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QWidget, 
                             QScrollArea, QAction, QVBoxLayout, QHBoxLayout, QFileDialog)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMenu, QAction, QFormLayout, QDialog,
    QComboBox, QLineEdit, QDialogButtonBox, QVBoxLayout, QPushButton, 
    QScrollArea, QWidget, QFileDialog
)

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from event import Sequence, Analog_Channel, Digital_Channel, Event, Jump, Ramp, RampType

class ChannelDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Add Channel')
        self.layout = QFormLayout(self)

        self.type_combo = QComboBox(self)
        self.type_combo.addItems(['Analog', 'Digital'])
        self.type_combo.currentIndexChanged.connect(self.update_form)

        self.name_edit = QLineEdit(self)
        self.card_number_edit = QLineEdit(self)
        self.channel_number_edit = QLineEdit(self)
        self.reset_value_edit = QLineEdit(self)

        self.layout.addRow('Type:', self.type_combo)
        self.layout.addRow('Name:', self.name_edit)
        self.layout.addRow('Card Number:', self.card_number_edit)
        self.layout.addRow('Channel Number:', self.channel_number_edit)
        self.layout.addRow('Reset Value:', self.reset_value_edit)

        # Analog-specific fields
        self.max_voltage_edit = QLineEdit(self)
        self.min_voltage_edit = QLineEdit(self)
        self.layout.addRow('Max Voltage:', self.max_voltage_edit)
        self.layout.addRow('Min Voltage:', self.min_voltage_edit)

        # Digital-specific fields
        self.card_id_edit = QLineEdit(self)
        self.bitpos_edit = QLineEdit(self)
        self.layout.addRow('Card ID:', self.card_id_edit)
        self.layout.addRow('Bit Position:', self.bitpos_edit)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
        self.update_form(self.type_combo.currentIndex())

    def update_form(self, index):
        if index == 0:  # Analog
            self.max_voltage_edit.show()
            self.min_voltage_edit.show()
            self.card_id_edit.hide()
            self.bitpos_edit.hide()
        elif index == 1:  # Digital
            self.max_voltage_edit.hide()
            self.min_voltage_edit.hide()
            self.card_id_edit.show()
            self.bitpos_edit.show()

    def get_data(self):
        data = {
            'type': self.type_combo.currentText(),
            'name': self.name_edit.text(),
            'card_number': int(self.card_number_edit.text()),
            'channel_number': int(self.channel_number_edit.text()),
            'reset_value': float(self.reset_value_edit.text())
        }
        if data['type'] == 'Analog':
            data['max_voltage'] = float(self.max_voltage_edit.text())
            data['min_voltage'] = float(self.min_voltage_edit.text())
        elif data['type'] == 'Digital':
            data['card_id'] = int(self.card_id_edit.text())
            data['bitpos'] = int(self.bitpos_edit.text())
        return data
    

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
        
        painter.drawLine(0, 25, self.width(), 25)
        
        for time in range(int(self.max_time) + 1):
            x = int(time * self.scale_factor)
            painter.drawLine(x, 20, x, 30)
            painter.drawText(QRect(x - 10, 30, 20, 20), Qt.AlignCenter, str(time))


class Events_Viewer_Widget(QWidget):
    def __init__(self, sequence, scale_factor=10, parent=None):
        super().__init__(parent)
        self.sequence = sequence
        self.scale_factor = scale_factor
        self.initUI()

    def initUI(self):
        all_events = self.sequence.all_events
        max_time = max(
            (event.start_time + (event.behavior.duration if isinstance(event.behavior, Ramp) else 0)) 
            for event in all_events
        )
        
        num_channels = len(self.sequence.channels)
        self.setFixedSize(int(max_time * self.scale_factor) + 50, num_channels * 100)
        layout = QVBoxLayout(self)
        time_axis = TimeAxisWidget(max_time, self.scale_factor, self)
        layout.addWidget(time_axis)
        
        for i, channel in enumerate(self.sequence.channels):
            buttons_container = QWidget(self)
            buttons_container.setFixedHeight(50)
            previous_end_time = 0.0
            for event in channel.events:
                start_time = event.start_time
                if isinstance(event.behavior, Ramp):
                    duration = event.behavior.duration
                    if start_time > previous_end_time:
                        gap_duration = start_time - previous_end_time
                        gap_button = QPushButton('gap', buttons_container)
                        gap_button.setGeometry(int(previous_end_time * self.scale_factor), 0, int(gap_duration * self.scale_factor), 50)
                        gap_button.setEnabled(False)
                    button = QPushButton(str(event.start_time), buttons_container)
                    button.setGeometry(int(start_time * self.scale_factor), 0, int(duration * self.scale_factor), 50)
                    previous_end_time = start_time + duration
                elif isinstance(event.behavior, Jump):
                    if start_time > previous_end_time:
                        gap_duration = start_time - previous_end_time
                        gap_button = QPushButton('gap', buttons_container)
                        gap_button.setGeometry(int(previous_end_time * self.scale_factor), 0, int(gap_duration * self.scale_factor), 50)
                        gap_button.setEnabled(False)
                    button = QPushButton('J', buttons_container)
                    button.setGeometry(int(start_time * self.scale_factor), 0, 10, 50)
                    previous_end_time = start_time + 10/self.scale_factor 
            
            layout.addWidget(buttons_container)
        self.setLayout(layout)

        def show_context_menu(self, pos):
            context_menu = QMenu(self)

            edit_behavior_action = QAction('Edit Behavior', self)
            delete_event_action = QAction('Delete Event', self)
            update_relative_time_action = QAction('Update Relative Time', self)
            update_absolute_time_action = QAction('Update Absolute Time', self)
            add_event_in_middle_action = QAction('Add Event in Middle', self)
            add_event_action = QAction('Add Event', self)
            add_channel_action = QAction('Add Channel', self)

            edit_behavior_action.triggered.connect(self.edit_behavior)
            delete_event_action.triggered.connect(self.delete_event)
            update_relative_time_action.triggered.connect(self.update_event_relative_time)
            update_absolute_time_action.triggered.connect(self.update_event_absolute_time)
            add_event_in_middle_action.triggered.connect(self.add_event_in_middle)
            add_event_action.triggered.connect(self.add_event)
            add_channel_action.triggered.connect(self.add_channel)

            context_menu.addAction(edit_behavior_action)
            context_menu.addAction(delete_event_action)
            context_menu.addAction(update_relative_time_action)
            context_menu.addAction(update_absolute_time_action)
            context_menu.addAction(add_event_in_middle_action)
            context_menu.addAction(add_event_action)
            context_menu.addAction(add_channel_action)

            context_menu.exec_(self.mapToGlobal(pos))

        def edit_behavior(self):
            print("Edit Behavior")  # Placeholder for actual functionality

        def delete_event(self):
            print("Delete Event")  # Placeholder for actual functionality

        def update_event_relative_time(self):
            print("Update Relative Time")  # Placeholder for actual functionality

        def update_event_absolute_time(self):
            print("Update Absolute Time")  # Placeholder for actual functionality

        def add_event_in_middle(self):
            print("Add Event in Middle")  # Placeholder for actual functionality

        def add_event(self):
            print("Add Event")  # Placeholder for actual functionality

        def add_channel(self):
            dialog = ChannelDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_data()
                print("Channel Data:", data)  # Placeholder for actual functionality

class Events_Scroller(QMainWindow):
    def __init__(self, scale_factor=10):
        super().__init__()
        self.sequence = None
        self.initUI(scale_factor)
    
    def initUI(self, scale_factor):
        self.scale_factor = scale_factor
        self.setWindowTitle('Events Scroller')
        self.setGeometry(100, 100, 800, 600)
        
        load_button = QPushButton('Load JSON', self)
        load_button.clicked.connect(self.load_json)
        
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        
        layout = QVBoxLayout()
        layout.addWidget(load_button)
        layout.addWidget(self.scroll_area)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_json(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load JSON File", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            self.sequence = Sequence.from_json(file_name)
            custom_widget = Events_Viewer_Widget(self.sequence, self.scale_factor, self)
            self.scroll_area.setWidget(custom_widget)


if __name__ == '__main__':
    scale_factor = 50
    app = QApplication([])
    window = Events_Scroller(scale_factor)
    window.show()
    app.exec_()
