import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox,
    QLineEdit, QDialogButtonBox, QMessageBox
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator
import numpy as np

# Assuming you have these classes defined somewhere in your code
class Jump:
    pass

class Ramp:
    pass

class Event:
    def __init__(self, behavior, parent=None):
        self.behavior = behavior
        self.parent = parent

class SweepDialog(QDialog):
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
            self.add_sweep_setting("Custom Sequence (comma-separated):", "custom_sequence", QIntValidator())

    def add_sweep_setting(self, label_text, setting_key, validator):
        label = QLabel(label_text)
        line_edit = QLineEdit()
        line_edit.setValidator(validator)
        self.sweep_settings_layout.addRow(label, line_edit)
        self.sweep_settings_widgets[setting_key] = line_edit

    def accept(self):
        parameter_name = self.parameter_name_combo.currentText()
        sweep_type = self.sweep_type_combo.currentText()
        settings = {key: widget.text() for key, widget in self.sweep_settings_widgets.items()}

        try:
            values = self.generate_sweep_values(sweep_type, settings)
            self.result = (parameter_name, values)
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
            values = list(map(int, sequence.split(',')))
            return values
        else:
            raise ValueError("Invalid sweep type.")

    def get_result(self):
        return getattr(self, 'result', None)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Example event initialization
    example_event = Event(behavior=Ramp(), parent=None)

    dialog = SweepDialog(example_event)
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
