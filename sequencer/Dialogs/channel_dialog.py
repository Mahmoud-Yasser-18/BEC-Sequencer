from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QFormLayout, QDialogButtonBox
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator
import sys 

# Add this class to the Dialogs/channel_dialog.py file
class ChannelDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Add Channel')
        self.layout = QFormLayout(self)

        self.type_combo = QComboBox(self)
        self.type_combo.addItems(['Analog', 'Digital'])
        self.type_combo.currentIndexChanged.connect(self.update_form)

        self.name_edit = QLineEdit(self)
        self.card_number_edit = QLineEdit(self)
        self.card_number_edit.setValidator(QIntValidator())
        self.channel_number_edit = QLineEdit(self)
        self.channel_number_edit.setValidator(QIntValidator())
        self.reset_value_edit = QLineEdit(self)
        self.reset_value_edit.setValidator(QDoubleValidator())

        self.layout.addRow('Type:', self.type_combo)
        self.layout.addRow('Name:', self.name_edit)
        self.layout.addRow('Card Number:', self.card_number_edit)
        self.layout.addRow('Channel Number:', self.channel_number_edit)
        self.layout.addRow('Reset Value:', self.reset_value_edit)

        # Analog-specific fields
        self.max_voltage_edit = QLineEdit(self)
        self.max_voltage_edit.setValidator(QDoubleValidator())
        self.min_voltage_edit = QLineEdit(self)
        self.min_voltage_edit.setValidator(QDoubleValidator())
        self.layout.addRow('Max Voltage:', self.max_voltage_edit)
        self.layout.addRow('Min Voltage:', self.min_voltage_edit)

        # Digital-specific fields
        self.card_id_edit = QLineEdit(self)
        self.card_id_edit.setValidator(QIntValidator())
        self.bitpos_edit = QLineEdit(self)
        self.bitpos_edit.setValidator(QIntValidator())
        self.layout.addRow('Card ID:', self.card_id_edit)
        self.layout.addRow('Bit Position:', self.bitpos_edit)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
        self.update_form(self.type_combo.currentIndex())

    def update_form(self, index):
        if index == 0:  # Analog
            self.max_voltage_edit.show()
            self.min_voltage_edit.show()
            self.card_id_edit.hide()
            self.bitpos_edit.hide()
        elif index == 1:  # Digital
            self.max_voltage_edit.hide()
            self.min_voltage_edit.hide()
            self.card_id_edit.show()
            self.bitpos_edit.show()

    def get_data(self):
        data = {
            'type': self.type_combo.currentText(),
            'name': self.name_edit.text(),
            'card_number': int(self.card_number_edit.text()),
            'channel_number': int(self.channel_number_edit.text()),
            'reset_value': float(self.reset_value_edit.text())
        }
        if data['type'] == 'Analog':
            data['max_voltage'] = float(self.max_voltage_edit.text())
            data['min_voltage'] = float(self.min_voltage_edit.text())
        elif data['type'] == 'Digital':
            data['card_id'] = int(self.card_id_edit.text())
            data['bitpos'] = int(self.bitpos_edit.text())
        return data



if __name__ == "__main__":
    app = QApplication(sys.argv)


    
    # For testing the RootEventDialog
    root_dialog = ChannelDialog()
    if root_dialog.exec_() == QDialog.Accepted:
        root_data = root_dialog.get_data()
        print(root_data)

