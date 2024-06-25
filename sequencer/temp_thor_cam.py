import sys
import threading
import queue
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QComboBox, QSpinBox, 
                             QFormLayout)
from PyQt5.QtCore import QTimer, Qt,QPoint, QRect
from PyQt5.QtGui import QImage, QPixmap,QPainter 
from PIL import Image
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK, TLCamera, Frame
from thorlabs_tsi_sdk.tl_camera_enums import SENSOR_TYPE, OPERATION_MODE
from thorlabs_tsi_sdk.tl_mono_to_color_processor import MonoToColorProcessorSDK

from PyQt5.QtGui import QImage, QPixmap, QPainter, QFont, QFontMetrics


try:
    # if on Windows, use the provided setup script to add the DLLs folder to the PATH
    from windows_setup import configure_path
    configure_path()
except ImportError:
    configure_path = None



# --- Your provided code classes ---

class ImageAcquisitionThread(threading.Thread):
    def __init__(self, camera):
        super(ImageAcquisitionThread, self).__init__()
        self._camera = camera
        self._camera.exposure_time_us = 1000
        self._camera.gain = 20
        self._previous_timestamp = 0

        if self._camera.camera_sensor_type != SENSOR_TYPE.BAYER:
            self._is_color = False
        else:
            self._mono_to_color_sdk = MonoToColorProcessorSDK()
            self._image_width = self._camera.image_width_pixels
            self._image_height = self._camera.image_height_pixels
            self._mono_to_color_processor = self._mono_to_color_sdk.create_mono_to_color_processor(
                SENSOR_TYPE.BAYER,
                self._camera.color_filter_array_phase,
                self._camera.get_color_correction_matrix(),
                self._camera.get_default_white_balance_matrix(),
                self._camera.bit_depth
            )
            self._is_color = True

        self._bit_depth = camera.bit_depth
        self._camera.image_poll_timeout_ms = 0
        self._image_queue = queue.Queue(maxsize=2)
        self._stop_event = threading.Event()

    def get_output_queue(self):
        return self._image_queue

    def stop(self):
        self._stop_event.set()

    def _get_color_image(self, frame):
        width = frame.image_buffer.shape[1]
        height = frame.image_buffer.shape[0]
        if (width != self._image_width) or (height != self._image_height):
            self._image_width = width
            self._image_height = height
        color_image_data = self._mono_to_color_processor.transform_to_24(frame.image_buffer,
                                                                         self._image_width,
                                                                         self._image_height)
        color_image_data = color_image_data.reshape(self._image_height, self._image_width, 3)
        return Image.fromarray(color_image_data, mode='RGB')

    def _get_image(self, frame):

        scaled_image = frame.image_buffer >> (self._bit_depth - 8)
        return Image.fromarray(scaled_image, mode='L')

    def run(self):
        while not self._stop_event.is_set():
            try:
                frame = self._camera.get_pending_frame_or_null()
                if frame is not None:
                    if self._is_color:
                        pil_image = self._get_color_image(frame)
                    else:

                        pil_image = self._get_image(frame)

                    self._image_queue.put_nowait((pil_image, frame.time_stamp_relative_ns_or_null))
            except queue.Full:
                pass
            except Exception as error:
                print(f"Encountered error: {error}, image acquisition will stop.")
                break
        print("Image acquisition has stopped")
        if self._is_color:
            self._mono_to_color_processor.dispose()
            self._mono_to_color_sdk.dispose()

    def __del__(self):
        self.stop() 
        self.join()

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPainter
import queue

class LiveViewWidget(QWidget):
    def __init__(self, image_queue):
        super(LiveViewWidget, self).__init__()
        self.image_queue = image_queue

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_image)
        self.timer.start(10)

    def update_image(self):
        try:
            # Get the image and timestamp from the queue
            image, timestamp = self.image_queue.get_nowait()

            # Convert the timestamp from microseconds to seconds
            time_seconds = timestamp / 1e6  # Convert microseconds to seconds

            # Convert the PIL image to a QImage
            if image.mode == 'RGB':
                data = image.tobytes("raw", "RGB")
                q_image = QImage(data, image.width, image.height, QImage.Format_RGB888)
            else:  # Grayscale image
                data = image.tobytes("raw", "L")
                q_image = QImage(data, image.width, image.height, QImage.Format_Grayscale8)

            # Create a QPixmap from the QImage
            pixmap = QPixmap.fromImage(q_image)

            # Resize the QPixmap according to the QLabel size, keeping aspect ratio
            scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Create a QPainter object to draw on the scaled QPixmap
            painter = QPainter(scaled_pixmap)

            # Set the font and color for the timestamp
            font = painter.font()
            font.setPointSize(12)  # Set the font size to 12 points for better visibility
            painter.setFont(font)
            painter.setPen(Qt.red)  # Set the text color to red

            # Define the text to draw, formatting the time to 2 decimal places
            text = f"Time: {time_seconds:.2f}s"

            # Define the text position to be in the upper-left corner
            margin_x = 10  # Margin from the left edge
            margin_y = 10  # Margin from the top edge
            text_position = QPoint(margin_x, margin_y + painter.fontMetrics().height())

            # Draw the timestamp text on the pixmap
            painter.drawText(text_position, text)

            # Finish painting
            painter.end()

            # Set the pixmap with the timestamp to the label
            self.image_label.setPixmap(scaled_pixmap)

        except queue.Empty:
            pass

    def resizeEvent(self, event):
        # Call the base class implementation first
        super(LiveViewWidget, self).resizeEvent(event)

        # Update the image to rescale it when the window is resized
        self.update_image()

class THORCAM_HANDLER():
    def __init__(self):
        self.sdk = TLCameraSDK()
        self.camera = None
        self.acquisition_thread = None
        self.camera_mode = None

    def get_camera_list(self):
        return self.sdk.discover_available_cameras()
    
    def open_camera(self, camera_index=None, serial_number=None):
        try:
            if self.camera:
                self.camera.dispose()
        except:
            print('No camera to dispose')

        if camera_index is not None:
            self.camera = self.sdk.open_camera(self.get_camera_list()[camera_index])
        elif serial_number is not None:
            self.camera = self.sdk.open_camera(serial_number)
        
        
    
    def change_mode(self, live_or_trigger):
        self.camera_mode = live_or_trigger
        try:
            self.camera.disarm()
        except:
            print   ('No camera to disarm')

        
        if live_or_trigger.lower() == 'live':
            self.camera.frames_per_trigger_zero_for_unlimited = 0
            self.camera.operation_mode = OPERATION_MODE.SOFTWARE_TRIGGERED
        else:
            self.camera.frames_per_trigger_zero_for_unlimited = 1
            self.camera.operation_mode = OPERATION_MODE.HARDWARE_TRIGGERED
        
        self.camera.arm(2)
        if live_or_trigger.lower() == 'live':
            self.camera.issue_software_trigger()
    
    def set_camera_params(self, exposure_time_us, gain):
        print('Setting camera parameters')
        print(f'Exposure time: {exposure_time_us} us')
        print(f'Gain: {gain}')


        if exposure_time_us < 64:
            exposure_time_us = 64
            print('Minimum exposure time is 64 us')
        if gain < 0:
            gain = 0
            print('Minimum gain is 0')

        if gain > 100:
            gain = 100
            print('Maximum gain is 100')

        try:
            self.camera.exposure_time_us = exposure_time_us
        except:
            print('No camera to set exposure')
        try:    
            self.camera.gain = gain
        except:
            print('No camera to set gain')


    
    def dispose_all_camera_resources(self):
        try:
            self.sdk.dispose()
        except:
            print('No sdk to dispose')
        try:        
            self.camera.dispose()
        except:
            print('No camera to dispose')

    def start_acquisition_thread(self):
        self.kill_acquisition_thread()
        self.acquisition_thread = ImageAcquisitionThread(self.camera)
        self.acquisition_thread.start()
    
    def kill_acquisition_thread(self):
        try:
            if self.acquisition_thread:
                self.acquisition_thread.stop()
                self.acquisition_thread.join()
        except:
            print('No thread to kill')

    def __del__(self):
        self.dispose_all_camera_resources()
        self.kill_acquisition_thread()

# --- Custom PyQt Widget for THORCAM_HANDLER control ---

class ThorCamControlWidget(QWidget):
    def __init__(self, parent=None):
        super(ThorCamControlWidget, self).__init__(parent)

        self.thor_cam = THORCAM_HANDLER()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("ThorCam Control Panel")
        self.resize(800, 600)

        # Layouts
        main_layout = QVBoxLayout()
        controls_layout = QHBoxLayout()
        settings_layout = QFormLayout()

        # Live View
        self.live_view = LiveViewWidget(image_queue=queue.Queue())
        
        # Camera List
        self.camera_list = QComboBox()
        self.refresh_cameras()
        self.camera_list.currentIndexChanged.connect(self.camera_selected)

        # Camera Controls
        self.open_button = QPushButton("Open Camera")
        self.open_button.clicked.connect(self.open_camera)

        self.close_button = QPushButton("Close Camera")
        self.close_button.clicked.connect(self.close_camera)


        # Camera Parameters
        self.exposure_spin = QSpinBox()
        self.exposure_spin.setRange(1, 1000000)
        self.exposure_spin.setValue(1000)

        self.gain_spin = QSpinBox()
        self.gain_spin.setRange(0, 100)
        self.gain_spin.setValue(20)

        self.camera_mode = QComboBox()
        self.camera_mode.addItems([ 'Trigger','Live'])
        self.camera_mode.currentIndexChanged.connect(self.change_mode)


        self.apply_params_button = QPushButton("Apply Parameters")
        self.apply_params_button.clicked.connect(self.apply_params)

        # Adding widgets to layouts
        settings_layout.addRow("Exposure Time (us):", self.exposure_spin)
        settings_layout.addRow("Gain:", self.gain_spin)
        settings_layout.addRow(self.apply_params_button)
        settings_layout.addRow("Camera Mode:", self.camera_mode)

        controls_layout.addWidget(QLabel("Select Camera:"))
        controls_layout.addWidget(self.camera_list)
        controls_layout.addWidget(self.open_button)
        controls_layout.addWidget(self.close_button)


        main_layout.addLayout(controls_layout)
        main_layout.addLayout(settings_layout)
        main_layout.addWidget(self.live_view,2)

        self.setLayout(main_layout)

    def change_mode(self):

        mode = self.camera_mode.currentText()
        try:
            self.thor_cam.change_mode(mode)
        except:
            print('No camera to change mode')
    def refresh_cameras(self):
        self.camera_list.clear()
        cameras = self.thor_cam.get_camera_list()
        self.camera_list.addItems(cameras)
        if cameras:
            self.camera_list.setCurrentIndex(0)

    def camera_selected(self, index):
        # self.open_camera()
        pass
    def open_camera(self):
        index = self.camera_list.currentIndex()
        if index >= 0:
            self.thor_cam.open_camera(camera_index=index)
            self.thor_cam.change_mode(self.camera_mode.currentText())
            self.thor_cam.start_acquisition_thread()
            self.live_view.image_queue = self.thor_cam.acquisition_thread.get_output_queue()
            self.live_view.timer.start(10)
            print('Camera opened')


    def close_camera(self):
        self.thor_cam.camera.dispose()
        self.live_view.timer.stop()

    def apply_params(self):
        exposure_time_us = self.exposure_spin.value()
        gain = self.gain_spin.value()
        self.thor_cam.set_camera_params(exposure_time_us, gain)
    
    # define what happens when the window is closed
    def closeEvent(self, event):
        self.thor_cam.dispose_all_camera_resources()
        event.accept()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ThorCamControlWidget()
    window.show()
    
    sys.exit(app.exec_())


    
