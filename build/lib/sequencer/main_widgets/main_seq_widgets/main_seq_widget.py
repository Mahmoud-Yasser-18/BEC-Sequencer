from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QWidget,  QLabel,
                             QScrollArea, QAction, QVBoxLayout, QHBoxLayout, 
                             QFileDialog, QFormLayout, QDialog, QComboBox, 
                             QLineEdit, QDialogButtonBox, QMenu)
from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QIcon
import gc
from sequencer.event import Sequence, Analog_Channel, Digital_Channel, Event, Jump, Ramp, RampType,EventBehavior
from sequencer.Dialogs.event_dialog import ChildEventDialog, RootEventDialog
from sequencer.Dialogs.channel_dialog import ChannelDialog
# from sequencer import Dialogs.event_dialog.ChannelDialog



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
        dialog = ChildEventDialog( [ch.name for ch in self.sequence.channels])
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            behavior = Jump(1)
            print(type(data["relative_time"]))
            child_event = self.sequence.add_event(
                channel_name=data['channel'],
                behavior=behavior,
                relative_time=float(data["relative_time"]),
                reference_time=data["reference_time"],
                parent_event=self.event
            )
            print(self.find_parents()[0])
            self.find_parents()[0].parent().refreshUI()
    def find_parents(self):
        return gc.get_referrers(self)

    def delete_event(self):
        self.sequence.delete_event(self.event.start_time,self.event.channel.name)
        print(self.find_parents()[0])
        self.find_parents()[0].parent().refreshUI()

class ChannelLabelWidget(QWidget):
    def __init__(self, channels, parent=None):
        super().__init__(parent)
        self.channels = channels
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        label = QLabel(" ", self)
        label.setFixedHeight(50)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        for channel in self.channels:
            label = QLabel(channel.name, self)
            label.setFixedHeight(50)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
        self.setFixedSize(100, len(self.channels) * 100)
        self.setLayout(layout)
        


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

        self.setFixedSize(500,500)

        self.scroll_area = QScrollArea(self)
        # self.scroll_area.setWidgetResizable(True)
        
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        self.h_layout = QHBoxLayout()
        self.main_layout.addWidget(self.scroll_area)

    def load_json(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Load JSON File", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_name:
            self.sequence = Sequence.from_json(file_name)
            self.refreshUI()
    
    def refreshUI(self):
        if self.sequence:
            for i in reversed(range(self.h_layout.count())):
                widget_to_remove = self.h_layout.itemAt(i).widget()
                self.h_layout.removeWidget(widget_to_remove)
                widget_to_remove.setParent(None)
            
            label_widget = ChannelLabelWidget(self.sequence.channels, self)
            self.h_layout.addWidget(label_widget)
            
            viewer_widget = Events_Viewer_Widget(self.sequence, self.scale_factor, self)
            self.h_layout.addWidget(viewer_widget)
            
            container = QWidget()
            container.setLayout(self.h_layout)
            self.scroll_area.setWidget(container)




class Rampagedwell(QMainWindow):
    def __init__(self, scale_factor=50):
        super().__init__()
        self.scale_factor = scale_factor
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Main Window')
        self.setGeometry(0,0, 800, 800)
        self.Events_Scroller_widget = Events_Scroller(self.scale_factor)
        self.setCentralWidget(self.Events_Scroller_widget)

class Rampagedwell(QMainWindow):
    def __init__(self, scale_factor=50):
        super().__init__()
        self.scale_factor = scale_factor
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Main Window')
        self.setGeometry(0,0, 400,400)
        self.Events_Scroller_widget = Events_Scroller(self.scale_factor)
        self.setCentralWidget(self.Events_Scroller_widget)
        
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
        self.Events_Scroller_widget.load_json()
    
    def set_scale_factor(self):
        dialog = ScaleFactorDialog(self.scale_factor, self)
        if dialog.exec_() == QDialog.Accepted:
            self.scale_factor = dialog.get_scale_factor()
            self.Events_Scroller_widget.scale_factor = self.scale_factor
            self.Events_Scroller_widget.refreshUI()

if __name__ == '__main__':
    scale_factor = 50
    app = QApplication([])
    window = Rampagedwell()
    window.show()
    app.exec_()
