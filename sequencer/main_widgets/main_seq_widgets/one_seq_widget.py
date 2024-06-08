# Filename: synced_table_widget.py

import sys
from typing import List, Optional
from PyQt5.QtWidgets import (
    QApplication, QHBoxLayout, QSizePolicy, QDialog,QLabel,QMenu, QPushButton, QWidget, QVBoxLayout, QScrollArea, QScrollBar
)
from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QPen

from PyQt5.QtCore import Qt, QRect, pyqtSignal, QPoint


from sequencer.Dialogs.channel_dialog import ChannelDialog
from sequencer.Dialogs.event_dialog import ChildEventDialog
from sequencer.event import Ramp, Jump, Sequence



class ChannelLabelWidget(QWidget):
    channel_right_clicked = pyqtSignal(QPoint)

    def __init__(self, sequence, parent=None):
        super().__init__(parent)
        self.sequence = sequence
        self.channels = [ch.name for ch in self.sequence.channels]
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        self.scroll_area = self.create_scroll_area()
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)

    def create_scroll_area(self) -> QScrollArea:
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)

        self.container_widget = QWidget()
        self.layout = QVBoxLayout(self.container_widget)

        spacer_label = QLabel(" ", self)
        spacer_label.setFixedHeight(50)
        spacer_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(spacer_label)

        for channel in self.channels:
            label = QLabel(channel, self)
            label.setFixedHeight(50)
            label.setAlignment(Qt.AlignCenter)
            label.setContextMenuPolicy(Qt.CustomContextMenu)
            label.customContextMenuRequested.connect(self.show_context_menu)
            self.layout.addWidget(label)

        self.container_widget.setLayout(self.layout)
        self.container_widget.setFixedSize(100, len(self.channels) * 100)

        scroll_area.setWidget(self.container_widget)
        scroll_area.setFixedSize(150, len(self.channels) * 100)
        return scroll_area

    def show_context_menu(self, position):
        self.channel_right_clicked.emit(self.mapToGlobal(position))


class EventButton(QPushButton):
    addChildEventSignal = pyqtSignal(object)
    deleteEventSignal = pyqtSignal(object)

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
            self.addChildEventSignal.emit(self.event)
        elif action == delete_action:
            self.deleteEventSignal.emit(self.event)


class TimeAxisWidget(QWidget):
    def __init__(self, max_time: float, scale_factor: float, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.max_time = max_time
        self.scale_factor = scale_factor
        self.initUI()

    def initUI(self) -> None:
        self.setFixedSize(int(self.max_time * self.scale_factor) + 50, 50)

    def paintEvent(self, event: any) -> None:
        painter = QPainter(self)
        pen = QPen(Qt.black, 2)
        painter.setPen(pen)
        self.draw_time_axis(painter)

    def draw_time_axis(self, painter: QPainter) -> None:
        painter.drawLine(0, 25, self.width(), 25)
        for time in range(int(self.max_time) + 1):
            x = int(time * self.scale_factor)
            painter.drawLine(x, 20, x, 30)
            painter.drawText(QRect(x - 10, 30, 20, 20), Qt.AlignCenter, str(time))


class EventsViewerWidget(QWidget):
    def __init__(self, sequence: Sequence, scale_factor: float, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.sequence = sequence
        self.scale_factor = scale_factor
        self.initUI()

    def initUI(self) -> None:
        main_layout = QVBoxLayout(self)
        self.scroll_area = self.create_scroll_area()
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)

    def create_scroll_area(self) -> QScrollArea:
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)

        container_widget = QWidget()
        self.container_layout = QVBoxLayout(container_widget)

        self.refreshUI(self.container_layout)

        container_widget.setLayout(self.container_layout)
        scroll_area.setWidget(container_widget)
        return scroll_area

    def refreshUI(self, layout: QVBoxLayout) -> None:
        self.clear_layout(layout)
        all_events = self.sequence.all_events
        max_time = max(
            (event.start_time + (event.behavior.duration if isinstance(event.behavior, Ramp) else 0))
            for event in all_events
        )

        num_channels = len(self.sequence.channels)
        self.setFixedSize(int(max_time * self.scale_factor) + 50, num_channels * 100)
        time_axis = TimeAxisWidget(max_time, self.scale_factor, self)
        layout.addWidget(time_axis)

        for channel in self.sequence.channels:
            buttons_container = self.create_buttons_container(channel)
            layout.addWidget(buttons_container)

    def clear_layout(self, layout: QVBoxLayout) -> None:
        for i in reversed(range(layout.count())):
            widget_to_remove = layout.itemAt(i).widget()
            layout.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)

    def create_buttons_container(self, channel: any) -> QWidget:
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
            button.addChildEventSignal.connect(self.add_child_event)
            button.deleteEventSignal.connect(self.delete_event)

            previous_end_time = start_time + (event.behavior.duration if isinstance(event.behavior, Ramp) else 10/self.scale_factor)
        
        return buttons_container
    def add_child_event(self, parent_event):
        dialog = ChildEventDialog([ch.name for ch in self.sequence.channels])
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            behavior = data['behavior']  # Replace this with actual logic to determine the behavior
            print( behavior['behavior_type'])
            if behavior['behavior_type'] == 'Jump':
                child_event = self.sequence.add_event(
                    channel_name=data['channel'],
                    behavior=Jump(data['jump_target_value']),
                    relative_time=float(data["relative_time"]),
                    reference_time=data["reference_time"],
                    parent_event=parent_event
                )
            else:
                child_event = self.sequence.add_event(
                    channel_name=data['channel'],
                    behavior=Ramp(behavior['ramp_duration'], behavior['ramp_type'], behavior['start_value'], behavior['end_value']),
                    relative_time=float(data["relative_time"]),
                    reference_time=data["reference_time"],
                    parent_event=parent_event
                )
            self.refreshUI(self.container_layout)

    def delete_event(self, event):
        self.sequence.delete_event(event.start_time, event.channel.name)
        self.refreshUI(self.container_layout)


class SyncedTableWidget(QWidget):
    def __init__(self, scale_factor: float = 100.0):
        super().__init__()
        self.scale_factor=scale_factor
        self.sequence = Sequence.from_json("sequencer/seq_data.json")
        self.layout_main = QHBoxLayout()
        
        self.setup_ui()
        self.setLayout(self.layout_main) 

    def setup_ui(self) -> None:
        self.channel_list = ChannelLabelWidget(self.sequence)
        self.data_table = EventsViewerWidget(self.sequence, self.scale_factor)

        self.channel_list.channel_right_clicked.connect(self.show_context_menu)

        self.channel_list.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.data_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.scroll_bar1 = self.channel_list.scroll_area.verticalScrollBar()
        self.scroll_bar2 = self.data_table.scroll_area.verticalScrollBar()
        self.scroll_bar1.valueChanged.connect(self.sync_scroll)
        self.scroll_bar2.valueChanged.connect(self.sync_scroll)

        
        self.layout_main.addWidget(self.channel_list)
        self.layout_main.addWidget(self.data_table)
        

    def sync_scroll(self, value: int) -> None:
        sender = self.sender()
        if sender == self.scroll_bar1:
            self.scroll_bar2.setValue(self.calculate_proportion(value, self.scroll_bar1, self.scroll_bar2))
        else:
            self.scroll_bar1.setValue(self.calculate_proportion(value, self.scroll_bar2, self.scroll_bar1))

    def calculate_proportion(self, value: int, scroll_bar_from: QScrollBar, scroll_bar_to: QScrollBar) -> int:
        proportion = value / scroll_bar_from.maximum() if scroll_bar_from.maximum() != 0 else 0
        return int(proportion * scroll_bar_to.maximum())

    def show_context_menu(self, position):
        context_menu = QMenu(self)
        add_channel_action = context_menu.addAction("Add Channel")
        action = context_menu.exec_(position)
        if action == add_channel_action:
            self.show_channel_dialog()


    def show_channel_dialog(self):
        dialog = ChannelDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if data['type'] == 'Analog':
                self.sequence.add_analog_channel(
                    name=data['name'],
                    card_number=data['card_number'],
                    channel_number=data['channel_number'],
                    reset_value=data['reset_value'],
                    max_voltage=data.get('max_voltage', 10),
                    min_voltage=data.get('min_voltage', -10)
                )
            elif data['type'] == 'Digital':
                # Add digital channel logic here, similar to analog channel
                pass
            self.refresh_UI()
    
    
    
    def refresh_UI(self):
        layout = self.layout()

        for i in reversed(range(layout.count())):
            widget_to_remove = layout.itemAt(i).widget()
            layout.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)

        self.setup_ui()





if __name__ == '__main__':
    app = QApplication(sys.argv)



    window = SyncedTableWidget()
    window.show()
    sys.exit(app.exec_())
