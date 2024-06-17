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
            self.ramp_type_combo.addItems(["LINEAR", "QUADRATIC", "EXPONENTIAL", "LOGARITHMIC"])
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
            self.ramp_type_combo.setCurrentText(event.behavior.ramp_type.name)

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


