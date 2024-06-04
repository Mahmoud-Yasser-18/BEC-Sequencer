from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QGridLayout, QSizePolicy, QMainWindow
)
from PyQt5.QtCore import Qt

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

        right_layout = QVBoxLayout()
        grid_layout = QGridLayout()
        for i, value_set in enumerate(values):
            for j, value in enumerate(value_set):
                grid_layout.addWidget(QLabel(value), i, j)

        grid_widget = QWidget()
        grid_widget.setLayout(grid_layout)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(grid_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

class MainWindow(QMainWindow):
    def __init__(self, channels, values, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Resizable Channel Grid")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)

        self.scrollable_channel_grid = QWidget()
        scrollable_layout = QVBoxLayout(self.scrollable_channel_grid)
        self.channel_grid = ChannelGrid(channels, values)
        scrollable_layout.addWidget(self.channel_grid)

        vertical_scroll_area = QScrollArea()
        vertical_scroll_area.setWidget(self.scrollable_channel_grid)
        vertical_scroll_area.setWidgetResizable(True)
        vertical_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        vertical_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        layout.addWidget(vertical_scroll_area)

        self.setLayout(layout)

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    channels = [f"Channel {i}" for i in range(1, 21)]
    values = [[f"Value {i}.{j}" for j in range(1, 11)] for i in range(1, 21)]

    main_window = MainWindow(channels, values)
    main_window.show()

    sys.exit(app.exec_())
