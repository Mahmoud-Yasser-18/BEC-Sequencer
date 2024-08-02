
import copy 
from PyQt5.QtWidgets import (
   QComboBox, QApplication, QHBoxLayout,QToolTip,QGridLayout, QMessageBox,QSizePolicy, QDialog,QLabel,QMenu, QPushButton, QWidget, QVBoxLayout, QScrollArea, QScrollBar,QInputDialog
)

from PyQt5.QtCore import Qt, QRect, pyqtSignal,QPoint
from sequencer.ADwin_Modules2 import calculate_time_ranges
from sequencer.time_frame import TimeInstance,Sequence,Event , Analog_Channel, Digital_Channel, Channel, RampType,creat_test
import sys
from typing import List, Optional
from PyQt5.QtWidgets import (
    QApplication, QHBoxLayout, QVBoxLayout, QScrollArea, QScrollBar, QMenuBar,
    QMenu, QAction, QPushButton, QWidget, QLabel, QDialog, QMessageBox, QFileDialog
)


from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QHBoxLayout
from sequencer.time_frame import Sequence, Event, Analog_Channel, Digital_Channel, Channel, RampType,Jump,Ramp
import sys
from PyQt5.QtWidgets import QApplication, QLabel, QSizePolicy, QGridLayout, QWidget
from PyQt5.QtGui import QPainter, QPolygon, QBrush
from PyQt5.QtCore import QPoint, Qt, QSize

from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QScrollArea, QVBoxLayout, QSizePolicy
from PyQt5.QtGui import QPainter, QBrush, QPolygon
from PyQt5.QtCore import QPoint, Qt, QSize

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
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)

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
        size = self.parent_widget.event_table.inner_widget.size()
        self.inner_widget.setMinimumWidth(size.width())


class ChannelLabelListWidget(QWidget):
    def __init__(self, sequence, parent_widget=None):
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
        channels = [ch.name for ch in self.sequence.channels]
        for channel in channels:
            button = QPushButton(channel)
            self.buttons.append(button)
            self.inner_layout.addWidget(button)
        
        self.inner_widget.setLayout(self.inner_layout)


from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QVBoxLayout, QApplication, QScrollArea
from PyQt5.QtCore import Qt

class EventButton(QPushButton):
    def __init__(self, channel:Channel, time_instance:TimeInstance, parent_widget:'EventsWidget'=None):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.channel = channel
        self.time_instance = time_instance

        self.setText(f'{self.channel.name} @ {self.time_instance.name}')
        # self.clicked.connect(self.get_row_and_col)
        self.clicked.connect(self.delete_col)
    def get_row_and_col(self):
        layout = self.parent_widget.inner_layout
        for row in range(layout.rowCount()):
            for col in range(layout.columnCount()):     
                try:
                    if layout.itemAtPosition(row, col).widget().channel.name == self.channel.name and layout.itemAtPosition(row, col).widget().time_instance.name == self.time_instance.name:
                        return row, col
                except Exception as e:
                    pass
        return None, None
    def get_col(self):
        layout = self.parent_widget.inner_layout
        for col in range(layout.columnCount()):
            if layout.itemAtPosition(1, col+1).widget().time_instance.name == self.time_instance.name:
                return col+1
        return
    
    def get_row(self):
        layout = self.parent_widget.inner_layout
        for row in range(layout.rowCount()):
            if layout.itemAtPosition(row+1, 1).widget().channel.name == self.channel.name :
                return row+1
                
        return None
    

    def delete_row(self):
        self.parent_widget.sequence.delete_channel(self.channel.name)
        layout = self.parent_widget.inner_layout
        row = self.get_row()
        if row is not None:
            for i in range(layout.columnCount()):
                item = layout.itemAtPosition(row, i)
                if item is not None:
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                        layout.removeWidget(widget)
                        
            # Shift remaining widgets up
            for r in range(row + 1, layout.rowCount()):
                for c in range(layout.columnCount()):
                    item = layout.itemAtPosition(r, c)
                    if item is not None:
                        widget = item.widget()
                        layout.removeWidget(widget)
                        layout.addWidget(widget, r - 1, c)
            self.parent_widget.parent_widget.channel_list.refresh_UI()
    def delete_col(self):
        self.parent_widget.sequence.delete_time_instance(self.time_instance.name)
        layout = self.parent_widget.inner_layout
        col = self.get_col()
        if col is not None:
            for i in range(layout.rowCount()):
                item = layout.itemAtPosition(i, col)
                if item is not None:
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                        layout.removeWidget(widget)
                        
            # Shift remaining widgets left
            for c in range(col + 1, layout.columnCount()):
                for r in range(layout.rowCount()):
                    item = layout.itemAtPosition(r, c)
                    if item is not None:
                        widget = item.widget()
                        layout.removeWidget(widget)
                        layout.addWidget(widget, r, c - 1)
            self.parent_widget.parent_widget.time_axis.refresh_UI()
from typing import Dict, Tuple
class EventsWidget(QWidget):
    def __init__(self, sequence: Sequence, parent_widget: 'SequenceViewerWdiget' = None):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.sequence = sequence
        self.buttons = {}
        self.time_instances = []
        self.setup_UI()

    def setup_UI(self):
        self.layout = QGridLayout(self)
        
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.inner_widget = QWidget()
        self.inner_layout = QGridLayout(self.inner_widget)
        
        self.time_instances = self.sequence.root_time_instance.get_all_time_instances()
        self.time_instances.sort(key=lambda ti: ti.get_absolute_time())

        channels = self.sequence.channels
        self.buttons: Dict[Tuple[int, int], EventButton] = {}
        # Add channel names and event buttons
        for row, channel in enumerate(channels):
            for col, time in enumerate(self.time_instances):
                button = EventButton(channel, time, self)
                self.buttons[(row, col)] = button
                self.inner_layout.addWidget(button, row + 1, col + 1)
        
        self.inner_widget.setLayout(self.inner_layout)
        self.scroll_area.setWidget(self.inner_widget)
        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)

    def refresh_UI(self):
        pass
        # loops through all the buttons and deletes time instances that has no parents except the root time instance
        

    def order_UI(self):
        pass 



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

