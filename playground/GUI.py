import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QVBoxLayout, QHBoxLayout, 
                             QWidget, QMenu, QAction, QDialog, QFormLayout, QLabel,
                             QDoubleSpinBox, QDialogButtonBox, QComboBox, QMenuBar, QLineEdit, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from event import Sequence, Analog_Channel, Digital_Channel, Event, Jump, Ramp, RampType
import matplotlib.pyplot as plt


class EventWidget(QWidget):
    def __init__(self, event, total_duration, parent=None):
        super().__init__(parent)
        self.event = event
        self.total_duration = total_duration
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)
        self.behavior_label = QLabel(f"Behavior: {self.event.behavior.__class__.__name__}", self)
        self.start_time_label = QLabel(f"Start Time: {self.event.start_time}", self)
        self.end_time_label = QLabel(f"End Time: {self.event.end_time}", self)
        self.layout.addWidget(self.behavior_label)
        self.layout.addWidget(self.start_time_label)
        self.layout.addWidget(self.end_time_label)
        self.setLayout(self.layout)
        self.adjust_size()

    def adjust_size(self):
        duration = self.event.end_time - self.event.start_time
        total_width = self.parent().width()
        self.setFixedWidth(int(total_width * (duration / self.total_duration)))


class EmptyWidget(QWidget):
    def __init__(self, duration, total_duration, parent=None):
        super().__init__(parent)
        self.duration = duration
        self.total_duration = total_duration
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)
        self.label = QLabel("No Event", self)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.adjust_size()

    def adjust_size(self):
        total_width = self.parent().width()
        self.setFixedWidth(int(total_width * (self.duration / self.total_duration)))


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


class EventDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Add Event')
        self.layout = QFormLayout(self)

        self.channel_combo = QComboBox(self)
        self.channel_combo.addItems(parent.get_channel_names())

        self.behavior_combo = QComboBox(self)
        self.behavior_combo.addItems(['Jump', 'Ramp'])
        self.behavior_combo.currentIndexChanged.connect(self.update_form)

        self.start_time_edit = QLineEdit(self)
        self.relative_time_edit = QLineEdit(self)
        self.reference_time_combo = QComboBox(self)
        self.reference_time_combo.addItems(['start', 'end'])

        self.target_value_edit = QLineEdit(self)
        self.duration_edit = QLineEdit(self)
        self.start_value_edit = QLineEdit(self)
        self.end_value_edit = QLineEdit(self)
        self.ramp_type_combo = QComboBox(self)
        self.ramp_type_combo.addItems([rt.value for rt in RampType])

        self.layout.addRow('Channel:', self.channel_combo)
        self.layout.addRow('Behavior:', self.behavior_combo)
        self.layout.addRow('Start Time:', self.start_time_edit)
        self.layout.addRow('Relative Time:', self.relative_time_edit)
        self.layout.addRow('Reference Time:', self.reference_time_combo)
        self.layout.addRow('Target Value:', self.target_value_edit)
        self.layout.addRow('Duration:', self.duration_edit)
        self.layout.addRow('Start Value:', self.start_value_edit)
        self.layout.addRow('End Value:', self.end_value_edit)
        self.layout.addRow('Ramp Type:', self.ramp_type_combo)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
        self.update_form(self.behavior_combo.currentIndex())

    def update_form(self, index):
        if index == 0:  # Jump
            self.target_value_edit.show()
            self.duration_edit.hide()
            self.start_value_edit.hide()
            self.end_value_edit.hide()
            self.ramp_type_combo.hide()
        elif index == 1:  # Ramp
            self.target_value_edit.hide()
            self.duration_edit.show()
            self.start_value_edit.show()
            self.end_value_edit.show()
            self.ramp_type_combo.show()

    def get_data(self):
        data = {
            'channel': self.channel_combo.currentText(),
            'behavior': self.behavior_combo.currentText(),
            'start_time': float(self.start_time_edit.text()) if self.start_time_edit.text() else None,
            'relative_time': float(self.relative_time_edit.text()) if self.relative_time_edit.text() else None,
            'reference_time': self.reference_time_combo.currentText(),
            'target_value': float(self.target_value_edit.text()) if self.target_value_edit.isVisible() else None,
            'duration': float(self.duration_edit.text()) if self.duration_edit.isVisible() else None,
            'start_value': float(self.start_value_edit.text()) if self.start_value_edit.isVisible() else None,
            'end_value': float(self.end_value_edit.text()) if self.end_value_edit.isVisible() else None,
            'ramp_type': self.ramp_type_combo.currentText() if self.ramp_type_combo.isVisible() else None
        }
        return data


class SequenceViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sequence = Sequence()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Sequence Viewer')
        self.setGeometry(100, 100, 1000, 600)  # Wider window
        self.setWindowIcon(QIcon('icon.png'))  # Optional: Set your window icon here

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.central_widget.setLayout(self.layout)

        self.create_menu_bar()

        self.statusBar().showMessage('Ready')

        self.update_channels()

    def create_menu_bar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')
        open_file_action = QAction('Open JSON', self)
        open_file_action.triggered.connect(self.load_json)
        file_menu.addAction(open_file_action)

        save_file_action = QAction('Save JSON', self)
        save_file_action.triggered.connect(self.save_json)
        file_menu.addAction(save_file_action)

        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        plot_action = QAction('Plot Events', self)
        plot_action.triggered.connect(self.plot_events)
        tools_menu.addAction(plot_action)

    def load_json(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            self.sequence = Sequence.from_json(file_name=file_name)
            self.update_channels()

    def save_json(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save JSON File", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            self.sequence.to_json(file_name)

    def update_channels(self):
        for i in reversed(range(self.layout.count())): 
            widgetToRemove = self.layout.itemAt(i).widget()
            if widgetToRemove is not None: 
                widgetToRemove.setParent(None)
        
        total_duration = self.get_total_duration()

        for channel in self.sequence.channels:
            self.add_channel_layout(channel, total_duration)

    def add_channel_layout(self, channel, total_duration):
        channel_layout = QVBoxLayout()
        channel_name_label = QLabel(channel.name, self)
        channel_layout.addWidget(channel_name_label)
        events_layout = QHBoxLayout()

        previous_end_time = 0
        events = sorted(channel.events, key=lambda event: event.start_time)
        for event in events:
            if event.start_time > previous_end_time:
                gap_duration = event.start_time - previous_end_time
                events_layout.addWidget(EmptyWidget(gap_duration, total_duration, self))
            events_layout.addWidget(EventWidget(event, total_duration, self))
            previous_end_time = event.end_time

        if previous_end_time < total_duration:
            gap_duration = total_duration - previous_end_time
            events_layout.addWidget(EmptyWidget(gap_duration, total_duration, self))

        channel_layout.addLayout(events_layout)
        self.layout.addLayout(channel_layout)

    def get_total_duration(self):
        all_events = self.sequence.get_all_events()
        if not all_events:
            return 0
        return max(event.end_time for event in all_events)

    def show_context_menu(self, position):
        menu = QMenu()

        add_event_action = QAction("Add Event", self)
        add_event_action.triggered.connect(self.add_event)
        menu.addAction(add_event_action)

        add_channel_action = QAction("Add Channel", self)
        add_channel_action.triggered.connect(self.add_channel)
        menu.addAction(add_channel_action)

        delete_channel_action = QAction("Delete Channel", self)
        delete_channel_action.triggered.connect(self.delete_channel)
        menu.addAction(delete_channel_action)

        menu.exec_(self.mapToGlobal(position))

    def add_channel(self):
        dialog = ChannelDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if data['type'] == 'Analog':
                new_channel = Analog_Channel(
                    name=data['name'],
                    card_number=data['card_number'],
                    channel_number=data['channel_number'],
                    reset_value=data['reset_value'],
                    max_voltage=data['max_voltage'],
                    min_voltage=data['min_voltage']
                )
                self.sequence.channels.append(new_channel)
            elif data['type'] == 'Digital':
                new_channel = Digital_Channel(
                    name=data['name'],
                    card_number=data['card_number'],
                    channel_number=data['channel_number'],
                    reset_value=data['reset_value'],
                    card_id=data['card_id'],
                    bitpos=data['bitpos']
                )
                self.sequence.channels.append(new_channel)
            self.update_channels()

    def delete_channel(self):
        dialog = ChannelDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            channel = self.sequence.find_channel_by_name(data['name'])
            if channel:
                self.sequence.channels.remove(channel)
            self.update_channels()

    def add_event(self):
        dialog = EventDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            channel = self.sequence.find_channel_by_name(data['channel'])
            if not channel:
                return
            if data['behavior'] == 'Jump':
                behavior = Jump(target_value=data['target_value'])
            elif data['behavior'] == 'Ramp':
                behavior = Ramp(duration=data['duration'], ramp_type=RampType(data['ramp_type']), start_value=data['start_value'], end_value=data['end_value'])
            self.sequence.add_event(channel.name, behavior, start_time=data['start_time'], relative_time=data['relative_time'], reference_time=data['reference_time'])
            self.update_channels()

    def plot_events(self):
        self.sequence.plot_with_event_tree()

    def get_channel_names(self):
        return [channel.name for channel in self.sequence.channels]


if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = SequenceViewer()
    viewer.show()
    sys.exit(app.exec_())
