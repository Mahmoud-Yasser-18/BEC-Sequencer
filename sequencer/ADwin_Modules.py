#! /usr/bin/python3
# -*- coding: cp1252 -*-



import ADwin
import os

from copy import deepcopy 
import numpy as np
from sequencer.event import Sequence,Digital_Channel, Analog_Channel, Jump, Ramp, Event, RampType
import time


def calculate_sequence_data(sequence: Sequence) -> None:

    all_events = sequence.all_events
    sequence_duration = sequence.sequence_dauation() 
    time_points = np.arange(0, sequence_duration, sequence.time_resolution) 
    update_list = np.zeros(len(time_points)) 


    done_events = []


    channel_card = []
    channel_number = []
    channel_value = [] 


    start_time = time.time() 


    # The inefficient way to do this is to loop through all the events and check if the time point is within the event time range 
    for t in range(len(time_points)): 
        for event in all_events: 
            
            
            if event in done_events: 
                continue


            if event.start_time <= time_points[t] <= event.end_time: 
                update_list[t]+=1 
                if  isinstance(event.channel, Digital_Channel):
                    channel_card.append(event.channel.card_number)
                    channel_number.append(event.channel.channel_number)
                    channel_value.append(event.behavior.target_value)
                    done_events.append(event)

                elif isinstance(event.channel, Analog_Channel): 
                    
                    if isinstance(event.behavior, Jump): 
                        channel_card.append(event.channel.card_number)
                        channel_number.append(event.channel.channel_number)
                        channel_value.append(event.behavior.target_value)
                        done_events.append(event)
                    elif isinstance(event.behavior, Ramp): 
                        channel_card.append(event.channel.card_number)
                        channel_number.append(event.channel.channel_number)
                        channel_value.append(event.behavior.func(time_points[t] - event.start_time))
                        
                        
            elif time_points[t] > event.end_time:
                # ramp is done 
                done_events.append(event)            
    total_time = time.time() - start_time 
    

    print("sequence duration: ", sequence_duration)
    print(f"Total time taken: {total_time}")        
    return update_list, channel_card, channel_number, channel_value


def calculate_time_ranges(all_events):

    time_ranges = []
    


    # Initialize variables
    current_time = 0
    active_events = []
    all_times = sorted(set([event.start_time for event in all_events] + [event.end_time for event in all_events]))

    # Iterate over all significant times
    for time in all_times:
        # Create a tuple for the time range and the active events before updating the active events
        if current_time != time:
            time_ranges.append(((current_time, time), active_events.copy()))
        
        # Remove events that have ended at or before the current time
        active_events = [event for event in active_events if event.end_time > time]

        # Add events that are starting at the current time
        starting_events = [event for event in all_events if event.start_time == time and event.end_time != time]
        active_events.extend(starting_events)

        # Handle instantaneous events
        instant_events = [event for event in all_events if event.start_time == event.end_time == time]
        if instant_events:
            time_ranges.append(((time, time), active_events + instant_events))

        current_time = time

    return time_ranges



            
            
def calculate_sequence_data_eff(sequence: Sequence,adwin_driver) -> None:
    
    
    time_resolution = adwin_driver.proceessdelay_unit*adwin_driver.processdelay
    print("Time resolution: ", time_resolution)

    channel_card = np.array([])
    channel_number = np.array([])
    channel_value= np.array([])
    update_list = np.array([]) 

    all_events = deepcopy(sequence.all_events)
    time_ranges=calculate_time_ranges(all_events)

    start_time2 = time.time()

    for time_range in time_ranges:
        if time_range[-1]:
            update_list=np.append(update_list,np.ones(int(np.rint((time_resolution+time_range[0][1]-time_range[0][0])/time_resolution)))*len(time_range[-1]))
            
            if time_range[0][0]==time_range[0][1]:
                
                time_axis = np.array([time_range[0][0]])
            else :
                time_axis = np.arange(time_range[0][0],time_resolution+ time_range[0][1], time_resolution)


            temp_channel_card_list =[] 
            temp_channel_number_list =[] 
            temp_channel_value_list =[]
            
            for event in time_range[-1]: 

                
                temp_channel_card_list.append(np.ones_like(time_axis)*event.channel.card_number)
                temp_channel_number_list.append(np.ones_like(time_axis)*event.channel.channel_number)
                
                if isinstance(event.behavior, Jump):
                
                    if isinstance(event.channel, Digital_Channel):
                        temp_channel_value_list.append(event.behavior.target_value)
                    else :                         
                        temp_channel_value_list.append(event.channel.default_voltage_func(event.behavior.target_value))
                
                elif isinstance(event.behavior, Ramp) and isinstance(event.channel, Analog_Channel): 
                    
                    temp_channel_value_list.append((event.channel.default_voltage_func(event.behavior.func(time_axis - event.start_time))))  
                    

            stacked_temp_channel_card_list = np.vstack( list(temp_channel_card_list))
            stacked_temp_channel_number_list = np.vstack( list(temp_channel_number_list))
            stacked_temp_channel_value_list = np.vstack( list(temp_channel_value_list))

            stacked_temp_channel_card_list = stacked_temp_channel_card_list.T
            stacked_temp_channel_number_list = stacked_temp_channel_number_list.T
            stacked_temp_channel_value_list = stacked_temp_channel_value_list.T
            
            stacked_temp_channel_card_list=stacked_temp_channel_card_list.flatten()
            stacked_temp_channel_number_list=stacked_temp_channel_number_list.flatten()
            stacked_temp_channel_value_list=stacked_temp_channel_value_list.flatten()
            
            channel_card=np.append(channel_card,stacked_temp_channel_card_list)
            channel_number=np.append(channel_number,stacked_temp_channel_number_list)
            channel_value=np.append(channel_value,stacked_temp_channel_value_list)

        else: 
            time_to_be_delayed = time_range[0][1]-time_range[0][0]
            

            # print("Time to be delayed: ", time_to_be_delayed)
            # print("Max cycles Time: ", adwin_driver.MAX_CYCLES_time)
            number_of_delays = np.floor(time_to_be_delayed / adwin_driver.MAX_CYCLES_time)
            # print("Number of delays: ", number_of_delays)
            # print(time_to_be_delayed % adwin_driver.MAX_CYCLES_time)
            reminder_of_delays =np.array(( time_to_be_delayed % adwin_driver.MAX_CYCLES_time))
            # print("Reminder of delays: ", reminder_of_delays)

            if reminder_of_delays:
                array_of_delays= np.append(-1* np.ones(int(number_of_delays))*adwin_driver.MAX_CYCLES,-1*reminder_of_delays/(time_resolution))
            else:
                array_of_delays=-1* np.ones(int(number_of_delays))*adwin_driver.MAX_CYCLES
            # print("array_of_delays: ", array_of_delays)
            
            update_list=np.append(update_list,array_of_delays)

    
    total_time = time.time() - start_time2 
    

    print("sequence duration: ", sequence.sequence_dauation())
    print(f"Total time taken: {total_time}")        


    return update_list, channel_card, channel_number, channel_value


class ADwin_Driver:
    def __init__(self, process_file="transfer_seq_data.TC1",PROCESSORTYPE = "12", absolute_path=0,processdelay=1000):
        self.PROCESSORTYPE = PROCESSORTYPE
        if self.PROCESSORTYPE == "12":
            self.proceessdelay_unit = 10**(-9)# For T12 processor, the time unit of the Processdelay (cycle time) is 1 ns for both high priority and low priority processes
        # if the processdelay is set to 1000, the cycle time is 1 us
        elif self.PROCESSORTYPE == "12.1":
            self.proceessdelay_unit = (1.5)*10**(-9)
        elif self.PROCESSORTYPE == "11":
            self.proceessdelay_unit = (3+1/3)*10**(-9)
        elif self.PROCESSORTYPE == "10":
            self.proceessdelay_unit = 25*10**(-9)
        elif self.PROCESSORTYPE == "9":
            self.proceessdelay_unit = 25*10**(-9)

        self.DEVICENUMBER = 0x1
        self.RAISE_EXCEPTIONS = 1 

        self.queue = []
        self.current_index = 0
        
        
        # the philosophy of changing the process delay is to be able to allow the user to change the cycle time of the ADwin system if so many channels are being changed at the same time
        self.processdelay = 1000
        
        self.MAX_CYCLES = int(2**31/  self.processdelay) # if we want to follow the old logic of putting everything in the units of process delay
        self.MAX_CYCLES_time = self.proceessdelay_unit*2**31 # The maximum time of a delay in seconds that can be achieved with the current process delay
        
        
        
        self.adw = ADwin.ADwin(self.DEVICENUMBER, self.RAISE_EXCEPTIONS)
        print("Booting ADwin-system... ")
        
        BTL = self.adw.ADwindir + "adwin" + self.PROCESSORTYPE + ".btl"
        self.adw.Boot(BTL)

        print("ADwin booted\n")
        print("Loading default process... ")
        if not absolute_path:
            self.adw.Load_Process(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), process_file)
            )
            print("Default process loaded\n")
        else:
            self.adw.Load_Process(process_file)
            print("Process loaded\n")

    def add_to_queue(self, sequence: Sequence):
        update_list, channel_card, channel_number, channel_value = calculate_sequence_data_eff(sequence,self)
        self.queue.append({
            "update_list": update_list,
            "channel_card": channel_card,
            "channel_number": channel_number,
            "channel_value": channel_value
        })

    def load_ADwin_Data(self, index,repeat=1):
        
        
        repeat = repeat
        update_list= list(self.queue[index]["update_list"].astype('int') )*repeat
        channel_card= list(self.queue[index]["channel_card"].astype('int') )*repeat
        # channel_number= list(self.queue[index]["channel_number"].astype('int') )*repeat
        channel_value= list(self.queue[index]["channel_value"])*repeat

        channel_number= self.queue[index]["channel_number"] 
        channel_number=channel_number*0 + 33
        channel_number=list(channel_number.astype('int'))*repeat
        
        start_time2 = time.time()
        self.adw.Set_Par(Index=1, Value=len(update_list))
        self.adw.Set_Par(Index=2, Value=int(self.processdelay))
        self.adw.Set_Par(Index=3, Value=int(max(update_list)))
        self.adw.SetData_Long(Data=update_list, DataNo=1, Startindex=1, Count=len(update_list))
        self.adw.SetData_Long(Data=channel_number, DataNo=2, Startindex=1, Count=len(channel_number))
        self.adw.SetData_Float(Data=channel_value, DataNo=3, Startindex=1, Count=len(channel_value))
        #self.adw.SetData_Long(Data=list(channel_card.astype('int')), DataNo=4, Startindex=1, Count=len(channel_card))

        total_time = time.time() - start_time2
        print(f"Total time taken to load data: {total_time}")

    def start_process(self, process_number):
        self.adw.Start_Process(process_number)

    def initiate_experiment(self, process_number=1, index=0,repeat=1):
        self.load_ADwin_Data(index,repeat=repeat)
        self.start_process(process_number)
    
    def is_process_running(self) -> bool:
        status = self.adw.Process_Status(1)
        # 1: Process is running.
        # 0: Process is not running.
        # <0: Process is being stopped.
        return status > 0
    
    def wait_for_process_to_complete(self, poll_interval=1):
        while self.is_process_running():
            print("Waiting for the current process to complete...")
            time.sleep(poll_interval)

    def initiate_all_experiments(self, process_number=1,repeat=1):
        for i in range(len(self.queue)):
            print(f"Initiating experiment {i + 1}/{len(self.queue)}")
            self.initiate_experiment(process_number, index=i,repeat=repeat)
            self.wait_for_process_to_complete()
            print(f"Experiment {i + 1} Completed.")

import matplotlib.pyplot as plt


if __name__ == "__main__":
    sequence = Sequence(time_resolution=0.001)
    analog_channel = sequence.add_analog_channel("Analog1", 2, 1)
    time_unit = 0.00001
    event1 = sequence.add_event("Analog1", Jump(0), start_time=0)
    event2 = sequence.add_event("Analog1", Jump(1), start_time=time_unit*1)
    event3 = sequence.add_event("Analog1", Jump(2), start_time=time_unit*2)
    event4 = sequence.add_event("Analog1", Jump(3), start_time=time_unit*3)
    event5 = sequence.add_event("Analog1", Ramp(duration=time_unit*1,ramp_type=RampType.LINEAR,start_value=3,end_value=0), start_time=time_unit*4)
    event6 = sequence.add_event("Analog1", Jump(0), start_time=time_unit*6)

    adwin_driver = ADwin_Driver(process_file="transfer_seq_data.TC1",processdelay=1000)
    adwin_driver.add_to_queue(sequence)
    adwin_driver.initiate_all_experiments(repeat=100000)
    update_list, channel_card, channel_number, channel_value = calculate_sequence_data_eff(sequence,adwin_driver)
    print(len(channel_value))
    # print(np.sum(update_list[update_list > 0]))
    # print(np.sum(channel_number))

    print(len(update_list))
    # print(update_list)
    # plt.plot(update_list)
    # plt.plot(channel_card) 
    # plt.plot(channel_number)
    # plt.scatter(np.arange(10),channel_value[:10])
    # plt.show()

