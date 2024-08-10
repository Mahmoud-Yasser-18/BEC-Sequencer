
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QVBoxLayout, QApplication, QScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
   QComboBox, QApplication, QHBoxLayout,QToolTip,QDialogButtonBox,QGridLayout, QMessageBox,QSizePolicy, QDialog,QLabel,QMenu, QPushButton, QWidget, QVBoxLayout, QScrollArea, QScrollBar,QInputDialog
)
from sequencer.time_frame import Event, Channel, TimeInstance
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel
from PyQt5.QtGui import QPainter, QPolygon, QBrush,QDoubleValidator

class AnalogEventDialog(QDialog):
    def __init__(self,channal:Channel, time_instance:TimeInstance):
        super().__init__()
        
        self.layout = QVBoxLayout()

        # Channel
        self.channel_label = QLabel("Channel:")
        self.channel_label_value = QLabel(channal.name)
        self.layout.addWidget(self.channel_label)
        self.layout.addWidget(self.channel_label_value)

        # Time instance
        self.time_instance_label = QLabel("Time Instance:")
        self.time_instance_label_value = QLabel(time_instance.name)
        self.layout.addWidget(self.time_instance_label)
        self.layout.addWidget(self.time_instance_label_value)


        self.comment_label = QLabel("Description of the event:")
        self.comment_text = QLineEdit()
        self.layout.addWidget(self.comment_label)
        self.layout.addWidget(self.comment_text)

        # Behavior type
        self.behavior_label = QLabel("Behavior Type:")
        self.behavior_combo = QComboBox()
        self.behavior_combo.addItems(["Jump", "Ramp"])
        self.layout.addWidget(self.behavior_label)
        self.layout.addWidget(self.behavior_combo)

        # Target value for Jump
        self.target_value_label = QLabel("Target Value (for Jump):")
        self.target_value_input = QLineEdit()
        self.target_value_input.setValidator(QDoubleValidator())
        self.layout.addWidget(self.target_value_label)
        self.layout.addWidget(self.target_value_input)

        # Ramp parameters
        self.ramp_duration_label = QLabel("Ramp Duration (for Ramp):")
        self.ramp_duration_input = QLineEdit()
        self.ramp_duration_input.setValidator(QDoubleValidator())
        self.layout.addWidget(self.ramp_duration_label)
        self.layout.addWidget(self.ramp_duration_input)

        self.start_value_label = QLabel("Start Value (for Ramp):")
        self.start_value_input = QLineEdit()
        self.start_value_input.setValidator(QDoubleValidator())
        self.layout.addWidget(self.start_value_label)
        self.layout.addWidget(self.start_value_input)

        self.end_value_label = QLabel("End Value (for Ramp):")
        self.end_value_input = QLineEdit()
        self.end_value_input.setValidator(QDoubleValidator())
        self.layout.addWidget(self.end_value_label)
        self.layout.addWidget(self.end_value_input)

        self.resoltion_label = QLabel("Resolution (for Ramp):")
        self.resoltion_input = QLineEdit()
        self.resoltion_input.setValidator(QDoubleValidator())
        self.layout.addWidget(self.resoltion_label)
        self.layout.addWidget(self.resoltion_input)

        self.ramp_type_label = QLabel("Ramp Type (for Ramp):")
        self.ramp_type_combo = QComboBox()
        self.ramp_type_combo.addItems(["linear","quadratic","exponential","logarithmic","generic","minimum jerk"])
        self.layout.addWidget(self.ramp_type_label)
        self.layout.addWidget(self.ramp_type_combo)



        self.behavior_combo.currentIndexChanged.connect(self.update_behavior_fields)




        self.setLayout(self.layout)
        self.update_behavior_fields()


    def add_ok_cancel_buttons(self):
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def update_behavior_fields(self):
        is_jump = self.behavior_combo.currentText() == "Jump"
        self.target_value_label.setVisible(is_jump)
        self.target_value_input.setVisible(is_jump)
        self.ramp_duration_label.setVisible(not is_jump)
        self.ramp_duration_input.setVisible(not is_jump)
        self.start_value_label.setVisible(not is_jump)
        self.start_value_input.setVisible(not is_jump)
        self.end_value_label.setVisible(not is_jump)
        self.end_value_input.setVisible(not is_jump)
        self.ramp_type_label.setVisible(not is_jump)
        self.ramp_type_combo.setVisible(not is_jump)
        self.resoltion_label.setVisible(not is_jump)
        self.resoltion_input.setVisible(not is_jump)
        self.adjustSize()

    def get_behavior(self):
        behavior_type = self.behavior_combo.currentText()
        
        if behavior_type == "Jump":
            jump_target_value = self.target_value_input.text()
            behavior_params = {
                'behavior_type': behavior_type,
                'jump_target_value': float(jump_target_value),
                'ramp_duration': None,
                'ramp_type': None,
                'start_value': None,
                'end_value': None,
                'comment': self.comment_text.text()
            }
        else:
            ramp_duration = self.ramp_duration_input.text()
            ramp_type = self.ramp_type_combo.currentText().lower()
            start_value = self.start_value_input.text()
            end_value = self.end_value_input.text()
            resolution = self.resoltion_input.text()
            behavior_params = {
                'behavior_type': behavior_type,
                'jump_target_value': None,
                'ramp_duration': float(ramp_duration),
                'ramp_type': ramp_type,
                'start_value': float (start_value),
                'end_value': float (end_value),
                'resolution': float(resolution),
                'comment': self.comment_text.text()

            }
        
        return behavior_params

class DigitalEventDialog(QDialog):
    def __init__(self,channal:Channel, time_instance:TimeInstance):
        super().__init__()
        
        self.layout = QVBoxLayout()

        # Channel
        self.channel_label = QLabel("Channel:")
        self.channel_label_value = QLabel(channal.name)
        self.layout.addWidget(self.channel_label)
        self.layout.addWidget(self.channel_label_value)

        # Time instance
        self.time_instance_label = QLabel("Time Instance:")
        self.time_instance_label_value = QLabel(time_instance.name)
        self.layout.addWidget(self.time_instance_label)
        self.layout.addWidget(self.time_instance_label_value)
        
        self.comment_label = QLabel("Description of the event:")
        self.comment_text = QLineEdit()
        self.layout.addWidget(self.comment_label)
        self.layout.addWidget(self.comment_text)

        # Behavior type
        # Target value for Jump
        self.target_value_label = QLabel("State:") # high or low from combobox
        self.target_value_combo = QComboBox()
        self.target_value_combo.addItems(["high", "low"])
        self.layout.addWidget(self.target_value_label)
        self.layout.addWidget(self.target_value_combo)
        self.setLayout(self.layout)
    
    def add_ok_cancel_buttons(self):
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
