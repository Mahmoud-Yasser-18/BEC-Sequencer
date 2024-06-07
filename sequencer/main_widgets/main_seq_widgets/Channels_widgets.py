import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QScrollArea, QMenu, QAction, QVBoxLayout
from PyQt5.QtCore import Qt, QPoint

class ChannelButton(QWidget):
    def __init__(self, channel_name):
        super().__init__()
        self.channel_name = channel_name
        self.initUI()

    def initUI(self):
        # Create the button
        self.button = QPushButton(self.channel_name, self)
        self.button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.button.customContextMenuRequested.connect(self.showContextMenu)

    def showContextMenu(self, pos):
        # Create the context menu
        context_menu = QMenu(self)
        
        # Add actions to the context menu
        view_action = QAction("View Details", self)
        view_action.triggered.connect(self.viewDetails)
        context_menu.addAction(view_action)
        
        favorite_action = QAction("Add to Favorites", self)
        favorite_action.triggered.connect(self.addToFavorites)
        context_menu.addAction(favorite_action)
        
        # Show the context menu at the cursor's position
        context_menu.exec_(self.button.mapToGlobal(pos))

    def viewDetails(self):
        print(f"Viewing details for {self.channel_name}")

    def addToFavorites(self):
        print(f"Added {self.channel_name} to favorites")

class ChannelButtonWidget(QWidget):
    def __init__(self, channels):
        super().__init__()
        self.initUI(channels)

    def initUI(self, channels):
        # Set up the main layout
        layout = QVBoxLayout()

        # Optional: Add a label
        self.label = QLabel("Channel List:")
        layout.addWidget(self.label)

        # Create a QScrollArea to hold the buttons
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Create a widget to hold the buttons inside the scroll area
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setAlignment(Qt.AlignTop)  # Align buttons to the top

        # Create and add a ChannelButton for each channel
        for channel in channels:
            channel_button = ChannelButton(channel)
            button_layout.addWidget(channel_button.button)

        # Add the button container to the scroll area
        self.scroll_area.setWidget(button_container)

        # Add the scroll area to the main layout
        layout.addWidget(self.scroll_area)

        # Set the layout for the main window
        self.setLayout(layout)

        # Set the window title and size
        self.setWindowTitle('Channels')
        self.resize(300, 400)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Example list of channels
    channels = [
        "BBC News",
        "CNN",
        "Al Jazeera",
        "Discovery Channel",
        "National Geographic",
        "History Channel",
        "Cartoon Network",
        "HBO",
        "Showtime",
        "Netflix",
    ]

    # Create and show the channel button widget
    window = ChannelButtonWidget(channels)
    window.show()

    sys.exit(app.exec_())
