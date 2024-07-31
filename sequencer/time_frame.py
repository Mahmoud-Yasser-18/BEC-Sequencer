import copy
import numpy as np
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, List, Optional, Union,Tuple, Dict, Any 
import bisect
import json 
import os
import sys
import time
import copy
import matplotlib.pyplot as plt

class Parameter:
    def __init__(self, name: str,event: 'Event',parameter_origin):
        self.name = name
        self.event = event
        self.parameter_origin = parameter_origin
    def get_value(self): 
        return self.event.get_event_attributes()[self.parameter_origin]

        
        



class RampType(Enum):
    LINEAR = 'linear'
    QUADRATIC = 'quadratic'
    EXPONENTIAL = 'exponential'
    LOGARITHMIC = 'logarithmic'
    GENERIC = 'generic'
    MINIMUM_JERK = 'minimum jerk'

    def __str__(self):
        return self.value



class EventBehavior(ABC):
    @abstractmethod
    def get_value_at_time(self, t: float) -> float:
        pass

class Jump(EventBehavior):
    def __init__(self, target_value: float):
        self.target_value = target_value

    def edit_jump(self, target_value: float):
        self.target_value = target_value


    def get_value_at_time(self, t: float) -> float:
        return self.target_value
    
    def __repr__(self) -> str:
        return f"Jump({self.target_value})"


class Ramp(EventBehavior):
    def __init__(self, start_time_instance:'TimeInstance',end_time_instance:'TimeInstance', ramp_type: RampType = RampType.LINEAR, start_value: float = 0, end_value: float = 1, func: Optional[Callable[[float], float]] = None, resolution=0.001):
        if start_value == end_value:
            raise ValueError("start_value and end_value must be different")
        
        if end_time_instance =="temp":
            pass 
        elif start_time_instance.get_absolute_time() >= end_time_instance.get_absolute_time():
            raise ValueError("start_time_instance must be less than end_time_instance")
        
        
        self.start_time_instance = start_time_instance
        self.end_time_instance = end_time_instance

        
        if ramp_type == RampType.EXPONENTIAL and (start_value == 0 or end_value == 0):
            raise ValueError("For exponential ramp, start_value and end_value must be non-zero")

        if resolution < 0.000001:
            raise ValueError("resolution must be at least 0.000001")
        
        self.ramp_type = ramp_type
        self.start_value = start_value
        self.end_value = end_value
        self.resolution = resolution
        
        if func:
            self.func = func
        else:
            self._set_func()
    
    def get_duration(self):
        return self.end_time_instance.get_absolute_time() - self.start_time_instance.get_absolute_time()

    def _set_func(self):
        if self.ramp_type == RampType.LINEAR:
            self.func = lambda t: self.start_value + (self.end_value - self.start_value) * (t / self.get_duration())
        elif self.ramp_type == RampType.QUADRATIC:
            self.func = lambda t: self.start_value + (self.end_value - self.start_value) * (t / self.get_duration())**2
        elif self.ramp_type == RampType.EXPONENTIAL:
            self.func = lambda t: self.start_value * (self.end_value / self.start_value) ** (t / self.get_duration())
        elif self.ramp_type == RampType.LOGARITHMIC:
            self.func = lambda t: self.start_value + (self.end_value - self.start_value) * (np.log10(t + 1) / np.log10(self.get_duration() + 1))
        elif self.ramp_type == RampType.MINIMUM_JERK:
            self.func = lambda t: self.start_value + (self.end_value - self.start_value) * (10 * (t/self.get_duration())**3 - 15 * (t/self.get_duration())**4 + 6 * (t/self.get_duration())**5)
        else : 
            raise ValueError("Invalid ramp type")
        
    def edit_ramp(self, start_time_instance: Optional['TimeInstance'] = None,end_time_instance: Optional['TimeInstance'] = None, 
      ramp_type: Optional[RampType] = None, start_value: Optional[float] = None, end_value: Optional[float] = None, func: Optional[Callable[[float], float]] = None, resolution: Optional[float] = None):
        new_start_time_instance = start_time_instance if start_time_instance is not None else self.start_time_instance
        new_end_time_instance = end_time_instance if end_time_instance is not None else self.end_time_instance

        if ramp_type is not None:
            try:
                new_ramp_type = ramp_type
            except KeyError:
                # Handle the case where the ramp_type string is not valid
                raise ValueError(f"Invalid ramp type: {ramp_type}")
        else:
            new_ramp_type = self.ramp_type

        new_start_value = start_value if start_value is not None else self.start_value
        new_end_value = end_value if end_value is not None else self.end_value
        new_resolution = resolution if resolution is not None else self.resolution
        
        if new_start_value == new_end_value:
            raise ValueError("start_value and end_value must be different")
        
        if new_start_time_instance.get_absolute_time() >= new_end_time_instance.get_absolute_time():
            raise ValueError("duration must be negative")
        
        if new_ramp_type == RampType.EXPONENTIAL and (new_start_value == 0 or new_end_value == 0):
            raise ValueError("For exponential ramp, start_value and end_value must be non-zero")
        
        if new_resolution < 0.000001:
            raise ValueError("resolution must be at least 0.000001")
        
        # Apply changes only after validation
        self.start_time_instance = new_start_time_instance
        self.end_time_instance = new_end_time_instance
        self.ramp_type = new_ramp_type
        self.start_value = new_start_value
        self.end_value = new_end_value
        self.resolution = new_resolution

        if func:
            self.func = func
        else:
            self._set_func()


    def get_value_at_time(self, t: float) -> float:
        if 0 <= t <= self.get_duration():
            return self.func(t)
        else:
            return self.end_value
    
    def __repr__(self) -> str:
        return f"Ramp({self.get_duration()}, {self.ramp_type.value}, {self.start_value}, {self.end_value})"

class Channel:
    def __init__(self, name: str, card_number: int, channel_number: int, reset: bool, reset_value: float):
        self.name = name
        self.card_number = card_number
        self.channel_number = channel_number
        self.reset = reset
        self.reset_value = reset_value
        self.events: List[Event] = []
    
    def add_event(self, event: 'Event'):
        index = bisect.bisect_left([e.get_start_time() for e in self.events], event.get_start_time())
        self.events.insert(index, event)
    def sort_events(self):
        self.events.sort(key=lambda event: event.get_start_time())

    def __repr__(self) -> str:
        return (
            f"Channel(\n"
            f"   name={self.name},\n"
            f"   card_number={self.card_number},\n"
            f"   channel_number={self.channel_number},\n"
            f"   reset={self.reset},\n"
            f"   reset_value={self.reset_value},\n"
            f"   events={self.events}\n"
            f")"
        )
    
    #vituak function to get the channel attributes
    def get_channel_attributes(self):
        return {
            "name": self.name,
            "card_number": self.card_number,
            "channel_number": self.channel_number,
            "reset": self.reset,
            "reset_value": self.reset_value
        }

    def check_for_overlapping_events(self):
        self.events.sort(key=lambda event: event.get_start_time())
        for i in range(len(self.events) - 1):
            current_event = self.events[i]
            next_event = self.events[i + 1]
            if current_event.get_end_time() > next_event.get_start_time():
                raise ValueError(f"Events {current_event} and {next_event} on channel {self.name} overlap.")


    def __eq__(self, other: object) -> bool:
        return self.name == other.name and self.card_number == other.card_number and self.channel_number == other.channel_number and self.reset == other.reset and self.reset_value == other.reset_value

class Analog_Channel(Channel):
    def __init__(self, name: str, card_number: int, channel_number: int, reset: bool = False, reset_value: float = 0, default_voltage_func: Callable[[float], float] = lambda a: a, max_voltage: float = 10, min_voltage: float = -10,LIMIT=65535, RANGE=20, OFFSET=10):
        super().__init__(name, card_number, channel_number, reset, reset_value)
        self.default_voltage_func = default_voltage_func  # Should map from whatever value to a value between -10 to 10 
        self.max_voltage = max_voltage
        self.min_voltage = min_voltage
        self.LIMIT=LIMIT
        self.RANGE=RANGE
        self.OFFSET=OFFSET

    def discretize(self,val) : # Should map from -10:10 to 0:65535
        return (val + self.OFFSET)/self.RANGE * self.LIMIT
  

    def __repr__(self) -> str:
        return (
            f"Analog_Channel(\n"
            f"   name={self.name},\n"
            f"   card_number={self.card_number},\n"
            f"   channel_number={self.channel_number},\n"
            f"   reset={self.reset},\n"
            f"   reset_value={self.reset_value},\n"
            f"   max_voltage={self.max_voltage},\n"
            f"   min_voltage={self.min_voltage},\n"
            f"   events={self.events}\n"
            f")"
        )
    def get_channel_attributes(self):
        return {
            "type": "analog",
            "name": self.name,
            "card_number": self.card_number,
            "channel_number": self.channel_number,
            "reset": self.reset,
            "reset_value": self.reset_value,
            "max_voltage": self.max_voltage,
            "min_voltage": self.min_voltage,
            "LIMIT":self.LIMIT,
            "RANGE":self.RANGE,
            "OFFSET":self.OFFSET,
            # "default_voltage_func": self.default_voltage_func

        }

    
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other) and self.default_voltage_func == other.default_voltage_func and self.max_voltage == other.max_voltage and self.min_voltage == other.min_voltage


class Digital_Channel(Channel):
    def __init__(self, name: str, card_number: int, channel_number: int,  reset: bool = False, reset_value: float = 0):
        super().__init__(name, card_number, channel_number, reset, reset_value)

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other) 

    def __repr__(self) -> str:
        return (
            f"Digital_Channel(\n"
            f"   name={self.name},\n"
            f"   card_number={self.card_number},\n"
            f"   channel_number={self.channel_number},\n"
            f"   reset={self.reset},\n"
            f"   reset_value={self.reset_value},\n"
            f"   events={self.events}\n"
            f")"
        )
    def get_channel_attributes(self):
        return {
            "type": "digital",
            "name": self.name,
            "card_number": self.card_number,
            "channel_number": self.channel_number,
            "reset": self.reset,
            "reset_value": self.reset_value,
        }
    
class Event:
    def __init__(self, channel: Channel, behavior: EventBehavior,comment:str ="",start_time_instance: Optional['TimeInstance'] = None,end_time_instance: Optional['TimeInstance'] = None):


        self.channel = channel
        self.behavior = behavior
        self.comment= comment
        self.is_sweept = False
        self.sweep_type = None
        self.sweep_settings = dict()
        self.reference_original_event = self
        self.associated_parameters = []
        if start_time_instance is not None:
            self.start_time_instance = start_time_instance
        else:
            raise ValueError("start_time_instance is required")
        
        if isinstance(behavior, Ramp):
            if end_time_instance=="temp":
                pass
            else:
                if end_time_instance is None:
                    raise ValueError("end_time_instance is required for Ramp events")
                else :
                    self.end_time_instance = self.end_time_instance
        else:
            self.end_time_instance = self.start_time_instance

            
        
        


        if isinstance(behavior, Ramp) and not isinstance(behavior, Jump):
            
            self.end_time_instance =  end_time_instance 
        else:
            self.end_time_instance = self.start_time_instance

        self.check_for_overlap(channel, behavior, self.get_start_time(), self.get_end_time())
        


        self.children: List[Event] = []
        index = bisect.bisect_left([e.get_start_time() for e in self.channel.events], self.get_start_time())
        self.channel.events.insert(index, self)
        self.start_time_instance.add_event(self)
        if isinstance(behavior, Ramp) and not isinstance(behavior, Jump) and self.end_time_instance != self.start_time_instance:
            self.end_time_instance.add_ending_ramp(self)
        
    def get_start_time(self):
        return self.start_time_instance.get_absolute_time()

    def get_end_time(self):
        return self.end_time_instance.get_absolute_time()
    
    

    def get_event_attributes(self):
        if isinstance(self.behavior, Jump):
            
                
            return {
                "type": "jump",
                "jump_target_value": self.behavior.target_value,
                "start_time": self.get_start_time(),
                "channel_name": self.channel.name,
                "comment":self.comment,
                "start_time_instance":self.start_time_instance.name,
                }

        elif isinstance(self.behavior, Ramp):
            return {
                "type": "ramp",
                "ramp_type": self.behavior.ramp_type,
                "start_value": self.behavior.start_value,
                "end_value": self.behavior.end_value,
                "func": self.behavior.func,
                "resolution": self.behavior.resolution,
                "channel_name": self.channel.name,
                "comment":self.comment,
                "start_time_instance":self.start_time_instance.name,
                "end_time_instance":self.end_time_instance.name
                }   



    def check_for_overlap(self, channel: Channel, behavior: EventBehavior, start_time: float, end_time: float):
        for event in channel.events:
            if not (end_time < event.get_start_time() or start_time > event.get_end_time()):
                if isinstance(behavior, Jump) and isinstance(event.behavior, Jump):
                    if start_time == event.get_start_time():
                        raise ValueError(f"Cannot have more than one jump at the same time on channel {channel.name}.")
                elif isinstance(behavior, Jump) and isinstance(event.behavior, Ramp):
                    if start_time != event.get_end_time():
                        raise ValueError(f"Jump events can only be added at the end of a ramp on channel {channel.name}.")
                else:
                    raise ValueError(f"Events on channel {channel.name} overlap with existing event {event.behavior} from {event.start_time} to {event.end_time}.")

class TimeInstance:
    def __init__(self, name: str, parent: Optional['TimeInstance'] = None, relative_time: int = 0):
        self.name: str = name
        self.parent: Optional['TimeInstance'] = parent
        self.relative_time: int = relative_time
        self.children: List['TimeInstance'] = []
        self.events: List[Event] = []
        self.ending_ramps: List[Event] = []
        if parent:
            parent.children.append(self)
        else :
            # check if the relative time is not 0 for the root time instance
            if relative_time != 0:
                raise ValueError("Relative time must be 0 for the root time instance")
            
    def add_event(self, event: 'Event') -> None:
        self.events.append(event)
    def add_ending_ramp(self, event: 'Event') -> None:
        self.ending_ramps.append(event)

    
    
    def edit_parent(self, new_parent: 'TimeInstance') -> None:
        # check if editing the parent will result in negative absolute time
        if new_parent.get_absolute_time() + self.relative_time < 0: 
            raise ValueError("new relative time will result in negative absolute time")
        
        if self.parent:
            self.parent.children.remove(self)
        self.parent = new_parent
        new_parent.children.append(self)

    def edit_name(self, new_name: str) -> None:
        if self.parent is None:
            raise Exception("Cannot change name of root time frame")
        
        root = self.get_root()
        all_children = root.get_all_children()
        
        for child in all_children:
            if child.name == new_name:
                raise Exception("Name already exists")
        
        self.name = new_name

    def edit_relative_time(self, new_relative_time: int) -> None:
        # check if the new relative time will result in negative absolute time
        if self.parent is not None:
            if self.parent.get_absolute_time() + new_relative_time < 0:
                raise ValueError("new relative time will result in negative absolute time")
        self.relative_time = new_relative_time

    def get_absolute_time(self) -> int:
        if self.parent is None:
            return self.relative_time
        return self.relative_time + self.parent.get_absolute_time()

    def add_child_time_instance(self, name: str, relative_time: int) -> 'TimeInstance':
        #  check if the relative time will result in negative absolute time
        if self.get_absolute_time() + relative_time < 0:
            raise ValueError("new relative time will result in negative absolute time")
        return TimeInstance(name, parent=self, relative_time=relative_time)

    def delete_self(self) -> None:
        
        if self.parent is None:
            raise Exception("Cannot delete root time frame")

        # check if deleting self will result in negative absolute time for any of the children

        # get all children of the current time instance
        children = self.get_all_children()
        delta = - self.relative_time 
        for child in children:
            if child.get_absolute_time() + delta < 0:
                raise ValueError("Deleting this time instance will result in negative absolute time for one of the children")
            
        for child in self.children:
            child.parent = self.parent
            self.parent.children.append(child)
        self.parent.children.remove(self)
        self.children = []

    def get_root(self) -> 'TimeInstance':
        if self.parent is None:
            return self
        return self.parent.get_root()

    def get_all_children(self) -> List['TimeInstance']:
        children: List['TimeInstance'] = []
        for child in self.children:
            children.append(child)
            children += child.get_all_children()
        return children
    
    def get_time_instance_by_name(self, name: str) -> Optional['TimeInstance']:
        if self.name == name:
            return self
        # get all children of the current time instance
        children = self.get_all_children()
        for child in children:
            if child.name == name:
                return child
        return None
    

    def print_children(self, depth: int = 0) -> None:
        print("  " * depth + str(self))
        for child in self.children:
            child.print_children(depth + 1)

    def get_events_string(self, depth: int = 0) -> str:
        events_string: str = ""
        for event in self.events:
            events_string += "  " * depth + str(event) + "\n"
        for child in self.children:
            events_string += child.get_events_string(depth + 1)
        return events_string

    def create_a_deep_copy_of_all_frames(self) -> 'TimeInstance':
        root = self.get_root()
        new_root = copy.deepcopy(root)
        return new_root

    def __str__(self) -> str:
        return f"TimeInstance(name={self.name}, absolute_time={self.get_absolute_time()}, events={self.events}, relative_time={self.relative_time})"

    def __repr__(self) -> str:
        return self.__str__()


class Sequence:
    def __init__(self,name:str):
        
        self.sequence_name=name
        self.root_time_instance = TimeInstance("root")
        
        
        # list of all channels in the sequence 
        self.channels: List[Channel] = []

    # adding a time instance to the sequence 
    def add_time_instance(self, name: str, parent: TimeInstance, relative_time: int) -> TimeInstance:
        return parent.add_child_time_instance(name, relative_time)
    
    

    # adding an event to the sequence by providing the channel, behavior, start_time_instance and end_time_instance (in case of ramp)
    def add_event(self, channel: Channel, behavior: EventBehavior,start_time_instance: TimeInstance, end_time_instance: Optional[TimeInstance] = None,comment:str="",) -> Event:
        # check if the channel is already in the sequence
        if channel not in self.channels:
            raise ValueError("Channel not found in the sequence.")
        # check if ramp end_time_instance is provided (also validate that the start time instance is less than end time instance)
        if isinstance(behavior, Ramp):
            if end_time_instance is None:
                raise ValueError("End time instance is required for ramp events.")
            if start_time_instance.get_absolute_time() >= end_time_instance.get_absolute_time():
                raise ValueError("start_time_instance must be less than end_time_instance")
        # check if the  behavior is a jump and is not within the max min range of the channel 
        if isinstance(channel, Analog_Channel) and isinstance(behavior, Jump):
            if behavior.target_value > channel.max_voltage or behavior.target_value < channel.min_voltage:
                raise ValueError(f"Jump value {behavior.target_value} is out of range for channel {channel.name} with min voltage {channel.min_voltage} and max voltage {channel.max_voltage}")
        
        if isinstance(channel, Analog_Channel) and isinstance(behavior, Ramp):
            if behavior.start_value > channel.max_voltage or behavior.start_value < channel.min_voltage:
                raise ValueError(f"Ramp start value {behavior.start_value} is out of range for channel {channel.name} with min voltage {channel.min_voltage} and max voltage {channel.max_voltage}")
            if behavior.end_value > channel.max_voltage or behavior.end_value < channel.min_voltage:
                raise ValueError(f"Ramp end value {behavior.end_value} is out of range for channel {channel.name} with min voltage {channel.min_voltage} and max voltage {channel.max_voltage}")

        # create the event 
        return Event(channel, behavior,comment,start_time_instance, end_time_instance)
    
    def find_event_by_time_and_channel(self, start_time_instance_name: str, channel_name: str) -> Optional[Event]:
        channel = self.find_channel_by_name(channel_name)
        for event in channel.events:
            if event.start_time_instance.name == start_time_instance_name:
                return event
        return None
    
    @staticmethod
    def copy_original_events_to_new_sequence(original_sequence: 'Sequence', new_sequence: 'Sequence'):
        for event in original_sequence.get_all_events():
            new_event = new_sequence.find_event_by_time_and_channel(event.start_time_instance.name, event.channel.name)
            new_event.reference_original_event = event
            new_event.is_sweept = True
    def create_a_copy_of_sequence(self) -> 'Sequence':
        temp_sequence = copy.deepcopy(self)
        self.copy_original_events_to_new_sequence(self, temp_sequence)
        return temp_sequence
    
    def edit_event(self, edited_event: Event, new_channel: Optional[Channel] = None, new_behavior: Optional[EventBehavior] = None, new_start_time_instance: Optional[TimeInstance] = None, new_end_time_instance: Optional[TimeInstance] = None, new_comment: Optional[str] = None):
        temp_sequence = self.create_a_copy_of_sequence()
        event = temp_sequence.find_event_by_time_and_channel(edited_event.start_time_instance.name, edited_event.channel.name)

        if new_channel is not None:
            event.channel = new_channel
        if new_behavior is not None:
            event.behavior = new_behavior
        if new_start_time_instance is not None:
            event.start_time_instance = new_start_time_instance
        if new_end_time_instance is not None:
            event.end_time_instance = new_end_time_instance
        if new_comment is not None:
            event.comment = new_comment
        
        for channel in temp_sequence.channels:
            channel.check_for_overlapping_events()
        
        event = edited_event
        if new_channel is not None:
            event.channel = new_channel
        if new_behavior is not None:
            event.behavior = new_behavior
        if new_start_time_instance is not None:
            event.start_time_instance = new_start_time_instance
        if new_end_time_instance is not None:
            event.end_time_instance = new_end_time_instance
        if new_comment is not None:
            event.comment = new_comment

        return event

    def edit_time_instance(self, edited_time_instance: TimeInstance, new_name: Optional[str] = None, new_relative_time: Optional[int] = None, new_parent: Optional[TimeInstance] = None):
        # don't allow to change anything for the root time instance
        if edited_time_instance.parent is None:
            raise ValueError("Cannot change the root")
        
        temp_sequence = self.create_a_copy_of_sequence()
        # find the time instance in the sequence
        time_instance = temp_sequence.root_time_instance.get_time_instance_by_name(edited_time_instance.name)
        # apply the changes 
        if new_name is not None:
            time_instance.edit_name(new_name)
        if new_relative_time is not None:
            time_instance.edit_relative_time(new_relative_time)
        if new_parent is not None:
            time_instance.edit_parent(new_parent)

        # check for overlapping events
        for channel in temp_sequence.channels:
            channel.check_for_overlapping_events()
        
        # apply the changes to the original sequence
        time_instance = edited_time_instance
        if new_name is not None:
            time_instance.edit_name(new_name)
        if new_relative_time is not None:
            time_instance.edit_relative_time(new_relative_time)
        if new_parent is not None:
            time_instance.edit_parent(new_parent)
        
        return time_instance



    def get_all_events(self) -> List[Event]:
        all_events: List[Event] = []
        for channel in self.channels:
            all_events += channel.events
        return all_events
    
    def check_for_overlapping_events(self):
        for channel in self.channels:
            channel.check_for_overlapping_events()
    
    def add_analog_channel(self, name: str, card_number: int, channel_number: int, reset: bool = False, reset_value: float = 0, default_voltage_func: Callable[[float], float] = lambda a: a, max_voltage: float = 10, min_voltage: float = -10) -> Analog_Channel:
        for channel in self.channels:
            if channel.name == name:
                raise ValueError(f"Channel name '{name}' is already in use.")

        # Ensure combination of card_number and channel_number is unique
        for channel in self.channels:
            if channel.card_number == card_number and channel.channel_number == channel_number:
                raise ValueError(f"Card number {card_number} and channel number {channel_number} combination is already in use.")

        channel = Analog_Channel(name, card_number, channel_number, reset, reset_value, default_voltage_func, max_voltage, min_voltage)
        
        self.channels.append(channel)
        return channel

    # add a new digital channel to the sequence
    def add_digital_channel(self, name: str, card_number: int, channel_number: int, reset: bool = False, reset_value: float = 0) -> Digital_Channel:
        for channel in self.channels:
            if channel.name == name:
                raise ValueError(f"Channel name '{name}' is already in use.")

        # Ensure combination of card_number and channel_number is unique
        for channel in self.channels:
            if channel.card_number == card_number and channel.channel_number == channel_number:
                raise ValueError(f"Card number {card_number} and channel number {channel_number} combination is already in use.")
                    
        channel = Digital_Channel(name, card_number, channel_number, reset, reset_value)
        self.channels.append(channel)
        return channel
    def find_channel_by_name(self, name: str) -> Optional[Channel]:
        for channel in self.channels:
            if channel.name == name:
                return channel
        return None
    def find_channel_by_channel_and_card_number(self, card_number: int, channel_number: int) -> Optional[Channel]:
        for channel in self.channels:
            if channel.card_number == card_number and channel.channel_number == channel_number:
                return channel
        return None


    def edit_digital_channel(self, name: str,new_name: Optional[str]=None, card_number: Optional[int]=None, channel_number: Optional[int]=None,  reset: Optional[bool]=None, reset_value: Optional[float]=None):
        channel = self.find_channel_by_name(name)
        # check if the new name is already taken by another channel
    
        if new_name is not None:
            temp_list_channel = [ch for ch in self.channels if ch.name != channel.name]
            for c in temp_list_channel:
                if c.name == new_name:
                    raise ValueError(f"Channel name {new_name} is already taken by another channel")
                
        # check if the new card_number and channel_number is already taken by another channel


        if card_number is not None or channel_number is not None:
            new_card_number = card_number if card_number is not None else channel.card_number
            new_channel_number = channel_number if channel_number is not None else channel.channel_number

            temp_list_channel = [ch for ch in self.channels if ch.name != channel.name]
            for c in temp_list_channel:
                if c.card_number == new_card_number and c.channel_number == new_channel_number:
                    raise ValueError(f"Card number {new_card_number} and channel number {new_channel_number} is already taken by another channel")
        
        if channel is None:
            raise ValueError(f"Channel {name} not found")
        if new_name is not None:
            channel.name = new_name
        if card_number is not None:
            channel.card_number = card_number
        if channel_number is not None:
            channel.channel_number = channel_number
        if reset is not None:
            channel.reset = reset
        if reset_value is not None:
            channel.reset_value = reset_value
    

    def edit_analog_channel(self, name: str,new_name: Optional[str]=None, card_number: Optional[int]=None, channel_number: Optional[int]=None, reset: Optional[bool]=None, reset_value: Optional[float]=None, default_voltage_func: Optional[Callable[[float], float]]=None, max_voltage: Optional[float]=None, min_voltage: Optional[float]=None):
        channel = self.find_channel_by_name(name)
        
        if channel is None:
            raise ValueError(f"Channel {name} not found")
        # check if the new name is already taken by another channel
        if new_name is not None:
            temp_list_channel = [ch for ch in self.channels if ch.name != channel.name]
            for c in temp_list_channel:
                if c.name == new_name:
                    raise ValueError(f"Channel name {new_name} is already taken by another channel")
        # check if the new card_number and channel_number is already taken by another channel
        if card_number is not None or channel_number is not None:
            new_card_number = card_number if card_number is not None else channel.card_number
            new_channel_number = channel_number if channel_number is not None else channel.channel_number
            temp_list_channel = [ch for ch in self.channels if ch.name != channel.name]

            for c in temp_list_channel:
                if c.card_number == new_card_number and c.channel_number == new_channel_number:
                    raise ValueError(f"Card number {new_card_number} and channel number {new_channel_number} is already taken by another channel")
                
        
        if new_name is not None:
            channel.name = new_name
        if card_number is not None:
            channel.card_number = card_number
        if channel_number is not None:
            channel.channel_number = channel_number
        if reset is not None:
            channel.reset = reset
        if reset_value is not None:
            channel.reset_value = reset_value
        if default_voltage_func is not None:
            channel.default_voltage_func = default_voltage_func
        if max_voltage is not None:
            channel.max_voltage = max_voltage
        if min_voltage is not None:
            channel.min_voltage = min_voltage

    def delete_channel(self, name: str) -> None:
        channel = self.find_channel_by_name(name)
        if channel is None:
            raise ValueError(f"Channel {name} not found")
        # loop through all events and remove the events from the channel and time instance
        for event in channel.events:
            if event.end_time_instance != event.start_time_instance:
                event.end_time_instance.ending_ramps.remove(event)
            event.start_time_instance.events.remove(event)
        self.channels.remove(channel)
        
    def delete_time_instance(self, name: str) -> None:
        # make sure the root time instance is not deleted
        if name == "root":
            raise ValueError("Cannot delete root time instance")
        # make a copy of the sequence 
        temp_sequence = self.create_a_copy_of_sequence()
        # remove every event from the time instance and its children 
        time_instance = temp_sequence.root_time_instance.get_time_instance_by_name(name)
        events = time_instance.events
        for event in events:
            if event.end_time_instance != event.start_time_instance:
                event.end_time_instance.ending_ramps.remove(event)
            event.start_time_instance.events.remove(event)
            event.channel.events.remove(event)
        # remove the time instance
        time_instance.delete_self()
        # check for overlapping events
        for channel in temp_sequence.channels:
            channel.check_for_overlapping_events()
        # apply the changes to the original sequence
        time_instance = self.root_time_instance.get_time_instance_by_name(name)
        events = time_instance.events
        for event in events:
            if event.end_time_instance != event.start_time_instance:
                event.end_time_instance.ending_ramps.remove(event)
            event.start_time_instance.events.remove(event)
            event.channel.events.remove(event)
        time_instance.delete_self()

    def sweep_time_instance_relative_time(self, sweep_time_instance: TimeInstance, relative_time_list: List[int]) -> List['Sequence']:
        # check if the sweep time instance is the root time instance
        # this retuns a list of new sequence with the updated time instances
        # it first creates a deep copy of the sequence and then edits the time instance relative time according to the list
        # Check if the sweep time instance is the root time instance
        if sweep_time_instance is self.root_time_instance:
            raise ValueError("Cannot sweep the root time instance")

        # List to hold the new sequences
        new_sequences = []

        for relative_time in relative_time_list:
            # Create a deep copy of the sequence
            temp_sequence = copy.deepcopy(self)
            
            # Find the corresponding time instance in the copied sequence
            copied_sweep_time_instance = temp_sequence.root_time_instance.get_time_instance_by_name(sweep_time_instance.name)
            
            # Edit the time instance relative time
            temp_sequence.edit_time_instance(copied_sweep_time_instance, new_relative_time=relative_time)
            
            # Append the modified sequence to the list of new sequences
            new_sequences.append(temp_sequence)

        return new_sequences
    def sweep_event_behavior(self, sweep_event: Event, value_list: List[float],parameter_name:str) -> List['Sequence']:
        # This function sweeps the event behavior of the provided event
        # It returns a list of new sequences with the updated event behavior
        # Create a deep copy of the sequence
        new_sequences = []
        for value in value_list:
            temp_sequence = copy.deepcopy(self)
            # Find the corresponding event in the copied sequence
            copied_sweep_event = temp_sequence.find_event_by_time_and_channel(sweep_event.start_time_instance.name, sweep_event.channel.name)
            # Edit the event behavior
            if isinstance(copied_sweep_event.behavior, Jump):
                copied_sweep_event.behavior.edit_jump(value)
            elif isinstance(copied_sweep_event.behavior, Ramp):
                if parameter_name == "start_value":
                    copied_sweep_event.behavior.edit_ramp(start_value=value)
                elif parameter_name == "end_value":
                    copied_sweep_event.behavior.edit_ramp(end_value=value)
                elif parameter_name == "resolution":
                    copied_sweep_event.behavior.edit_ramp(resolution=value)
                elif parameter_name == "ramp_type":
                    copied_sweep_event.behavior.edit_ramp(ramp_type=value)
            # Append the modified sequence to the list of new sequences
            new_sequences.append(temp_sequence)
        return new_sequences
    
    def to_json(self,filename: Optional[str] = None) -> str:
        def serialize_TimeInstances(TimeInstance: TimeInstance) -> dict:
            return {
                "relative_time": TimeInstance.relative_time,
                "name": TimeInstance.name,
                "events": [event.get_event_attributes() for event in TimeInstance.events],
                "ending_ramps": [event.get_event_attributes() for event in TimeInstance.ending_ramps],
                "children": [serialize_TimeInstances(child) for child in TimeInstance.children]
            }
        
        # get the root time instance
        # serialize the root time instance
        root_data = serialize_TimeInstances(self.root_time_instance)
        # serialize the channels


        data = {
            "name": self.sequence_name,
            "channels": [channel.get_channel_attributes() for channel in self.channels],
            "root_time_instance": root_data
        }
        if filename:
            with open(filename, 'w') as file:
                json.dump(data, file, indent=4)

        return json.dumps(data, indent=4)

    @staticmethod
    def from_json(file_name: Optional[str] = None,json_input: Optional[str] = None) -> 'Sequence':
        #print(json_input)
        if json_input is not None and file_name is not None:
            raise ValueError("Provide either a JSON string or a file name, not both.")

        if json_input is None and file_name is None:
            raise ValueError("Provide either a JSON string or a file name.")

        if file_name:
            with open(file_name, 'r') as file:
                json_str = file.read()
        else:
            json_str = json_input

        data = json.loads(json_str)
        sequence = Sequence(data["name"])
        for channel_data in data["channels"]:
            if channel_data["type"] == "analog":
                channel = Analog_Channel(channel_data["name"], channel_data["card_number"], channel_data["channel_number"], channel_data["reset"], channel_data["reset_value"], max_voltage=channel_data["max_voltage"], min_voltage=channel_data["min_voltage"])
            else:
                channel = Digital_Channel(channel_data["name"], channel_data["card_number"], channel_data["channel_number"], channel_data["reset"], channel_data["reset_value"])
            sequence.channels.append(channel)

        def deserialize_TimeInstances(TimeInstance_data: dict, parent: TimeInstance) -> TimeInstance:
            TimeInstance_new = TimeInstance(TimeInstance_data["name"], parent, TimeInstance_data["relative_time"])
            for child_data in TimeInstance_data["children"]:
                deserialize_TimeInstances(child_data, TimeInstance_new)
            for event_data in TimeInstance_data["events"]:
                channel = sequence.find_channel_by_name(event_data["channel_name"])
                if event_data["type"] == "jump":
                    behavior = Jump(event_data["jump_target_value"])
                else:
                    behavior = Ramp(TimeInstance_new,"temp", event_data["ramp_type"], event_data["start_value"], event_data["end_value"], event_data["resolution"])
                Event(channel, behavior, event_data["comment"],TimeInstance_new,"temp")
            for event_data in TimeInstance_data["ending_ramps"]:
                event = sequence.find_event_by_time_and_channel(TimeInstance_data["name"], event_data["channel_name"])
                event.end_time_instance = TimeInstance_new

            return TimeInstance_new
        
        root = deserialize_TimeInstances(data["root_time_instance"], None)
        sequence.root_time_instance = root
        return sequence

    

        
if __name__ == "__main__":
    seq = Sequence("test")
    ch1 = seq.add_analog_channel("ch1", 1, 1)
    ch2 = seq.add_analog_channel("ch2", 1, 2)
    ch3 = seq.add_analog_channel("ch3", 1, 3)
    ch4 = seq.add_analog_channel("ch4", 1, 4)

    root = seq.root_time_instance
    t1 = seq.add_time_instance("t1", root, 0)
    t2 = seq.add_time_instance("t2", root, 1000)
    t3 = seq.add_time_instance("t3", t2, 1000)
    t4 = seq.add_time_instance("t4", t3, 1000)
    t5 = seq.add_time_instance("t5", t4, 1000)
    t6 = seq.add_time_instance("t6", t5, 1000)


    e1 = seq.add_event(ch1, Jump(5), t1)
    e2 = seq.add_event(ch2, Jump(1), t1)
    e3 = seq.add_event(ch3, Jump(5), t1)
    e4 = seq.add_event(ch4, Jump(3), t1)
    e5 = seq.add_event(ch1, Jump(5), t2)
    e6 = seq.add_event(ch2, Jump(1.5), t2)
    e7 = seq.add_event(ch3, Jump(5), t3)

    # print(seq.to_json())
    seq.to_json (filename="test1.json")
    seq2= Sequence.from_json(file_name="test1.json")
    seq2.to_json(filename="test2.json")
     
