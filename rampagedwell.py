import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout, QMenuBar, QAction
from PyQt5.QtCore import Qt

class MainSequenceViewer(QWidget):
    def __init__(self, parent=None):
        super(MainSequenceViewer, self).__init__(parent)
        self.layout = QVBoxLayout()
        self.menu_bar = QMenuBar(self)
        
        self.file_menu = self.menu_bar.addMenu('Files')
        self.tools_menu = self.menu_bar.addMenu('Tools')
        
        self.file_action = QAction('Open', self)
        self.file_menu.addAction(self.file_action)
        
        self.tools_action = QAction('Settings', self)
        self.tools_menu.addAction(self.tools_action)
        
        self.layout.setMenuBar(self.menu_bar)
        self.setLayout(self.layout)

class PlotViewer(QWidget):
    def __init__(self, parent=None):
        super(PlotViewer, self).__init__(parent)
        self.layout = QVBoxLayout()
        self.menu_bar = QMenuBar(self)
        
        self.file_menu = self.menu_bar.addMenu('Files')
        self.tools_menu = self.menu_bar.addMenu('Tools')
        
        self.file_action = QAction('Open', self)
        self.file_menu.addAction(self.file_action)
        
        self.tools_action = QAction('Settings', self)
        self.tools_menu.addAction(self.tools_action)
        
        self.layout.setMenuBar(self.menu_bar)
        self.setLayout(self.layout)

class SweeperViewer(QWidget):
    def __init__(self, parent=None):
        super(SweeperViewer, self).__init__(parent)
        self.layout = QVBoxLayout()
        self.menu_bar = QMenuBar(self)
        
        self.file_menu = self.menu_bar.addMenu('Files')
        self.tools_menu = self.menu_bar.addMenu('Tools')
        
        self.file_action = QAction('Open', self)
        self.file_menu.addAction(self.file_action)
        
        self.tools_action = QAction('Settings', self)
        self.tools_menu.addAction(self.tools_action)
        
        self.layout.setMenuBar(self.menu_bar)
        self.setLayout(self.layout)

class OptimizationWindow(QWidget):
    def __init__(self, parent=None):
        super(OptimizationWindow, self).__init__(parent)
        self.layout = QVBoxLayout()
        self.menu_bar = QMenuBar(self)
        
        self.file_menu = self.menu_bar.addMenu('Files')
        self.tools_menu = self.menu_bar.addMenu('Tools')
        
        self.file_action = QAction('Open', self)
        self.file_menu.addAction(self.file_action)
        
        self.tools_action = QAction('Settings', self)
        self.tools_menu.addAction(self.tools_action)
        
        self.layout.setMenuBar(self.menu_bar)
        self.setLayout(self.layout)

class Imaging(QWidget):
    def __init__(self, parent=None):
        super(Imaging, self).__init__(parent)
        self.layout = QVBoxLayout()
        self.menu_bar = QMenuBar(self)
        
        self.file_menu = self.menu_bar.addMenu('Files')
        self.tools_menu = self.menu_bar.addMenu('Tools')
        
        self.file_action = QAction('Open', self)
        self.file_menu.addAction(self.file_action)
        
        self.tools_action = QAction('Settings', self)
        self.tools_menu.addAction(self.tools_action)
        
        self.layout.setMenuBar(self.menu_bar)
        self.setLayout(self.layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        
        self.setWindowTitle('PyQt5 GUI')
        self.setGeometry(100, 100, 1000, 800)
        
        self.main_widget = QWidget()
        self.main_layout = QGridLayout(self.main_widget)
        
        self.main_sequence_viewer = MainSequenceViewer(self)
        self.plot_viewer = PlotViewer(self)
        self.sweeper_viewer = SweeperViewer(self)
        self.optimization_window = OptimizationWindow(self)
        self.imaging = Imaging(self)
        
        self.main_layout.addWidget(self.main_sequence_viewer, 0, 0, 4, 2)
        self.main_layout.addWidget(self.imaging, 4, 0, 4, 2)
        
        self.main_layout.addWidget(self.plot_viewer, 0, 2, 4, 1)
        self.main_layout.addWidget(self.optimization_window, 4, 2, 2, 1)
        self.main_layout.addWidget(self.sweeper_viewer, 6, 2, 2, 1)
        
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)
        
        self.menu_bar = self.menuBar()
        
        self.file_menu = self.menu_bar.addMenu('Files')
        self.tools_menu = self.menu_bar.addMenu('Tools')
        
        self.file_action = QAction('Open', self)
        self.file_menu.addAction(self.file_action)
        
        self.tools_action = QAction('Settings', self)
        self.tools_menu.addAction(self.tools_action)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
