import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QScrollArea, QLabel, QHBoxLayout, QScrollBar
from PyQt5.QtCore import Qt

class ScrollAreaWithTopScrollBar(QWidget):
    def __init__(self):
        super().__init__()

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Horizontal Scrollbar on Top")
        self.setGeometry(100, 100, 600, 200)

        # Main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        # Custom scroll area with top scrollbar
        scroll_area_with_top_scrollbar = ScrollAreaWithTopScrollBar()

        # Content widget to be scrolled
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)

        # Add content to the content widget
        for i in range(20):
            label = QLabel(f"Label {i+1}")
            content_layout.addWidget(label)

        content_widget.setLayout(content_layout)

        # Set the content widget in the custom scroll area
        scroll_area_with_top_scrollbar.setWidget(content_widget)

        # Add the custom scroll area to the main layout
        main_layout.addWidget(scroll_area_with_top_scrollbar)

        # Set the main widget as the central widget of the QMainWindow
        self.setCentralWidget(main_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
