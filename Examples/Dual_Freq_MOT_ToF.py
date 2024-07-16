import sequencer 
import datetime
from sequencer.event import Sequence,Jump,Ramp,Event ,Digital_Channel, Analog_Channel,SequenceManager
from sequencer.ADwin_Modules import ADwin_Driver
import numpy as np

DFM_ToF = Sequence("Dual_Freq_MOT_ToF")

DFM_ToF.add_analog_channel("MOT Coils", 2,1)
DFM_ToF.add_analog_channel("Camera Trigger", 2, 2)
DFM_ToF.add_analog_channel("Trap TTL", 2, 3)
DFM_ToF.add_analog_channel("Trap FM", 2, 4)
DFM_ToF.add_analog_channel("Trap AM", 2, 5)
DFM_ToF.add_analog_channel("Repump TTL", 2, 6)
DFM_ToF.add_analog_channel("Repump FM", 2, 7)
DFM_ToF.add_analog_channel("Repump AM", 2, 8)
DFM_ToF.add_analog_channel("D1 AOM FM", 3,1)
DFM_ToF.add_analog_channel("D1 AOM AM", 3,2)
DFM_ToF.add_analog_channel("D1 EOM FM", 3,3)
DFM_ToF.add_analog_channel("D1 EOM AM", 3,4)
DFM_ToF.add_analog_channel("Absorption Imaging FM", 3,5)
DFM_ToF.add_analog_channel("Absorption Imaging TTL", 3,6)

### Setting the Initialized Status: Turning the D1 and D2 Beams Off, Coils Off. Goal: Unload the MOT.

t = 0

DFM_ToF.add_event("MOT Coils", Jump(3.3), start_time=t) # Coils Off
DFM_ToF.add_event("Camera Trigger", Jump(0), start_time=t) # Cam Trigger Low
DFM_ToF.add_event("Trap TTL", Jump(0), start_time=t) # Trap Beam Off
DFM_ToF.add_event("Trap FM", Jump(2.8), start_time=t) # Default Trap FM
DFM_ToF.add_event("Trap AM", Jump(1.5), start_time=t) # Default Trap AM
DFM_ToF.add_event("Repump TTL", Jump(0), start_time=t) # Repump Beam Off
DFM_ToF.add_event("Repump FM", Jump(1.6), start_time=t) # Default Repump FM
DFM_ToF.add_event("Repump AM", Jump(0.5), start_time=t) # Default Rempump AM
DFM_ToF.add_event("D1 AOM FM", Jump(0), start_time=t) # Default D1 Cooling FM
DFM_ToF.add_event("D1 AOM AM", Jump(0), start_time=t) # D1 AOM Off
DFM_ToF.add_event("D1 EOM FM", Jump(0), start_time=t) # D1 EOM FM, N/A
DFM_ToF.add_event("D1 EOM AM", Jump(0), start_time=t) # D1 EOM AM, N/A
DFM_ToF.add_event("Absorption Imaging FM", Jump(7.5), start_time=t) # Defauly Abs Beam Detuning
DFM_ToF.add_event("Absorption Imaging TTL", Jump(0), start_time=t) # Absorption Beam Off

### Wait 1 sec for the MOT to unload, then Load the MOT. Goal: Load the MOT

t = 1

Initiate_MOT = DFM_ToF.add_event("MOT Coils", Jump(0), start_time=t, comment = 'Initiate MOT, Coils On') # Coils On

DFM_ToF.add_event("Trap TTL", Jump(3.3), relative_time = 0, parent_event = Initiate_MOT, comment='Trap Beam On') # Trap Beam On
DFM_ToF.add_event("Repump TTL", Jump(3.3), relative_time = 0, parent_event = Initiate_MOT, comment='Repump Beam On') # Repump Beam On

DFM_ToF.add_event("Trap FM", Jump(2.8), relative_time = 0, parent_event = Initiate_MOT, comment='Trap FM') # Trap FM
DFM_ToF.add_event("Repump FM", Jump(1.6), relative_time = 0, parent_event = Initiate_MOT, comment='Repump FM') # Repump FM

DFM_ToF.add_event("Trap AM", Jump(1.5), relative_time = 0, parent_event = Initiate_MOT, comment='Trap AM') # Trap AM
DFM_ToF.add_event("Repump AM", Jump(0.5), relative_time = 0, parent_event = Initiate_MOT, comment='Rempump AM') # Rempump AM

t_load = 5 # MOT Load Time

### Creat a Dual-Frequency MOT by additionally doing Gray Molasses

# Turn off the D2 Trap Beam
Initiate_DFM = DFM_ToF.add_event("Trap TTL", Jump(0), relative_time = t_load, parent_event = Initiate_MOT, comment= "[Initiate DFM], Trap Off") # Trap Beam Off

# Decrease the Power in the Repump Beams
DFM_ToF.add_event("Repump AM", Jump(2.5),  relative_time = 0, parent_event = Initiate_DFM, comment= "Repump AM Low Power") # D1 AM Low Power

# Turn On the D1 Cooling Beam (but keep the D1 Repump Beam Off)
DFM_ToF.add_event("D1 AOM AM", Jump(10), relative_time = 0, parent_event = Initiate_DFM, comment= "D1 AOM On") # D1 AOM On
DFM_ToF.add_event("D1 AOM FM", Jump(0), relative_time = 0, parent_event = Initiate_DFM, comment= "Set the Detuning of the D1 Beam") # Set the Detuning of the D1 Beam
DFM_ToF.add_event("D1 EOM FM", Jump(0), relative_time = 0, parent_event = Initiate_DFM, comment= "D1 EOM FM") # D1 EOM FM (We have a resonant EOM, this creates an RF signal away from the EOM's resonance.)

### Image the MOT after the CMOT Stage

# Turn off the MOT Beams and bring the MOT Beams on Resonance for ToF Imaging

DFM_Time = 7e-3
ToF_Time = 0.2e-3
t_exp = 64e-6

Initiate_ToF = DFM_ToF.add_event("MOT Coils", Jump(3.3), relative_time = DFM_Time, parent_event = Initiate_DFM, comment= "[Initiate ToF], Coils Off")

DFM_ToF.add_event("Trap TTL", Jump(0), relative_time = 0, parent_event = Initiate_ToF, comment= "Trap Beam Off")
DFM_ToF.add_event("Repump TTL", Jump(0), relative_time = 0, parent_event = Initiate_ToF, comment= "Repump Beam Off")
DFM_ToF.add_event("D1 AOM AM", Jump(0), relative_time = 0, parent_event = Initiate_ToF, comment= "D1 Beams Off")

DFM_ToF.add_event("Trap FM", Jump(0),  relative_time = 0, parent_event = Initiate_ToF, comment= "Trap FM Res")
DFM_ToF.add_event("Repump FM", Jump(4),  relative_time = 0, parent_event = Initiate_ToF, comment= "Repump FM Res")

Trig_High_IWA = DFM_ToF.add_event("Camera Trigger", Jump(3.3), relative_time = ToF_Time, parent_event = Initiate_ToF, comment= "[Take a picture], Cam Trigger High")
DFM_ToF.add_event("Repump AM", Jump(0.5),  relative_time = 0, parent_event = Trig_High_IWA, comment= "Repump AM High Power") # D1 AM Low Power
DFM_ToF.add_event("Trap TTL", Jump(3.3), relative_time=0,parent_event=Trig_High_IWA,comment= "Trap Beam On")
DFM_ToF.add_event("Repump TTL", Jump(3.3), relative_time=0,parent_event=Trig_High_IWA,comment= "Repump Beam On")

DFM_ToF.add_event("Camera Trigger", Jump(0), relative_time=t_exp,parent_event=Trig_High_IWA, comment= "[Picture Taken], Cam Trigger Low")


# DFM_ToF.plot_with_event_tree(start_time=6.006, end_time=6.1,resolution=0.00000001)
DFM_ToF.to_json('Dual_Freq_MOT_ToF.json')