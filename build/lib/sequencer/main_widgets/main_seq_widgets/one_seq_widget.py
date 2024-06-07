# Filename: synced_table_widget.py

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QListWidget, QScrollBar, QSizePolicy
)
from PyQt5.QtCore import Qt

class ChannelListWidget(QListWidget):
    def __init__(self, channels):
        super().__init__()
        self.channels = channels
        self.setup_ui()

    def setup_ui(self):
        for channel in self.channels:
            self.addItem(channel)

        longest_channel_name = max(self.channels, key=len)
        font_metrics = self.fontMetrics()
        channel_width = font_metrics.horizontalAdvance(longest_channel_name) + 50  # Adding some padding
        self.setFixedWidth(channel_width)

class DataTableWidget(QTableWidget):
    def __init__(self, data):
        super().__init__(len(data), len(data[0]))
        self.data = data
        self.setup_ui()

    def setup_ui(self):
        self.setHorizontalHeaderLabels([f'Time {i}' for i in range(len(self.data[0]))])

        for i, channel_data in enumerate(self.data):
            for j, value in enumerate(channel_data):
                self.setItem(i, j, QTableWidgetItem(str(value)))

class SyncedTableWidget(QWidget):
    def __init__(self, channels, data):
        super().__init__()

        self.channel_list = ChannelListWidget(channels)
        self.data_table = DataTableWidget(data)

        self.channel_list.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.data_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.scroll_bar1 = self.channel_list.verticalScrollBar()
        self.scroll_bar2 = self.data_table.verticalScrollBar()
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

if __name__ == '__main__':
    app = QApplication(sys.argv)

    channels = [f'Channel {i}' for i in range(20)]
    data = [[j for j in range(100)] for i in range(20)]

    window = SyncedTableWidget(channels, data)
    window.show()
    sys.exit(app.exec_())
