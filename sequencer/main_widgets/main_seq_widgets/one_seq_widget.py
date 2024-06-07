# Filename: synced_table_widget.py

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,QMenu,  QDialog,QHBoxLayout, QPushButton,QTableWidget, QTableWidgetItem, QListWidget, QScrollBar, QSizePolicy,QLabel)

from PyQt5.QtCore import Qt, QRect, pyqtSignal

from PyQt5.QtGui import QPainter, QPen, QIcon

from sequencer.Dialogs.event_dialog import ChildEventDialog
from sequencer.event import Ramp, Jump, Sequence


from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt5.QtCore import Qt

class ChannelLabelWidget(QWidget):
    def __init__(self, channels, parent=None):
        super().__init__(parent)
        self.channels = channels
        self.initUI()

    def initUI(self):
        # Create the main layout for this widget
        main_layout = QVBoxLayout(self)
        
        # Create a QScrollArea
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        
        # Create a container widget and its layout
        container_widget = QWidget()
        layout = QVBoxLayout(container_widget)
        
        # Add a top spacer label
        spacer_label = QLabel(" ", self)
        spacer_label.setFixedHeight(50)
        spacer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(spacer_label)
        
        # Add channel labels
        for channel in self.channels:
            label = QLabel(channel, self)
            label.setFixedHeight(50)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
        
        # Set the layout for the container widget
        container_widget.setLayout(layout)
        container_widget.setFixedSize(100, len(self.channels) * 100)
        
        # Set the container widget as the scroll area's widget
        self.scroll_area.setWidget(container_widget)
        self.scroll_area.setFixedSize(150, len(self.channels) * 100)
        # Add the scroll area to the main layout
        main_layout.addWidget(self.scroll_area)
        

        # Set the main layout for this widget
        self.setLayout(main_layout)



# class ChannelListWidget(QListWidget):
#     def __init__(self, channels):
#         super().__init__()
#         self.channels = channels
#         self.setup_ui()

#     def setup_ui(self):
#         for channel in self.channels:
#             self.addItem(channel)

#         longest_channel_name = max(self.channels, key=len)
#         font_metrics = self.fontMetrics()
#         channel_width = font_metrics.horizontalAdvance(longest_channel_name) + 50  # Adding some padding
#         self.setFixedWidth(channel_width)
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

            child_event = self.sequence.add_event(
                channel_name=data['channel'],
                behavior=behavior,
                relative_time=float(data["relative_time"]),
                reference_time=data["reference_time"],
                parent_event=self.event
            )
            print(type(self.parent().parent()))
            self.parent().parent().refreshUI()

    def delete_event(self):
        self.sequence.delete_event(self.event.start_time,self.event.channel.name)
        self.parent().parent().refreshUI()
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


from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QPushButton
from PyQt5.QtCore import Qt

class Events_Viewer_Widget(QWidget):
    def __init__(self, sequence, scale_factor=100, parent=None):
        super().__init__(parent)
        self.sequence = sequence
        self.scale_factor = scale_factor
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        
        # Create a scroll area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        
        # Create a container widget and its layout
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        
        # Initial setup
        self.refreshUI(container_layout)
        
        # Set the layout for the container widget
        container_widget.setLayout(container_layout)
        
        # Set the container widget as the scroll area's widget
        self.scroll_area.setWidget(container_widget)
        
        # Add the scroll area to the main layout
        main_layout.addWidget(self.scroll_area)
        
        # Set the main layout for this widget
        self.setLayout(main_layout)

    def refreshUI(self, layout):
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




class SyncedTableWidget(QWidget):
    def __init__(self, channels, data):
        super().__init__()
        self.sequence = Sequence.from_json("sequencer/seq_data.json")
        self.channel_list = ChannelLabelWidget([ch.name for ch in self.sequence.channels])
        self.data_table   = Events_Viewer_Widget(self.sequence, scale_factor=100)

        self.channel_list.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.data_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.scroll_bar1 = self.channel_list.scroll_area.verticalScrollBar()
        self.scroll_bar2 = self.data_table.scroll_area.verticalScrollBar()
        self.scroll_bar1.valueChanged.connect(self.sync_scroll)
        self.scroll_bar2.valueChanged.connect(self.sync_scroll)

        layout = QHBoxLayout()
        layout.addWidget(self.channel_list)
        layout.addWidget(self.data_table)
        self.setLayout(layout)

    def sync_scroll(self, value):
        sender = self.sender()
        if sender == self.scroll_bar1:
            proportion = value / self.scroll_bar1.maximum() if self.scroll_bar1.maximum() != 0 else 0
            self.scroll_bar2.setValue(int(proportion * self.scroll_bar2.maximum()))
        else:
            proportion = value / self.scroll_bar2.maximum() if self.scroll_bar2.maximum() != 0 else 0
            self.scroll_bar1.setValue(int(proportion * self.scroll_bar1.maximum()))
    def refreshUI(self):
        if self.sequence:
            for i in reversed(range(self.h_layout.count())):
                widget_to_remove = self.h_layout.itemAt(i).widget()
                self.h_layout.removeWidget(widget_to_remove)
                widget_to_remove.setParent(None)

            label_widget= ChannelLabelWidget([ch.name for ch in self.sequence.channels],self)
            self.h_layout.addWidget(label_widget)
            
            viewer_widget = Events_Viewer_Widget(self.sequence, self.scale_factor, self)
            self.h_layout.addWidget(viewer_widget)
            
            container = QWidget()
            container.setLayout(self.h_layout)
            self.scroll_area.setWidget(container)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    channels = [f'Channel {i}' for i in range(20)]
    data = [[j for j in range(100)] for i in range(20)]

    window = SyncedTableWidget(channels, data)
    window.show()
    sys.exit(app.exec_())
