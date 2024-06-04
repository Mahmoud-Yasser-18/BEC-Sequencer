from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QWidget, 
                             QScrollArea, QAction, QVBoxLayout, QHBoxLayout, 
                             QFileDialog, QFormLayout, QDialog, QComboBox, 
                             QLineEdit, QDialogButtonBox, QMenu)
from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QIcon
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

class AddEventDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Child Event")
        self.layout = QFormLayout(self)
        
        self.behavior_type = QComboBox(self)
        self.behavior_type.addItems(["Jump", "Ramp"])
        self.layout.addRow("Behavior Type:", self.behavior_type)
        
        self.duration = QLineEdit(self)
        self.layout.addRow("Duration (for Ramp):", self.duration)
        
        self.relative_time = QLineEdit(self)
        self.layout.addRow("Relative Time:", self.relative_time)
        
        self.reference_time = QLineEdit(self)
        self.layout.addRow("Reference Time:", self.reference_time)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
    
    def get_data(self):
        return {
            "behavior_type": self.behavior_type.currentText(),
            "duration": float(self.duration.text()) if self.duration.text() else None,
            "relative_time": float(self.relative_time.text()) if self.relative_time.text() else None,
            "reference_time": self.reference_time.text()
        }

class EventButton(QPushButton):
    def __init__(self, event, scale_factor, sequence, parent=None):
        super().__init__(parent)
        self.event = event
        self.scale_factor = scale_factor
        self.sequence = sequence
        self.initUI()
    
    def initUI(self):
        if isinstance(self.event.behavior, Ramp):
            duration = self.event.behavior.duration
            self.setGeometry(int(self.event.start_time * self.scale_factor), 0, int(duration * self.scale_factor), 50)
            self.setText(str(self.event.start_time))
        elif isinstance(self.event.behavior, Jump):
            self.setGeometry(int(self.event.start_time * self.scale_factor), 0, 10, 50)
            self.setText('J')
        else:
            self.setGeometry(int(self.event.start_time * self.scale_factor), 0, 50, 50)
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def show_context_menu(self, pos):
        context_menu = QMenu(self)
        add_child_action = context_menu.addAction("Add Child Event")
        delete_action = context_menu.addAction("Delete Event")
        
        action = context_menu.exec_(self.mapToGlobal(pos))
        if action == add_child_action:
            self.add_child_event()
        elif action == delete_action:
            self.delete_event()
    
    def add_child_event(self):
        dialog = AddEventDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            behavior = Jump(1)
            print(data)
            child_event = self.sequence.add_event(
                channel_name=self.event.channel.name,
                behavior=behavior,
                relative_time=data["relative_time"],
                reference_time=data["reference_time"],
                parent_event=self.event
            )
            self.parent().parent().refreshUI()

    def delete_event(self):
        self.sequence.delete_event(self.event.start_time,self.event.channel.name)
        self.parent().parent().refreshUI()



class Events_Viewer_Widget(QWidget):
    def __init__(self, sequence, scale_factor=100, parent=None):
        super().__init__(parent)
        self.sequence = sequence
        self.scale_factor = scale_factor
        self.initUI()

    def initUI(self):
        self.setLayout(QVBoxLayout())  
        self.refreshUI()

    def refreshUI(self):
        layout = self.layout()
        for i in reversed(range(layout.count())):
            widget_to_remove = layout.itemAt(i).widget()
            layout.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)
        
        all_events = self.sequence.all_events
        max_time = max(
            (event.start_time + (event.behavior.duration if isinstance(event.behavior, Ramp) else 0)) 
            for event in all_events
        )
        
        num_channels = len(self.sequence.channels)
        self.setFixedSize(int(max_time * self.scale_factor) + 50, num_channels * 100)
        time_axis = TimeAxisWidget(max_time, self.scale_factor, self)
        layout.addWidget(time_axis)
        
        for i, channel in enumerate(self.sequence.channels):
            buttons_container = QWidget(self)
            buttons_container.setFixedHeight(50)
            previous_end_time = 0.0
            for event in channel.events:
                start_time = event.start_time
                if start_time > previous_end_time:
                    gap_duration = start_time - previous_end_time
                    gap_button = QPushButton('gap', buttons_container)
                    gap_button.setGeometry(int(previous_end_time * self.scale_factor), 0, int(gap_duration * self.scale_factor), 50)
                    gap_button.setEnabled(False)
                button = EventButton(event, self.scale_factor, self.sequence, buttons_container)
                previous_end_time = start_time + (event.behavior.duration if isinstance(event.behavior, Ramp) else 10/self.scale_factor)
            
            layout.addWidget(buttons_container)
        self.setLayout(layout)



class Events_Scroller(QWidget):
    def __init__(self, scale_factor=10):
        super().__init__()
        self.sequence = None
        self.initUI(scale_factor)
    
    def initUI(self, scale_factor):
        self.scale_factor = scale_factor
        self.setWindowTitle('Events Scroller')
        self.setGeometry(500, 500, 500,500)
        
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        
        layout = QHBoxLayout()

        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)

class ScaleFactorDialog(QDialog):
    def __init__(self, current_scale_factor, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Set Scale Factor')
        self.layout = QFormLayout(self)
        
        self.scale_factor_edit = QLineEdit(self)
        self.scale_factor_edit.setText(str(current_scale_factor))
        self.layout.addRow('Scale Factor:', self.scale_factor_edit)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
    
    def get_scale_factor(self):
        return int(self.scale_factor_edit.text())

class Rampagedwell(QMainWindow):
    def __init__(self, scale_factor=10):
        super().__init__()
        self.scale_factor = scale_factor
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Main Window')
        self.setGeometry(800, 800, 800, 800)
        self.custom_widget = Events_Scroller(self.scale_factor)
        self.setCentralWidget(self.custom_widget)
        
        # Create the menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        
        # Add Load JSON action
        load_action = QAction('Load JSON', self)
        load_action.triggered.connect(self.load_json)
        file_menu.addAction(load_action)

        # Add Set Scale Factor action
        scale_factor_action = QAction('Set Scale Factor', self)
        scale_factor_action.triggered.connect(self.set_scale_factor)
        file_menu.addAction(scale_factor_action)
    
    def load_json(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load JSON File", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            self.custom_widget.sequence = Sequence.from_json(file_name)
            custom_widget = Events_Viewer_Widget(self.custom_widget.sequence, self.scale_factor, self)
            self.custom_widget.scroll_area.setWidget(custom_widget)
    
    def set_scale_factor(self):
        dialog = ScaleFactorDialog(self.scale_factor, self)
        if dialog.exec_() == QDialog.Accepted:
            self.scale_factor = dialog.get_scale_factor()
            if self.custom_widget.sequence:
                custom_widget = Events_Viewer_Widget(self.custom_widget.sequence, self.scale_factor, self)
                self.custom_widget.scroll_area.setWidget(custom_widget)

if __name__ == '__main__':
    scale_factor = 50
    app = QApplication([])
    window = Rampagedwell()
    window.show()
    app.exec_()
