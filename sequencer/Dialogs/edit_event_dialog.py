import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QDialogButtonBox
)
from PyQt5.QtGui import QDoubleValidator


from sequencer.event import Event, Ramp, Jump, RampType,Sequence,SequenceManager, create_test_sequence

# Assuming Channel and EventBehavior classes are defined elsewhere

class EditEventDialog(QDialog):
    def __init__(self,  event):
        super().__init__()

        self.layout = QVBoxLayout()

        # Channel
        self.channel_label = QLabel("Channel:")
        self.channel_label = QLabel(event.channel.name)

        self.layout.addWidget(self.channel_label)
        self.layout.addWidget(self.channel_label)

        # Behavior type
        self.behavior_type = type(event.behavior).__name__
        self.behavior_label = QLabel("Behavior Type:")
        self.behavior_label.setText(f"Behavior Type: {self.behavior_type}")
        self.layout.addWidget(self.behavior_label)

        # Target value for Jump
        if self.behavior_type == "Jump":
            self.target_value_label = QLabel("Target Value (for Jump):")
            self.target_value_input = QLineEdit()
            self.target_value_input.setValidator(QDoubleValidator())
            self.layout.addWidget(self.target_value_label)
            self.layout.addWidget(self.target_value_input)

        # Ramp parameters
        if self.behavior_type == "Ramp":
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

            self.ramp_type_label = QLabel("Ramp Type (for Ramp):")
            self.ramp_type_combo = QComboBox()
            self.ramp_type_combo.addItems(["linear","quadratic","exponential","logarithmic","generic","minimum jerk"])
            self.layout.addWidget(self.ramp_type_label)
            self.layout.addWidget(self.ramp_type_combo)

        # Event-specific fields
        if event.parent is not None:
            self.setWindowTitle("Edit Child Event Data")
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

        else:
            self.setWindowTitle("Edit Root Event Data")
            # Start time
            self.start_time_label = QLabel("Start Time:")
            self.start_time_input = QLineEdit()
            self.start_time_input.setValidator(QDoubleValidator())
            self.layout.addWidget(self.start_time_label)
            self.layout.addWidget(self.start_time_input)

        self.setLayout(self.layout)
        self.add_ok_cancel_buttons()

        # Load event data if provided
        self.load_event_data(event)

    def add_ok_cancel_buttons(self):
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def load_event_data(self, event):

        
        if self.behavior_type == "Jump":
            self.target_value_input.setText(str(event.behavior.target_value))
        elif self.behavior_type == "Ramp":
            self.ramp_duration_input.setText(str(event.behavior.duration))
            self.start_value_input.setText(str(event.behavior.start_value))
            self.end_value_input.setText(str(event.behavior.end_value))
            self.ramp_type_combo.setCurrentText(str(event.behavior.ramp_type))

        if event.parent is not None:
            self.relative_time_input.setText(str(event.relative_time))
            self.reference_time_combo.setCurrentText(event.reference_time)
        else:
            self.start_time_input.setText(str(event.start_time))

    def get_data(self):
        behavior_data = {}
        if self.behavior_type == "Jump":
            behavior_data['target_value'] = float(self.target_value_input.text())
        elif self.behavior_type == "Ramp":
            behavior_data['duration'] = float(self.ramp_duration_input.text())
            behavior_data['start_value'] = float(self.start_value_input.text())
            behavior_data['end_value'] = float(self.end_value_input.text())
            behavior_data['ramp_type'] = self.ramp_type_combo.currentText()

        data = {

            'behavior_type': self.behavior_type,
            'behavior_data': behavior_data
        }

        if hasattr(self, 'start_time_input'):
            data['start_time'] = float(self.start_time_input.text())
        else:
            data['relative_time'] = float(self.relative_time_input.text())
            data['reference_time'] = self.reference_time_combo.currentText()
        
        return data
import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox,
    QLineEdit, QDialogButtonBox, QMessageBox
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator
import numpy as np



class SweepEventDialog(QDialog):
    def __init__(self, event):
        super().__init__()

        self.setWindowTitle('Parameter Sweep Dialog')

        self.event = event

        # Check event behavior and hierarchy
        self.is_jump = isinstance(event.behavior, Jump)
        self.is_ramp = isinstance(event.behavior, Ramp)
        self.is_root = event.parent is None
        self.is_child = not self.is_root

        # Main layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Form layout
        self.form_layout = QFormLayout()
        self.layout.addLayout(self.form_layout)

        # Parameter name combo box
        self.parameter_name_label = QLabel("Parameter Name:")
        self.parameter_name_combo = QComboBox()

        if self.is_jump:
            self.parameter_name_combo.addItems(["jump_target_value"])
        elif self.is_ramp:
            self.parameter_name_combo.addItems([
                "duration", "ramp_type", "start_value", "end_value", "func", "resolution"
            ])

        if self.is_child:
            self.parameter_name_combo.addItems(["relative_time", "reference_time"])
        elif self.is_root:
            self.parameter_name_combo.addItems(["start_time"])

        self.form_layout.addRow(self.parameter_name_label, self.parameter_name_combo)

        # Sweep type combo box
        self.sweep_type_label = QLabel("Sweep Type:")
        self.sweep_type_combo = QComboBox()
        self.sweep_type_combo.addItems([
            "Linear Sweep", "Logarithmic Sweep", "Geometric Sweep", "Custom Sequence Sweep"
        ])
        self.sweep_type_combo.currentIndexChanged.connect(self.update_sweep_settings)
        self.form_layout.addRow(self.sweep_type_label, self.sweep_type_combo)

        # Sweep settings fields
        self.sweep_settings_layout = QFormLayout()
        self.layout.addLayout(self.sweep_settings_layout)
        self.sweep_settings_widgets = {}

        self.update_sweep_settings()

        # Dialog buttons (OK and Cancel)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def update_sweep_settings(self):
        # Clear current sweep settings
        self.clear_layout(self.sweep_settings_layout)
        self.sweep_settings_widgets.clear()

        # Add new settings fields based on selected sweep type
        sweep_type = self.sweep_type_combo.currentText()

        if sweep_type == "Linear Sweep":
            self.add_sweep_setting("Start:", "start", QDoubleValidator())
            self.add_sweep_setting("End:", "end", QDoubleValidator())
            self.add_sweep_setting("Step Size:", "step_size", QDoubleValidator())
        elif sweep_type == "Logarithmic Sweep":
            self.add_sweep_setting("Start:", "start", QDoubleValidator())
            self.add_sweep_setting("End:", "end", QDoubleValidator())
            self.add_sweep_setting("Base:", "base", QDoubleValidator())
        elif sweep_type == "Geometric Sweep":
            self.add_sweep_setting("Start:", "start", QDoubleValidator())
            self.add_sweep_setting("End:", "end", QDoubleValidator())
            self.add_sweep_setting("Factor:", "factor", QDoubleValidator())
        elif sweep_type == "Custom Sequence Sweep":
            self.add_sweep_setting("Custom Sequence (comma-separated):", "custom_sequence", None)

    def add_sweep_setting(self, label_text, setting_key, validator):
        label = QLabel(label_text)
        line_edit = QLineEdit()
        if validator:
            line_edit.setValidator(validator)
        self.sweep_settings_layout.addRow(label, line_edit)
        self.sweep_settings_widgets[setting_key] = line_edit

    def accept(self):
        parameter_name = self.parameter_name_combo.currentText()
        sweep_type = self.sweep_type_combo.currentText()
        settings = {key: widget.text() for key, widget in self.sweep_settings_widgets.items()}

        try:
            values = self.generate_sweep_values(sweep_type, settings)
            self.result = (parameter_name, values,sweep_type, settings)
            super().accept()
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))

    def generate_sweep_values(self, sweep_type, settings):
        if sweep_type == "Linear Sweep":
            start = float(settings.get("start", 0))
            end = float(settings.get("end", 0))
            step_size = float(settings.get("step_size", 1))
            return list(np.arange(start, end + step_size, step_size))
        elif sweep_type == "Logarithmic Sweep":
            start = float(settings.get("start", 1))
            end = float(settings.get("end", 1))
            base = float(settings.get("base", 10))
            if start <= 0 or end <= 0:
                raise ValueError("Logarithmic Sweep requires positive start and end values.")
            num_points = int(np.log(end / start) / np.log(base)) + 1
            return list(start * np.power(base, np.arange(num_points)))
        elif sweep_type == "Geometric Sweep":
            start = float(settings.get("start", 1))
            end = float(settings.get("end", 1))
            factor = float(settings.get("factor", 2))
            if start <= 0 or end <= 0 or factor <= 0:
                raise ValueError("Geometric Sweep requires positive start, end, and factor values.")
            values = []
            current = start
            while current <= end:
                values.append(current)
                current *= factor
            return values
        elif sweep_type == "Custom Sequence Sweep":
            sequence = settings.get("custom_sequence", "")
            try:
                values = list(map(float, sequence.split(',')))
            except ValueError:
                raise ValueError("Custom Sequence must contain valid floating point numbers separated by commas.")
            return values
        else:
            raise ValueError("Invalid sweep type.")

    def get_result(self):
        return getattr(self, 'result', None)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Example event initialization
    seq= create_test_sequence("test")
    example_event = seq.all_events[0]
    dialog = SweepEventDialog(example_event)
    if dialog.exec_() == QDialog.Accepted:
        result = dialog.get_result()
        if result:
            parameter_name, values = result
            print(f"Parameter: {parameter_name}")
            print(f"Sweep Values: {values}")
        else:
            print("No result")
    else:
        print("Dialog canceled")

    sys.exit(app.exec_())



if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    seq= create_test_sequence("test")



    for trail_event in seq.all_events:
        
        # For testing the EditEventDialog for root event
        edit_dialog = EditEventDialog( event=trail_event)
        if edit_dialog.exec_() == QDialog.Accepted:
            edited_data = edit_dialog.get_data()
            print(edited_data)


    # sys.exit(app.exec_())


