# Filename: synced_table_widget.py

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QListWidget, QScrollBar, QSizePolicy
)
from PyQt5.QtCore import Qt

class SyncedTableWidget(QWidget):
    def __init__(self, channels, data):
        super().__init__()

        # Initialize channels and data
        self.channels = channels
        self.data = data

        # Create the channel names list
        self.channel_list = QListWidget()
        for channel in channels:
            self.channel_list.addItem(channel)

        # Calculate the width for the channel list based on the longest channel name
        longest_channel_name = max(channels, key=len)
        font_metrics = self.channel_list.fontMetrics()
        channel_width = font_metrics.horizontalAdvance(longest_channel_name) + 50  # Adding some padding
        self.channel_list.setFixedWidth(channel_width)

        # Create the values table
        self.table = QTableWidget(len(channels), len(data[0]))
        self.table.setHorizontalHeaderLabels([f'Time {i}' for i in range(len(data[0]))])

        # Populate the table with data
        for i, channel_data in enumerate(data):
            for j, value in enumerate(channel_data):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))

        # Ensure both widgets have the same height
        self.channel_list.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Synchronize the vertical scroll bars relatively
        self.scroll_bar1 = self.channel_list.verticalScrollBar()
        self.scroll_bar2 = self.table.verticalScrollBar()
        self.scroll_bar1.valueChanged.connect(self.sync_scroll)
        self.scroll_bar2.valueChanged.connect(self.sync_scroll)

        # Layout setup
        layout = QHBoxLayout()
        layout.addWidget(self.channel_list)
        layout.addWidget(self.table)
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

    # Example data
    channels = [f'Channel {i}' for i in range(20)]
    data = [[j for j in range(100)] for i in range(20)]

    window = SyncedTableWidget(channels, data)
    window.show()
    sys.exit(app.exec_())
