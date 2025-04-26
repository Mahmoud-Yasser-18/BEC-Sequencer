import sequencer 
import datetime
from sequencer.Sequence.sequence import Sequence,Jump
from sequencer.Drivers.ADwin_Modules import ADwin_Driver
import numpy as np

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
# Make sure that there  is no MOT loaded.
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
MOT_LOADING_STAGE= tof.add_event("MOT Coils", Jump(0), start_time=t,comment= "MOT LOADING STAGE: Coils On")
tof.add_event("Trap TTL", Jump(3.3), start_time=t,comment= "Trap Beam On") 
tof.add_event("Repump TTL", Jump(3.3), start_time=t,comment= "Repump Beam On") 
tof.add_event("Trap FM", Jump(2.8), start_time=t,comment= "Trap FM") 
tof.add_event("Repump FM", Jump(1.6), start_time=t,comment= "Repump FM") 
tof.add_event("Trap AM", Jump(1.5), start_time=t,comment= "Trap AM") 
tof.add_event("Repump AM", Jump(0.5), start_time=t,comment= "Rempump AM") 
# Load the MOT for 5 sec 
t = 6 
# Turn off the MOT Beams and bring the MOT Beams on Resonance for ToF Imaging
TOF_STAGE = tof.add_event("MOT Coils", Jump(3.3), start_time=t, comment= "Coils Off") 
tof.add_event("Trap TTL", Jump(0), start_time=t,comment= "Trap Beam Off")
tof.add_event("Repump TTL", Jump(0), start_time=t,comment= "Repump Beam Off")
tof.add_event("Trap FM", Jump(0),  start_time=t ,comment= "Trap Beam Resonance")
tof.add_event("Repump FM", Jump(4),  start_time=t ,comment= "Repump Beam On")

Trig_High_IWA = tof.add_event("Camera Trigger", Jump(3.3), relative_time=0.0002,parent_event=TOF_STAGE, comment= "Cam Trigger High")
tof.add_event("Trap TTL", Jump(3.3), relative_time=0,parent_event=Trig_High_IWA,comment= "Trap Beam On")
tof.add_event("Repump TTL", Jump(3.3), relative_time=0,parent_event=Trig_High_IWA,comment= "Repump Beam On")
t_exp = 64e-6
Trig_Low_IWA = tof.add_event("Camera Trigger", Jump(0), relative_time=t_exp,parent_event=Trig_High_IWA, comment= "Cam Trigger Low")
tof.print_event_tree()
tof.plot_with_event_tree()
tof.to_json("Time_of_Flight_Thermometery.json")

#adwin= ADwin_Driver() # create an instance of the ADwin driver
# adwin.add_to_queue(tof) # add the sequence to the queue 
# adwin.initiate_all_experiments() # run the sequence

# to create sweep for the time of flight thermometery
# seq_manager = SequenceManager()
# seq_manager.load_sequence(tof)
# seq_manager.sweep_sequence_temp( sequence_name="Time of Flight Thermometery", # Sequence name
#                             parameter="relative_time", # Parameter to sweep
#                             values=[0.0001, 0.0002, 0.0003, 0.0004, 0.0005], # Values to sweep 
#                             event_to_sweep=Trig_High_IWA) # Event to sweep on
# sweep_list = seq_manager.get_sweep_sequences_main()
# for seq in sweep_list.values():
#     adwin.add_to_queue(seq)
# adwin.initiate_all_experiments() # run the sequences in the queue