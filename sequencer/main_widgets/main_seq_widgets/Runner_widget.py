from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QListWidget, QListWidgetItem, QAbstractItemView, QMessageBox
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, 
    QListWidgetItem, QProgressBar, QInputDialog, QMessageBox, QAbstractItemView
)
from PyQt5.QtCore import Qt
from collections import OrderedDict
from typing import List, Optional

from sequencer.event import SequenceManager

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QListWidget, QListWidgetItem, QAbstractItemView, QMessageBox
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QListWidget, QListWidgetItem, QAbstractItemView, QMessageBox, QApplication, QMenu
from PyQt5.QtCore import Qt, QPoint

class CustomSequenceWidget(QWidget):
    def __init__(self, sequence_manager):
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
        self.run_selected_sequences_button = QPushButton("Run Selected Sequences")
        self.run_selected_sequences_button.clicked.connect(self.run_selected_sequences)
        buttons_layout.addWidget(self.run_selected_sequences_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

        self.setStyleSheet("""
            QWidget {
                background-color: #2e2e2e;
                color: #f0f0f0;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QComboBox, QListWidget, QPushButton {
                background-color: #3e3e3e;
                border: 1px solid #f0f0f0;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #606060;
            }
            QListWidget::item {
                border: 1px solid #f0f0f0;
                border-radius: 3px;
                margin: 3px;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #505050;
                color: #ffffff;
            }
        """)

    def add_sequence_to_list(self):
        sequence_name = self.sequence_combo_box.currentText()
        if sequence_name:
            self.selected_sequences_list.addItem(sequence_name)

    def run_selected_sequences(self):
        sequence_names = [self.selected_sequences_list.item(i).text() for i in range(self.selected_sequences_list.count())]
        try:
            custom_sequence = self.sequence_manager.get_custom_sequence(sequence_names)
            self.run_sequence(custom_sequence)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def run_sequence(self, sequence):
        # Placeholder for running the sequence; replace with actual logic
        print(f"Running sequence: {sequence.sequence_name}")
        self.parent().progress_bar.setValue(100)

    def show_context_menu(self, position: QPoint):
        context_menu = QMenu(self)
        remove_action = context_menu.addAction("Remove")
        action = context_menu.exec_(self.selected_sequences_list.mapToGlobal(position))

        if action == remove_action:
            item = self.selected_sequences_list.itemAt(position)
            self.selected_sequences_list.takeItem(self.selected_sequences_list.row(item))



class Runner(QWidget):
    def __init__(self, sequence_manager: SequenceManager):
        super().__init__()
        self.sequence_manager = sequence_manager
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Run Main Button
        self.run_main_button = QPushButton("Run Main")
        self.run_main_button.clicked.connect(self.run_main)
        layout.addWidget(self.run_main_button)

        # Run Custom Sequence Widget
        self.custom_sequence_widget = CustomSequenceWidget(self.sequence_manager)
        layout.addWidget(self.custom_sequence_widget)

        # Run Sweep Button
        self.run_sweep_button = QPushButton("Run Sweep")
        self.run_sweep_button.clicked.connect(self.run_sweep)
        layout.addWidget(self.run_sweep_button)

        # Progress Bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        self.setWindowTitle('Runner Widget')
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #f0f0f0;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QPushButton {
                background-color: #3e3e3e;
                border: 1px solid #f0f0f0;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #606060;
            }
            QProgressBar {
                background-color: #3e3e3e;
                border: 1px solid #f0f0f0;
                border-radius: 5px;
                text-align: center;
                padding: 5px;
            }
            QProgressBar::chunk {
                background-color: #00bfff;
            }
        """)
        self.show()

    def run_main(self):
        try:
            main_sequence = self.sequence_manager.get_main_sequence()
            self.run_sequence(main_sequence)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def run_sweep(self):
        try:
            sweep_sequences = self.sequence_manager.get_sweep_sequences()
            for seq in sweep_sequences:
                self.run_sequence(seq)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def run_sequence(self, sequence):
        # Placeholder for running the sequence; replace with actual logic
        print(f"Running sequence: {sequence.sequence_name}")
        self.progress_bar.setValue(100)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    sequence_manager = SequenceManager()
    sequence_manager.add_new_sequence("Seq1")
    sequence_manager.add_new_sequence("Seq2")
    sequence_manager.add_new_sequence("Seq3")
    runner = Runner(sequence_manager)
    sys.exit(app.exec_())

