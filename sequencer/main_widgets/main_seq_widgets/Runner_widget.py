from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QListWidget, QListWidgetItem, QAbstractItemView, QMessageBox
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QTableWidget,
    QListWidgetItem, QProgressBar, QInputDialog, QMessageBox, QAbstractItemView,QTableWidgetItem
)
from PyQt5.QtCore import Qt
from collections import OrderedDict
from typing import List, Optional
from PyQt5.QtCore import QTimer


from sequencer.event import SequenceManager
from sequencer.ADwin_Modules import ADwin_Driver

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QListWidget, QListWidgetItem, QAbstractItemView, QMessageBox
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QListWidget, QListWidgetItem, QAbstractItemView, QMessageBox, QApplication, QMenu
from PyQt5.QtCore import Qt, QPoint
class ParameterListWidget(QWidget):
    def __init__(self, parameters=None, parent=None):
        super(ParameterListWidget, self).__init__(parent)
        if parameters is None:
            parameters = dict()
        # Create the main layout
        self.layout = QVBoxLayout()

        # Create the QTableWidget
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["Parameter", "Value"])

        # Populate the table with parameter names and values
        self.populate_table(parameters)

        # Add the QTableWidget to the layout
        self.layout.addWidget(self.table_widget)

        # Add a button to demonstrate updating parameters

        # Set the layout for the widget
        self.setLayout(self.layout)

    def populate_table(self, parameters):
        """Populates the QTableWidget with parameter names and values."""
        self.table_widget.setRowCount(len(parameters.items()))
        for row, (name, value) in enumerate(parameters.items()):
            self.table_widget.setItem(row, 0, QTableWidgetItem(str(name)))
            self.table_widget.setItem(row, 1, QTableWidgetItem(str(0)))

    def update_parameters(self, new_parameters):
        """Updates the QTableWidget with new parameters."""
        self.populate_table(new_parameters)





class CustomSequenceWidget(QWidget):
    def __init__(self, sequence_manager: SequenceManager):
        super().__init__()
        self.sequence_manager = sequence_manager
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # ComboBox for sequence names
        self.sequence_combo_box = QComboBox()
        for sequence_name in self.sequence_manager.main_sequences.keys():
            self.sequence_combo_box.addItem(sequence_name)
        layout.addWidget(self.sequence_combo_box)

        # ListWidget to display selected sequences
        self.selected_sequences_list = QListWidget()
        self.selected_sequences_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.selected_sequences_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.selected_sequences_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.selected_sequences_list)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Button to add sequences to the list
        self.add_sequence_button = QPushButton("Add Sequence")
        self.add_sequence_button.clicked.connect(self.add_sequence_to_list)
        buttons_layout.addWidget(self.add_sequence_button)

        # Button to run selected sequences


        layout.addLayout(buttons_layout)
        self.setLayout(layout)

        # self.setStyleSheet("""
        #     QWidget {
        #         background-color: #2e2e2e;
        #         color: #f0f0f0;
        #         font-family: Arial, sans-serif;
        #         font-size: 14px;
        #     }
        #     QComboBox, QListWidget, QPushButton {
        #         background-color: #3e3e3e;
        #         border: 1px solid #f0f0f0;
        #         border-radius: 5px;
        #         padding: 5px;
        #     }
        #     QPushButton:hover {
        #         background-color: #505050;
        #     }
        #     QPushButton:pressed {
        #         background-color: #606060;
        #     }
        #     QListWidget::item {
        #         border: 1px solid #f0f0f0;
        #         border-radius: 3px;
        #         margin: 3px;
        #         padding: 5px;
        #     }
        #     QListWidget::item:selected {
        #         background-color: #505050;
        #         color: #ffffff;
        #     }
        # """)

    def add_sequence_to_list(self):
        sequence_name = self.sequence_combo_box.currentText()
        if sequence_name:
            self.selected_sequences_list.addItem(sequence_name)



    def get_sequences_names(self):
        return  [self.selected_sequences_list.item(i).text() for i in range(self.selected_sequences_list.count())]



    def show_context_menu(self, position: QPoint):
        context_menu = QMenu(self)
        remove_action = context_menu.addAction("Remove")
        action = context_menu.exec_(self.selected_sequences_list.mapToGlobal(position))

        if action == remove_action:
            item = self.selected_sequences_list.itemAt(position)
            self.selected_sequences_list.takeItem(self.selected_sequences_list.row(item))

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QProgressBar, QCheckBox,
    QMenuBar, QAction, QMessageBox
)
from PyQt5.QtGui import QIcon
import os 


    


class Runner(QWidget):
    def __init__(self, sequence_manager: SequenceManager):
        super().__init__()
        self.sequence_manager = sequence_manager

        
        
        
        self.save_path = "../data/source"
        self.refreash_sweep_queue()
        print("Here")
        print(self.main_sweep_queue.keys())
        
        
        # create the folder if it does not exist 
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
        self.initUI()
        
        
        
    def boot_ADwin(self):
        # load the default ADwin process
        try:
            self.ADwin = ADwin_Driver()
            # show a message box to inform the user that the ADwin has been booted
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("ADwin")
            msg_box.setText("ADwin booted successfully")
            QTimer.singleShot(2000, msg_box.close)  # Close the message box after 2000 milliseconds (2 seconds)
            msg_box.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def initUI(self):
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create menu bar
        menu_bar = QMenuBar(self)
        tools_menu = menu_bar.addMenu('Tools')
        
        load_adwin_action = QAction('Load ADwin', self)
        load_adwin_action.triggered.connect(self.boot_ADwin)
        tools_menu.addAction(load_adwin_action)

        # Add menu bar to the layout
        main_layout.setMenuBar(menu_bar)

        # Run Main Button
        self.run_main_button = QPushButton("Run Main")
        self.run_main_button.clicked.connect(self.run_main)
        main_layout.addWidget(self.run_main_button)

        # Run Custom Sequence Widget
        self.custom_sequence_widget = CustomSequenceWidget(self.sequence_manager)
        main_layout.addWidget(self.custom_sequence_widget)

        # Run Sweep Button
        self.run_sweep_button = QPushButton("Run Sweep")
        self.run_sweep_button.clicked.connect(self.run_sweep)


        self.combo_sweep = QComboBox()
        self.combo_sweep.addItems(["main","custom"])
        # self.combo_sweep.currentIndexChanged.connect(self.check_sweep)
        self.randomize_queue_button = QPushButton("Randomize")
        self.randomize_queue_button.clicked.connect(self.randomize_queue)


        self.sweep_runner_layout = QHBoxLayout()
        self.sweep_runner_layout.addWidget(self.run_sweep_button)
        self.sweep_runner_layout.addWidget(self.combo_sweep)
        self.sweep_runner_layout.addWidget(self.randomize_queue_button)



        main_layout.addLayout(self.sweep_runner_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)

        print(self.main_sweep_queue)
        self.sweep_viewer =  ParameterListWidget(self.main_sweep_queue)
        
        self.sweep_viewer.populate_table(self.main_sweep_queue)
        main_layout.addWidget(self.sweep_viewer)

        self.setLayout(main_layout)
        self.setWindowTitle('Runner Widget')
        self.setWindowIcon(QIcon('path_to_icon.png'))  # Add path to your icon
        # self.setStyleSheet("""
        #     QWidget {
        #         background-color: #1e1e1e;
        #         color: #f0f0f0;
        #         font-family: Arial, sans-serif;
        #         font-size: 14px;
        #     }
        #     QMenuBar {
        #         background-color: #3e3e3e;
        #         color: #f0f0f0;
        #     }
        #     QMenuBar::item {
        #         background-color: #3e3e3e;
        #         color: #f0f0f0;
        #     }
        #     QMenuBar::item:selected {
        #         background-color: #505050;
        #     }
        #     QPushButton {
        #         background-color: #3e3e3e;
        #         border: 1px solid #f0f0f0;
        #         border-radius: 5px;
        #         padding: 10px;
        #     }
        #     QPushButton:hover {
        #         background-color: #505050;
        #     }
        #     QPushButton:pressed {
        #         background-color: #606060;
        #     }
        #     QProgressBar {
        #         background-color: #3e3e3e;
        #         border: 1px solid #f0f0f0;
        #         border-radius: 5px;
        #         text-align: center;
        #         padding: 5px;
        #     }
        #     QProgressBar::chunk {
        #         background-color: #00bfff;
        #     }
        # """)
        self.show()

    def refreash_sweep_queue(self):
        self.main_sweep_queue =self.sequence_manager.get_sweep_sequences_main()
    
    def refreash_custom_sweep_queue(self):
        self.custom_sweep_queue =self.sequence_manager.get_sweep_sequences_custom(self.custom_sequence_widget.get_sequences_names())
    
    def randomize_queue(self):
        pass



    def run_main(self):
        try:
            main_sequence = self.sequence_manager.get_main_sequence()
            self.run_sequence(main_sequence)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def run_sweep(self):
        try:
            if self.combo_sweep.currentText() == "main":
                sweep_sequences = self.sequence_manager.get_sweep_sequences_main()
                for seq in sweep_sequences:
                    self.run_sequence(seq)
            else:
                sweep_sequences = self.sequence_manager.get_sweep_sequences_custom()
                for seq in sweep_sequences:
                    self.run_sequence(seq)


        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def run_sequence(self, sequence):
        # Placeholder for running the sequence; replace with actual logic
        print(f"Running sequence: {sequence.sequence_name}")
        self.progress_bar.setValue(100)


from sequencer.event import create_test_seq_manager
if __name__ == '__main__':
    app = QApplication(sys.argv)
    sequence_manager = create_test_seq_manager()
    # sequence_manager.add_new_sequence("Seq1")
    # sequence_manager.add_new_sequence("Seq2")
    # sequence_manager.add_new_sequence("Seq3")
    runner = Runner(sequence_manager)
    sys.exit(app.exec_())

