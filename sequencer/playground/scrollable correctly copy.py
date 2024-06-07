from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QScrollBar, QHBoxLayout, QLabel, QScrollArea, QGridLayout, QMainWindow
)
from PyQt5.QtCore import Qt

class ScrollAreaWithTopScrollBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        # Custom horizontal scrollbar
        self.horizontal_scrollbar = QScrollBar(Qt.Horizontal)
        layout.addWidget(self.horizontal_scrollbar)

        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable internal horizontal scrollbar
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.scroll_area)

        # Sync the custom scrollbar with the scroll area's horizontal scrollbar
        self.scroll_area.horizontalScrollBar().valueChanged.connect(self.horizontal_scrollbar.setValue)
        self.horizontal_scrollbar.valueChanged.connect(self.scroll_area.horizontalScrollBar().setValue)

    def setWidget(self, widget):
        self.scroll_area.setWidget(widget)
        self.horizontal_scrollbar.setRange(0, self.scroll_area.horizontalScrollBar().maximum())
        self.scroll_area.horizontalScrollBar().rangeChanged.connect(self.horizontal_scrollbar.setRange)

class ChannelGrid(QWidget):
    def __init__(self, channels, values, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channels = channels
        self.values = values

        main_layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()
        for channel in channels:
            left_layout.addWidget(QLabel(channel))
        
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setFixedWidth(150)

        grid_layout = QGridLayout()
        for i, value_set in enumerate(values):
            for j, value in enumerate(value_set):
                grid_layout.addWidget(QLabel(value), i, j)

        grid_widget = QWidget()
        grid_widget.setLayout(grid_layout)

        # Replace the original scroll area with ScrollAreaWithTopScrollBar
        self.scroll_area_with_top_scrollbar = ScrollAreaWithTopScrollBar()
        self.scroll_area_with_top_scrollbar.setWidget(grid_widget)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(self.scroll_area_with_top_scrollbar)

        self.setLayout(main_layout)

class MainWindow(QMainWindow):
    def __init__(self, channels, values, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Resizable Channel Grid")
        self.setGeometry(100, 100, 800, 600)

        # Create the ChannelGrid
        channel_grid = ChannelGrid(channels, values)

        # Create a vertical layout for the central widget
        central_layout = QVBoxLayout()

        # Add the custom horizontal scrollbar to the central layout
        central_layout.addWidget(channel_grid.scroll_area_with_top_scrollbar.horizontal_scrollbar)

        # Add the ChannelGrid to the central layout
        central_layout.addWidget(channel_grid)

        # Create a central widget and set the layout
        central_widget = QWidget()
        central_widget.setLayout(central_layout)

        # Set the central widget of the MainWindow
        self.setCentralWidget(central_widget)

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    channels = [f"Channel {i}" for i in range(1, 21)]
    values = [[f"Value {i}.{j}" for j in range(1, 11)] for i in range(1, 21)]

    main_window = MainWindow(channels, values)
    main_window.show()

    sys.exit(app.exec_())
