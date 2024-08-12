
import copy 
from PyQt5.QtWidgets import (
   QComboBox, QApplication, QHBoxLayout,QToolTip,QGridLayout, QMessageBox,QSizePolicy, QDialog,QLabel,QMenu, QPushButton, QWidget, QVBoxLayout, QScrollArea, QScrollBar,QInputDialog
)

from PyQt5.QtCore import Qt, QRect, pyqtSignal,QPoint
from sequencer.ADwin_Modules2 import calculate_time_ranges
from sequencer.time_frame import TimeInstance,Sequence,Event , Analog_Channel, Digital_Channel, Channel, RampType,creat_test ,Jump,Ramp,Digital
import sys
from typing import List, Optional
from PyQt5.QtWidgets import (
    QApplication, QHBoxLayout, QVBoxLayout, QScrollArea, QScrollBar, QMenuBar,QDialogButtonBox,
    QMenu, QAction, QPushButton, QWidget, QLabel, QDialog, QMessageBox, QFileDialog
)


from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QHBoxLayout
from sequencer.time_frame import Sequence, Event, Analog_Channel, Digital_Channel, Channel, RampType,Jump,Ramp
import sys
from PyQt5.QtWidgets import QApplication, QLabel, QSizePolicy, QGridLayout, QWidget
from PyQt5.QtGui import QPainter, QPolygon, QBrush,QDoubleValidator
from PyQt5.QtCore import QPoint, Qt, QSize

from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QScrollArea, QVBoxLayout, QSizePolicy
from PyQt5.QtGui import QPainter, QBrush, QPolygon
from PyQt5.QtCore import QPoint, Qt, QSize
from sequencer.GUI.Dialogs.channel_dialog import ChannelDialog, Edit_Digital_Channel, Edit_Analog_Channel
from sequencer.GUI.Dialogs.events_dialogs import AnalogEventDialog, DigitalEventDialog


class ScrollAreaWithShiftScroll(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def wheelEvent(self, event):
        if event.modifiers() == Qt.ShiftModifier:
            # Scroll horizontally if Shift is pressed
            delta = event.angleDelta().y()
            scroll_bar = self.horizontalScrollBar()
        else:
            # Scroll vertically by default
            delta = event.angleDelta().y()
            scroll_bar = self.verticalScrollBar()
        
        # Perform the scroll
        scroll_bar.setValue(scroll_bar.value() - delta)

class QArrowWidget(QLabel):
    """Responsible for drawing arrows which show parent-child relationship."""
    def __init__(self, arrow_list, grid, start_pos=(0, 0), parent=None):
        super().__init__(parent)
        self.grid = grid
        self.start_pos = start_pos
        self.grid.addWidget(self, self.start_pos[0], self.start_pos[1], 1, -1)
        self.figureOutHowToDrawArrows(arrow_list)
        # self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)

    def sizeHint(self):
        return QSize(1000, (self.max_height + 1) * 10 + 5)

    def figureOutHowToDrawArrows(self, arrow_list):
        n_cols = 0
        for arrow in arrow_list:
            n_cols = max(max(n_cols, arrow[0]), arrow[1])
        self.n_cols = n_cols + 1

        self.arrow_list = arrow_list

        availability = []
        self.height_list = []
        for arrow in arrow_list:
            left_index = min(arrow[0], arrow[1])
            right_index = max(arrow[0], arrow[1])
            used = [False] * (right_index - left_index)
            for i, avail in enumerate(availability):
                if all(avail[left_index:right_index]):
                    height = i
                    break
            else:
                height = len(availability)
                availability.append([True] * self.n_cols)
            availability[height][left_index:right_index] = used
            self.height_list.append(height)
        self.max_height = len(availability)

    def paintEvent(self, event):
        centers = []
        r = self.grid.cellRect(self.start_pos[0], self.start_pos[1])
        top_left = r.topLeft()
        for i in range(self.n_cols):
            r = self.grid.cellRect(self.start_pos[0], i + self.start_pos[1])
            c = r.bottomRight() - top_left
            centers.append(c)

        qp = QPainter()
        qp.begin(self)
        # get self size 
        size = self.size()
        # get the width of a cell 
        cell_width = size.width() / self.n_cols


        for arrow, height in zip(self.arrow_list, self.height_list):
            center_left = centers[arrow[0]]
            center_right = centers[arrow[1]]
            
            hp = 10 * height + 5

            def drawArrow(qp, x1, x2, height):
                length = 5
                qp.drawLine(x1, height, x2, height)
                qp.drawLine(x1, height - length, x1, height + length)
                brush = QBrush(Qt.SolidPattern)
                qp.setBrush(brush)
                if x1 > x2:
                    length = -5
                points = [QPoint(x2, height),
                          QPoint(x2 - length, height - length),
                          QPoint(x2 - length, height + length)]
                arrowHead = QPolygon(points)
                qp.drawPolygon(arrowHead)
            
            drawArrow(qp, center_left.x()-cell_width, center_right.x()-cell_width, hp)
        qp.end()
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel
from PyQt5.QtGui import QIntValidator

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel, QShortcut
from PyQt5.QtGui import QIntValidator, QKeySequence
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel, QShortcut
from PyQt5.QtGui import QIntValidator, QKeySequence
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel
from PyQt5.QtGui import QIntValidator, QKeyEvent
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLineEdit, QLabel, QPushButton, QFormLayout, QMessageBox)
from PyQt5.QtGui import QIntValidator

class AddChildTimeInstanceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Child Time Instance")
        self.initUI()

    def initUI(self):
        layout = QFormLayout()

        self.name_edit = QLineEdit()
        layout.addRow("Name:", self.name_edit)

        self.relative_time_edit = QLineEdit()
        self.relative_time_edit.setValidator(QIntValidator())
        layout.addRow("Relative Time:", self.relative_time_edit)

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.add_child)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

    def add_child(self):
        name = self.name_edit.text()
        relative_time = self.relative_time_edit.text()

        if not name or not relative_time:
            QMessageBox.warning(self, "Input Error", "All fields are required.")
            return

        try:
            relative_time = int(relative_time)
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Relative time must be an integer.")
            return

        self.name = name
        self.relative_time = relative_time

class EditParentTimeInstanceDialog(QDialog):
    def __init__(self, parent_widget: 'TimeInstanceLabel'):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.all_children = [child.name for child in self.parent_widget.time_instance.get_root().get_all_children() if child.name != self.parent_widget.time_instance.name]
        self.initUI()

    def initUI(self):
        layout = QFormLayout()

        self.parent_time_instance_combo = QComboBox()
        self.parent_time_instance_combo.addItems(self.all_children)
        layout.addRow("Parent Time Instance:", self.parent_time_instance_combo)

        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_parent)
        layout.addWidget(self.edit_button)

        self.setLayout(layout)

    def edit_parent(self):
        parent_time_instance_name = self.parent_time_instance_combo.currentText()

        if not parent_time_instance_name:
            QMessageBox.warning(self, "Input Error", "Parent time instance is required.")
            return

        self.parent_time_instance_name = parent_time_instance_name
        self.accept()



from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QLabel, QMenu, QAction, QDialog, QFormLayout, QPushButton, QMessageBox, QComboBox)
from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import Qt

class TimeInstanceLabel(QWidget):
    def __init__(self, time_instance: 'TimeInstance', parent_widget: 'TimeInstanceWidget' = None):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.time_instance = time_instance
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Editable name
        self.name_edit = QLineEdit(self.time_instance.name)
        self.name_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.name_edit.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.name_edit)

        # Editable relative time with numeric validation
        self.relative_time_edit = QLineEdit(str(self.time_instance.relative_time))
        self.relative_time_edit.setValidator(QIntValidator())
        layout.addWidget(self.relative_time_edit)

        # Non-editable absolute time
        self.absolute_time_label = QLabel(str(self.time_instance.get_absolute_time()))
        layout.addWidget(self.absolute_time_label)

        # Connect signals
        self.name_edit.editingFinished.connect(self.change_name)
        self.relative_time_edit.editingFinished.connect(self.change_relative_time)

        self.setLayout(layout)
    
    def change_name(self):
        self.time_instance.edit_name(self.name_edit.text())
        self.parent_widget.refresh_UI()
    
    def change_relative_time(self):
        self.time_instance.edit_relative_time(int(self.relative_time_edit.text()))
        self.parent_widget.refresh_UI()

    def show_context_menu(self, position):
        context_menu = QMenu(self)
        
        add_child_action = QAction("Add Child Time Instance", self)
        add_child_action.triggered.connect(self.add_child_time_instance)
        context_menu.addAction(add_child_action)
        
        edit_parent_action = QAction("Edit Parent Time Instance", self)
        edit_parent_action.triggered.connect(self.edit_parent_time_instance)
        context_menu.addAction(edit_parent_action)
        
        delete_action = QAction("Delete Time Instance", self)
        delete_action.triggered.connect(self.delete_time_instance)
        context_menu.addAction(delete_action)
        
        context_menu.exec_(self.name_edit.mapToGlobal(position))

    def add_child_time_instance(self):
        dialog = AddChildTimeInstanceDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                self.time_instance.add_child_time_instance(dialog.name, dialog.relative_time)
                self.parent_widget.parent_widget.event_table.add_time_instance(
                    self.time_instance.get_child_time_instance_by_name(dialog.name)
                )
                self.parent_widget.refresh_UI()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def edit_parent_time_instance(self):
        dialog = EditParentTimeInstanceDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # try:
                self.parent_widget.parent_widget.sequence.edit_time_instance(self.time_instance,new_parent_name=dialog.parent_time_instance_name)
                self.parent_widget.refresh_UI()
            # except Exception as e:
            #     QMessageBox.critical(self, "Error", str(e))

    def delete_time_instance(self):
        self.parent_widget.parent_widget.sequence.delete_time_instance(self.time_instance.name)
        self.parent_widget.parent_widget.event_table.delete_time_instance(self.time_instance)
        self.parent_widget.refresh_UI()

        # self.parent_widget.parent_widget.event_table()



class TimeInstanceWidget(QWidget):
    def __init__(self, root_time_instance: 'TimeInstance', parent_widget: 'SequenceViewerWdiget' = None):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.root_time_instance = root_time_instance
        self.setWindowTitle('Time Instance Visualization')
        self.setGeometry(100, 100, 1000, 600)

        self.setup_UI()
        self.refresh_UI()

    def setup_UI(self):
        # Create a container widget to hold the grid layout
        self.inner_widget = QWidget()
        self.grid = QGridLayout(self.inner_widget)
        self.inner_widget.setLayout(self.grid)

        # Create a QScrollArea and set the container widget as its widget
        self.scroll_area = ScrollAreaWithShiftScroll()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.inner_widget)

        # Create a layout for TimeInstanceWidget and add the scroll area
        layout = QVBoxLayout()
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

    def refresh_UI(self):

        # Clear the grid layout
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Get and sort time instances
        self.time_instances = self.root_time_instance.get_all_time_instances()
        self.time_instances.sort(key=lambda ti: ti.get_absolute_time())

        # Add custom labels to grid for each time instance
        self.labels = {}
        for i, time_instance in enumerate(self.time_instances):
            label_widget = TimeInstanceLabel(time_instance, self)
            self.grid.addWidget(label_widget, 0, i)
            self.labels[time_instance] = (0, i)

        # Add the arrow widget in row 2
        arrow_list = []
        for time_instance in self.time_instances:
            if time_instance.parent:
                parent_index = self.labels[time_instance.parent][1]
                child_index = self.labels[time_instance][1]
                arrow_list.append((parent_index, child_index))

        self.arrow_widget = QArrowWidget(arrow_list, self.grid, start_pos=(3, 0), parent=self)

from PyQt5.QtWidgets import QPushButton

class ChannelButton(QPushButton):
    def __init__(self, channel:Channel, parent_widget:'ChannelLabelListWidget'=None):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.channel = channel
        self.setText(f'{self.channel.name}')

    def get_channel_index(self):
        return self.parent_widget.sequence.channels.index(self.channel)

    
    def delete_channel(self):
        self.parent_widget.sequence.delete_channel(self.channel.name)
        self.parent_widget.refresh_UI()
        self.parent_widget.parent_widget.event_table.delete_channel(self.channel)
    def add_channel(self):
        # open the add channel dialog
        dialog = ChannelDialog()
        
        # get current index
        index = self.get_channel_index()

        if dialog.exec_() == QDialog.Accepted:
            
            data= dialog.get_data()
            print(f"data: {data}")
            if data['type'] == 'Analog':
                self.parent_widget.sequence.add_analog_channel(name=data['name'], card_number=data['card_number'], channel_number=data['channel_number'], reset_value=data['reset_value'], max_voltage=data['max_voltage'], min_voltage=data['min_voltage'],index=index)
            else:
                self.parent_widget.sequence.add_digital_channel(name=data['name'], card_number=data['card_number'], channel_number=data['channel_number'], index=index)
            new_channel = self.parent_widget.sequence.find_channel_by_name(data['name'])
            self.parent_widget.refresh_UI()
            self.parent_widget.parent_widget.event_table.add_channel(new_channel)


    def edit_channel(self):
        # open the edit channel dialog
        if isinstance(self.channel, Analog_Channel):
            dialog = Edit_Analog_Channel(self.channel)
        else:
            dialog = Edit_Digital_Channel(self.channel)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if isinstance(self.channel, Digital_Channel):
                self.parent_widget.sequence.edit_digital_channel(name=self.channel.name,new_name=data['name'], card_number=data['card_number'], channel_number=data['channel_number'])
            else: 
                self.parent_widget.sequence.edit_analog_channel(name=self.channel.name,new_name=data['name'], card_number=data['card_number'], channel_number=data['channel_number'], reset_value=data['reset_value'], max_voltage=data['max_voltage'], min_voltage=data['min_voltage'])
            self.parent_widget.refresh_UI()
            
        
    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        delete_action = context_menu.addAction("Delete Channel")
        delete_action.triggered.connect(self.delete_channel)
        add_action = context_menu.addAction("Add Channel")
        add_action.triggered.connect(self.add_channel)
        edit_action = context_menu.addAction("Edit Channel")
        edit_action.triggered.connect(self.edit_channel)
        context_menu.exec_(event.globalPos())


from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

class ChannelLabelListWidget(QWidget):
    def __init__(self, sequence:Sequence, parent_widget:'SequenceViewerWdiget'=None):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.sequence = sequence
        self.buttons = []
        self.setup_UI()
        
    def setup_UI(self):
        self.layout = QVBoxLayout(self)
        
        self.scroll_area = ScrollAreaWithShiftScroll(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.inner_widget = QWidget()
        self.inner_layout = QVBoxLayout(self.inner_widget)

        self.scroll_area.setWidget(self.inner_widget)
        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)
        
        self.refresh_UI()
        
    def refresh_UI(self):
        for button in self.buttons:
            self.inner_layout.removeWidget(button)
            button.deleteLater()
        
        self.buttons = []
        
        for channel in self.sequence.channels:
            button = ChannelButton(channel,self)
            self.buttons.append(button)
            button.setFixedHeight(50)
            self.inner_layout.addWidget(button)
        
        self.inner_widget.setLayout(self.inner_layout)




from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDialog

class EventButton(QWidget):
    def __init__(self, channel: Channel, time_instance: TimeInstance, parent_widget: 'EventsWidget'):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.channel = channel
        self.time_instance = time_instance

        # Initialize the layout
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        # Initial call to set up the UI
        self.refresh_UI()

    def get_col(self):
        layout = self.parent_widget.inner_layout
        for col in range(layout.columnCount()):
            if layout.itemAtPosition(1, col + 1).widget().time_instance.name == self.time_instance.name:
                return col + 1
        return None

    def get_row(self):
        layout = self.parent_widget.inner_layout
        for row in range(layout.rowCount()):
            if layout.itemAtPosition(row + 1, 1).widget().channel.name == self.channel.name:
                return row + 1
        return None

    def refresh_UI(self):
        # Clear the current layout
        for i in reversed(range(self.layout.count())):
            widget_to_remove = self.layout.itemAt(i).widget()
            self.layout.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)

        # Check if the time instance contains any events in the channel
        ramp_value = self.channel.detect_a_ramp(self.time_instance)
        if ramp_value is not None:
            ramp = ramp_value[0]
            value = ramp_value[1]
            # Add a label to display the value
            value_label = QLabel(f'Ramp {ramp.behavior.ramp_type}: {value}')
            self.layout.addWidget(value_label)
            return

        event_time = self.channel.get_event_by_time_instance(self.time_instance)
        if event_time is None:
            all_events = self.channel.events
            all_events.sort(key=lambda event: event.start_time_instance.get_absolute_time())
            for i, event in enumerate(all_events):
                if event.start_time_instance.get_absolute_time() > self.time_instance.get_absolute_time():
                    break
            else:
                i = len(all_events)
            if i == 0:
                value = self.channel.reset_value
            else:
                value = all_events[i-1].behavior.get_value_at_time(self.time_instance.get_absolute_time())
            value_button = QPushButton(f'Value: {value}')
            value_button.clicked.connect(self.add_event)
            # Add a button to display the value and connect to the create event when clicked 
            self.layout.addWidget(value_button)
        else:
            event = event_time[0]
            time_ref = event_time[1]
            if isinstance(event.behavior, Ramp):
                if time_ref == 'start':
                    value = event.behavior.start_value
                    # Create a vertical layout with a label and numeric value spin box
                    value_layout = QVBoxLayout()
                    # add a combobox to select the ramp type
                    ramp_combo = QComboBox()
                    ramp_combo.addItems([e.value for e in RampType])
                    preselected_ramp_type = event.behavior.ramp_type.value
                    ramp_combo.setCurrentText(preselected_ramp_type)
                    ramp_combo.currentIndexChanged.connect(lambda index: self.edit_ramp_type(event))
                    value_layout.addWidget(ramp_combo)
                    value_label = QLabel('Start Value:')
                    value_spinbox = QDoubleSpinBox()
                    # make the range of the spin box between the min and max voltage of the channel
                    value_spinbox.setRange(self.channel.min_voltage, self.channel.max_voltage)
                    value_spinbox.setValue(value)
                    value_spinbox.valueChanged.connect(lambda val: self.edit_start_value(event, val))
                    value_layout.addWidget(value_label)
                    value_layout.addWidget(value_spinbox)
                    self.layout.addLayout(value_layout)
                else:
                    value = event.behavior.end_value
                    # Create a vertical layout with a label and numeric value spin box
                    value_layout = QVBoxLayout()
                    value_label = QLabel('End Value:')
                    value_spinbox = QDoubleSpinBox()
                    # make the range of the spin box between the min and max voltage of the channel
                    value_spinbox.setRange(self.channel.min_voltage, self.channel.max_voltage)
                    value_spinbox.setValue(value)
                    value_spinbox.valueChanged.connect(lambda val: self.edit_end_value(event, val))
                    value_layout.addWidget(value_label)
                    value_layout.addWidget(value_spinbox)
                    self.layout.addLayout(value_layout)
            elif isinstance(event.behavior, Jump):
                value = event.behavior.target_value
                # Create a vertical layout with a label and numeric value spin box
                value_layout = QVBoxLayout()
                value_label = QLabel('Target Value:')
                value_spinbox = QDoubleSpinBox()
                value_spinbox.setRange(self.channel.min_voltage, self.channel.max_voltage)
                value_spinbox.setValue(value)
                value_spinbox.valueChanged.connect(lambda val: self.edit_target_value(event, val))
                value_layout.addWidget(value_label)
                value_layout.addWidget(value_spinbox)
                self.layout.addLayout(value_layout)
            elif isinstance(event.behavior, Digital):
                value = event.behavior.target_value
                combo_box = QComboBox()
                combo_box.addItems(['Off', 'On'])
                combo_box.setCurrentIndex(1 if value == 1 else 0)
                self.layout.addWidget(combo_box)
                # Create a combo box to display the value and connect to the target value (On =1 , Off = 0)
                # Connect it to edit target value
                combo_box.currentIndexChanged.connect(lambda index: self.edit_target_value(event, index))
            # Connect to delete event

    def edit_start_value(self, event, value):
        self.parent_widget.sequence.edit_event_behavior(edited_event=event, start_value=value)
        self.refresh_row_after_me()
        # Make a deep copy of the event behavior

    def edit_end_value(self, event, value):
        self.parent_widget.sequence.edit_event_behavior(edited_event=event, end_value=value)
        self.refresh_row_after_me()
        self.refresh_row_after_me()
        self.refresh_row_before_me()
        self.refresh_row_before_me()

        # Make a deep copy of the event behavior

    def edit_target_value(self, event, value):
        self.parent_widget.sequence.edit_event_behavior(edited_event=event, target_value=value)
        # Make a deep copy of the event behavior

    def edit_ramp_type(self,event):
        value = RampType(self.sender().currentText())
        self.parent_widget.sequence.edit_event_behavior(edited_event=event, ramp_type=value)
        self.refresh_row_after_me()
        # Make a deep copy of the event behavior

    def add_event(self):
        # Add an event to the time instance and channel 
        if isinstance(self.channel, Analog_Channel):
            dialog = AnalogEventDialog(self.channel, self.time_instance)
        else:
            dialog = DigitalEventDialog(self.channel, self.time_instance)
        dialog.add_ok_cancel_buttons()
        if dialog.exec_() == QDialog.Accepted:
            behavior = dialog.get_behavior()
            if isinstance(self.channel, Analog_Channel):
                if behavior['behavior_type'] == 'Ramp':
                    behavior_instance = Ramp(behavior['ramp_type'], behavior['start_value'], behavior['end_value'], behavior['ramp_duration'], behavior['resolution'],comment= behavior['comment'])
                
                elif behavior['behavior_type'] == 'Jump':
                    behavior_instance = Jump(behavior['jump_target_value'])
                    self.parent_widget.sequence.add_event(self.channel.name,behavior_instance, self.time_instance,comment= behavior['comment'])
            else:
                behavior_instance = Digital(behavior['state'])
                self.parent_widget.sequence.add_event(self.channel.name,behavior_instance, self.time_instance,comment= behavior['comment'])
            self.refresh_UI()
        self.refresh_row_after_me()

    def delete_event(self):
        # Delete the event from the time instance and channel
        self.parent_widget.sequence.delete_event(self.channel.name, self.time_instance.name)
        self.refresh_UI()
        self.refresh_row_after_me()
    
    def refresh_row_after_me(self):
        row = self.get_row()
        col = self.get_col()
        # loop over the columns and refresh the UI
        for i in range(col+1, self.parent_widget.inner_layout.columnCount()):
            item = self.parent_widget.inner_layout.itemAtPosition(row, i)
            if item is not None:
                try:
                    widget = item.widget()
                    widget.refresh_UI()
                except Exception as e:
                    pass
    def refresh_row_before_me(self):
        row = self.get_row()
        col = self.get_col()
        # loop over the columns and refresh the UI
        for i in range(col-1, 0, -1):
            item = self.parent_widget.inner_layout.itemAtPosition(row, i)
            if item is not None:
                try:
                    widget = item.widget()
                    widget.refresh_UI()
                except Exception as e:
                    pass

from typing import Dict, Tuple
class EventsWidget(QWidget):
    def __init__(self, sequence: Sequence, parent_widget: 'SequenceViewerWdiget' = None):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.sequence = sequence
        self.time_instances = []
        self.setup_UI()

    def setup_UI(self):
        self.layout = QGridLayout(self)
        
        self.scroll_area = ScrollAreaWithShiftScroll(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.inner_widget = QWidget()
        self.inner_layout = QGridLayout(self.inner_widget)
        
        self.time_instances = self.sequence.root_time_instance.get_all_time_instances()
        self.time_instances.sort(key=lambda ti: ti.get_absolute_time())

        channels = self.sequence.channels
        max_width = 0
        fixed_width = 200
        fixed_height = 60
        # Calculate the maximum width and height required for the buttons
        for row, channel in enumerate(channels):
            for col, time in enumerate(self.time_instances):
                button = EventButton(channel, time, self)
                self.inner_layout.addWidget(button, row , col )
                self.inner_layout.setColumnMinimumWidth(col,fixed_width)
                self.inner_layout.setRowMinimumHeight(row,fixed_height)

        self.inner_widget.setLayout(self.inner_layout)
        self.scroll_area.setWidget(self.inner_widget)
        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)

    def get_row(self, channel: Channel) -> int:
        for row in range(self.inner_layout.rowCount()):
            try:
                if self.inner_layout.itemAtPosition(row, 1).widget().channel == channel:
                    return row
            except Exception as e:
                pass
        return None
    def get_col(self, time_instance: TimeInstance) -> int:
        for col in range(self.inner_layout.columnCount()): 
            try:
                if self.inner_layout.itemAtPosition(1, col).widget().time_instance == time_instance:
                    return col
            except Exception as e:
                pass
        return None
    def get_shape(self):
        # itereate over the layout and get the shape of the grid
        max_row = 0
        max_col = 0
        for row in range(self.inner_layout.rowCount()):
            if self.inner_layout.itemAtPosition(row, 1) is not None:
                max_row = row
        for col in range(self.inner_layout.columnCount()):
            if self.inner_layout.itemAtPosition(1, col) is not None:
                max_col = col
            
        return max_row, max_col
    
    
    def add_channel(self, channel: Channel):
        # check for the index of the channel
        index = self.sequence.channels.index(channel)
        # add the channel to the layout by shifting the rows down
        n_rows, n_cols = self.get_shape()
        for i in range(n_rows+1, index+1):
            for j in range(n_cols+1):
                item = self.inner_layout.itemAtPosition(i, j)
                if item is not None:
                    widget = item.widget()
                    self.inner_layout.removeWidget(widget)
                    self.inner_layout.addWidget(widget, i+1, j)
        # add the channel to the layout by looping over the time instances
        for i, time_instance in enumerate(self.sequence.root_time_instance.get_all_time_instances()):
            button = EventButton(channel, time_instance, self)
            self.inner_layout.addWidget(button, index+1, i+1)
        




    
    def delete_channel(self, channel: Channel):
        # get the row of the channel 
        row = self.get_row(channel=channel)
        if row is not None:
            for i in range(self.inner_layout.columnCount()):
                item = self.inner_layout.itemAtPosition(row, i)
                if item is not None:
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                        self.inner_layout.removeWidget(widget)
                        
            # Shift remaining widgets up
            for r in range(row + 1, self.inner_layout.rowCount()):
                for c in range(self.inner_layout.columnCount()):
                    item = self.inner_layout.itemAtPosition(r, c)
                    if item is not None:
                        widget = item.widget()
                        self.inner_layout.removeWidget(widget)
                        self.inner_layout.addWidget(widget, r - 1, c)
    def delete_time_instance(self, time_instance):
        # get the column of the time instance 
        col = self.get_col(time_instance=time_instance)
        if col is not None:
            for i in range(self.inner_layout.rowCount()):
                item = self.inner_layout.itemAtPosition(i, col)
                if item is not None:
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                        self.inner_layout.removeWidget(widget)
                        
            # Shift remaining widgets left
            for c in range(col + 1, self.inner_layout.columnCount()):
                for r in range(self.inner_layout.rowCount()):
                    item = self.inner_layout.itemAtPosition(r, c)
                    if item is not None:
                        widget = item.widget()
                        self.inner_layout.removeWidget(widget)
                        self.inner_layout.addWidget(widget, r, c - 1)
        self.order_UI()
    
    
    def add_time_instance(self, time_instance: TimeInstance):
        # figure out the right place to add the time instance
        current_time_instances = [self.inner_layout.itemAtPosition(1, i).widget().time_instance for i in range(1, self.inner_layout.columnCount())]
        n_rows, n_cols = self.get_shape()
        # look for the right place to add the time instance
        for i, current_time_instance in enumerate(current_time_instances):
            if time_instance.get_absolute_time() < current_time_instance.get_absolute_time():
                break
        else:
            i = n_cols
        
        #  shift the columns to the right if needed
        if i < n_cols:
            for j in range(n_rows+1):
                for k in range(n_cols+1, i, -1):
                    item = self.inner_layout.itemAtPosition(j+1, k)
                    if item is not None:
                        widget = item.widget()
                        self.inner_layout.removeWidget(widget)
                        self.inner_layout.addWidget(widget, j+1, k + 1)
        # add a dummy button for the new time instance

        # add the time instance for each channel
        for j, channel in enumerate(self.sequence.channels):
            button = EventButton(channel, time_instance, self)
            self.inner_layout.addWidget(button, j+1 , i+1)
        
        self.order_UI()
            
    def order_UI(self):
        # get the shape of the grid
        n_row, n_col = self.get_shape()
        # get the time instances
        current_time_instances = [self.inner_layout.itemAtPosition(1, i).widget().time_instance for i in range(1, n_col+1)]
        target_time_instances = self.sequence.root_time_instance.get_all_time_instances()
        target_time_instances.sort(key=lambda ti: ti.get_absolute_time())
        # make a dictionary of column current index and target index
        col_map = {}
        for i, current_time_instance in enumerate(current_time_instances):
            target_time_instance = target_time_instances[i]
            col_map[current_time_instance] = target_time_instance
        # iterate over the layout and reorder the time instances
        for i in range(1, n_col+1):
            current_time_instance = self.inner_layout.itemAtPosition(1, i).widget().time_instance
            target_time_instance = col_map[current_time_instance]
            if current_time_instance != target_time_instance:
                # get the index of the target time instance
                target_index = target_time_instances.index(target_time_instance)
                # shift the columns to the right if needed
                for j in range(n_row+1):
                    for k in range(n_col+1, target_index, -1):
                        item = self.inner_layout.itemAtPosition(j+1, k)
                        if item is not None:
                            widget = item.widget()
                            self.inner_layout.removeWidget(widget)
                            self.inner_layout.addWidget(widget, j+1, k + 1)
                # reorder the time instance for each channel
                for j in range(1, n_row+1):
                    item = self.inner_layout.itemAtPosition(j, i)
                    if item is not None:
                        widget = item.widget()
                        self.inner_layout.removeWidget(widget)
                        self.inner_layout.addWidget(widget, j, target_index+1)


class SequenceViewerWdiget(QWidget):
    def __init__(self, sequence:Sequence, parent_widget=None):
        super().__init__()
        self.parent_widget = parent_widget
        self.sequence = sequence
        self.syncing = False  # Flag to prevent multiple updates
        self.layout_main = QGridLayout()
        
        self.setLayout(self.layout_main)
        self.combo_box_type = QComboBox()


        self.setup_ui()
        
    def setup_ui(self) -> None:
        
        
        # Create and configure widgets
        self.channel_list = ChannelLabelListWidget(self.sequence,parent_widget=self)
        self.event_table = EventsWidget(self.sequence, parent_widget=self)

        self.time_axis = TimeInstanceWidget(self.sequence.root_time_instance, parent_widget=self)

        


        self.scroll_bar1 = self.channel_list.scroll_area.verticalScrollBar()
        self.scroll_bar2 = self.event_table.scroll_area.verticalScrollBar()
        self.scroll_bar1.valueChanged.connect(self.sync_scroll)
        self.scroll_bar2.valueChanged.connect(self.sync_scroll)

        self.scroll_bar3 = self.event_table.scroll_area.horizontalScrollBar()
        self.scroll_bar4 = self.time_axis.scroll_area.horizontalScrollBar()
        self.scroll_bar3.valueChanged.connect(self.sync_scroll_vertical)
        self.scroll_bar4.valueChanged.connect(self.sync_scroll_vertical)




        self.layout_main.addWidget(self.combo_box_type, 0, 0)
        self.layout_main.addWidget(self.time_axis, 0, 1)  # Top-right slot
        self.layout_main.addWidget(self.channel_list, 1, 0)  # Bottom-left slot
        self.layout_main.addWidget(self.event_table, 1, 1)  # Bottom-right slot
        self.layout_main.setColumnStretch(1, 1)  # Column 0 will take up 1 part of the available space
        self.layout_main.setRowStretch(1, 1)  # Row 1 will take up 1 part of the available space
        

    def refresh_channels(self):
        self.channel_list.refresh_UI()
        self.time_axis.refresh_UI()

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


    def refresh_UI(self):
        layout = self.layout()
        for i in reversed(range(layout.count())):
            widget_to_remove = layout.itemAt(i).widget()
            layout.removeWidget(widget_to_remove)
            widget_to_remove.setParent(None)
        self.setup_ui()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Create the main window
    DFM_ToF = creat_test()
    window = SequenceViewerWdiget(DFM_ToF)
    window.show()
    sys.exit(app.exec_())

