# Filename: synced_table_widget.py

import sys
from typing import List, Optional
from PyQt5.QtWidgets import (
    QApplication, QHBoxLayout,QToolTip,QGridLayout, QMessageBox,QSizePolicy, QDialog,QLabel,QMenu, QPushButton, QWidget, QVBoxLayout, QScrollArea, QScrollBar,QInputDialog
)
from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QPen

from PyQt5.QtCore import Qt, QRect, pyqtSignal, QPoint


from sequencer.Dialogs.channel_dialog import ChannelDialog
from sequencer.Dialogs.event_dialog import ChildEventDialog,RootEventDialog
from sequencer.Dialogs.edit_event_dialog import EditEventDialog
from sequencer.event import Ramp, Jump, Sequence

import sys
from typing import List, Optional
from PyQt5.QtWidgets import (
    QApplication, QHBoxLayout, QVBoxLayout, QScrollArea, QScrollBar, QMenuBar,
    QMenu, QAction, QPushButton, QWidget, QLabel, QDialog, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint

from sequencer.Dialogs.channel_dialog import ChannelDialog
from sequencer.Dialogs.event_dialog import ChildEventDialog, RootEventDialog
from sequencer.Dialogs.edit_event_dialog import EditEventDialog
from sequencer.event import Ramp, Jump, Sequence, SequenceManager



class ChannelLabelWidget(QWidget):
    channel_right_clicked = pyqtSignal(QPoint)
    buttonclicked = pyqtSignal()

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
        self.setStyleSheet("""
            QWidget {
                background-color: #2C3E50;
                color: #ECF0F1;
                font-size: 16px;
                font-family: Arial, sans-serif;
            }
            QLabel {
                background-color: #34495E;
                border: 1px solid #1ABC9C;
                border-radius: 5px;
                padding: 5px;
            }
            QLabel:hover {
                background-color: #1ABC9C;
                color: #2C3E50;
            }
            QPushButton {
                background-color: #1ABC9C;
                border: none;
                color: #2C3E50;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #16A085;
            }
            QPushButton:pressed {
                background-color: #148F77;
            }
        """)

    def create_scroll_area(self) -> QScrollArea:
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)

        self.container_widget = QWidget()
        self.layout = QVBoxLayout(self.container_widget)

        if not self.channels:
            add_channel_button = QPushButton("Add Channel", self)
            add_channel_button.setFixedHeight(20)
            add_channel_button.clicked.connect(self.add_channel)
            self.layout.addWidget(add_channel_button, alignment=Qt.AlignCenter)
        else:
            for channel in self.channels:
                label = QLabel(channel, self)
                label.setFixedHeight(50)
                label.setAlignment(Qt.AlignCenter)
                label.setContextMenuPolicy(Qt.CustomContextMenu)
                label.customContextMenuRequested.connect(self.show_context_menu)
                self.layout.addWidget(label)

        self.container_widget.setLayout(self.layout)
        self.container_widget.setFixedSize(100, len(self.channels) * 100 if self.channels else 100)

        scroll_area.setWidget(self.container_widget)
        scroll_area.setFixedWidth(150)
        return scroll_area

    def show_context_menu(self, position):
        self.channel_right_clicked.emit(self.mapToGlobal(position))

    def add_channel(self):
        self.buttonclicked.emit()

class GapButton(QPushButton):
    addEventSignal = pyqtSignal(object)

    def __init__(self, channel, parent, previous_event):
        super().__init__(parent)
        self.channel = channel
        self.previous_event = previous_event
        self.initUI()

    def initUI(self):
        if self.previous_event is None:
            self.setText("Add Event")
        else:
            if isinstance(self.previous_event.behavior, Ramp):
                self.setText(str(self.previous_event.behavior.end_value))
            elif isinstance(self.previous_event.behavior, Jump):
                self.setText(str(self.previous_event.behavior.target_value))

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        no_event_stylesheet = """
        QPushButton {
            background-color: #4CAF50; /* Green */
            border: 2px solid #388E3C; /* Darker green border */
            padding: 10px;
            border-radius: 10px;
            color: white;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #45a049;
        }

        QPushButton:pressed {
            background-color: #3e8e41;
        }

        QPushButton:checked {  /* If you need a checked/active state for no-event buttons */
            background-color: #90EE90; /* Light green */
            border: 2px solid #698B69; /* Darker light green border */
        }

        QPushButton:disabled {
            background-color: #9E9E9E; /* Grayed-out color */
            border: 2px solid #616161; /* Darker gray border */
            color: #333333; /* Dark text for contrast */
        }

        QPushButton:focus {
            outline: 2px solid #007BFF; /* Blue outline */
        }
        """
        self.setStyleSheet(no_event_stylesheet)

    def enterEvent(self, event):
        if self.previous_event:
            if isinstance(self.previous_event.behavior, Ramp):
                behavior = f"Holding on {self.previous_event.behavior.end_value} after {self.previous_event.behavior.ramp_type} ramp"
            elif isinstance(self.previous_event.behavior, Jump):
                behavior = f"Holding on {self.previous_event.behavior.target_value} after jump"
            else:
                behavior = "Unknown behavior"
            QToolTip.showText(event.globalPos(), behavior, self)
        else:
            QToolTip.showText(event.globalPos(), "No previous event", self)
        super().enterEvent(event)

    def show_context_menu(self, pos):
        context_menu = QMenu(self)
        add_event_action = context_menu.addAction("Add Event")
        action = context_menu.exec_(self.mapToGlobal(pos))
        if action == add_event_action:
            self.addEventSignal.emit(self.channel)

class EventButton(QPushButton):
    addChildEventSignal = pyqtSignal(object)
    deleteEventSignal = pyqtSignal(object)
    editEventSignal = pyqtSignal(object)

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
            self.setText(str(self.event.behavior.ramp_type) + ' ' + str(self.event.behavior.start_value) + '->' + str(self.event.behavior.end_value))
        elif isinstance(self.event.behavior, Jump):
            self.setGeometry(int(self.event.start_time * self.scale_factor), 0, 10, 50)
            self.setText('J')
        else:
            self.setGeometry(int(self.event.start_time * self.scale_factor), 0, 50, 50)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        event_stylesheet = """
        QPushButton {
            background-color: #FF5733; /* Orange */
            border: 2px solid #C70039; /* Dark red border */
            padding: 10px;
            border-radius: 10px;
            color: white;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #D14928;
        }

        QPushButton:pressed {
            background-color: #C04022;
        }

        QPushButton:checked {
            background-color: #FFC300; /* Yellow for active state */
            border: 2px solid #FFA500; /* Orange border */
        }

        QPushButton:disabled {
            background-color: #9E9E9E; /* Grayed-out color */
            border: 2px solid #616161; /* Darker gray border */
            color: #333333; /* Dark text for contrast */
        }

        QPushButton:focus {
            outline: 2px solid #007BFF; /* Blue outline */
        }
        """
        self.setStyleSheet(event_stylesheet)

    def enterEvent(self, event):
        if isinstance(self.event.behavior, Ramp):
            behavior = f"{self.event.behavior.ramp_type} Ramp of {self.event.behavior.duration} from {self.event.behavior.start_value} to {self.event.behavior.end_value}"
        elif isinstance(self.event.behavior, Jump):
            behavior = f"Jump to {self.event.behavior.target_value}"
        else:
            behavior = "Unknown behavior"
        QToolTip.showText(event.globalPos(), behavior, self)
        super().enterEvent(event)

    def show_context_menu(self, pos):
        context_menu = QMenu(self)
        add_child_action = context_menu.addAction("Add Child Event")
        delete_action = context_menu.addAction("Delete Event")
        edit_action = context_menu.addAction("Edit Event")

        action = context_menu.exec_(self.mapToGlobal(pos))
        if action == add_child_action:
            self.addChildEventSignal.emit(self.event)
        elif action == delete_action:
            self.deleteEventSignal.emit(self.event)
        elif action == edit_action:
            self.editEventSignal.emit(self.event)

class TimeAxisContent(QWidget):
    def __init__(self, max_time, scale_factor, parent=None):
        super().__init__(parent)
        self.max_time = max_time
        self.scale_factor = scale_factor
        self.initUI()

    def initUI(self) -> None:
        self.setFixedSize(int(self.max_time * self.scale_factor) + 50, 50)
        self.setStyleSheet("""
            QWidget {
                background-color: #2C3E50;
                color: #ECF0F1;
            }
        """)

    def paintEvent(self, event: any) -> None:
        painter = QPainter(self)
        pen = QPen(Qt.white, 2)
        painter.setPen(pen)
        self.draw_time_axis(painter)

    def draw_time_axis(self, painter: QPainter) -> None:
        painter.drawLine(0, 25, self.width(), 25)
        for time in range(int(self.max_time) + 1):
            x = int(time * self.scale_factor)
            painter.drawLine(x, 20, x, 30)
            painter.drawText(QRect(x - 10, 30, 20, 20), Qt.AlignCenter, str(time))
class TimeAxisWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.max_time = parent.max_time  # Example max time
        self.scale_factor = parent.scale_factor  # Example scale factor
        self.initUI()
        self.setFixedHeight(105)
        self.setStyleSheet("""
            QWidget {
                background-color: #2C3E50;
                color: #ECF0F1;
                font-size: 16px;
                font-family: Arial, sans-serif;
            }
        """)

    def initUI(self) -> None:
        # Create the scroll area
        self.scroll_area = QScrollArea(self)

        # Create the content widget for the scroll area
        content_widget = TimeAxisContent(self.max_time, self.scale_factor, self)
        self.scroll_area.setWidget(content_widget)

        # Create a layout and add the scroll area to it
        layout = QVBoxLayout()
        layout.addWidget(self.scroll_area)

        # Set the layout for this widget
        self.setLayout(layout)

class EventsViewerWidget(QWidget):
    changes_in_event = pyqtSignal()

    def __init__(self, sequence: Sequence, scale_factor: float, parent: QWidget):
        super().__init__()
        self.sequence = sequence
        self.scale_factor = scale_factor
        self.parent = parent
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)
        self.initUI()

    def initUI(self) -> None:
        self.scroll_area = self.create_scroll_area()
        self.main_layout.addWidget(self.scroll_area)
        self.setStyleSheet("""
            QWidget {
                background-color: #2C3E50;
                color: #ECF0F1;
                font-size: 16px;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #FF5733;
                border: none;
                color: #ECF0F1;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D14928;
            }
            QPushButton:pressed {
                background-color: #C04022;
            }
            QPushButton:checked {
                background-color: #FFC300;
                border: 2px solid #FFA500;
            }
        """)

    def create_scroll_area(self) -> QScrollArea:
        scroll_area = QScrollArea(self)

        self.container_widget = QWidget()
        self.container_layout = QVBoxLayout(self.container_widget)

        self.populate_events()

        self.container_widget.setLayout(self.container_layout)
        self.container_widget.setFixedSize(int(self.max_time * self.scale_factor) + 50, self.num_channels * 100)
        scroll_area.setWidget(self.container_widget)
        return scroll_area

    def refreshUI(self) -> None:
        self.clear_layout(self.container_layout)
        self.populate_events()
        self.container_widget.setFixedSize(int(self.max_time * self.scale_factor) + 50, self.num_channels * 100)
        self.changes_in_event.emit()

    def clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def populate_events(self) -> None:
        if len(self.sequence.channels) == 0:
            self.max_time = 1
            self.num_channels = 1
            return
        if len(self.sequence.all_events) == 0:
            self.max_time = 0
            self.num_channels = len(self.sequence.channels)
            for channel in self.sequence.channels:
                buttons_container = self.create_buttons_container(channel)
                self.container_layout.addWidget(buttons_container)
            return
        
        all_events = self.sequence.all_events
        self.max_time = max(
            (event.start_time + (event.behavior.duration if isinstance(event.behavior, Ramp) else 0))
            for event in all_events
        )

        self.num_channels = len(self.sequence.channels)

        for channel in self.sequence.channels:
            buttons_container = self.create_buttons_container(channel)
            self.container_layout.addWidget(buttons_container)

    def create_buttons_container(self, channel: any) -> QWidget:
        buttons_container = QWidget(self)
        buttons_container.setFixedHeight(50)
        previous_end_time = 0.0
        previous_event = None

        for event in channel.events:
            start_time = event.start_time
            if start_time > previous_end_time:
                gap_duration = start_time - previous_end_time
                gap_button = GapButton(channel, buttons_container, previous_event)
                gap_button.setGeometry(int(previous_end_time * self.scale_factor), 0, int(gap_duration * self.scale_factor), 50)
                gap_button.addEventSignal.connect(self.add_event)

            previous_event = event
            button = EventButton(event, self.scale_factor, self.sequence, buttons_container)
            button.addChildEventSignal.connect(self.add_child_event)
            button.deleteEventSignal.connect(self.delete_event)
            button.editEventSignal.connect(self.edit_event)

            previous_end_time = start_time + (event.behavior.duration if isinstance(event.behavior, Ramp) else 10 / self.scale_factor)

        if previous_event:
            gap_duration = self.max_time - previous_end_time
            if gap_duration > 0:
                gap_button = GapButton(channel, buttons_container, previous_event)
                gap_button.setGeometry(int(previous_end_time * self.scale_factor), 0, int(gap_duration * self.scale_factor), 50)
                gap_button.addEventSignal.connect(self.add_event)
        
        gap_button = GapButton(channel, buttons_container, previous_event)
        gap_button.setGeometry(int(previous_end_time * self.scale_factor), 0, int((self.max_time - previous_end_time+1) * self.scale_factor), 50)
        gap_button.addEventSignal.connect(self.add_event)
        
        return buttons_container

    def add_event(self, channel):
        try:
            dialog = RootEventDialog([channel.name])
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_data()
                behavior = data['behavior']
                if behavior['behavior_type'] == 'Jump':
                    self.sequence.add_event(
                        channel_name=channel.name,
                        behavior=Jump(behavior['jump_target_value']),
                        start_time=float(data["start_time"])
                    )
                else:
                    self.sequence.add_event(
                        channel_name=channel.name,
                        behavior=Ramp(behavior['ramp_duration'], behavior['ramp_type'], behavior['start_value'], behavior['end_value']),
                        start_time=float(data["start_time"])
                    )
                self.refreshUI()
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)

    def add_child_event(self, parent_event):
        try:
            dialog = ChildEventDialog([ch.name for ch in self.sequence.channels])
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_data()
                behavior = data['behavior']
                if behavior['behavior_type'] == 'Jump':
                    self.sequence.add_event(
                        channel_name=data['channel'],
                        behavior=Jump(behavior['jump_target_value']),
                        relative_time=float(data["relative_time"]),
                        reference_time=data["reference_time"],
                        parent_event=parent_event
                    )
                else:
                    self.sequence.add_event(
                        channel_name=data['channel'],
                        behavior=Ramp(behavior['ramp_duration'], behavior['ramp_type'], behavior['start_value'], behavior['end_value']),
                        relative_time=float(data["relative_time"]),
                        reference_time=data["reference_time"],
                        parent_event=parent_event
                    )
                self.refreshUI()
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)

    def delete_event(self, event_to_delete):
        try:
            self.sequence.delete_event(event_to_delete)
            self.refreshUI()
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)

    def edit_event(self, event_to_edit):
        try:
            dialog = RootEventDialog([ch.name for ch in self.sequence.channels], event_to_edit)
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_data()
                behavior = data['behavior']
                if behavior['behavior_type'] == 'Jump':
                    self.sequence.update_event(
                        event_to_edit,
                        channel_name=data['channel'],
                        behavior=Jump(behavior['jump_target_value']),
                        start_time=float(data["start_time"])
                    )
                else:
                    self.sequence.update_event(
                        event_to_edit,
                        channel_name=data['channel'],
                        behavior=Ramp(behavior['ramp_duration'], behavior['ramp_type'], behavior['start_value'], behavior['end_value']),
                        start_time=float(data["start_time"])
                    )
                self.refreshUI()
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)

class SyncedTableWidget(QWidget):
    def __init__(self, sequence, scale_factor: float = 100.0):
        super().__init__()
        self.scale_factor = scale_factor
        self.sequence = sequence
        self.syncing = False  # Flag to prevent multiple updates
        self.setup_ui()
        
    def setup_ui(self) -> None:
        self.layout_main = QGridLayout()
        self.setLayout(self.layout_main)
        
        self.channel_list = ChannelLabelWidget(self.sequence)
        self.data_table = EventsViewerWidget(self.sequence, self.scale_factor, parent=self)
        self.data_table.changes_in_event.connect(self.refresh_UI)
        self.time_axis = TimeAxisWidget(self.data_table)
        
        self.channel_list.channel_right_clicked.connect(self.show_context_menu)        
        self.channel_list.buttonclicked.connect(self.show_channel_dialog)

        self.scroll_bar1 = self.channel_list.scroll_area.verticalScrollBar()
        self.scroll_bar2 = self.data_table.scroll_area.verticalScrollBar()
        self.scroll_bar1.valueChanged.connect(self.sync_scroll)
        self.scroll_bar2.valueChanged.connect(self.sync_scroll)

        self.scroll_bar3 = self.data_table.scroll_area.horizontalScrollBar()
        self.scroll_bar4 = self.time_axis.scroll_area.horizontalScrollBar()
        self.scroll_bar3.valueChanged.connect(self.sync_scroll_vertical)
        self.scroll_bar4.valueChanged.connect(self.sync_scroll_vertical)

        # Adding widgets to the grid layout
        self.layout_main.addWidget(QWidget(), 0, 0)  # Empty top-left slot
        self.layout_main.addWidget(self.time_axis, 0, 1)  # Top-right slot
        self.layout_main.addWidget(self.channel_list, 1, 0)  # Bottom-left slot
        self.layout_main.addWidget(self.data_table, 1, 1)  # Bottom-right slot
        self.layout_main.setColumnStretch(0, 0)  # Column 0 (channel_list) - does not expand
        self.layout_main.setColumnStretch(1, 1)  # Column 1 (time_axis and data_table) - expands to fill space


    def sync_scroll_vertical(self, value: int) -> None:
        if self.syncing:
            return
        self.syncing = True
        sender = self.sender()
        if sender == self.scroll_bar3:
            self.scroll_bar4.setValue(self.calculate_proportion(value, self.scroll_bar3, self.scroll_bar4))
        else:
            self.scroll_bar3.setValue(self.calculate_proportion(value, self.scroll_bar4, self.scroll_bar3))
        self.syncing = False

    def sync_scroll(self, value: int) -> None:
        if self.syncing:
            return
        self.syncing = True
        sender = self.sender()
        if sender == self.scroll_bar1:
            self.scroll_bar2.setValue(self.calculate_proportion(value, self.scroll_bar1, self.scroll_bar2))
        else:
            self.scroll_bar1.setValue(self.calculate_proportion(value, self.scroll_bar2, self.scroll_bar1))
        self.syncing = False

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


from sequencer.event import SequenceManager


# self.main_sequences[sequence.sequence_name] = {"index":index, "seq":sequence}
# class to handle sequence manager
from PyQt5.QtWidgets import (
    QScrollArea, QHBoxLayout, QVBoxLayout, QInputDialog, QDialog, QMessageBox, QPushButton, QMenuBar, QAction, QFileDialog, QWidget, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette

class SequenceManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.sequence_manager = SequenceManager()
        self.selected_sequence_button = None
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.menu_bar = self.create_menu_bar()
        self.layout.addWidget(self.menu_bar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.scroll_area.setWidget(self.button_container)

        self.layout.addWidget(self.scroll_area)

        self.sequence_view_area = QWidget()
        self.sequence_view_layout = QVBoxLayout(self.sequence_view_area)
        self.layout.addWidget(self.sequence_view_area,2)

        self.update_buttons()


    def create_menu_bar(self):
        menu_bar = QMenuBar(self)
        file_menu = QMenu("File", self)

        load_action = QAction("Load Sequence Manager", self)
        load_action.triggered.connect(self.load_sequence_manager)
        file_menu.addAction(load_action)

        save_action = QAction("Save Sequence Manager", self)
        save_action.triggered.connect(self.save_sequence_manager)
        file_menu.addAction(save_action)

        menu_bar.addMenu(file_menu)
        return menu_bar

    def save_sequence_manager(self):
        file_dialog = QFileDialog(self)
        file_name, _ = file_dialog.getSaveFileName(self, "Save Sequence Manager", "", "JSON Files (*.json)")
        if file_name:
            self.sequence_manager.to_json(file_name=file_name)

    def load_sequence_manager(self):
        file_dialog = QFileDialog(self)
        file_name, _ = file_dialog.getOpenFileName(self, "Open Sequence Manager", "", "JSON Files (*.json)")
        if file_name:
            self.sequence_manager = SequenceManager.from_json(file_name=file_name)
            self.update_buttons()
            self.display_sequence(flag=True)

    def update_buttons(self):
        for i in reversed(range(self.button_layout.count())):
            self.button_layout.itemAt(i).widget().setParent(None)

        for sequence_name in self.sequence_manager.main_sequences:
            button = QPushButton(sequence_name, self)
            button.clicked.connect(self.display_sequence)
            button.setStyleSheet(self.get_button_style(False))
            self.button_layout.addWidget(button)

        add_button = QPushButton("+", self)
        add_button.clicked.connect(self.add_new_sequence)
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: 2px solid #4CAF50;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """)
        self.button_layout.addWidget(add_button, alignment=Qt.AlignLeft)

    def get_button_style(self, selected):
        if selected:
            return """
                QPushButton {
                    background-color: #FFC300; /* Bright Yellow */
                    color: white;
                    border: 2px solid #C70039;
                    border-radius: 10px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #FFB200; /* Slightly Darker Yellow */
                }
                QPushButton:pressed {
                    background-color: #FFA200; /* Even Darker Yellow */
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: 2px solid #1976D2;
                    border-radius: 10px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #1E88E5;
                }
                QPushButton:pressed {
                    background-color: #1565C0;
                }
            """

    def add_new_sequence(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Sequence")

        layout = QVBoxLayout(dialog)

        new_sequence_button = QPushButton("Create New Sequence", dialog)
        load_sequence_button = QPushButton("Load Sequence from File", dialog)

        layout.addWidget(new_sequence_button)
        layout.addWidget(load_sequence_button)

        new_sequence_button.clicked.connect(lambda: self.create_new_sequence(dialog))
        load_sequence_button.clicked.connect(lambda: self.load_sequence_from_file(dialog))

        dialog.setLayout(layout)
        dialog.exec_()

    def create_new_sequence(self, dialog):
        sequence_name, ok = QInputDialog.getText(dialog, "Add New Sequence", "Enter sequence name:")
        if ok and sequence_name:
            try:
                self.sequence_manager.add_new_sequence(sequence_name)
                self.update_buttons()
                self.display_sequence(flag=True)
            except Exception as e:
                QMessageBox.critical(dialog, "Error", str(e))
        dialog.accept()

    def load_sequence_from_file(self, dialog):
        file_dialog = QFileDialog(self)
        file_name, _ = file_dialog.getOpenFileName(self, "Load Sequence from JSON", "", "JSON Files (*.json)")
        if file_name:
            try:
                sequence = Sequence.from_json(file_name)
                self.sequence_manager.load_sequence(sequence)
                self.update_buttons()
                self.display_sequence(flag=True)
            except Exception as e:
                QMessageBox.critical(dialog, "Error, File is corrupt due to ", str(e))
        dialog.accept()

    def display_sequence(self,flag=False):
        button = self.sender()
        if not flag:
            sequence_name = button.text()
            sequence = self.sequence_manager.main_sequences[sequence_name]["seq"]
        else :
            sequence = list(self.sequence_manager.main_sequences.values())[-1]["seq"]
            sequence_name = sequence.sequence_name
        for i in reversed(range(self.sequence_view_layout.count())):
            widget_to_remove = self.sequence_view_layout.itemAt(i).widget()
            self.sequence_view_layout.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)

        synced_table_widget = SyncedTableWidget(sequence)
        self.sequence_view_layout.addWidget(synced_table_widget)

        if self.selected_sequence_button:
            self.selected_sequence_button.setStyleSheet(self.get_button_style(False))
        if not flag:
            self.selected_sequence_button = button
            self.selected_sequence_button.setStyleSheet(self.get_button_style(True))
        else:
            button = self.button_layout.itemAt(self.button_layout.count()-2).widget()
            self.selected_sequence_button = button
            self.selected_sequence_button.setStyleSheet(self.get_button_style(True))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SequenceManagerWidget()
    window.show()
    sys.exit(app.exec_())
