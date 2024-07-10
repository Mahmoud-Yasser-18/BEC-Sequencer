# Filename: synced_table_widget.py

import sys
from typing import List, Optional
from PyQt5.QtWidgets import (
   QComboBox, QApplication, QHBoxLayout,QToolTip,QGridLayout, QMessageBox,QSizePolicy, QDialog,QLabel,QMenu, QPushButton, QWidget, QVBoxLayout, QScrollArea, QScrollBar,QInputDialog
)
from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QPen

from PyQt5.QtCore import Qt, QRect, pyqtSignal, QPoint



from sequencer.Dialogs.event_dialog import ChildEventDialog,RootEventDialog,ParameterDialog
from sequencer.Dialogs.edit_event_dialog import EditEventDialog,SweepEventDialog
from sequencer.event import Ramp, Jump, Sequence,Event
from sequencer.ADwin_Modules import calculate_time_ranges

from sequencer.event import SequenceManager,Sequence,Event , Analog_Channel, Digital_Channel, Channel, RampType

import sys
from typing import List, Optional
from PyQt5.QtWidgets import (
    QApplication, QHBoxLayout, QVBoxLayout, QScrollArea, QScrollBar, QMenuBar,
    QMenu, QAction, QPushButton, QWidget, QLabel, QDialog, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint

from sequencer.Dialogs.channel_dialog import ChannelDialog,Edit_Analog_Channel,Edit_Digital_Channel,CustomDialog,ExistingChannelDialog

from sequencer.Dialogs.event_dialog import ChildEventDialog, RootEventDialog
from sequencer.Dialogs.edit_event_dialog import EditEventDialog
from sequencer.event import Ramp, Jump, Sequence, SequenceManager

from sequencer.imaging.THORCAM.imaging_software import ThorCamControlWidget
from sequencer.imaging.THORCAM.data_viewer import DataItemViewer

from sequencer.main_widgets.main_seq_widgets.Runner_widget import Runner
class ChannelLabel(QWidget):
    def __init__(self, channel_name, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.channel_name = channel_name
        self.initUI()

    def initUI(self):
        self.label = QLabel(self.channel_name, self)
        self.label.setFixedHeight(50)
        self.label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.label.customContextMenuRequested.connect(self.show_context_menu)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def show_context_menu(self, pos):
        context_menu = QMenu(self)
        add_channel_action = context_menu.addAction("Add New Channel")
        add_existing_channel_action = context_menu.addAction("Add Existing Channel from another Sequence")
        edit_channel_action = context_menu.addAction("Edit Channel")
        delete_channel_action = context_menu.addAction("Delete Channel")

        action = context_menu.exec_(self.mapToGlobal(pos))
        if action == edit_channel_action:
            self.parent.on_edit_channel(self.channel_name)
        elif action == delete_channel_action:
            self.parent.on_delete_channel(self.channel_name)
        elif action == add_channel_action:
            self.parent.on_add_channel()
        elif action == add_existing_channel_action:
            self.parent.on_add_existing_channel()

class ChannelLabelWidget(QWidget):
    add_channel_clicked = pyqtSignal()
    add_existing_channel_clicked = pyqtSignal()
    edit_channel_clicked = pyqtSignal(str)
    delete_channel_clicked = pyqtSignal(str)
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
                color: #ECF0F1;  /* Text color for contrast */
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
            # add right click menu 
            add_channel_button.setContextMenuPolicy(Qt.CustomContextMenu)
            add_channel_button.customContextMenuRequested.connect(self.show_context_menu_for_button)
            #add right click which has option to add existing channel and connect it to the no_add_existing_channel
            
            self.layout.addWidget(add_channel_button, alignment=Qt.AlignCenter)
        else:
            for channel in self.channels:
                channel_label = ChannelLabel(channel, self)
                self.layout.addWidget(channel_label)

        self.container_widget.setLayout(self.layout)
        self.container_widget.setFixedHeight(len(self.channels) * 100 if self.channels else 100)
        self.container_widget.adjustSize()

        scroll_area.setWidget(self.container_widget)
        scroll_area.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                width: 10px;  /* Adjust the width as needed */
            }
        """)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area.setFixedWidth(200)
        return scroll_area
    
    def show_context_menu_for_button(self, pos):
        context_menu = QMenu(self)
        add_channel_action = context_menu.addAction("Add New Channel")
        add_existing_channel_action = context_menu.addAction("Add Existing Channel from another Sequence")

        action = context_menu.exec_(self.mapToGlobal(pos))
        if action == add_channel_action:
            self.on_add_channel()
        elif action == add_existing_channel_action:
            self.on_add_existing_channel()


    def on_edit_channel(self, channel_name):
        self.edit_channel_clicked.emit(channel_name)

    def on_delete_channel(self, channel_name):
        self.delete_channel_clicked.emit(channel_name)

    def on_add_channel(self): 
        self.add_channel_clicked.emit()

    def on_add_existing_channel(self):
        self.add_existing_channel_clicked.emit()

    def add_channel(self):
        self.buttonclicked.emit()


class GapButton(QPushButton):
    addEventSignal = pyqtSignal(object)

    def __init__(self, channel, parent, previous_event,event):
        super().__init__(parent)
        self.channel = channel  
        self.previous_event = previous_event
        self.next_event = event 
        self.initUI()

    def initUI(self):
        if self.previous_event is None:
            self.setText("Add Event")
            self.clicked.connect(self.add_event)
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
                if self.next_event is not None: 
                    behavior = f"starting from time {self.previous_event.end_time} to {self.next_event.start_time}\nHolding on {self.previous_event.behavior.end_value} after {self.previous_event.behavior.ramp_type} ramp"
                else : 
                    behavior = f"starting from time {self.previous_event.end_time}\nHolding on {self.previous_event.behavior.end_value} after {self.previous_event.behavior.ramp_type} ramp"

            elif isinstance(self.previous_event.behavior, Jump):
                if self.next_event is not None: 
                    behavior = f"starting from time {self.previous_event.end_time} to {self.next_event.start_time}\nHolding on {self.previous_event.behavior.target_value} after jump"
                else :
                    behavior = f"starting from time {self.previous_event.end_time}\nHolding on {self.previous_event.behavior.target_value} after jump"
            else:
                behavior = "Unknown behavior"
            QToolTip.showText(event.globalPos(), behavior, self)
        else:
            QToolTip.showText(event.globalPos(), "No previous event", self)
        super().enterEvent(event)

    def add_event(self):
        self.addEventSignal.emit(self.channel)

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
    sweepEventSignal = pyqtSignal(object)
    unsweepEventSignal = pyqtSignal(object)
    addParameterSignal = pyqtSignal(object)
    removeParameterSignal = pyqtSignal(object)

    def __init__(self, event: Event , scale_factor, sequence, parent=None, view_type= "Linear",flag=0,next_event=None):
        super().__init__(parent)
        self.event = event
        self.scale_factor = scale_factor
        self.sequence = sequence
        self.view_type = view_type
        self.flag = flag 
        self.next_event = next_event
        self.initUI()

    def initUI(self):
        base_stylesheet = """
        QPushButton {{
            background-color: {background_color}; 
            border: {border_size} solid {border_color}; 
            padding: 10px;
            border-radius: {border_radius};
            color: white;
            font-weight: bold;
        }}

        QPushButton:hover {{
            background-color: {hover_color};
        }}

        QPushButton:pressed {{
            background-color: {pressed_color};
        }}

        QPushButton:checked {{
            background-color: #FFC300; /* Yellow for active state */
            border: 2px solid #FFA500; /* Orange border */
        }}

        QPushButton:disabled {{
            background-color: #9E9E9E; /* Grayed-out color */
            border: 2px solid #616161; /* Darker gray border */
            color: #333333; /* Dark text for contrast */
        }}

        QPushButton:focus {{
            outline: 2px solid #007BFF; /* Blue outline */
        }}
        """

        ramp_styles = {
            "background_color": "#FF5733",  # Orange
            "border_color": "#C70039",  # Dark red border
            "hover_color": "#D14928",
            "pressed_color": "#C04022",
            "border_radius": "15px",
            "border_size": "2px"
        }

        jump_styles = {
            "background_color": "#8A2BE2",  # Blue Violet
            "border_color": "#4B0082",  # Indigo
            "hover_color": "#7B68EE",  # Medium Slate Blue
            "pressed_color": "#6A5ACD",  # Slate Blue
              "border_radius": "15px",
              "border_size": "2px"
        }


        if self.view_type == "Linear" or self.view_type == "Linear Event":
                

            if isinstance(self.event.behavior, Ramp):
                duration = self.event.behavior.duration
                # make sure the duration is at least 1
                if int(duration * self.scale_factor) < 10:
                    self.setGeometry(int(self.event.start_time * self.scale_factor), 0, 10, 50)
                    self.setText('R')
                else:
                    self.setGeometry(int(self.event.start_time * self.scale_factor), 0, int(duration * self.scale_factor), 50)
                    self.setText(str(self.event.behavior.ramp_type) + ' ' + str(self.event.behavior.start_value) + '->' + str(self.event.behavior.end_value))
                stylesheet_data = ramp_styles

            elif isinstance(self.event.behavior, Jump):
                self.setGeometry(int(self.event.start_time * self.scale_factor), 0, 10, 50)
                self.setText('J')
                stylesheet_data =  jump_styles
        elif self.view_type == "Event":
            self.setFixedSize(int(self.scale_factor*2), 50)
            if isinstance(self.event.behavior, Ramp):
                self.setText(str(self.event.behavior.ramp_type) + ' ' + str(self.event.behavior.start_value) + '->' + str(self.event.behavior.end_value))
                stylesheet_data = ramp_styles
            elif isinstance(self.event.behavior, Jump):
                self.setText(f'Jump to {self.event.behavior.target_value}')
                stylesheet_data =  jump_styles


        if self.event.associated_parameters:
            stylesheet_data["border_color"] = "#9E9E9E"  # Purple border
            stylesheet_data["border_radius"] = "0px"
            stylesheet_data["border_size"] = "5px"
        
        if self.event.is_sweept:
            stylesheet_data["border_color"] = "#FFFFFF"  # Purple border
            stylesheet_data["border_size"] = "5px"
            

        # Apply the stylesheet
        stylesheet = base_stylesheet.format(**stylesheet_data)
        self.setStyleSheet(stylesheet)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)


    def enterEvent(self, event:Event):
        if self.flag :
            if isinstance(self.event.behavior, Ramp):
                behavior = f"Start time: {self.event.start_time}\nEnd time: {self.event.end_time}\n{self.event.behavior.ramp_type} Ramp of duration {self.event.behavior.duration} from value {self.event.behavior.start_value} to {self.event.behavior.end_value}"
            elif isinstance(self.event.behavior, Jump):
                behavior = f"Start time: {self.event.start_time}\nEnd time: {self.next_event.start_time}\nJump to {self.event.behavior.target_value}"
            else:
                behavior = "Unknown behavior"
            if self.event.associated_parameters:
                behavior += "\n\nAssociated Parameters:"
                # associated_parameters is a list 
                for p in self.event.associated_parameters:
                    behavior += f"\n{p.name}: {p.get_value()}"
            behavior += f"comment: {self.event.comment}"

            QToolTip.showText(event.globalPos(), behavior, self)
            super().enterEvent(event)
 
        else : 
            if isinstance(self.event.behavior, Ramp):
                behavior = f"Start time: {self.event.start_time}\nEnd time: {self.event.end_time}\n{self.event.behavior.ramp_type} Ramp of duration {self.event.behavior.duration} from value {self.event.behavior.start_value} to {self.event.behavior.end_value}"
            elif isinstance(self.event.behavior, Jump):
                behavior = f"Start time: {self.event.start_time}\nEnd time: {self.event.end_time}\nJump to {self.event.behavior.target_value}"
            else:
                behavior = "Unknown behavior"
            if self.event.associated_parameters:
                behavior += "\n\nAssociated Parameters:"
                # associated_parameters is a list 
                for p in self.event.associated_parameters:
                    behavior += f"\n{p.name}: {p.get_value()}"
            QToolTip.showText(event.globalPos(), behavior, self)
            super().enterEvent(event)

    def show_context_menu(self, pos):
        context_menu = QMenu(self)
        add_child_action = context_menu.addAction("Add Child Event")
        delete_action = context_menu.addAction("Delete Event")
        edit_action = context_menu.addAction("Edit Event")
        sweep_action = context_menu.addAction("Sweep Event")
        unsweep_action = context_menu.addAction("Unweep Event")
        add_parameter_action = context_menu.addAction("Add Parameter")
        remove_parameter_action = context_menu.addAction("Remove Parameter")

        action = context_menu.exec_(self.mapToGlobal(pos))
        if action == add_child_action:
            self.addChildEventSignal.emit(self.event)
        elif action == delete_action:
            self.deleteEventSignal.emit(self.event)
        elif action == edit_action:
            self.editEventSignal.emit(self.event)
        elif action == sweep_action:
            self.sweepEventSignal.emit(self.event)
        elif action == unsweep_action:
            self.unsweepEventSignal.emit(self.event)

        elif action == add_parameter_action:
            self.addParameterSignal.emit(self.event)
        elif action == remove_parameter_action:
            self.removeParameterSignal.emit(self.event)

        

        
    

class TimeAxisContent(QWidget):
    def __init__(self,sequence:Sequence, max_time, scale_factor, parent=None,view_type: str = "Linear"):
        super().__init__(parent)
        self.max_time = max_time
        self.scale_factor = scale_factor
        self.sequence = sequence
        self.view_type = view_type
        self.initUI()

    def initUI(self) -> None:
        if self.view_type == "Linear" or self.view_type == "Linear Event":
            self.setFixedSize(int(self.max_time * self.scale_factor) + 50, 50)
        elif self.view_type == "Event":
            time_ranges = calculate_time_ranges(self.sequence.all_events)
            i=0
            for time_range in time_ranges:
                if time_range[0][0] ==time_range[0][1]and (self.sequence.all_events[-1].end_time!=time_range[0][1] ):
                    continue
                i+=1
            
            self.setFixedSize(int((i) * self.scale_factor*2) + 50, 50)


            
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
        if self.view_type == "Linear":
            for time in range(int(self.max_time) + 1):
                x = int(time * self.scale_factor)
                painter.drawLine(x, 20, x, 30)
                painter.drawText(QRect(x - 30, 30, 60, 20), Qt.AlignCenter, str(time))
        elif self.view_type == "Linear Event":
            time_ranges=calculate_time_ranges(self.sequence.all_events) 

            for time_range in time_ranges:
                start_time, end_time = time_range[0]
                x_start = int(start_time * self.scale_factor)
                painter.drawLine(x_start, 20, x_start, 30)
                painter.drawText(QRect(x_start- 30, 30, 60, 20), Qt.AlignCenter, f"{start_time}")
        elif self.view_type == "Event":
            time_ranges=calculate_time_ranges(self.sequence.all_events)
            i=0
            for time_range in time_ranges:
                if time_range[0][0] ==time_range[0][1] and (self.sequence.all_events[-1].end_time!=time_range[0][1] ):
                    continue
                start_time, end_time = time_range[0]
                # x_start = int(start_time * self.scale_factor)
                x_start_i = int(i * self.scale_factor*2)
                painter.drawLine(x_start_i, 20, x_start_i, 30)
                painter.drawText(QRect(x_start_i- 30, 30, 60, 20), Qt.AlignCenter, f"{start_time}")
                i+=1



class TimeAxisWidget(QWidget):
    def __init__(self,sequence, parent: Optional[QWidget] = None,view_type: str = "Linear"):
        super().__init__(parent)
        self.max_time = parent.max_time  # Example max time
        self.scale_factor = parent.scale_factor  # Example scale factor
        self.view_type = view_type
        self.sequence = sequence
        self.initUI()
        self.setFixedHeight(80)
        self.setStyleSheet("""
            QWidget {
                background-color: #2C3E50;
                color: #ECF0F1;
                font-size: 16px;
            }
            
            QScrollBar:horizontal {
                height: 1px;  /* Adjust the height as needed */
            }
            
            
            }
        """)

    def initUI(self) -> None:
        # Create the scroll area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Ensure horizontal scrollbar is always shown

        # Create the content widget for the scroll area
        content_widget = TimeAxisContent(sequence=self.sequence,max_time=self.max_time,scale_factor= self.scale_factor, parent=self,view_type=self.view_type)
        self.scroll_area.setWidget(content_widget)

        # Create a layout and add the scroll area to it
        layout = QVBoxLayout()
        layout.addWidget(self.scroll_area)

        # Set the layout for this widget
        self.setLayout(layout)

class EventsViewerWidget(QWidget):
    changes_in_event = pyqtSignal()

    def __init__(self,sequence_manager:SequenceManager , sequence: Sequence, scale_factor: float, parent: QWidget):
        super().__init__()
        self.sequence_manager = sequence_manager
        self.sequence = sequence
        self.scale_factor = scale_factor
        self.parent = parent
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)


        self.sequence_range_index = {}
        
        for  index,range in enumerate(calculate_time_ranges(self.sequence.all_events)):
            if range[0][0] ==range[0][1] and (self.sequence.all_events[-1].end_time!=range[0][1] ):
                continue
            self.sequence_range_index[range[0][0]] = index

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
        if self.sequence_manager.view_type == "Linear" or self.sequence_manager.view_type == "Linear Event":

            self.container_widget.setFixedSize(int(self.max_time * self.scale_factor) + 50, self.num_channels * 100)
        elif self.sequence_manager.view_type == "Event":
            self.container_widget.setFixedSize(int((len(self.sequence_range_index.items())) * self.scale_factor*2) + 50, self.num_channels * 100)
        scroll_area.setWidget(self.container_widget)
        scroll_area.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                width: 10px;  /* Adjust the width as needed */
            }
            }
        """)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        return scroll_area

    def refreshUI(self) -> None:
        self.clear_layout(self.container_layout)
        self.populate_events()
        if self.sequence_manager.view_type == "Linear" or self.sequence_manager.view_type == "Linear Event":
            self.container_widget.setFixedSize(int(self.max_time * self.scale_factor) + 50, self.num_channels * 100)
        elif self.sequence_manager.view_type == "Event":
            self.container_widget.setFixedSize(int(len(self.sequence_range_index.items()) * self.scale_factor*2) + 50, self.num_channels * 100)

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
        event = None
        if self.sequence_manager.view_type == "Linear" or self.sequence_manager.view_type == "Linear Event":
                

            for event in channel.events:
                start_time = event.start_time
                if start_time > previous_end_time:
                    gap_duration = start_time - previous_end_time
                    gap_button = GapButton(channel, buttons_container, previous_event,event)
                    gap_button.setGeometry(int(previous_end_time * self.scale_factor), 0, int(gap_duration * self.scale_factor), 50)
                    gap_button.addEventSignal.connect(self.add_event)

                previous_event = event
                button = EventButton(event, self.scale_factor, self.sequence, buttons_container)

                button.addChildEventSignal.connect(self.add_child_event)
                button.deleteEventSignal.connect(self.delete_event)
                button.editEventSignal.connect(self.edit_event)
                button.sweepEventSignal.connect(self.sweep_event)
                button.unsweepEventSignal.connect(self.unsweep_event)
                button.addParameterSignal.connect(self.add_parameter)
                button.removeParameterSignal.connect(self.remove_parameter)

                previous_end_time = start_time + (event.behavior.duration if isinstance(event.behavior, Ramp) else 10 / self.scale_factor)

            if previous_event:
                gap_duration = self.max_time - previous_end_time
                if gap_duration > 0:
                    gap_button = GapButton(channel, buttons_container, previous_event,event)
                    gap_button.setGeometry(int(previous_end_time * self.scale_factor), 0, int(gap_duration * self.scale_factor), 50)
                    gap_button.addEventSignal.connect(self.add_event)
            
            gap_button = GapButton(channel, buttons_container, previous_event,event= None)
            gap_button.setGeometry(int(previous_end_time * self.scale_factor), 0, int((self.max_time - previous_end_time+1) * self.scale_factor), 50)
            gap_button.addEventSignal.connect(self.add_event)
            
            return buttons_container
        elif self.sequence_manager.view_type == "Event":
            previous_end_time = 0
            time_ranges = calculate_time_ranges(channel.events)
            time_ranges2 =[time_range for time_range in time_ranges if time_range[1] != []]

            time_ranges_start = [time_range[0][0] for time_range in time_ranges if time_range[1] != []]
            j=0
            i=0
            for key, value in self.sequence_range_index.items():
                if key not in time_ranges_start:
                    # make a gap button 
                    try:
                        gap_button = GapButton(channel, buttons_container, previous_event,event=time_ranges2[i][1][0])
                        gap_button.setGeometry(int(j * self.scale_factor*2), 0, int( 2* self.scale_factor), 50)
                        gap_button.addEventSignal.connect(self.add_event)
                        previous_end_time = key
                    except:
                        pass
                else:
                    # make an event button 
                    event = time_ranges2[i][1][0]
                    previous_event = event
                    i+=1
                    try :
                        button = EventButton(event, self.scale_factor, self.sequence, buttons_container,view_type=self.sequence_manager.view_type,flag=1,next_event=time_ranges2[i][1][0])
                    except:
                        button = EventButton(event, self.scale_factor, self.sequence, buttons_container,view_type=self.sequence_manager.view_type)
                    button.setGeometry(int(j * self.scale_factor*2), 0, int( 2* self.scale_factor), 50)
                    button.addChildEventSignal.connect(self.add_child_event)
                    button.deleteEventSignal.connect(self.delete_event)
                    button.editEventSignal.connect(self.edit_event)
                    button.sweepEventSignal.connect(self.sweep_event)
                    button.unsweepEventSignal.connect(self.unsweep_event)
                    button.addParameterSignal.connect(self.add_parameter)
                    button.removeParameterSignal.connect(self.remove_parameter)

                j+=1

            return buttons_container
            


    
    def remove_parameter(self, event:Event):
        try:

            parameter_name=QInputDialog.getItem(self, 'Remove Parameter', 'Enter the parameter name to remove',[p.name for p in event.associated_parameters], 0, False)

            self.sequence.remove_parameter(parameter_name=parameter_name[0])
            self.refreshUI()
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)
            self.refreshUI()
    def add_parameter(self, event:Event):
        try:
            possible_parameters = event.get_event_attributes()
            
            dialog = ParameterDialog(possible_parameters)
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.getInputs()
                parameter_name = data[0]
                parameter_name_new: str = data[1]

                
                if parameter_name_new is None or parameter_name_new.strip == "":
                    raise Exception("Parameter name cannot be empty")

                self.sequence.add_parameter_to_event(event, parameter_name=parameter_name_new.strip(),parameter_value=possible_parameters[parameter_name],parameter_origin=parameter_name )
                self.refreshUI()

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)

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
                        behavior=Ramp(behavior['ramp_duration'], RampType(behavior['ramp_type']), behavior['start_value'], behavior['end_value'],resolution=behavior['resolution']),
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
                        behavior=Ramp(behavior['ramp_duration'], RampType(behavior['ramp_type']), behavior['start_value'], behavior['end_value']),
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
            self.sequence.delete_event(event_to_delete=event_to_delete)
            self.refreshUI()
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)

    def edit_event(self, event_to_edit):
        try:
            dialog = EditEventDialog( event_to_edit)
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_data()

                behavior = data['behavior_data']
                if data['behavior_type'] == 'Jump':
                    self.sequence.edit_event(
                        edited_event=event_to_edit,



                        jump_target_value=behavior.get('target_value', None),
                        new_relative_time= float(data.get ("relative_time",None)) if data.get ("relative_time",None) else None,
                        new_reference_time= data.get ('reference_time',None),
                        new_start_time=float(data.get ("start_time",None)) if data.get ("start_time",None) else None)    
                        
                else:
                    self.sequence.edit_event(
                        edited_event=event_to_edit,
                        # channel_name=data['channel'],
                        duration= behavior['duration'],
                        start_value= behavior['start_value'],
                        end_value= behavior['end_value'],
                        ramp_type= RampType(behavior['ramp_type']),
                        new_relative_time= float(data.get ("relative_time",None)) if data.get ("relative_time",None) else None,
                        new_reference_time= data.get ('reference_time',None),
                        new_start_time=float(data.get ("start_time",None)) if data.get ("start_time",None) else None
                                                                )
                self.refreshUI()
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self,"Error", error_message)
    
    def sweep_event(self, event_to_sweep):
        try:
            dialog = SweepEventDialog(event_to_sweep)

            if dialog.exec_() == QDialog.Accepted:
                result = dialog.get_result()
                if result:
                    
                    parameter_name, values = result
                    self.sequence_manager.sweep_sequence_temp(self.sequence.sequence_name, parameter_name, values,event_to_sweep=event_to_sweep)
                    self.refreshUI()

                else:
                    pass
            else:
                pass
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)
    
    def unsweep_event(self, event_to_unsweep):
        try:
            self.sequence_manager.remove_sweep_sequence(self.sequence.sequence_name,event_to_sweep=event_to_unsweep)
            self.refreshUI()
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)

import copy
class SyncedTableWidget(QWidget):
    def __init__(self, sequence_manager:SequenceManager, sequence:Sequence, scale_factor: float = 100.0,view_type="Linear"):
        super().__init__()
        self.sequence_manager = sequence_manager
        self.scale_factor = scale_factor
        self.sequence = sequence
        self.syncing = False  # Flag to prevent multiple updates
        self.layout_main = QGridLayout()
        
        self.setLayout(self.layout_main)
        self.combo_box_type = QComboBox()
        option_list = ["Linear","Linear Event","Event"]
        option_list.remove(copy.deepcopy(self.sequence_manager.view_type))

        self.combo_box_type.addItems([copy.deepcopy(self.sequence_manager.view_type)]+option_list)
        self.combo_box_type.currentTextChanged.connect(self.change_view_type)

        self.setup_ui()
        
    def setup_ui(self) -> None:
        
        self.layout_main.setHorizontalSpacing(0)  # Set horizontal spacing to 0 pixels
        self.layout_main.setVerticalSpacing(0)    # Set vertical spacing to 0 pixels
        self.layout_main.setContentsMargins(0, 0, 0, 0)  # Set content margins to 0 pixels on all sides
        
        
        
        # Create and configure widgets
        self.channel_list = ChannelLabelWidget(self.sequence)
        self.data_table = EventsViewerWidget(self.sequence_manager,self.sequence, self.scale_factor, parent=self)
        self.data_table.changes_in_event.connect(self.refresh_UI)
        self.time_axis = TimeAxisWidget(sequence=self.sequence,parent=self.data_table,view_type=self.sequence_manager.view_type)
        
        self.channel_list.add_channel_clicked.connect(self.show_channel_dialog)
        self.channel_list.add_existing_channel_clicked.connect(self.show_existing_channel_dialog)
        self.channel_list.buttonclicked.connect(self.show_channel_dialog)
        self.channel_list.edit_channel_clicked.connect(self.edit_channel)
        self.channel_list.delete_channel_clicked.connect(self.delete_channel)

        self.scroll_bar1 = self.channel_list.scroll_area.verticalScrollBar()
        self.scroll_bar2 = self.data_table.scroll_area.verticalScrollBar()
        self.scroll_bar1.valueChanged.connect(self.sync_scroll)
        self.scroll_bar2.valueChanged.connect(self.sync_scroll)

        self.scroll_bar3 = self.data_table.scroll_area.horizontalScrollBar()
        self.scroll_bar4 = self.time_axis.scroll_area.horizontalScrollBar()
        self.scroll_bar3.valueChanged.connect(self.sync_scroll_vertical)
        self.scroll_bar4.valueChanged.connect(self.sync_scroll_vertical)




        self.layout_main.addWidget(self.combo_box_type, 0, 0)

        self.layout_main.addWidget(self.time_axis, 0, 1)  # Top-right slot
        self.layout_main.addWidget(self.channel_list, 1, 0)  # Bottom-left slot
        self.layout_main.addWidget(self.data_table, 1, 1)  # Bottom-right slot
        self.layout_main.setColumnStretch(0, 0)  # Column 0 (channel_list) - does not expand
        self.layout_main.setColumnStretch(1, 1)  # Column 1 (time_axis and data_table) - expands to fill space

    def show_existing_channel_dialog(self):
        dialog = ExistingChannelDialog(self.sequence_manager,self.sequence)
        if dialog.exec_() == QDialog.Accepted:
            Channel_name = dialog.get_data()
            self.sequence_manager.add_existing_channel_to_sequence(self.sequence.sequence_name, Channel_name)
            self.refresh_UI()

        

    def change_view_type(self,view_type):
        self.sequence_manager.view_type =view_type
        self.refresh_UI()
        
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


    def edit_channel(self, channel_name: str) -> None:
        channel = self.sequence.find_channel_by_name(channel_name)
        try:
            if isinstance(channel, Analog_Channel):
                dialog = Edit_Analog_Channel( channel)
                if dialog.exec_() == QDialog.Accepted:
                    data = dialog.get_data()
                    self.sequence.edit_analog_channel(
                        name=channel_name,
                        new_name=data['name'],
                        card_number=data['card_number'],
                        channel_number=data['channel_number'],
                        reset_value=data['reset_value'],
                        max_voltage=data.get('max_voltage', 10),
                        min_voltage=data.get('min_voltage', -10)
                    )
            elif isinstance(channel, Digital_Channel):
                dialog = Edit_Digital_Channel( channel)
                if dialog.exec_() == QDialog.Accepted:
                    data = dialog.get_data()
                    self.sequence.edit_digital_channel(
                                            name=channel_name,
                        new_name=data['name'],
                        card_number=data['card_number'],
                        channel_number=data['channel_number'],
                        reset_value=data['reset_value']
                    )
            self.refresh_UI()
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)


    
    def delete_channel(self, channel_name: str) -> None:
        try:
            self.sequence.delete_channel(channel_name)
            self.refresh_UI()
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)
            

    def show_channel_dialog(self):
        try :
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
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)    
        self.refresh_UI()

    def refresh_UI(self):
        layout = self.layout()
        for i in reversed(range(layout.count())):
            widget_to_remove = layout.itemAt(i).widget()
            layout.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)
        self.setup_ui()






# self.main_sequences[sequence.sequence_name] = {"index":index, "seq":sequence}
# class to handle sequence manager
from PyQt5.QtWidgets import (
    QScrollArea, QHBoxLayout, QVBoxLayout, QInputDialog, QDialog, QMessageBox, QPushButton, QMenuBar, QAction, QFileDialog, QWidget, QApplication
)
from PyQt5.QtCore import Qt,QMimeData
from PyQt5.QtGui import QColor, QPalette,QDrag



class DraggableButton(QPushButton):
    save_sequence_signal = pyqtSignal(str)  # Signal to emit a number
    save_sequence_signal_csv = pyqtSignal(str)  # Signal to emit a number
    delete_sequence_signal = pyqtSignal(str)  # Signal to emit a number
    edit_sequence_signal = pyqtSignal(str)  # Signal to emit a number
    plot_sequence_signal = pyqtSignal(str)  # Signal to emit a numbero
    print_sequence_signal = pyqtSignal(str)  # Signal to emit a number


    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.text_to_emit = text 
        self.parent = parent
        self.setAcceptDrops(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def mouseMoveEvent(self, event):
        if event.buttons() != Qt.LeftButton:
            return
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.text())
        drag.setMimeData(mime_data)
        drag.exec_(Qt.MoveAction)

    def dragEnterEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        if event.source() != self:
            self.parent.move_button(self, event.source())

    def show_context_menu(self, position):
        context_menu = QMenu(self)
        save_sequence_action = QAction('Save Sequence', self)
        save_sequence_action.triggered.connect(self.save_sequence)
        context_menu.addAction(save_sequence_action)

        save_sequence_action_csv = QAction('Save Sequence as CSV', self)
        save_sequence_action_csv.triggered.connect(self.save_sequence_csv)
        context_menu.addAction(save_sequence_action_csv)


        delete_sequence_action = QAction('delete Sequence', self)
        delete_sequence_action.triggered.connect(self.delete_sequence)
        context_menu.addAction(delete_sequence_action)
        
        edit_sequence_action = QAction('edit Sequence', self)
        edit_sequence_action.triggered.connect(self.edit_sequence)
        context_menu.addAction(edit_sequence_action)
        
        plot_sequence_action = QAction('plot Sequence', self)
        plot_sequence_action.triggered.connect(self.plot_sequence)
        context_menu.addAction(plot_sequence_action)

        print_sequence_action = QAction('print Sequence', self)
        print_sequence_action.triggered.connect(self.print_sequence)
        context_menu.addAction(print_sequence_action)

        
        
        context_menu.exec_(self.mapToGlobal(position))
        

    def save_sequence(self):

        self.save_sequence_signal.emit(self.text_to_emit)

    def save_sequence_csv(self):            
            self.save_sequence_signal_csv.emit(self.text_to_emit)

    def edit_sequence(self):

        self.edit_sequence_signal.emit(self.text_to_emit)
    def delete_sequence(self):

        self.delete_sequence_signal.emit(self.text_to_emit)
    def plot_sequence(self):

        self.plot_sequence_signal.emit(self.text_to_emit)

    def print_sequence(self):

        self.print_sequence_signal.emit(self.text_to_emit)  


class SequenceManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.sequence_manager = SequenceManager()
        self.selected_sequence_button = None
        self.view_type ="Linear"
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
        self.layout.addWidget(self.sequence_view_area, 2)

        self.update_buttons()

    def create_menu_bar(self):
        menu_bar = QMenuBar(self)
        file_menu = QMenu("File", self)
        tools_menu = QMenu("tools", self)

        load_action = QAction("Load Sequence Manager", self)
        load_action.triggered.connect(self.load_sequence_manager)
        file_menu.addAction(load_action)

        save_action = QAction("Save Sequence Manager", self)
        save_action.triggered.connect(self.save_sequence_manager)
        file_menu.addAction(save_action)

        open_runner_action = QAction("Open Runner", self)
        open_runner_action.triggered.connect(self.open_runner)
        tools_menu.addAction(open_runner_action)


        
        open_camera_action = QAction("Open Camera", self)
        open_camera_action.triggered.connect(self.open_camera)
        tools_menu.addAction(open_camera_action)


        
        open_data_view_action = QAction("Open Data Viewer", self)
        open_data_view_action.triggered.connect(self.open_data_view)
        tools_menu.addAction(open_data_view_action)




        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(tools_menu)
        
        return menu_bar
    def open_data_view(self):
        try:
            self.data_view_widget = DataItemViewer()
            self.data_view_widget.show()
        except Exception as e:
            error_message = f"Can not Open Data View, An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)

    def open_runner(self):
        try:
            self.runner_widget = Runner(self.sequence_manager)
            self.runner_widget.show()
        except Exception as e:
            error_message = f"Can not Open Runner, An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)
    def open_camera(self):
        try:
            self.camera_widget = ThorCamControlWidget()
            self.camera_widget.show()
        except Exception as e:
            error_message = f"Can not Open Camera, An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)
            
            

    def save_sequence_manager(self):
        try:
            file_dialog = QFileDialog(self)
            file_name, _ = file_dialog.getSaveFileName(self, "Save Sequence Manager", "", "JSON Files (*.json)")
            if file_name:
                self.sequence_manager.to_json(file_name=file_name)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)

    def load_sequence_manager(self):
        try:
            file_dialog = QFileDialog(self)
            file_name, _ = file_dialog.getOpenFileName(self, "Open Sequence Manager", "", "JSON Files (*.json)")
            if file_name:
                self.sequence_manager = SequenceManager.from_json(file_name=file_name)
                self.update_buttons()
                self.display_sequence(flag=True)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)

    def save_sequence(self, sequence_name):
        try:
            file_dialog = QFileDialog(self)
            file_name, _ = file_dialog.getSaveFileName(self, "Save Singel Sequence", "", "JSON Files (*.json)")
            if file_name:
                self.sequence_manager.main_sequences[sequence_name]["seq"].to_json(file_name)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)
            
        # self.sequence_manager.main_sequences[sequence_name]["seq"].to_json(file_name+".json")
    def save_sequence_CSV(self, sequence_name): 
        try:
            file_dialog = QFileDialog(self)
            file_name, _ = file_dialog.getSaveFileName(self, "Save Singel Sequence", "", "CSV Files (*.csv)")
            if file_name:
                self.sequence_manager.main_sequences[sequence_name]["seq"].to_csv(file_name+".csv")
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)

    def delete_sequence(self, sequence_name):
        try:
            self.sequence_manager.delete_sequence(sequence_name)
            self.update_buttons()
            self.display_sequence(flag=True)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)

    def edit_sequence(self, sequence_name):
        # ask user for new name
        try:
            new_sequence_name, ok = QInputDialog.getText(self, "Edit Sequence Name", "Enter new sequence name:")
            if ok and new_sequence_name:
                    
                self.sequence_manager.change_sequence_name(old_name=sequence_name, new_name=new_sequence_name)
                self.update_buttons()
                self.display_sequence(flag=True)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)

    def print_sequence(self, sequence_name):
        try:
            seq = self.sequence_manager.main_sequences[sequence_name]["seq"]
            text = seq.get_event_tree()

            # make a message to print the text
            msg = QMessageBox()
            msg.setWindowTitle("Sequence Tree")
            msg.setText(text)
            msg.exec_()
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)

        
         
        

    def plot_sequence(self, sequence_name):
        try:
            #makZe a dialog to ask for channel name with a combobox
            channels =["All Channels"]+ [ch.name for ch in self.sequence_manager.main_sequences[sequence_name]["seq"].channels] 
            types = ["Normal","With Relations"]
            dialog = CustomDialog(channels, types)
            if dialog.exec_() == QDialog.Accepted:
                channel_name, channel_type,resolution = dialog.get_values()
                print(f"Selected Channel: {channel_name}, Type: {channel_type}")

                if channel_name != "All Channels":
                    if channel_type == "Normal":
                        self.sequence_manager.main_sequences[sequence_name]["seq"].plot([channel_name],resolution=resolution)
                    else :
                        self.sequence_manager.main_sequences[sequence_name]["seq"].plot_all([channel_name],resolution=resolution)

                else:  
                    if channel_type == "Normal":
                        self.sequence_manager.main_sequences[sequence_name]["seq"].plot(resolution=resolution)
                    else :
                        self.sequence_manager.main_sequences[sequence_name]["seq"].plot_all(resolution=resolution)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)


    def update_buttons(self):
        for i in reversed(range(self.button_layout.count())):
            self.button_layout.itemAt(i).widget().setParent(None)

        for sequence_name in self.sequence_manager.main_sequences:
            button = DraggableButton(sequence_name, self)
            button.clicked.connect(self.display_sequence)
            button.save_sequence_signal.connect(self.save_sequence)
            button.save_sequence_signal_csv.connect(self.save_sequence_CSV)
            button.delete_sequence_signal.connect(self.delete_sequence)
            button.edit_sequence_signal.connect(self.edit_sequence)
            button.plot_sequence_signal.connect(self.plot_sequence)
            button.print_sequence_signal.connect(self.print_sequence)


            button.setStyleSheet(self.get_button_style(False))
            self.button_layout.addWidget(button)

        add_button = DraggableButton("+", self)
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

    def move_button(self, target, source):
        source_index = self.button_layout.indexOf(source)
        target_index = self.button_layout.indexOf(target)

        #rearrange the sequences in the sequence manager
        # target_index_manager = self.sequence_manager.main_sequences[target.text()]["index"]


        self.sequence_manager.move_sequence_to_index(source.text(),target_index )


        self.button_layout.insertWidget(target_index, source)



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

    def display_sequence(self, flag=False):
        button = self.sender()
        if not flag:
            sequence_name = button.text()
            sequence = self.sequence_manager.main_sequences[sequence_name]["seq"]
        else:
            if len(self.sequence_manager.main_sequences.items() )== 0 :
                return
            sequence = list(self.sequence_manager.main_sequences.values())[-1]["seq"]
            sequence_name = sequence.sequence_name

        for i in reversed(range(self.sequence_view_layout.count())):
            widget_to_remove = self.sequence_view_layout.itemAt(i).widget()
            self.sequence_view_layout.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)
        
        synced_table_widget = SyncedTableWidget(self.sequence_manager, sequence,view_type=self.view_type)
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
# experiment description : 
