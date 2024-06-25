import sys
import threading
import queue
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from PIL import Image
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK, TLCamera, Frame
from thorlabs_tsi_sdk.tl_camera_enums import SENSOR_TYPE,OPERATION_MODE
from thorlabs_tsi_sdk.tl_mono_to_color_processor import MonoToColorProcessorSDK

try:
    # if on Windows, use the provided setup script to add the DLLs folder to the PATH
    from windows_setup import configure_path
    configure_path()
except ImportError:
    configure_path = None

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
                    self._image_queue.put_nowait(pil_image)
            except queue.Full:
                pass
            except Exception as error:
                print(f"Encountered error: {error}, image acquisition will stop.")
                break
        print("Image acquisition has stopped")
        if self._is_color:
            self._mono_to_color_processor.dispose()
            self._mono_to_color_sdk.dispose()

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
            image = self.image_queue.get_nowait()
            if image.mode == 'RGB':
                data = image.tobytes("raw", "RGB")
                q_image = QImage(data, image.width, image.height, QImage.Format_RGB888)
            else:  # Grayscale image
                data = image.tobytes("raw", "L")
                q_image = QImage(data, image.width, image.height, QImage.Format_Grayscale8)
            pixmap = QPixmap.fromImage(q_image)
            self.image_label.setPixmap(pixmap)
        except queue.Empty:
            pass

class THORCAM_HANDELER():
    def __init__(self):
        self.sdk=TLCameraSDK() 

    def get_camera_list(self):
        return self.sdk.discover_available_cameras()
    
    def open_camera(self, camera_index=None,serial_number=None):
        try : 
            self.camera.dispose()
        except:
            print('No camera to dispose')

        if camera_index is None:
            self.camera = self.sdk.open_camera(serial_number)
        else:
            self.camera = self.sdk.open_camera(self.get_camera_list()[camera_index])
    
    def change_mode(self, live_or_trigger):
        self.camera_mode = live_or_trigger
        self.camera.disarm()
        if live_or_trigger == 'live':
            self.camera.frames_per_trigger_zero_for_unlimited = 0
        else:
            self.camera.frames_per_trigger_zero_for_unlimited = 1
            self.camera.operation_mode= OPERATION_MODE.HARDWARE_TRIGGER
        
        self.camera.arm(2)
        if live_or_trigger == 'live':
            self.camera.issue_software_trigger()
    
    def set_camera_params(self, exposure_time_us, gain):
        self.camera.disarm()
        self.camera.exposure_time_us = exposure_time_us
        self.camera.gain = gain
        self.camera.arm(2)
        if self.camera_mode == 'live':
            self.camera.issue_software_trigger()
    
    
    def dispose_all_camera_resources(self):
        try :
            self.sdk.dispose()
        except:
            print('No sdk to dispose')
        try:        
            self.camera.dispose()
        except:
            print('No camera to dispose')


    def start_acquisition_thread(self):
        self.acquisition_thread = ImageAcquisitionThread(self.camera)
        self.acquisition_thread.start()
    
    def kill_acquisition_thread(self):
        try:
            self.acquisition_thread.stop()
            self.acquisition_thread.join()
        except:
            print('No thread to kill')
# when the class is destroyed, the resources are automatically disposed
    def __del__(self):
        try :
            self.dispose_all_camera_resources()
        except:
            print('No resources to dispose')
        try :
            self.kill_acquisition_thread()
        except:
            print('No thread to kill')

if __name__ == "__main__":
    # test THORCAM_HANDELER
    live_or_trigger='live'
    thor_cam = THORCAM_HANDELER()
    camera_list = thor_cam.get_camera_list()
    print(camera_list)
    thor_cam.open_camera(serial_number=camera_list[0])
    thor_cam.change_mode(live_or_trigger)
    thor_cam.set_camera_params(1000, 20)
    thor_cam.start_acquisition_thread()
    app = QApplication(sys.argv)
    window = LiveViewWidget(image_queue=thor_cam.acquisition_thread.get_output_queue())
    window.setWindowTitle(thor_cam.camera.name)
    window.resize(800, 600)
    window.show()
    app.exec_()
    thor_cam.dispose_all_camera_resources()






# if __name__ == "__main__":
#     live_or_trigger='trigger'
#     with TLCameraSDK() as sdk:
#         camera_list = sdk.discover_available_cameras()
#         with sdk.open_camera(camera_list[0]) as camera:
#             print("Generating app...")
#             if live_or_trigger == 'live':
#                 camera.frames_per_trigger_zero_for_unlimited = 0
#             else:
#                 camera.frames_per_trigger_zero_for_unlimited = 1
#                 camera.operation_mode= OPERATION_MODE.HARDWARE_TRIGGERED

#             app = QApplication(sys.argv)
#             acquisition_thread = ImageAcquisitionThread(camera)
#             window = LiveViewWidget(image_queue=acquisition_thread.get_output_queue())
#             window.setWindowTitle(camera.name)
#             window.resize(800, 600)
#             window.show()

#             print("Setting camera parameters...")


#             # camera.frames_per_trigger_zero_for_unlimited = 0
#             camera.arm(2)
#             if live_or_trigger == 'live':
#                 camera.issue_software_trigger()
            
#             print("Starting image acquisition thread...")
#             acquisition_thread.start()

#             print("App starting")
#             app.exec_()

#             print("Waiting for image acquisition thread to finish...")
#             acquisition_thread.stop()
#             acquisition_thread.join()
#             camera.dispose()
#             sdk.dispose()

#             print("Closing resources...")
#     print("App terminated. Goodbye!")