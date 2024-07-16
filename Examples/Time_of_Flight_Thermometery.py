import sequencer 
import datetime
from sequencer.event import Sequence,Jump,Ramp,Event ,Digital_Channel, Analog_Channel,SequenceManager
from sequencer.ADwin_Modules import ADwin_Driver
import numpy as np
ad = ADwin_Driver() 

tof = Sequence("Time of Flight Thermometery")

tof.add_analog_channel("MOT Coils", 2,1)
tof.add_analog_channel("Camera Trigger", 2, 2)
tof.add_analog_channel("Trap TTL", 2, 3)
tof.add_analog_channel("Trap FM", 2, 4)
tof.add_analog_channel("Trap AM", 2, 5)
tof.add_analog_channel("Repump TTL", 2, 6)
tof.add_analog_channel("Repump FM", 2, 7)
tof.add_analog_channel("Repump AM", 2, 8)
tof.add_analog_channel("D1 AOM FM", 3,1)
tof.add_analog_channel("D1 AOM AM", 3,2)
tof.add_analog_channel("D1 EOM FM", 3,3)
tof.add_analog_channel("D1 EOM AM", 3,4)
tof.add_analog_channel("Absorption Imaging FM", 3,5)
tof.add_analog_channel("Absorption Imaging TTL", 3,6)

t = 0


tof.add_event("MOT Coils", Jump(3.3), start_time=t,comment= "Coils Off" ) 
tof.add_event("Camera Trigger", Jump(0), start_time=t,comment= "Cam Trigger Low")
tof.add_event("Trap TTL", Jump(0), start_time=t,comment= "Trap Beam Off")
tof.add_event("Trap FM", Jump(2.8), start_time=t,comment= "Default Trap FM") 
tof.add_event("Trap AM", Jump(1.5), start_time=t,comment= "Default Trap AM") 
tof.add_event("Repump TTL", Jump(0), start_time=t,comment= "Repump Beam Off") 
tof.add_event("Repump FM", Jump(1.6), start_time=t,comment= "Default Repump FM") 
tof.add_event("Repump AM", Jump(0.5), start_time=t,comment= "Default Rempump AM") 
tof.add_event("D1 AOM FM", Jump(0), start_time=t,comment= "Default D1 Cooling FM") 
tof.add_event("D1 AOM AM", Jump(0), start_time=t,comment= "D1 AOM Off") 
tof.add_event("D1 EOM FM", Jump(0), start_time=t,comment= "D1 EOM FM, N/A") 
tof.add_event("D1 EOM AM", Jump(0), start_time=t,comment= "D1 EOM AM, N/A") 
tof.add_event("Absorption Imaging FM", Jump(7.5), start_time=t,comment= "Defauly Abs Beam Detuning")
tof.add_event("Absorption Imaging TTL", Jump(0), start_time=t,comment= "Absorption Beam Off") 


# Wait 1 sec for the MOT to unload, then Load the MOT.

t = 1



tof.add_event("MOT Coils", Jump(0), start_time=t,comment= "Coils On")
tof.add_event("Trap TTL", Jump(3.3), start_time=t,comment= "Trap Beam On") 
tof.add_event("Repump TTL", Jump(3.3), start_time=t,comment= "Repump Beam On") 

Trap_FM = tof.add_event("Trap FM", Jump(2.8), start_time=t,comment= "Trap FM") 
Repump_FM = tof.add_event("Repump FM", Jump(1.6), start_time=t,comment= "Repump FM") 

Trap_AM = tof.add_event("Trap AM", Jump(1.5), start_time=t,comment= "Trap AM") 
Repump_AM = tof.add_event("Repump AM", Jump(0.5), start_time=t,comment= "Rempump AM") 

# Load the MOT for 5 sec 

t = 6 

# Turn off the MOT Beams and bring the MOT Beams on Resonance for ToF Imaging

tof.add_event("MOT Coils", Jump(3.3), start_time=t, comment= "Coils Off") 
Trap_Off = tof.add_event("Trap TTL", Jump(0), start_time=t,comment= "Trap Beam Off")
Repump_Off = tof.add_event("Repump TTL", Jump(0), start_time=t,comment= "Repump Beam Off")

Trap_FM_Res = tof.add_event("Trap FM", Jump(0),  start_time=t ,comment= "Trap Beam Resonance")
Repump_FM_Res = tof.add_event("Repump FM", Jump(4),  start_time=t ,comment= "Repump Beam On")

Trig_High_IWA = tof.add_event("Camera Trigger", Jump(3.3), relative_time=0.0002,parent_event=Trap_Off, comment= "Cam Trigger High")

Trap_On = tof.add_event("Trap TTL", Jump(3.3), relative_time=0,parent_event=Trig_High_IWA,comment= "Trap Beam On")
Repump_On = tof.add_event("Repump TTL", Jump(3.3), relative_time=0,parent_event=Trig_High_IWA,comment= "Repump Beam On")

t_exp = 64e-6
Trig_Low_IWA = tof.add_event("Camera Trigger", Jump(0), relative_time=t_exp,parent_event=Trig_High_IWA, comment= "Cam Trigger Low")


# tof.to_json("Time_of_Flight_Thermometery.json")
# seq_list = tof.sweep_event_parameters("relative_time",list(np.arange(0.0002,0.002,0.0002)),event_to_sweep=Trig_High_IWA)
# print(seq_list)
# for seq in seq_list.values() :  
#     ad.add_to_queue(seq)

# ad.initiate_all_experiments()




# tof.to_json(f"Time_of_Flight_Thermometery.json")
