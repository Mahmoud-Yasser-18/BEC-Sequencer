import sequencer 
import datetime
from sequencer.event import Sequence,Jump,Ramp,Event ,Digital_Channel, Analog_Channel,SequenceManager
from sequencer.ADwin_Modules import ADwin_Driver
import numpy as np

MOT_Default = Sequence("MOT Default")

MOT_Default.add_analog_channel("MOT Coils", 2,1)
MOT_Default.add_analog_channel("Camera Trigger", 2, 2)
MOT_Default.add_analog_channel("Trap TTL", 2, 3)
MOT_Default.add_analog_channel("Trap FM", 2, 4)
MOT_Default.add_analog_channel("Trap AM", 2, 5)
MOT_Default.add_analog_channel("Repump TTL", 2, 6)
MOT_Default.add_analog_channel("Repump FM", 2, 7)
MOT_Default.add_analog_channel("Repump AM", 2, 8)
MOT_Default.add_analog_channel("D1 AOM FM", 3,1)
MOT_Default.add_analog_channel("D1 AOM AM", 3,2)
MOT_Default.add_analog_channel("D1 EOM FM", 3,3)
MOT_Default.add_analog_channel("D1 EOM AM", 3,4)
MOT_Default.add_analog_channel("Absorption Imaging FM", 3,5)
MOT_Default.add_analog_channel("Absorption Imaging TTL", 3,6)
MOT_Default.add_analog_channel("test7", 3,7)
MOT_Default.add_analog_channel("test8", 3,8)



t = 0

MOT_Default.add_event("MOT Coils", Jump(0), start_time=t,comment = "Coils On") 
MOT_Default.add_event("Camera Trigger", Jump(0), start_time=t,comment = "Cam Trigger Low") 
MOT_Default.add_event("Trap TTL", Jump(3.3), start_time=t,comment = "Trap Beam On") 
MOT_Default.add_event("Trap FM", Jump(2.8), start_time=t,comment = "Default Trap FM") 
MOT_Default.add_event("Trap AM", Jump(1.5), start_time=t,comment = "Default Trap AM") 
MOT_Default.add_event("Repump TTL", Jump(3.3), start_time=t,comment = "Repump Beam On") 
MOT_Default.add_event("Repump FM", Jump(1.6), start_time=t,comment = "Default Repump FM") 
MOT_Default.add_event("Repump AM", Jump(0.5), start_time=t,comment = "Default Rempump AM") 
MOT_Default.add_event("D1 AOM FM", Jump(0), start_time=t,comment = "Default D1 Cooling FM") 
MOT_Default.add_event("D1 AOM AM", Jump(0), start_time=t,comment = "D1 AOM Off") 
MOT_Default.add_event("D1 EOM FM", Jump(0), start_time=t,comment = "D1 EOM FM, N/A") 
MOT_Default.add_event("D1 EOM AM", Jump(0), start_time=t,comment = "D1 EOM AM, N/A") 
MOT_Default.add_event("Absorption Imaging FM", Jump(7.5), start_time=t,comment = "Defauly Abs Beam Detuning") 
MOT_Default.add_event("Absorption Imaging TTL", Jump(3.3), start_time=t,comment = "Abs Beam On") 
now = datetime.datetime.now()
time_stamp = now.strftime("%Y-%m-%d_%H-%M-%S-%f")
MOT_Default.to_json(f"MOT_Default.json")

