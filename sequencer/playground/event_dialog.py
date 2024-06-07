import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QDialog, QMessageBox, QFormLayout, QComboBox, QLineEdit, QDialogButtonBox

# Assuming Event, Channel, EventBehavior, Ramp, Jump are defined as per your previous code
# If these are not available, we will define some mock versions for testing

from event import Event, Channel,Ramp, Analog_Channel,Digital_Channel,Sequence,Jump # Assuming these are defined in a module named event
# AddEventDialog class from your refined code
class AddEventDialog(QDialog):
    def __init__(self, channel, behaviors, parent=None):
        super().__init__(parent)
        self.channel = channel
        self.behaviors = behaviors
        
        self.setWindowTitle("Add Child Event")
        self.layout = QFormLayout(self)
        
        self.behavior_type = QComboBox(self)
        self.behavior_type.addItems([behavior.__class__.__name__ for behavior in self.behaviors])
        self.behavior_type.currentIndexChanged.connect(self.update_fields_visibility)
        self.layout.addRow("Behavior Type:", self.behavior_type)
        
        self.duration = QLineEdit(self)
        self.layout.addRow("Duration (for Ramp):", self.duration)
        
        self.relative_time = QLineEdit(self)
        self.layout.addRow("Relative Time:", self.relative_time)
        
        self.reference_time = QLineEdit(self)
        self.layout.addRow("Reference Time:", self.reference_time)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.create_event)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
        
        self.update_fields_visibility()

    def update_fields_visibility(self):
        selected_behavior = self.behavior_type.currentText()
        if selected_behavior == "Ramp":
            self.duration.setVisible(True)
        else:
            self.duration.setVisible(False)
            self.duration.clear()

    # def create_event(self):
    #     try:
    #         behavior_name = self.behavior_type.currentText()
    #         behavior = next(behavior for behavior in self.behaviors if behavior.__class__.__name__ == behavior_name)
            
    #         start_time = None
    #         if isinstance(behavior, Ramp):
    #             duration = self.duration.text()
    #             if not duration:
    #                 raise ValueError("Duration is required for Ramp behavior.")
    #             duration = float(duration)
    #             behavior.duration = duration

    #         relative_time = self.relative_time.text()
    #         reference_time = self.reference_time.text() or "start"
    #         relative_time = float(relative_time) if relative_time else None
            
    #         if reference_time not in ["start", "end"]:
    #             raise ValueError("Invalid reference time. Use 'start' or 'end'.")
            
    #         new_event = Event(
    #             channel=self.channel,
    #             behavior=behavior,
    #             relative_time=relative_time,
    #             reference_time=reference_time,
    #             parent=None  # Modify as needed for parent events
    #         )
            
    #         QMessageBox.information(self, "Success", f"Event created: {new_event}", QMessageBox.Ok)
    #         self.accept()  # Close the dialog
    #         return new_event
        
    #     except ValueError as e:
    #         QMessageBox.critical(self, "Input Error", str(e), QMessageBox.Ok)
    #     except Exception as e:
    #         QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}", QMessageBox.Ok)

    def get_data(self):
        return {
            "behavior_type": self.behavior_type.currentText(),
            "duration": float(self.duration.text()) if self.duration.text() else None,
            "relative_time": float(self.relative_time.text()) if self.relative_time.text() else None,
            "reference_time": self.reference_time.text() or "start"
        }

def main():
    app = QApplication(sys.argv)
    
    # Create a main window
    main_window = QMainWindow()
    main_window.setWindowTitle("Event Dialog Test")
    
    # Create a central widget with a layout
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    # Create a button to open the dialog
    button = QPushButton("Add Event")
    layout.addWidget(button)
    
    # Set the central widget
    main_window.setCentralWidget(central_widget)
    
    # Create a mock channel and behaviors
    # channel = Channel("Channel 1")
    # behaviors = [Ramp(), Jump()]
    
    def open_dialog():
        dialog = AddEventDialog( main_window)
        if dialog.exec() == QDialog.Accepted:
            # Event creation was successful
            new_event = dialog.create_event()
            if new_event:
                print("New Event Created:", new_event)
    
    # Connect the button to the dialog
    button.clicked.connect(open_dialog)
    
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
