
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

class TimeInstanceWidget(QWidget):
    def __init__(self, root_time_instance: 'TimeInstance', parent_widget=None):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.root_time_instance = root_time_instance
        self.setWindowTitle('Time Instance Visualization')
        self.setGeometry(100, 100, 1000, 600)
        self.time_instances = self.root_time_instance.get_all_time_instances()
        self.time_instances.sort(key=lambda ti: ti.get_absolute_time())

        # Create a container widget to hold the grid layout
        self.inner_widget = QWidget()
        self.grid = QGridLayout(self.inner_widget)
        self.inner_widget.setLayout(self.grid)

        # Add labels to grid for each time instance in the row above arrows
        self.labels = {}
        for i, time_instance in enumerate(self.time_instances):
            label = QLabel(time_instance.name)
            self.grid.addWidget(label, 0, i )  # Place labels in row 0
            self.grid.addWidget(QLabel(str(time_instance.relative_time)), 1, i )  # Place labels in row 1
            self.grid.addWidget(QLabel(str(time_instance.get_absolute_time())), 2, i )  # Place labels in row 1
            
            self.labels[time_instance] = (0, i )

        # Add the arrow widget in row 2
        arrow_list = []
        for time_instance in self.time_instances:
            if time_instance.parent:
                parent_index = self.labels[time_instance.parent][1]   # Adjust parent index
                child_index = self.labels[time_instance][1]   # Adjust child index
                arrow_list.append((parent_index, child_index))

        # Add the arrow widget, which is placed in row 2
        self.arrow_widget = QArrowWidget(arrow_list, self.grid, start_pos=(3, 0), parent=self)
        # change the size of the first column of the grid
        

        # Create a QScrollArea and set the container widget as its widget
        self.scroll_area = ScrollAreaWithShiftScroll()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.inner_widget)

        # Create a layout for TimeInstanceWidget and add the scroll area
        layout = QVBoxLayout()
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

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
        for row in range(layout.rowCount()-1):
            for col in range(layout.columnCount()-1):                                
                if layout.itemAtPosition(row+1, col+1).widget().channel.name == self.channel.name and layout.itemAtPosition(row+1, col+1).widget().time_instance.name == self.time_instance.name:
                    print('row:',row+1)
                    print('col:',col+1)
                    return row+1, col+1
        return None, None

    def delete_row(self):
        self.parent_widget.sequence.delete_channel(self.channel.name)
        layout = self.parent_widget.inner_layout
        row, col = self.get_row_and_col()
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
        row, col = self.get_row_and_col()
        if col is not None:
            for i in range(layout.rowCount()):
                item = layout.itemAtPosition(i, col)
                if item is not None:
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                        layout.removeWidget(widget)
                        
            # Shift remaining widgets up
            for c in range(col + 1, layout.columnCount()):
                for r in range(layout.rowCount()):
                    item = layout.itemAtPosition(r, c)
                    if item is not None:
                        widget = item.widget()
                        layout.removeWidget(widget)
                        layout.addWidget(widget, r, c - 1)
            self.parent_widget.parent_widget.time_axis.refresh_UI()

    
    # def remove_row(self):
    #     # get the layout of the parent widget
    #     layout = self.parent_widget.inner_layout
    
# gridLayout = QGridLayout(widget)

# # Row index to remove
# row_index = 1  # Adjust as needed

# # Remove widgets from the specified row
# for col in range(gridLayout.columnCount()):
#     item = gridLayout.itemAtPosition(row_index, col)
#     if item is not None:
#         widget = item.widget()
#         if widget is not None:
#             widget.deleteLater()  # Delete the widget

# # Shift items in the layout to reflect the removal
# gridLayout.removeRow(row_index)



class EventsWidget(QWidget):
    def __init__(self, sequence:Sequence, parent_widget:'SequenceViewerWdiget' = None):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.layout = QGridLayout(self)
        
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.inner_widget = QWidget()
        self.inner_layout = QGridLayout(self.inner_widget)
        
        self.buttons = {}
        self.sequence = sequence
        time_instances = self.sequence.get_all_time_instances()
        channels = self.sequence.channels
        
        # Add channel names and event buttons
        for row, channel in enumerate(channels):
            for col, time in enumerate(time_instances):
                button = EventButton(channel, time,self)
                self.buttons[(row, col)] = button
                self.inner_layout.addWidget(button, row + 1, col + 1)
        
        self.inner_widget.setLayout(self.inner_layout)
        self.scroll_area.setWidget(self.inner_widget)
        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)





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
        self.data_table = EventsWidget(self.sequence, parent_widget=self)

        self.time_axis = TimeInstanceWidget(self.sequence.root_time_instance, parent_widget=self)

        


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

