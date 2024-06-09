#! /usr/bin/python3
# -*- coding: cp1252 -*-



import ADwin
import os

from copy import deepcopy 
import numpy as np
from sequencer.event import Sequence,Digital_Channel, Analog_Channel, Jump, Ramp, Event
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



            
            
def calculate_sequence_data_eff(sequence: Sequence) -> None:
    

    channel_card = np.array([])
    channel_number = np.array([])
    channel_value= np.array([])
    update_list = np.array([]) 

    all_events = deepcopy(sequence.all_events)
    time_ranges=calculate_time_ranges(all_events)

    start_time = time.time()

    for time_range in time_ranges:
        if time_range[-1]:
            update_list=np.append(update_list,np.ones(int(np.rint((sequence.time_resolution+time_range[0][1]-time_range[0][0])/sequence.time_resolution)))*len(time_range[-1]))
            
            if time_range[0][0]==time_range[0][1]:
                
                time_axis = np.array([time_range[0][0]])
            else :
                time_axis = np.arange(time_range[0][0],sequence.time_resolution+ time_range[0][1], sequence.time_resolution)


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
                    temp_channel_value_list.append(event.channel.discretize(event.channel.default_voltage_func(event.behavior.func(time_axis - event.start_time))))  
                    

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
            
            update_list=np.append(update_list,time_range[0][0]-time_range[0][1])

        
    total_time = time.time() - start_time 
    

    print("sequence duration: ", sequence.sequence_dauation())
    print(f"Total time taken: {total_time}")        


    return update_list, channel_card, channel_number, channel_value


class ADwin_Driver:
    def __init__(self, process_file="transfer_seq_data.TC1", absolute_path=0):
        self.PROCESSORTYPE = "12"
        self.DEVICENUMBER = 0x1
        self.RAISE_EXCEPTIONS = 1 


        self.adw.Process_Status(1)
        # 1 : Process is running.
        # 0 : Process is not running, that means, it has not been loaded, started or stopped.
        # <0:Process is being stopped, that means, it has received Stop_Process, but still waits for the last event.

        
        self.queue = []
        
        self.current_index = 0
        
        self.processdelay= 1000         

        
        self.updatelist=[] 
        self.chnum=[]
        self.chval=[]
        
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

   
   
    def add_to_queue(self,sequence: Sequence):
        update_list, channel_card, channel_number, channel_value = calculate_sequence_data_eff(sequence)
        self.queue.append({
            "update_list": update_list,
            "channel_card": channel_card,
            "channel_number": channel_number,
            "channel_value": channel_value
        })

    
    def load_ADwin_Data(self,index):
        update_list, channel_card, channel_number, channel_value = self.queue[index]
        
        self.adw.Set_Par(Index=1,Value=len(update_list))
        self.adw.Set_Par(Index=2,Value=self.processdelay)
        self.adw.Set_Par(Index=3,Value= max(update_list))
        self.adw.SetData_Double(Data=update_list,DataNo=1,Startindex=1,Count=len(update_list))
        self.adw.SetData_Double(Data=channel_number,DataNo=2,Startindex=1,Count=len(channel_number))
        self.adw.SetData_Double(Data=channel_value,DataNo=3,Startindex=1,Count=len(channel_value))
        self.adw.SetData_Double(Data=channel_card,DataNo=4,Startindex=1,Count=len(channel_card))


    


    def start_process(self, process_number):
        self.adw.Start_Process(process_number)


    def initiate_experiment(self,process_number=1):
        self.load_ADwin_Data()
        self.start_process(process_number)


if __name__ == "__main__":
    adw = ADwin_Driver()
    
