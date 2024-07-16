import sequencer 
import datetime
from sequencer.event import Sequence,Jump,Ramp,Event ,Digital_Channel, Analog_Channel,SequenceManager
from sequencer.ADwin_Modules import ADwin_Driver
import numpy as np

# from MOT_default import MOT_Default

abs_img = Sequence("Absorption Imaging")

abs_img.add_analog_channel("MOT Coils", 2,1)
abs_img.add_analog_channel("Camera Trigger", 2, 2)
abs_img.add_analog_channel("Trap TTL", 2, 3)
abs_img.add_analog_channel("Trap FM", 2, 4)
abs_img.add_analog_channel("Trap AM", 2, 5)
abs_img.add_analog_channel("Repump TTL", 2, 6)
abs_img.add_analog_channel("Repump FM", 2, 7)
abs_img.add_analog_channel("Repump AM", 2, 8)
abs_img.add_analog_channel("D1 AOM FM", 3,1)
abs_img.add_analog_channel("D1 AOM AM", 3,2)
abs_img.add_analog_channel("D1 EOM FM", 3,3)
abs_img.add_analog_channel("D1 EOM AM", 3,4)
abs_img.add_analog_channel("Absorption Imaging FM", 3,5)
abs_img.add_analog_channel("Absorption Imaging TTL", 3,6)

# Setting the Initialized Status: Turning the D1 and D2 Beams Off, Coils Off, Goal: Unload the MOT.

t = 0

abs_img.add_event("MOT Coils", Jump(3.3), start_time=t, comment= "Coils Off") # Coils Off
abs_img.add_event("Camera Trigger", Jump(0), start_time=t, comment= "Cam Trigger Low") # Cam Trigger Low
abs_img.add_event("Trap TTL", Jump(0), start_time=t, comment= "Trap Beam Off") # Trap Beam Off
abs_img.add_event("Trap FM", Jump(2.8), start_time=t, comment= "Default Trap FM") # Default Trap FM
abs_img.add_event("Trap AM", Jump(1.5), start_time=t, comment= "Default Trap AM") # Default Trap AM
abs_img.add_event("Repump TTL", Jump(0), start_time=t, comment= "Repump Beam Off") # Repump Beam Off
abs_img.add_event("Repump FM", Jump(1.6), start_time=t, comment= "Default Repump FM") # Default Repump FM
abs_img.add_event("Repump AM", Jump(0.5), start_time=t, comment= "Default Rempump AM") # Default Rempump AM
abs_img.add_event("D1 AOM FM", Jump(0), start_time=t, comment= "Default D1 Cooling FM") # Default D1 Cooling FM
abs_img.add_event("D1 AOM AM", Jump(0), start_time=t, comment= "D1 AOM Off") # D1 AOM Off
abs_img.add_event("D1 EOM FM", Jump(0), start_time=t, comment= "D1 EOM FM, N/A") # D1 EOM FM, N/A
abs_img.add_event("D1 EOM AM", Jump(0), start_time=t, comment= "D1 EOM AM, N/A") # D1 EOM AM, N/A
abs_img.add_event("Absorption Imaging FM", Jump(7.5), start_time=t, comment= "Defauly Abs Beam Detuning") # Defauly Abs Beam Detuning
abs_img.add_event("Absorption Imaging TTL", Jump(0), start_time=t, comment= "Absorption Beam Off") # Absorption Beam Off

# Wait 1 sec for the MOT to unload, then Load the MOT.

t = 1

abs_img.add_event("MOT Coils", Jump(0), start_time=t, comment= "Coils On") # Coils On

abs_img.add_event("Trap TTL", Jump(3.3), start_time=t, comment= "Trap Beam On") # Trap Beam On
abs_img.add_event("Repump TTL", Jump(3.3), start_time=t, comment= "Repump Beam On") # Repump Beam On

Trap_FM = abs_img.add_event("Trap FM", Jump(2.8), start_time=t, comment= "Trap FM") # Trap FM
Repump_FM = abs_img.add_event("Repump FM", Jump(1.6), start_time=t, comment= "Repump FM") # Repump FM

Trap_AM = abs_img.add_event("Trap AM", Jump(1.5), start_time=t, comment= "Trap AM") # Trap AM
Repump_AM = abs_img.add_event("Repump AM", Jump(0.5), start_time=t, comment= "Rempump AM") # Rempump AM

# Load the MOT for 5 sec, turn on the Probe, turn the MOT / Coils Off to take IWA

t = 6 

Probe_Detuning = abs_img.add_event("Absorption Imaging FM", Jump(7.5), start_time=t, comment= "Abs Beam FM") # Abs Beam FM
Probe_On = abs_img.add_event("Absorption Imaging TTL", Jump(3.3), start_time=t, comment= "Abs Beam On") # Abs Beam On

abs_img.add_event("MOT Coils", Jump(3.3), start_time=t, comment= "Coils Off") # Coils Off
abs_img.add_event("Trap TTL", Jump(0), start_time=t, comment= "Trap Beam Off") # Trap Beam Off
abs_img.add_event("Repump TTL", Jump(0), start_time=t, comment= "Repump Beam Off") # Repump Beam Off

t_exp = 120e-6

Trig_High_IWA = abs_img.add_event("Camera Trigger", Jump(3.3), parent_event = Probe_On, relative_time = 100e-6, comment= "Cam Trigger High") # Cam Trigger High
Trig_Low_IWA = abs_img.add_event("Camera Trigger", Jump(0), parent_event = Trig_High_IWA, relative_time = t_exp, comment= "Coils Off") # Coils Off

# Take the IWOA

Trig_High_IWOA = abs_img.add_event("Camera Trigger", Jump(3.3), parent_event = Trig_Low_IWA, relative_time = 50e-3, comment= "Cam Trigger High") # Cam Trigger High
Trig_Low_IWOA = abs_img.add_event("Camera Trigger", Jump(0), parent_event=Trig_High_IWOA, relative_time = t_exp, comment= "Coils Off") # Coils Off

now = datetime.datetime.now()
time_stamp = now.strftime("%Y-%m-%d_%H-%M-%S-%f")
abs_img.to_json(f"Absorption_Imaging.json")
# adwin_driver = ADwin_Driver()
# # adwin_driver.add_to_queue(abs_img)

# Probe_FM = list(np.arange(7.0,8.1,0.1))
# list_of_seq = abs_img.sweep_event_parameters("jump_target_value", Probe_FM, event_to_sweep = Probe_Detuning)

# for seq in list_of_seq.values():
#     # seq.print_sequence("Trap FM")
#     adwin_driver.add_to_queue(seq)

# adwin_driver.initiate_all_experiments(process_number=1,repeat=1)
# adwin_driver.repeat_process(process_number=1, repeat=1000,poll_interval=0.1)

