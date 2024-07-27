import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox,QDialogButtonBox,QMessageBox,QHBoxLayout
)
from PyQt5.QtGui import QDoubleValidator

class ParameterDialog(QDialog):
    def __init__(self, possible_parameters, parent=None):
        super(ParameterDialog, self).__init__(parent)

        self.possible_parameters = possible_parameters

        self.setWindowTitle("Add Parameter")

        # Layout
        layout = QVBoxLayout()

        # Dropdown for parameter names
        self.comboBox = QComboBox()
        self.comboBox.addItems(self.possible_parameters.keys())
        layout.addWidget(QLabel("Select the parameter to add:"))
        layout.addWidget(self.comboBox)

        # Text box for new name
        self.newNameLineEdit = QLineEdit()
        layout.addWidget(QLabel("Enter the parameter name:"))
        layout.addWidget(self.newNameLineEdit)

        # OK and Cancel buttons
        self.okButton = QPushButton("OK")
        self.cancelButton = QPushButton("Cancel")
        self.okButton.setEnabled(False)  # Initially disable the OK button
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        layout.addWidget(self.okButton)
        layout.addWidget(self.cancelButton)

        self.setLayout(layout)

        # Connect the textChanged signal to a slot
        self.newNameLineEdit.textChanged.connect(self.check_input)

    def check_input(self):
        if self.newNameLineEdit.text().strip():
            self.okButton.setEnabled(True)
        else:
            self.okButton.setEnabled(False)

    def getInputs(self):
        return self.comboBox.currentText(), self.newNameLineEdit.text()



class BaseEventDialog(QDialog):
    def __init__(self, channels):
        super().__init__()
        
        self.layout = QVBoxLayout()

        # Channel
        self.channel_label = QLabel("Channel:")
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(channels)
        self.layout.addWidget(self.channel_label)
        self.layout.addWidget(self.channel_combo)

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

class RootEventDialog(BaseEventDialog):
    def __init__(self, channels):
        super().__init__(channels)
        self.setWindowTitle("Root Event Data Input Dialog")

        # Start time
        self.start_time_label = QLabel("Start Time:")
        self.start_time_input = QLineEdit()
        self.start_time_input.setValidator(QDoubleValidator())
        self.layout.addWidget(self.start_time_label)
        self.layout.addWidget(self.start_time_input)
        self.add_ok_cancel_buttons()

    def get_data(self):
        data = {

            'behavior': self.get_behavior(),
            'start_time': float(self.start_time_input.text()),
            'relative_time': None,
            'reference_time': None
        }
        return data

class RemoveParameterDialog(QDialog):
    def __init__(self, parent=None, parameters=None):
        super(RemoveParameterDialog, self).__init__(parent)
        self.parent_widget = parent
        self.parameters = parameters
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Remove Parameter')

        layout = QVBoxLayout()

        self.label = QLabel('Select the parameter name to remove:')
        layout.addWidget(self.label)

        self.combo_box = QComboBox()
        self.combo_box.addItems([p.name for p in self.parameters])
        layout.addWidget(self.combo_box)

        button_layout = QHBoxLayout()

        self.ok_button = QPushButton('OK')
        self.ok_button.clicked.connect(self.remove_parameter)
        button_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def remove_parameter(self):
        parameter_name = self.combo_box.currentText()
        try:
            self.parent_widget.sequence.remove_parameter(parameter_name=parameter_name)
            self.accept()  # Close the dialog
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)
            self.parent_widget.refreshUI()


class ChildEventDialog(BaseEventDialog):
    def __init__(self, channels):
        super().__init__(channels)
        self.setWindowTitle("Child Event Data Input Dialog")

        # Relative time
        self.relative_time_label = QLabel("Relative Time:")
        self.relative_time_input = QLineEdit()
        self.relative_time_input.setValidator(QDoubleValidator())
        self.layout.addWidget(self.relative_time_label)
        self.layout.addWidget(self.relative_time_input)

        # Reference time
        self.reference_time_label = QLabel("Reference Time:")
        self.reference_time_combo = QComboBox()
        self.reference_time_combo.addItems(["start", "end"])
        self.layout.addWidget(self.reference_time_label)
        self.layout.addWidget(self.reference_time_combo)
        self.add_ok_cancel_buttons()

    def get_data(self):
        data = {
            'channel': self.channel_combo.currentText(),
            'behavior': self.get_behavior(),
            'start_time': None,
            'relative_time': float(self.relative_time_input.text()),
            'reference_time': self.reference_time_combo.currentText()
        }
        return data

if __name__ == "__main__":
    app = QApplication(sys.argv)

    channels = ["Channel 1", "Channel 2", "Channel 3"]
    
    # For testing the RootEventDialog
    root_dialog = RootEventDialog(channels)
    if root_dialog.exec_() == QDialog.Accepted:
        root_data = root_dialog.get_data()
        print(root_data)

    # For testing the ChildEventDialog
    child_dialog = ChildEventDialog(channels)
    if child_dialog.exec_() == QDialog.Accepted:
        child_data = child_dialog.get_data()
        print(child_data)

    sys.exit(app.exec_())
