import unittest
import json
import bisect
import csv
import math
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, List, Optional, Union,Tuple, Dict, Any 
import matplotlib.pyplot as plt
import copy

import matplotlib.cm as cm
import numpy as np


class Parameter:
    def __init__(self, name: str,event: 'Event',parameter_origin):
        self.name = name
        self.event = event
        self.parameter_origin = parameter_origin
    def get_value(self): 
        print(self.event.get_event_attributes())
        print(self.parameter_origin)
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


class sine(EventBehavior):
    def __init__(self, amplitude: float, frequency: float, phase: float, offset: float,resolution: float=0.001):
        if amplitude < 0:
            raise ValueError("amplitude must be non-negative")
        if frequency <= 0:
            raise ValueError("frequency must be positive")
        if offset < 0:
            raise ValueError("offset must be non-negative")
        

        self.amplitude = amplitude
        self.frequency = frequency
        self.phase = phase
        self.offset = offset
        self.resolution=resolution

    def get_value_at_time(self, t: float) -> float:
        return self.amplitude * np.sin(2 * np.pi * self.frequency * t + self.phase) + self.offset
    
    def __repr__(self) -> str:
        return f"sine({self.amplitude}, {self.frequency}, {self.phase}, {self.offset})"
    


class Ramp(EventBehavior):
    def __init__(self, duration: float, ramp_type: RampType = RampType.LINEAR, start_value: float = 0, end_value: float = 1, func: Optional[Callable[[float], float]] = None, resolution=0.001):
        if start_value == end_value:
            raise ValueError("start_value and end_value must be different")
        
        if duration == 0:
            raise ValueError("duration must be non-zero")
        
        if ramp_type == RampType.EXPONENTIAL and (start_value == 0 or end_value == 0):
            raise ValueError("For exponential ramp, start_value and end_value must be non-zero")

        if resolution < 0.000001:
            raise ValueError("resolution must be at least 0.000001")
        
        self.duration = duration
        self.ramp_type = ramp_type
        self.start_value = start_value
        self.end_value = end_value
        self.resolution = resolution
        
        print (self.ramp_type)
        if func:
            self.func = func
        else:
            self._set_func()

    def _set_func(self):
        if self.ramp_type == RampType.LINEAR:
            self.func = lambda t: self.start_value + (self.end_value - self.start_value) * (t / self.duration)
        elif self.ramp_type == RampType.QUADRATIC:
            self.func = lambda t: self.start_value + (self.end_value - self.start_value) * (t / self.duration)**2
        elif self.ramp_type == RampType.EXPONENTIAL:
            self.func = lambda t: self.start_value * (self.end_value / self.start_value) ** (t / self.duration)
        elif self.ramp_type == RampType.LOGARITHMIC:
            self.func = lambda t: self.start_value + (self.end_value - self.start_value) * (np.log10(t + 1) / np.log10(self.duration + 1))
        elif self.ramp_type == RampType.MINIMUM_JERK:
            self.func = lambda t: self.start_value + (self.end_value - self.start_value) * (10 * (t/self.duration)**3 - 15 * (t/self.duration)**4 + 6 * (t/self.duration)**5)
        else : 
            raise ValueError("Invalid ramp type")
        
    def edit_ramp(self, duration: Optional[float] = None, ramp_type: Optional[RampType] = None, start_value: Optional[float] = None, end_value: Optional[float] = None, func: Optional[Callable[[float], float]] = None, resolution: Optional[float] = None):
        new_duration = duration if duration is not None else self.duration
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
        
        if new_duration == 0:
            raise ValueError("duration must be non-zero")
        
        if new_ramp_type == RampType.EXPONENTIAL and (new_start_value == 0 or new_end_value == 0):
            raise ValueError("For exponential ramp, start_value and end_value must be non-zero")
        
        if new_resolution < 0.000001:
            raise ValueError("resolution must be at least 0.000001")
        
        # Apply changes only after validation
        self.duration = new_duration
        self.ramp_type = new_ramp_type
        self.start_value = new_start_value
        self.end_value = new_end_value
        self.resolution = new_resolution

        if func:
            self.func = func
        else:
            self._set_func()


    def get_value_at_time(self, t: float) -> float:
        if 0 <= t <= self.duration:
            return self.func(t)
        else:
            return self.end_value
    
    def __repr__(self) -> str:
        return f"Ramp({self.duration}, {self.ramp_type.value}, {self.start_value}, {self.end_value})"

class Channel:
    def __init__(self, name: str, card_number: int, channel_number: int, reset: bool, reset_value: float):
        self.name = name
        self.card_number = card_number
        self.channel_number = channel_number
        self.reset = reset
        self.reset_value = reset_value
        self.events: List[Event] = []
    
    def add_event(self, event: 'Event'):
        index = bisect.bisect_left([e.start_time for e in self.events], event.start_time)
        self.events.insert(index, event)

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
    def check_for_overlapping_events(self):
        self.events.sort(key=lambda event: event.start_time)
        for i in range(len(self.events) - 1):
            current_event = self.events[i]
            next_event = self.events[i + 1]
            if current_event.end_time > next_event.start_time:
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
    
    def __eq__(self, other: object) -> bool:
        return super().__eq__(other) and self.default_voltage_func == other.default_voltage_func and self.max_voltage == other.max_voltage and self.min_voltage == other.min_voltage

class Digital_Channel(Channel):
    def __init__(self, name: str, card_number: int, channel_number: int, card_id: str, bitpos: int, reset: bool = False, reset_value: float = 0):
        super().__init__(name, card_number, channel_number, reset, reset_value)
        self.card_id = card_id
        self.bitpos = bitpos

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other) and self.card_id == other.card_id and self.bitpos == other.bitpos

    def __repr__(self) -> str:
        return (
            f"Digital_Channel(\n"
            f"   name={self.name},\n"
            f"   card_number={self.card_number},\n"
            f"   channel_number={self.channel_number},\n"
            f"   card_id={self.card_id},\n"
            f"   bitpos={self.bitpos},\n"
            f"   reset={self.reset},\n"
            f"   reset_value={self.reset_value},\n"
            f"   events={self.events}\n"
            f")"
        )

class Event:
    def __init__(self, channel: Channel, behavior: EventBehavior, start_time: Optional[float] = None, relative_time: Optional[float] = None, reference_time: str = "start", parent: Optional['Event'] = None):
        if start_time is not None and relative_time is not None:
            raise ValueError("Provide either start_time or relative_time, not both.")

        self.channel = channel
        self.behavior = behavior
        self.parent = parent
        self.reference_time = reference_time if parent else None

        self.is_sweept = False
        self.reference_original_event = self
        self.associated_parameters = []

        if start_time is not None:
            self.start_time = start_time
            self.relative_time = None
        else:
            if parent is None:
                raise ValueError("Root event must have start_time specified.")
            self.reference_time = reference_time
            self.relative_time = relative_time
            if reference_time == "start":
                self.start_time = parent.start_time + relative_time
            elif reference_time == "end":
                self.start_time = parent.end_time + relative_time
            else:
                raise ValueError("Invalid reference_time. Use 'start' or 'end'.")

        if isinstance(behavior, Ramp) and not isinstance(behavior, Jump):
            self.end_time = self.start_time + behavior.duration
        else:
            self.end_time = self.start_time

        self.check_for_overlap(channel, behavior, self.start_time, self.end_time)

        self.children: List[Event] = []
        index = bisect.bisect_left([e.start_time for e in self.channel.events], self.start_time)
        self.channel.events.insert(index, self)


    def get_event_attributes(self):
        if isinstance(self.behavior, Jump):
            
                
            return {
                "jump_target_value": self.behavior.target_value,
                "start_time": self.start_time,
                "relative_time": self.relative_time,
                "reference_time" : self.reference_time    
                }

        elif isinstance(self.behavior, Ramp):
            return {
                "duration": self.behavior.duration,
                "ramp_type": self.behavior.ramp_type,
                "start_value": self.behavior.start_value,
                "end_value": self.behavior.end_value,
                "func": self.behavior.func,
                "resolution": self.behavior.resolution,
                "start_time": self.start_time,
                "relative_time": self.relative_time,
                "reference_time" : self.reference_time    
                }   

    def update_times(self, delta: float):
        self.start_time += delta
        self.end_time += delta
        for child in self.children:
            child.update_times(delta)
    
    def update_times_end(self, delta: float):
        self.end_time += delta
        for child in self.children:
            if child.reference_time == 'end':
                child.update_times(delta)

    def update_relative_time(self, new_relative_time: float, new_reference_time: Optional[str] = None):
        if new_reference_time:
            self.reference_time = new_reference_time

        if self.reference_time == "start":
            parent_time = self.parent.start_time
        elif self.reference_time == "end":
            parent_time = self.parent.end_time
        else:
            raise ValueError("Invalid reference_time. Use 'start' or 'end'.")

        delta = (parent_time + new_relative_time) - self.start_time
        self.relative_time = new_relative_time
        self.update_times(delta)

    def check_for_overlap(self, channel: Channel, behavior: EventBehavior, start_time: float, end_time: float):
        for event in channel.events:
            if not (end_time < event.start_time or start_time > event.end_time):
                if isinstance(behavior, Jump) and isinstance(event.behavior, Jump):
                    if start_time == event.start_time:
                        raise ValueError(f"Cannot have more than one jump at the same time on channel {channel.name}.")
                elif isinstance(behavior, Jump) and isinstance(event.behavior, Ramp):
                    if start_time != event.end_time:
                        raise ValueError(f"Jump events can only be added at the end of a ramp on channel {channel.name}.")
                else:
                    raise ValueError(f"Events on channel {channel.name} overlap with existing event {event.behavior} from {event.start_time} to {event.end_time}.")



    def __gt__(self, other: 'Event') -> bool:
        return self.start_time > other.start_time

    def __lt__(self, other: 'Event') -> bool:
        return self.start_time < other.start_time

    def __ge__(self, other: 'Event') -> bool:
        return self.__gt__(other) or self.start_time == other.start_time

    def __le__(self, other: 'Event') -> bool:
        return self.__lt__(other) or self.start_time == self.start_time

    def __repr__(self) -> str:
        return (
            f"Event(\n"
            f"    channel={self.channel.name},\n"
            f"    behavior={self.behavior},\n"
            f"    start_time={self.start_time},\n"
            f"    end_time={self.end_time},\n"
            f"    parent={self.parent.channel.name if self.parent else None}\n"
            f")"
        )
    

    def print_event_hierarchy(self, level: int = 0, indent: str = "    "):
        """Prints the event and its children recursively with indentation, avoiding duplicates."""
        print(f"{indent*level}{self.behavior} on {self.channel.name} at {self.start_time}")

        for child in self.children:
            child.print_event_hierarchy(level + 1, indent)
    
    def get_text_event_hierarchy(self, level: int = 0, indent: str = "    "):
        """Prints the event and its children recursively with indentation, avoiding duplicates."""
        text = f"{indent*level}{self.behavior} on {self.channel.name} at {self.start_time}\n"

        for child in self.children:
            text += child.get_text_event_hierarchy(level + 1, indent)
        
        return text     



class Sequence:
    def __init__(self,name:str):
        
        self.sequence_name=name

        
        # list of all channels in the sequence 
        self.channels: List[Channel] = []
        # list of all events in the sequence 
        self.all_events: List[Event] = []




    def check_for_overlapping_events(self):
        for channel in self.channels:
            channel.check_for_overlapping_events()
    

    def add_parameter_to_event(self,event: Event,parameter_name,parameter_value,parameter_origin):
        # ff the event is not in the sequence
        if event not in self.all_events:
            raise ValueError("Event not found in the sequence")
        p = Parameter(parameter_name,event,parameter_origin)
        event.associated_parameters.append(p)



    def remove_parameter(self,parameter_name):
        for event in self.all_events:
            for p in event.associated_parameters:
                if p.name == parameter_name:
                    event.associated_parameters.remove(p)

                    return
        raise ValueError("Parameter not found in the sequence")
    
    
    def get_parameter_dict(self):
        parameter_dict = {}
        for event in self.all_events:
            for p in event.associated_parameters:
                parameter_dict[p.name] = p.get_value() 
        return parameter_dict
        
        
    # add a new analog channel to the sequence
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
    def add_digital_channel(self, name: str, card_number: int, channel_number: int, card_id: str, bitpos: int, reset: bool = False, reset_value: float = 0) -> Digital_Channel:
        for channel in self.channels:
            if channel.name == name:
                raise ValueError(f"Channel name '{name}' is already in use.")

        # Ensure combination of card_number and channel_number is unique
        for channel in self.channels:
            if channel.card_number == card_number and channel.channel_number == channel_number:
                raise ValueError(f"Card number {card_number} and channel number {channel_number} combination is already in use.")
                    
        channel = Digital_Channel(name, card_number, channel_number, card_id, bitpos, reset, reset_value)
        self.channels.append(channel)
        return channel

    def edit_digital_channel(self, name: str,new_name: Optional[str]=None, card_number: Optional[int]=None, channel_number: Optional[int]=None, card_id: Optional[str]=None, bitpos: Optional[int]=None, reset: Optional[bool]=None, reset_value: Optional[float]=None):
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
        if card_id is not None:
            channel.card_id = card_id
        if bitpos is not None:
            channel.bitpos = bitpos
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
        
    def delete_channel(self, name: str):
        #check first for a temp sequence
        temp_sequence = copy.deepcopy(self)
        self.copy_original_events_to_new_sequence(self, temp_sequence)
        
        channel = temp_sequence.find_channel_by_name(name)
        
        channel = self.find_channel_by_name(name)
        if channel is None:
            raise ValueError(f"Channel {name} not found")
        for event in channel.events:
            self.delete_event(start_time=event.start_time,channel_name=name)
        
        temp_sequence.channels.remove(channel)

        # Apply the changes to the original sequence if no overlaps are found
        channel = self.find_channel_by_name(name)
        for event in channel.events:
            self.delete_event(start_time=event.start_time,channel_name=name)
        self.channels.remove(channel)



    # add a new event to the sequence
    def add_event(self, channel_name: str, behavior: EventBehavior, start_time: Optional[float] = None, relative_time: Optional[float] = None, reference_time: str = "start", parent_event: Optional[Event] = None) -> Event:
        if start_time is not None and relative_time is not None:
            raise ValueError("Provide either start_time or relative_time, not both.")

        channel = self.find_channel_by_name(channel_name)
        
        if channel is None:
            raise ValueError(f"Channel {channel_name} not found")

        if isinstance(channel, Digital_Channel) and isinstance(behavior, Ramp):
            raise ValueError("Ramp behavior cannot be added to a digital channel.")

        # check if the  behavior is a jump and is not within the max min range of the channel 
        if isinstance(channel, Analog_Channel) and isinstance(behavior, Jump):
            if behavior.target_value > channel.max_voltage or behavior.target_value < channel.min_voltage:
                raise ValueError(f"Jump value {behavior.target_value} is out of range for channel {channel.name} with min voltage {channel.min_voltage} and max voltage {channel.max_voltage}")
        
        if isinstance(channel, Analog_Channel) and isinstance(behavior, Ramp):
            if behavior.start_value > channel.max_voltage or behavior.start_value < channel.min_voltage:
                raise ValueError(f"Ramp start value {behavior.start_value} is out of range for channel {channel.name} with min voltage {channel.min_voltage} and max voltage {channel.max_voltage}")
            if behavior.end_value > channel.max_voltage or behavior.end_value < channel.min_voltage:
                raise ValueError(f"Ramp end value {behavior.end_value} is out of range for channel {channel.name} with min voltage {channel.min_voltage} and max voltage {channel.max_voltage}")
        

        if parent_event is None:
            if start_time is None:
                raise ValueError("Root event must have start_time specified.")
            if start_time < 0:
                raise ValueError("start_time must be non-negative.")
            event = Event(channel, behavior, start_time=start_time)
        else:
            if relative_time is None:
                raise ValueError("Child event must have relative_time specified.")
            if relative_time+parent_event.start_time < 0:
                raise ValueError("Negative time is not allowed.")
            
            event = Event(channel, behavior, relative_time=relative_time, reference_time=reference_time, parent=parent_event)
            parent_event.children.append(event)

        bisect.insort(self.all_events, event)  # Sort by start_time
        return event

    # find a channel by its name 
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

    # find an event by its start time and channel name
    def find_event_by_time_and_channel(self, start_time: float, channel_name: str) -> Optional[Event]:
        channel = self.find_channel_by_name(channel_name)
        if channel is None:
            return None
        # Binary search for the event in the sorted list
        index = bisect.bisect_left([event.start_time for event in channel.events], start_time)
        if index != len(channel.events) and channel.events[index].start_time == start_time:
            return channel.events[index]
        return None
    
    # add a new event in the middle of the sequence
    def add_event_in_middle(self, parent_start_time: float, parent_channel_name: str, child_events: List[tuple], relative_time: float, reference_time: str, behavior: EventBehavior, channel_name: str) -> Event:
        temp_sequence = copy.deepcopy(self)
        self.copy_original_events_to_new_sequence(self, temp_sequence)
        parent_event = temp_sequence.find_event_by_time_and_channel(parent_start_time, parent_channel_name)
        if parent_event is None:
            raise ValueError(f"Parent event not found for start_time {parent_start_time} and channel {parent_channel_name}")

        new_event = temp_sequence.add_event(channel_name, behavior, relative_time=relative_time, reference_time=reference_time, parent_event=parent_event)

        for child_start_time, child_channel_name in child_events:
            child_event = temp_sequence.find_event_by_time_and_channel(child_start_time, child_channel_name)
            if child_event is None:
                raise ValueError(f"Child event not found for start_time {child_start_time} and channel {child_channel_name}")
            if child_event.parent != parent_event:
                raise ValueError(f"Event {child_event} is not a child of {parent_event}")

            parent_event.children.remove(child_event)
            child_event.parent = new_event
            new_event.children.append(child_event)

            if child_event.reference_time == 'start':
                new_start_time = new_event.start_time + child_event.relative_time
            elif child_event.reference_time == 'end':
                new_start_time = new_event.end_time + child_event.relative_time
            else:
                raise ValueError("Invalid reference_time. Use 'start' or 'end'.")

            delta = new_start_time - child_event.start_time
            child_event.update_times(delta)

        for channel in temp_sequence.channels:
            channel.check_for_overlapping_events()

        # Apply the changes to the original sequence if no overlaps are found
        parent_event = self.find_event_by_time_and_channel(parent_start_time, parent_channel_name)
        new_event = self.add_event(channel_name, behavior, relative_time=relative_time, reference_time=reference_time, parent_event=parent_event)

        for child_start_time, child_channel_name in child_events:
            child_event = self.find_event_by_time_and_channel(child_start_time, child_channel_name)
            parent_event.children.remove(child_event)
            child_event.parent = new_event
            new_event.children.append(child_event)
            delta = (new_event.start_time + child_event.relative_time) - child_event.start_time
            child_event.update_times(delta)

        return new_event

    # add a new event at the end of the sequence
    def get_all_events(self) -> List[Event]:
        return self.all_events

    # print all events in the sequence 
    def print_sequence(self,channel_name:str=None):

        if channel_name is not None:
            channel = self.find_channel_by_name(channel_name)
            for event in channel.events:
                print(f"Event: {event.behavior} on {event.channel.name} at {event.start_time}")
        else:
                
            for event in self.all_events:
                print(f"Event: {event.behavior} on {event.channel.name} at {event.start_time}")

    # update the absolute time of an event
    def update_event_absolute_time(self, start_time: float, channel_name: str, new_start_time: float):
        temp_sequence = copy.deepcopy(self)
        self.copy_original_events_to_new_sequence(self, temp_sequence)
        event = temp_sequence.find_event_by_time_and_channel(start_time, channel_name)
        if event is None:
            raise ValueError(f"Event not found for start_time {start_time} and channel {channel_name}")
        if event.parent is not None:
            raise ValueError("Only non-child events can have their absolute time changed.")

        delta = new_start_time - event.start_time
        event.update_times(delta)

        for channel in temp_sequence.channels:
            channel.check_for_overlapping_events()

        # Apply the changes to the original sequence if no overlaps are found
        event = self.find_event_by_time_and_channel(start_time, channel_name)
        delta = new_start_time - event.start_time
        event.update_times(delta)
        self.all_events.sort(key=lambda event: event.start_time)

    # update the relative time of an event 
    def update_event_relative_time(self, start_time: float, channel_name: str, new_relative_time: float, new_reference_time: Optional[str] = None):
        temp_sequence = copy.deepcopy(self)
        self.copy_original_events_to_new_sequence(self, temp_sequence)
        event = temp_sequence.find_event_by_time_and_channel(start_time, channel_name)
        if event is None:
            raise ValueError(f"Event not found for start_time {start_time} and channel {channel_name}")
        if event.parent is None:
            raise ValueError("Only child events can have their relative time changed.")

        if new_reference_time is None:
            new_reference_time = event.reference_time

        if new_reference_time == "start":
            new_start_time = event.parent.start_time + new_relative_time
        elif new_reference_time == "end":
            new_start_time = event.parent.end_time + new_relative_time
        else:
            raise ValueError("Invalid reference_time. Use 'start' or 'end'.")

        delta = new_start_time - event.start_time
        event.reference_time = new_reference_time
        event.update_times(delta)

        for channel in temp_sequence.channels:
            channel.check_for_overlapping_events()

        # Apply the changes to the original sequence if no overlaps are found
        event = self.find_event_by_time_and_channel(start_time, channel_name)
        event.update_relative_time(new_relative_time, new_reference_time)
        self.all_events.sort(key=lambda event: event.start_time)

    # delete an event from the sequence
    def delete_event(self, start_time: Optional[float]= None, channel_name: Optional[str]= None,event_to_delete: Optional[Event]=None):
        
        
        temp_sequence = copy.deepcopy(self)
        self.copy_original_events_to_new_sequence(self, temp_sequence)

        if (event_to_delete is not None) and (start_time is not  None) and (channel_name is not None):
            raise ValueError("Provide either event_to_delete or start_time and channel_name, not both.")
        if event_to_delete is None and (start_time is None or channel_name is None):
            raise ValueError("Provide either event_to_delete or start_time and channel_name.")
        if event_to_delete is not None:
            start_time = event_to_delete.start_time
            channel_name = event_to_delete.channel.name
        
        event = temp_sequence.find_event_by_time_and_channel(start_time, channel_name)
        if event is None:
            raise ValueError(f"Event not found for start_time {start_time} and channel {channel_name}")

        if event.parent is None:
            for child in event.children:
                child.parent = None
        else:
            parent = event.parent
            for child in event.children:
                child.parent = parent
                parent.children.append(child)
                if child.reference_time == 'start':
                    new_start_time = parent.start_time + child.relative_time
                elif child.reference_time == 'end':
                    new_start_time = parent.end_time + child.relative_time
                else:
                    raise ValueError("Invalid reference_time. Use 'start' or 'end'.")
                delta = new_start_time - child.start_time
                child.update_times(delta)
                
        event.children.clear()
        
        event.channel.events.remove(event)
        temp_sequence.all_events.remove(event)
        
        for channel in temp_sequence.channels:
            channel.check_for_overlapping_events()

        # Apply the changes to the original sequence if no overlaps are found
        event = self.find_event_by_time_and_channel(start_time, channel_name)
        if event.parent is None:
            for child in event.children:
                child.parent = None
        else:
            parent = event.parent
            for child in event.children:
                child.parent = parent
                parent.children.append(child)
                if child.reference_time == 'start':
                    new_start_time = parent.start_time + child.relative_time
                elif child.reference_time == 'end':
                    new_start_time = parent.end_time + child.relative_time
                else:
                    raise ValueError("Invalid reference_time. Use 'start' or 'end'.")
                delta = new_start_time - child.start_time
                child.update_times(delta)
                
        event.children.clear()
        
        event.channel.events.remove(event)
        self.all_events.remove(event)
        
        self.all_events.sort(key=lambda event: event.start_time)

    

    def edit_event(self, start_time: Optional[float]=None, channel_name: Optional[str]=None,
                   edited_event: Optional[Event]=None,
                    duration: Optional[float] = None, ramp_type: Optional[RampType] = None, start_value: Optional[float] = None, end_value: Optional[float] = None, func: Optional[Callable[[float], float]] = None, resolution: Optional[float] = None, 
                    jump_target_value: Optional[float] = None,
                      new_start_time: Optional[float] = None,
                        new_relative_time: Optional[float] = None,
                          new_reference_time: Optional[str] = None):
        temp_sequence = copy.deepcopy(self)
        self.copy_original_events_to_new_sequence(self, temp_sequence)
        

        
        if (edited_event is not None) and (start_time is not  None) and (channel_name is not None):
            raise ValueError("Provide either edited_event or start_time and channel_name, not both.")
        
        if edited_event is None and (start_time is None or channel_name is None):
            raise ValueError("Provide either edited_event or start_time and channel_name.")
        

        if edited_event is None:
            event = temp_sequence.find_event_by_time_and_channel(start_time, channel_name)
        else:
            event = temp_sequence.find_event_by_original_reference(edited_event)

        # check if the new values are within the range of the channel 
        if jump_target_value is not None and isinstance(event.behavior, Jump):
            if jump_target_value > event.channel.max_voltage or jump_target_value < event.channel.min_voltage:
                raise ValueError(f"Jump value {jump_target_value} is out of range for channel {event.channel.name} with min voltage {event.channel.min_voltage} and max voltage {event.channel.max_voltage}")
        if start_value is not None and isinstance(event.behavior, Ramp):
            if start_value > event.channel.max_voltage or start_value < event.channel.min_voltage:
                raise ValueError(f"Ramp start value {start_value} is out of range for channel {event.channel.name} with min voltage {event.channel.min_voltage} and max voltage {event.channel.max_voltage}")
        if end_value is not None and isinstance(event.behavior, Ramp):
            if end_value > event.channel.max_voltage or end_value < event.channel.min_voltage:
                raise ValueError(f"Ramp end value {end_value} is out of range for channel {event.channel.name} with min voltage {event.channel.min_voltage} and max voltage {event.channel.max_voltage}")
            


        if event is None:
            raise ValueError(f"Event not found for start_time {start_time} and channel {channel_name}")

        if new_start_time is not None and new_relative_time is not None:
            raise ValueError("Provide either new_start_time or new_relative_time, not both.")

        if new_start_time is not None:
            delta = new_start_time - event.start_time
            event.update_times(delta)
        elif new_relative_time is not None:
            if new_reference_time is None:
                new_reference_time = event.reference_time

            if new_reference_time == "start":
                new_start_time = event.parent.start_time + new_relative_time
            elif new_reference_time == "end":
                new_start_time = event.parent.end_time + new_relative_time
            else:
                raise ValueError("Invalid reference_time. Use 'start' or 'end'.")
            if new_start_time < 0:
                raise ValueError("Negative time is not allowed.")

            delta = new_start_time - event.start_time
            event.reference_time = new_reference_time
            event.update_times(delta)

        if isinstance(event.behavior, Ramp): 
            event.behavior.edit_ramp(duration, ramp_type, start_value, end_value, func, resolution)
            delta_duration = event.behavior.duration-  event.end_time+  event.start_time 
            if delta_duration:
                event.update_times_end(delta_duration)

        elif isinstance(event.behavior, Jump):
            event.behavior.edit_jump(jump_target_value)
        
        temp_sequence.all_events.sort(key=lambda event: event.start_time)

        for channel in temp_sequence.channels:
            channel.events.sort(key=lambda event: event.start_time)
            channel.check_for_overlapping_events()

        # Apply the changes to the original sequence if no overlaps are found
        if edited_event is None:
            event = self.find_event_by_time_and_channel(start_time, channel_name)
        else:
            event = self.find_event_by_original_reference(edited_event)    


        if new_start_time is not None:
            delta = new_start_time - event.start_time
            event.update_times(delta)
        elif new_relative_time is not None:
            if new_reference_time is None:
                new_reference_time = event.reference_time

            if new_reference_time == "start":
                new_start_time = event.parent.start_time + new_relative_time
            elif new_reference_time == "end":
                new_start_time = event.parent.end_time + new_relative_time
            else:
                raise ValueError("Invalid reference_time. Use 'start' or 'end'.")

            delta = new_start_time - event.start_time
            event.reference_time = new_reference_time
            event.update_times(delta)

        if isinstance(event.behavior, Ramp): 
            event.behavior.edit_ramp(duration, ramp_type, start_value, end_value, func, resolution)
            delta_duration = event.behavior.duration-  event.end_time+  event.start_time 
            if delta_duration:
                # print("delta_duration",delta_duration)
                event.update_times_end(delta_duration)

        elif isinstance(event.behavior, Jump):
            event.behavior.edit_jump(jump_target_value)
        
        
        if event.associated_parameters: 
            # update associated_parameters
            
            pass 

        
        self.all_events.sort(key=lambda event: event.start_time)

        for channel in self.channels:
            channel.events.sort(key=lambda event: event.start_time)
            channel.check_for_overlapping_events()

    def find_event_by_original_reference(self, reference_original_event: Event) -> Optional[Event]:
        if reference_original_event is None:
            raise ValueError("Provide a valid reference_original_event.")
        for event in self.all_events:
            if event.reference_original_event == reference_original_event:
                return event
        raise ValueError("Event not found.")

    @staticmethod
    def copy_original_events_to_new_sequence(original_sequence: 'Sequence', new_sequence: 'Sequence'):
        for event in original_sequence.all_events:
            # print("event",event)
            new_event = new_sequence.find_event_by_time_and_channel(event.start_time, event.channel.name)
            # print("new_event",new_event)
            new_event.reference_original_event = event.reference_original_event
            new_event.is_sweept = True
    

    def sweep_event_parameters(self, parameter: str, values: List[float],start_time: Optional[float]=None, channel_name: Optional[str]=None, event_to_sweep: Optional[Event] = None):
        # Find the event to sweep
        if event_to_sweep is not None and start_time is not  None and channel_name is not None:
            raise ValueError("Provide either event_to_sweep or start_time and channel_name, not both.")
        
        if event_to_sweep is None and (start_time is None or channel_name is None):
            raise ValueError("Provide either event_to_sweep or start_time and channel_name.")
        


        
        list_of_sequences=dict()
        # know which parameter to sweep
        if parameter == "duration":
            for value in values:
                temp_sequence = copy.deepcopy(self)        
                self.copy_original_events_to_new_sequence(self, temp_sequence)

                try:
                    temp_sequence.edit_event( edited_event=event_to_sweep, start_time=start_time, channel_name=channel_name, duration=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "ramp_type":
            for value in values:
                temp_sequence = copy.deepcopy(self)        
                self.copy_original_events_to_new_sequence(self, temp_sequence)

                try:
                    temp_sequence.edit_event( edited_event=event_to_sweep, start_time=start_time, channel_name=channel_name, ramp_type=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "start_value":
            for value in values:
                temp_sequence = copy.deepcopy(self)        
                self.copy_original_events_to_new_sequence(self, temp_sequence)

                try:
                    temp_sequence.edit_event( edited_event=event_to_sweep, start_time=start_time, channel_name=channel_name, start_value=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "end_value":
            for value in values:
                temp_sequence = copy.deepcopy(self)        
                self.copy_original_events_to_new_sequence(self, temp_sequence)

                try:
                    temp_sequence.edit_event( edited_event=event_to_sweep, start_time=start_time, channel_name=channel_name, end_value=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "func":
            for value in values:
                temp_sequence = copy.deepcopy(self)        
                self.copy_original_events_to_new_sequence(self, temp_sequence)

                try:
                    temp_sequence.edit_event( edited_event=event_to_sweep, start_time=start_time, channel_name=channel_name, func=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "resolution":
            for value in values:
                temp_sequence = copy.deepcopy(self)        
                self.copy_original_events_to_new_sequence(self, temp_sequence)

                try:
                    temp_sequence.edit_event( edited_event=event_to_sweep, start_time=start_time, channel_name=channel_name, resolution=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "jump_target_value":
            for value in values:
                temp_sequence = copy.deepcopy(self)        
                self.copy_original_events_to_new_sequence(self, temp_sequence)

                try:
                    temp_sequence.edit_event( edited_event=event_to_sweep, start_time=start_time, channel_name=channel_name, jump_target_value=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "start_time":
            for value in values:
                temp_sequence = copy.deepcopy(self)        
                self.copy_original_events_to_new_sequence(self, temp_sequence)

                try:
                    temp_sequence.edit_event( edited_event=event_to_sweep, start_time=start_time, channel_name=channel_name, new_start_time=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "relative_time":
            for value in values:
                temp_sequence = copy.deepcopy(self)        
                self.copy_original_events_to_new_sequence(self, temp_sequence)

                try:
                    temp_sequence.edit_event( edited_event=event_to_sweep, start_time=start_time, channel_name=channel_name, new_relative_time=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "reference_time":
            for value in values:
                temp_sequence = copy.deepcopy(self)        
                self.copy_original_events_to_new_sequence(self, temp_sequence)

                try:
                    temp_sequence.edit_event( edited_event=event_to_sweep, start_time=start_time, channel_name=channel_name, new_reference_time=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        else:

            raise ValueError(f"Invalid parameter: {parameter}")

        return list_of_sequences
        




    def print_event_tree(self, level: int = 0, indent: str = "    "):
        root_events = [event for event in self.all_events if event.parent is None]
        for root_event in root_events:
            root_event.print_event_hierarchy(level, indent)
        
    def get_event_tree(self, level: int = 0, indent: str = "    "):
        root_events = [event for event in self.all_events if event.parent is None]
        event_tree_text = ""
        for root_event in root_events:
            event_tree_text+=root_event.get_text_event_hierarchy(level, indent)+"\n"
        return event_tree_text
    
    
    #string of the class 
    def __repr__(self) -> str:
        return (
            f"Sequence(\n"
            f"   channels={self.channels},\n"
            f"   all_events={self.all_events}\n"
            f")"
        )


    def plot_all(self, channels_to_plot: Optional[List[str]] = None, resolution: float = 0.1, start_time: Optional[float] = None, end_time: Optional[float] = None,plot_now: bool =True):
        if channels_to_plot is None:
            channels_to_plot = [channel.name for channel in self.channels]
        else:
            invalid_channels = [name for name in channels_to_plot if not any(channel.name == name for channel in self.channels)]
            if invalid_channels:
                raise ValueError(f"Invalid channel names: {', '.join(invalid_channels)}")
        
        if start_time is None or end_time is None:
            all_time_points = sorted(set(event.start_time for event in self.all_events) | set(event.end_time for event in self.all_events))
            if start_time is None:
                start_time = all_time_points[0]
            if end_time is None:
                end_time = all_time_points[-1]
        
        fig, ax = plt.subplots(figsize=(12, 6))

        y_offset = 0

        for channel_name in channels_to_plot:
            channel = next(channel for channel in self.channels if channel.name == channel_name)
            events = sorted(channel.events, key=lambda event: event.start_time)
            
            time_points: List[float] = []
            values: List[float] = []
            last_value = channel.reset_value
            
            for event in events:
                if event.start_time > end_time:
                    break
                if event.end_time < start_time:
                    continue
                
                if event.start_time > start_time and (not time_points or time_points[-1] < start_time):
                    time_points.append(start_time)
                    values.append(last_value + y_offset)
                
                if time_points and event.start_time > time_points[-1]:
                    time_points.append(event.start_time)
                    values.append(last_value + y_offset)
                
                current_time = max(start_time, event.start_time)
                while current_time <= min(end_time, event.end_time):
                    time_points.append(current_time)
                    last_value = event.behavior.get_value_at_time(current_time - event.start_time)
                    values.append(last_value + y_offset)
                    current_time += resolution
                
                if current_time > event.end_time:
                    last_value = event.behavior.get_value_at_time(event.end_time - event.start_time)
                    time_points.append(event.end_time)
                    values.append(last_value + y_offset)
            
            if not time_points or time_points[-1] < end_time:
                time_points.append(end_time)
                values.append(last_value + y_offset)
            
            ax.plot(time_points, values, label=channel.name)
            y_offset += 10  # Translate the y values for each channel by an offset

        ax.set_xlabel("Time")
        ax.set_ylabel("Value")
        ax.legend()
        ax.grid(True)
        
        plt.tight_layout()
        if plot_now:
            plt.show()

    def plot(self, channels_to_plot: Optional[List[str]] = None, resolution: float = 0.1, start_time: Optional[float] = None, end_time: Optional[float] = None, plot_now: bool =True):
        if channels_to_plot is None:
            channels_to_plot = [channel.name for channel in self.channels]
        else:
            invalid_channels = [name for name in channels_to_plot if not any(channel.name == name for channel in self.channels)]
            if invalid_channels:
                raise ValueError(f"Invalid channel names: {', '.join(invalid_channels)}")
        
        if start_time is None or end_time is None:
            all_time_points = sorted(set(event.start_time for event in self.all_events) | set(event.end_time for event in self.all_events))
            if start_time is None:
                start_time = all_time_points[0]
            if end_time is None:
                end_time = all_time_points[-1]
        
        num_channels = len(channels_to_plot)
        fig, axes = plt.subplots(num_channels, 1, figsize=(12, 6 * num_channels), sharex=True)
        
        if num_channels == 1:
            axes = [axes]
        
        for ax, channel_name in zip(axes, channels_to_plot):
            channel = next(channel for channel in self.channels if channel.name == channel_name)
            events = sorted(channel.events, key=lambda event: event.start_time)
            
            time_points: List[float] = []
            values: List[float] = []
            last_value = channel.reset_value
            
            for event in events:
                if event.start_time > end_time:
                    break
                if event.end_time < start_time:
                    continue
                
                if event.start_time > start_time and (not time_points or time_points[-1] < start_time):
                    time_points.append(start_time)
                    values.append(last_value)
                
                if time_points and event.start_time > time_points[-1]:
                    time_points.append(event.start_time)
                    values.append(last_value)
                
                current_time = max(start_time, event.start_time)
                while current_time <= min(end_time, event.end_time):
                    time_points.append(current_time)
                    last_value = event.behavior.get_value_at_time(current_time - event.start_time)
                    values.append(last_value)
                    current_time += resolution
                
                if current_time > event.end_time:
                    last_value = event.behavior.get_value_at_time(event.end_time - event.start_time)
                    time_points.append(event.end_time)
                    values.append(last_value)
            
            if not time_points or time_points[-1] < end_time:
                time_points.append(end_time)
                values.append(last_value)
            
            ax.plot(time_points, values, label=channel.name)
            ax.set_ylabel(channel.name)
            ax.legend()
            ax.grid(True)
        
        axes[-1].set_xlabel("Time")
        plt.tight_layout()
        if plot_now:
            plt.show()  

    def to_json(self, filename: Optional[str] = None) -> str:
        def serialize_event(event: Event) -> dict:
            event_data = {
                "channel_name": event.channel.name,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "behavior": {
                    "type": "Jump" if isinstance(event.behavior, Jump) else "Ramp",
                    "details": {}
                },
                "reference_time": event.reference_time,
                "associated_parameters": [
                    {"name": param.name, "origin": param.parameter_origin} for param in event.associated_parameters
                ],

                "children": [serialize_event(child) for child in event.children]
            }
            if isinstance(event.behavior, Jump):
                event_data["behavior"]["details"] = {
                    "target_value": event.behavior.target_value
                }
            elif isinstance(event.behavior, Ramp):
                event_data["behavior"]["details"] = {
                    "duration": event.behavior.duration,
                    "ramp_type": event.behavior.ramp_type.value,
                    "start_value": event.behavior.start_value,
                    "end_value": event.behavior.end_value
                }
            return event_data

        data = {
            "name": self.sequence_name,
            "channels": [],
            "events": []
        }

        for channel in self.channels:
            channel_data = {
                "name": channel.name,
                "card_number": channel.card_number,
                "channel_number": channel.channel_number,
                "reset": channel.reset,
                "reset_value": channel.reset_value,
                "type": "Analog" if isinstance(channel, Analog_Channel) else "Digital",
                "extra": {}
            }
            if isinstance(channel, Analog_Channel):
                channel_data["extra"] = {
                    "default_voltage_func": None,
                    "max_voltage": channel.max_voltage,
                    "min_voltage": channel.min_voltage
                }
            if isinstance(channel, Digital_Channel):
                channel_data["extra"] = {
                    "card_id": channel.card_id,
                    "bitpos": channel.bitpos
                }
            data["channels"].append(channel_data)

        root_events = [event for event in self.all_events if event.parent is None]
        data["events"] = [serialize_event(event) for event in root_events]
        if filename:
            with open(filename, 'w') as file:
                json.dump(data, file, indent=4)

        return json.dumps(data, indent=4)

    def to_csv(self, filename: str):
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['channel_name', 'start_time', 'end_time', 'behavior_type', 'target_value', 'duration', 'ramp_type', 'start_value', 'end_value'])
            for event in self.all_events:
                if isinstance(event.behavior, Jump):
                    writer.writerow([event.channel.name, event.start_time, event.end_time, 'Jump', event.behavior.target_value, None, None, None, None])
                elif isinstance(event.behavior, Ramp):
                    writer.writerow([event.channel.name, event.start_time, event.end_time, 'Ramp', None, event.behavior.duration, event.behavior.ramp_type.value, event.behavior.start_value, event.behavior.end_value])

    @staticmethod
    def from_json(file_name: Optional[str] = None,json_input: Optional[str] = None) -> 'Sequence':
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
        print(data["name"])
        sequence = Sequence(data["name"])

        channel_map = {}
        for channel_data in data["channels"]:
            if channel_data["type"] == "Analog":
                channel = sequence.add_analog_channel(
                    name=channel_data["name"],
                    card_number=channel_data["card_number"],
                    channel_number=channel_data["channel_number"],
                    reset=channel_data["reset"],
                    reset_value=channel_data["reset_value"],
                    max_voltage=channel_data["extra"]["max_voltage"],
                    min_voltage=channel_data["extra"]["min_voltage"]
                )
            elif channel_data["type"] == "Digital":
                channel = sequence.add_digital_channel(
                    name=channel_data["name"],
                    card_number=channel_data["card_number"],
                    channel_number=channel_data["channel_number"],
                    card_id=channel_data["extra"]["card_id"],
                    bitpos=channel_data["extra"]["bitpos"],
                    reset=channel_data["reset"],
                    reset_value=channel_data["reset_value"]
                )
            channel_map[channel_data["name"]] = channel
        
        

        def deserialize_event(event_data: dict, parent: Optional[Event] = None) -> Event:
            behavior_data = event_data["behavior"]
            if behavior_data["type"] == "Jump":
                behavior = Jump(target_value=behavior_data["details"]["target_value"])
            elif behavior_data["type"] == "Ramp":
                behavior = Ramp(
                    duration=behavior_data["details"]["duration"],
                    ramp_type=RampType(behavior_data["details"]["ramp_type"]),
                    start_value=behavior_data["details"]["start_value"],
                    end_value=behavior_data["details"]["end_value"]
                )

            event = sequence.add_event(
                channel_name=event_data["channel_name"],
                behavior=behavior,
                start_time=event_data["start_time"] if parent is None else None,
                relative_time=None if parent is None else event_data["start_time"] - (parent.end_time if event_data["reference_time"] == "end" else parent.start_time),
                reference_time=event_data["reference_time"],
                parent_event=parent
            )
            for param_data in event_data["associated_parameters"]:
                param = Parameter(name=param_data["name"], event=event,parameter_origin=param_data["origin"])
                event.associated_parameters.append(param)
                sequence.parameters_list.append(param)


            for child_data in event_data["children"]:
                deserialize_event(child_data, event)

            return event

        for root_event_data in data["events"]:
            deserialize_event(root_event_data)

        return sequence


    def plot_event_tree(self,plot_now: bool =True):
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Create a dictionary to map channels to their vertical positions
        channel_positions = {channel.name: i for i, channel in enumerate(self.channels)}
        all_times = sorted(set(event.start_time for event in self.all_events) | set(event.end_time for event in self.all_events))
        
        # Create a color map

        def draw_event(event, level=0, parent_pos=None):
            # Plot the event
            channel_pos = channel_positions[event.channel.name]
            event_pos = (event.start_time, channel_pos)
            ax.plot(event_pos[0], event_pos[1], 'o', color=color_map(level))
            
            # Annotate the event with its level
            ax.text(event_pos[0], event_pos[1], f'Level {level}', ha='right', va='bottom', fontsize=8, color='black')

            # Draw arrow from parent to current event
            if parent_pos is not None:
                arrow_width = max(20.0 / (5*level + 1), 0.1)  # Decrease arrow width with level, ensuring minimum width
                ax.annotate("", xy=event_pos, xytext=parent_pos, 
                            arrowprops=dict(arrowstyle="->", lw=arrow_width, color=color_map(level)))

            # Draw event's children
            for child in event.children:
                draw_event(child, level + 1, event_pos)

        # Draw all root events
        root_events = [event for event in self.all_events if event.parent is None]
        max_level = max(len(event.children) for event in root_events)
        color_map = cm.get_cmap('tab10', max_level + 1)

        for root_event in root_events:
            draw_event(root_event)

        # Set axis limits
        ax.set_xlim(min(all_times) - 1, max(all_times) + 1)
        ax.set_ylim(-1, len(self.channels))

        # Set axis labels and title
        ax.set_xlabel("Time")
        ax.set_ylabel("Channel")
        ax.set_title("Event Tree Diagram")
        ax.set_yticks(list(channel_positions.values()))
        ax.set_yticklabels(list(channel_positions.keys()))

        # Add grid
        ax.grid(True)
        plt.tight_layout()
        if plot_now:
            plt.show()

    def plot_with_event_tree(self, channels_to_plot: Optional[List[str]] = None, resolution: float = 0.1, start_time: Optional[float] = None, end_time: Optional[float] = None,plot_now: bool =True):
        if channels_to_plot is None:
            channels_to_plot = [channel.name for channel in self.channels]
        else:
            invalid_channels = [name for name in channels_to_plot if not any(channel.name == name for channel in self.channels)]
            if invalid_channels:
                raise ValueError(f"Invalid channel names: {', '.join(invalid_channels)}")
        
        if start_time is None or end_time is None:
            all_time_points = sorted(set(event.start_time for event in self.all_events) | set(event.end_time for event in self.all_events))
            if start_time is None:
                start_time = all_time_points[0]
            if end_time is None:
                end_time = all_time_points[-1]
        
        fig, ax = plt.subplots(figsize=(15, 8))

        y_offset = 0
        channel_positions = {channel.name: y_offset + i * 10 for i, channel in enumerate(self.channels)}

        # Plot channels
        for channel_name in channels_to_plot:
            channel = next(channel for channel in self.channels if channel.name == channel_name)
            events = sorted(channel.events, key=lambda event: event.start_time)
            
            time_points: List[float] = []
            values: List[float] = []
            last_value = channel.reset_value
            
            for event in events:
                if event.start_time > end_time:
                    break
                if event.end_time < start_time:
                    continue
                
                if event.start_time > start_time and (not time_points or time_points[-1] < start_time):
                    time_points.append(start_time)
                    values.append(last_value + channel_positions[channel.name])
                
                if time_points and event.start_time > time_points[-1]:
                    time_points.append(event.start_time)
                    values.append(last_value + channel_positions[channel.name])
                
                current_time = max(start_time, event.start_time)
                while current_time <= min(end_time, event.end_time):
                    time_points.append(current_time)
                    last_value = event.behavior.get_value_at_time(current_time - event.start_time)
                    values.append(last_value + channel_positions[channel.name])
                    current_time += resolution
                
                if current_time > event.end_time:
                    last_value = event.behavior.get_value_at_time(event.end_time - event.start_time)
                    time_points.append(event.end_time)
                    values.append(last_value + channel_positions[channel.name])
            
            if not time_points or time_points[-1] < end_time:
                time_points.append(end_time)
                values.append(last_value + channel_positions[channel.name])
            
            ax.plot(time_points, values, label=channel.name)

        # Plot event tree
        all_times = sorted(set(event.start_time for event in self.all_events) | set(event.end_time for event in self.all_events))

        def draw_event(event, level=0, parent_pos=None):
            # Plot the event
            channel_pos = channel_positions[event.channel.name]
            event_value = event.behavior.get_value_at_time(0) + channel_pos
            event_pos = (event.start_time, event_value)
            ax.plot(event_pos[0], event_pos[1], 'o', color=color_map(level))
            
            # Annotate the event with its level
            ax.text(event_pos[0], event_pos[1], f'Level {level}', ha='right', va='bottom', fontsize=8, color='black')

            # Draw dotted arrow from parent to current event
            if parent_pos is not None:
                arrow_width = max(20.0 / (5*level + 1), 0.1)  # Decrease arrow width with level, ensuring minimum width
                ax.annotate("", xy=event_pos, xytext=parent_pos, 
                            arrowprops=dict(arrowstyle="->", lw=arrow_width, linestyle='dotted', color=color_map(level)))

            # Draw event's children
            for child in event.children:
                draw_event(child, level + 1, event_pos)

        # Draw all root events
        root_events = [event for event in self.all_events if event.parent is None]
        max_level = max(len(event.children) for event in root_events)
        color_map = cm.get_cmap('tab10', max_level + 1)

        for root_event in root_events:
            draw_event(root_event)

        # Set axis limits
        ax.set_xlim(min(all_times) - 1, max(all_times) + 1)
        ax.set_ylim(-10, len(self.channels) * 10)

        # Set axis labels and title
        ax.set_xlabel("Time")
        ax.set_ylabel("Channel")
        ax.set_title("Event Tree Diagram with Channel Plots")
        ax.set_yticks(list(channel_positions.values()))
        ax.set_yticklabels(list(channel_positions.keys()))

        # Add grid
        ax.grid(True)
        plt.tight_layout()
        if plot_now:
            plt.show()
    
    def find_sequence_dauation(self):
        return max(
            (event.start_time + (event.behavior.duration if isinstance(event.behavior, Ramp) else 0))
            for event in self.all_events
        )


    # returns a new sequence with the events of the new sequence added to the original sequence with a time difference if specified
    def add_sequence(self, new_sequence: 'Sequence', time_difference: float = 0.000001):
        temp_original_sequence = copy.deepcopy(self)
        temp_new_sequence = copy.deepcopy(new_sequence)
        self.copy_original_events_to_new_sequence(self, temp_original_sequence)
        self.copy_original_events_to_new_sequence(new_sequence, temp_new_sequence)



        # Check for channel conflicts in names and properties
        original_sequence_channels_names = [ch.name for ch in temp_original_sequence.channels]
        new_sequence_channels_names = [ch.name for ch in temp_new_sequence.channels]
        intersection_channels_name = list(set(original_sequence_channels_names) & set(new_sequence_channels_names))
        
        
        for channel_name in intersection_channels_name:
            if  temp_original_sequence.find_channel_by_name(channel_name)== temp_new_sequence.find_channel_by_name(channel_name):
                pass
            else:
                raise ValueError(f"Channel {channel_name} already exists in the original sequence but with different properties")

        # Check for channel conflicts in channel_number and card number 
        original_sequence_channels = [(ch.card_number, ch.channel_number) for ch in temp_original_sequence.channels]
        new_sequence_channels = [(ch.card_number, ch.channel_number) for ch in temp_new_sequence.channels]
        intersection_channels = list(set(original_sequence_channels) & set(new_sequence_channels))
        for channel in intersection_channels:
            if  temp_original_sequence.find_channel_by_channel_and_card_number(channel[0], channel[1])== temp_new_sequence.find_channel_by_channel_and_card_number(channel[0], channel[1]):
                pass
            else:
                raise ValueError(f"Channel {channel} already exists in the original sequence but with different properties")
        # all channels are unique and do not conflict with the original sequence 
        
        
        original_sequence_channels_duration = temp_original_sequence.find_sequence_dauation()
        # adding the events from the new sequence to the original sequence
        for event in temp_new_sequence.all_events:
            # add each event to the list of events in the original sequence and channels with only changing the start time 
            event.start_time += (original_sequence_channels_duration+time_difference)
            event.end_time += (original_sequence_channels_duration+time_difference)
            temp_original_sequence.all_events.append(event)

            # add the event to the channel events list in the original sequence            
            temp_original_sequence.find_channel_by_name(event.channel.name).events.append(event)
        
        try: 
            temp_original_sequence.check_for_overlapping_events()
        except: 
            print("There is an overlapping events in the end of the original sequence and the start of the new sequence. Please adjust the time difference.")
            raise ValueError(f"There is an overlapping events in the end of the original sequence ({temp_original_sequence.sequence_name}) and the start of the new sequence ({temp_new_sequence.sequence_name}). Please adjust the time difference.")
        
        return temp_original_sequence



from collections import OrderedDict

class SequenceManager:
    def __init__(self) -> None:
        self.main_sequences = OrderedDict()
        self.custom_sequence= None
        self.view_type = "Linear"
        self.to_be_swept = []
        
        
    def get_all_channels_names(self): 
        all_channels_names = []
        all_channels_references = []
        for sequence in self.main_sequences.values():
            for channel in sequence["seq"].channels:
                if channel.name not in all_channels_names: 
                    all_channels_names.append(channel.name)
                    all_channels_references.append(channel)
        return all_channels_names,all_channels_references 
    
    def create_new_existing_channel(self, channel_name):
        all_channels,all_channels_references = self.get_all_channels_names()
        if channel_name not in all_channels:
            raise ValueError(f"Channel with name {channel_name} does not exist.")
        target_channel   = all_channels_references[all_channels.index(channel_name)]
        # create a new channel with the same properties as the target channel 
        if isinstance(target_channel, Analog_Channel):
            new_channel = Analog_Channel(
                name=target_channel.name,
                card_number=target_channel.card_number,
                channel_number=target_channel.channel_number,
                reset=target_channel.reset,
                reset_value=target_channel.reset_value,
                max_voltage=target_channel.max_voltage,
                min_voltage=target_channel.min_voltage
            )
        elif isinstance(target_channel, Digital_Channel):
            new_channel = Digital_Channel(
                name=target_channel.name,
                card_number=target_channel.card_number,
                channel_number=target_channel.channel_number,
                reset=target_channel.reset,
                reset_value=target_channel.reset_value,
                card_id=target_channel.card_id,
                bitpos=target_channel.bitpos
            )
        return new_channel
    def add_existing_channel_to_sequence(self, sequence_name, channel_name): 
        print(self.main_sequences.keys())  
        print(sequence_name)
        sequence = self.main_sequences[sequence_name]["seq"]
        new_channel = self.create_new_existing_channel(channel_name)
        # chen
        for channel in sequence.channels:
            if channel.name == new_channel.name:
                raise ValueError(f"Channel already exists in the sequence.")
            
        # Ensure combination of card_number and channel_number is unique
        for channel in sequence.channels:
            if channel.card_number == new_channel.card_number and channel.channel_number == new_channel.channel_number:
                raise ValueError(f"Card number {new_channel.card_number} and channel number {new_channel.channel_number} combination is already in use.")

        sequence.channels.append(new_channel)

        
    def add_new_sequence(self,  sequence_name: str,index: Optional[int] = None):
        #assert non conflicting index or name
        if sequence_name in self.main_sequences:
            raise ValueError(f"Sequence with name {sequence_name} already exists.")
        if index in (seq["index"] for seq in self.main_sequences.values()):
            raise ValueError(f"Sequence with index {index} already exists.")
        
        if index is None:
            index = len(self.main_sequences)
        self.main_sequences[sequence_name] = {"index":index, "seq":Sequence(sequence_name),"sweep_list":OrderedDict()}
    
    def load_sequence(self,  sequence: Sequence,index: Optional[int] = None):
        if sequence.sequence_name in self.main_sequences:
            raise ValueError(f"Sequence with name {sequence.sequence_name} already exists.")
        if index in (seq["index"] for seq in self.main_sequences.values()):
            raise ValueError(f"Sequence wi  th index {index} already exists.")
        
        if index is None:
            index = len(self.main_sequences)

        self.main_sequences[sequence.sequence_name] = {"index":index, "seq":sequence,"sweep_list":OrderedDict()}

    def change_sequence_name(self, old_name: str, new_name: str):
        if old_name not in self.main_sequences:
            raise ValueError(f"Sequence with name {old_name} not found.")
        
        if new_name in self.main_sequences:
            raise ValueError(f"Sequence with name {new_name} already exists.")
        
        self.main_sequences[new_name] = self.main_sequences.pop(old_name)
        self.main_sequences[new_name]["seq"].sequence_name = new_name
        if self.main_sequences[new_name]["sweep_list"]:
            for key, seq in self.main_sequences[new_name]["sweep_list"]:
                seq.sequence_name = new_name

    def change_sequence_index(self, sequence_name: str, new_index: int):
        if sequence_name not in self.main_sequences:
            raise ValueError(f"Sequence with name {sequence_name} not found.")
        
        if new_index in (seq["index"] for seq in self.main_sequences.values()):
            raise ValueError(f"Sequence with index {new_index} already exists.")
        
        self.main_sequences[sequence_name]["index"] = new_index
    
    def swap_sequence_index(self, sequence_name1: str, sequence_name2: str):
        if sequence_name1 not in self.main_sequences:
            raise ValueError(f"Sequence with name {sequence_name1} not found.")
        
        if sequence_name2 not in self.main_sequences:
            raise ValueError(f"Sequence with name {sequence_name2} not found.")
        
        index1 = self.main_sequences[sequence_name1]["index"]
        index2 = self.main_sequences[sequence_name2]["index"]
        self.main_sequences[sequence_name1]["index"] = index2
        self.main_sequences[sequence_name2]["index"] = index1
    
    def move_sequence_to_index(self, sequence_name: str, new_index: int):
        if sequence_name not in self.main_sequences:
            raise ValueError(f"Sequence with name {sequence_name} not found.")

        current_index = self.main_sequences[sequence_name]["index"]

        if new_index not in (seq["index"] for seq in self.main_sequences.values()):
            raise ValueError(f" can not exchange index with {new_index} as it does not exist.")

        if current_index == new_index:
            return
        
        for seq_name, seq_data in self.main_sequences.items():
            if  current_index> seq_data["index"] and seq_data["index"]>=new_index:
                self.main_sequences[seq_name]["index"] += 1
            elif current_index< seq_data["index"] and seq_data["index"]<=new_index:
                self.main_sequences[seq_name]["index"] -= 1
        
        self.main_sequences[sequence_name]["index"] = new_index
        #swap the indexes index of the sequence to be moved with the index of the sequence at the new index
        

            
        self.sort_sequences()
        

    def delete_sequence(self, sequence_name: str):
        if sequence_name not in self.main_sequences:
            raise ValueError(f"Sequence with name {sequence_name} not found.")
        
        self.main_sequences.pop(sequence_name)
        self.sort_sequences()

    
    def sort_sequences(self):
        self.main_sequences = OrderedDict(sorted(self.main_sequences.items(), key=lambda item: item[1]["index"]))
        # reindex the sequences
        for i, (seq_name, seq_data) in enumerate(self.main_sequences.items()):
            self.main_sequences[seq_name]["index"] = i
        


    def load_sequence_json(self, json: str, index):
        if index in self.main_sequences:
            raise ValueError(f"Sequence with index {index} already exists.")
        
        sequence = Sequence.from_json(json)
        if sequence.sequence_name in self.main_sequences:
            raise ValueError(f"Sequence with name {sequence.sequence_name} already exists.")
        
        self.main_sequences[sequence.sequence_name] = {"index":index, "seq":sequence}
    
    
    def sweep_sequence_temp(self,sequence_name: str,parameter: str, values: List[float],start_time: Optional[float]=None, channel_name: Optional[str]=None, event_to_sweep: Optional[Event] = None):
        # make a dictionary to store the sweeping information 
        if sequence_name not in self.main_sequences:
            raise ValueError(f"Sequence with name {sequence_name} not found.")
        self.to_be_swept.append({"sequence_name":sequence_name,
                                 "parameter":parameter,
                                 "values":values,
                                 "start_time":start_time,
                                 "channel_name":channel_name,
                                 "event_to_sweep":event_to_sweep})
        event_to_sweep.is_sweept = True 
    
    def remove_sweep_sequence(self,sequence_name: str, event_to_sweep: Optional[Event] = None):
        if sequence_name not in self.main_sequences:
            raise ValueError(f"Sequence with name {sequence_name} not found.")
        
        self.to_be_swept = [sweep for sweep in self.to_be_swept if event_to_sweep!=sweep["event_to_sweep"]]
        event_to_sweep.is_sweept = False
        
        
     

    def sweep_sequence(self,sequence_name: str,parameter: str, values: List[float],start_time: Optional[float]=None, channel_name: Optional[str]=None, event_to_sweep: Optional[Event] = None):
        if sequence_name not in self.main_sequences:
            raise ValueError(f"Sequence with name {sequence_name} not found.")

        new_sweep_dict = OrderedDict()
        if  len(self.main_sequences[sequence_name]["sweep_list"])!=0:
            for old_key, old_seq in self.main_sequences[sequence_name]["sweep_list"].items():

                temp_sweep = old_seq.sweep_event_parameters(parameter=parameter, values=values, start_time=start_time, channel_name=channel_name, event_to_sweep=event_to_sweep)
                for new_key, new_seq in temp_sweep.items():

                    new_sweep_dict[(new_key,old_key)] = new_seq
            self.main_sequences[sequence_name]["sweep_list"]= new_sweep_dict
                
        else:
            new_sweep_dict = self.main_sequences[sequence_name]["seq"].sweep_event_parameters(parameter=parameter, values=values, start_time=start_time, channel_name=channel_name, event_to_sweep=event_to_sweep)
            self.main_sequences[sequence_name]["sweep_list"]= new_sweep_dict

    def get_main_sequence(self ):
     
        # put all sequences in a list and sort them by the index
        seq_list = list(self.main_sequences.values())
        seq_list.sort(key=lambda seq: seq["index"])

        # Run the sequences in order
        main_sequence = seq_list[0]["seq"]
        for seq in seq_list[1:]:
            main_sequence = main_sequence.add_sequence(seq["seq"])

        return main_sequence

    def get_sweep_sequences_main(self):
        # put all sequences in a list and sort them by the index
        #  use self.to_be_swept
        if not self.to_be_swept:
            return [] 
        for sweep in self.to_be_swept:
            self.sweep_sequence(sequence_name=sweep["sequence_name"],parameter=sweep["parameter"], values=sweep["values"],start_time=sweep["start_time"], channel_name=sweep["channel_name"], event_to_sweep=sweep["event_to_sweep"])
        
        
        
        seq_list = list(self.main_sequences.values())
        seq_list.sort(key=lambda seq: seq["index"])

        # make a list of all the sweep sequences and compine them according to the index
        sweep_sequences = [[s] for s in seq_list[0]["sweep_list"].values()] if len(seq_list[0]["sweep_list"].items())!=0 else [[seq_list[0]["seq"]]]
        sweep_sequences_keys = [[s] for s in seq_list[0]["sweep_list"].keys()  ]if len(seq_list[0]["sweep_list"].items())!=0 else [] 

        for seq in seq_list[1:]:
            if len(seq["sweep_list"].items())!=0:
                
                if sweep_sequences_keys == []:
                    for key in seq["sweep_list"].keys():
                        sweep_sequences_keys.append([key])
                else:

                    new_sweep_sequences_key = []
                    for sweep_seq_key in seq["sweep_list"].keys():
                        for sweep in sweep_sequences_keys:
                            temp_key = list(copy.copy(sweep))
                            print("temp_key",temp_key)
                            temp_key.append(sweep_seq_key)
                            new_sweep_sequences_key.append(tuple((temp_key)))
                    
                    sweep_sequences_keys = new_sweep_sequences_key


                
                
                    
                    

                new_sweep_sequences = []
                for sweep_seq in seq["sweep_list"].values():
                    for sweep in sweep_sequences:
                        temp = copy.copy(sweep)
                        temp.append(sweep_seq)
                        new_sweep_sequences.append(temp)
                
                sweep_sequences = new_sweep_sequences
            else:
                for sweep in sweep_sequences:
                    sweep.append(seq["seq"])
        

        final_sweep_sequences = []

        
        
        if sweep_sequences_keys:
            for sweep in sweep_sequences:

                main_sweep = sweep[0]
                for seq in sweep[1:]:
                    main_sweep = main_sweep.add_sequence(seq)   
                final_sweep_sequences.append(main_sweep)
            
            if len(sweep_sequences_keys[0]) <2:
                new_sweep_sequences_key = [tuple(s) for s in sweep_sequences_keys]
                sweep_sequences_keys= new_sweep_sequences_key
 
        final_dictionary = dict(zip(sweep_sequences_keys,final_sweep_sequences))

        # clear the  seq["sweep_list"] from the main sequences 
        for seq in self.main_sequences.values():
            seq["sweep_list"] = OrderedDict()
        
        return final_dictionary

    def get_custom_sequence(self, sequence_name: List[str]) -> Sequence:
        if not self.to_be_swept:
            return [] 
        for sweep in self.to_be_swept:
            self.sweep_sequence(sequence_name=sweep["sequence_name"],parameter=sweep["parameter"], values=sweep["values"],start_time=sweep["start_time"], channel_name=sweep["channel_name"], event_to_sweep=sweep["event_to_sweep"])
        
        # put all sequences in a list and sort them by the index
        seq_list = [self.main_sequences[seq_name] for seq_name in sequence_name]
        if not seq_list: 
            return []
        # Run the sequences in order
        self.custom_sequence = seq_list[0]["seq"]
        for seq in seq_list[1:]:
            self.custom_sequence = self.custom_sequence.add_sequence(seq["seq"])

        return self.custom_sequence

    def get_sweep_sequences_custom(self, sequence_name: List[str]):
        print(sequence_name)
        seq_list = [self.main_sequences[seq_name] for seq_name in sequence_name]
        # print(seq_list)

        # make a list of all the sweep sequences and compine them according to the index
        sweep_sequences = [[s] for s in seq_list[0]["sweep_list"].values()] if len(seq_list[0]["sweep_list"].items())!=0 else [[seq_list[0]["seq"]]]
        sweep_sequences_keys = [[s] for s in seq_list[0]["sweep_list"].keys()  ]if len(seq_list[0]["sweep_list"].items())!=0 else [] 

        for seq in seq_list[1:]:
            if len(seq["sweep_list"].items())!=0:
                
                if sweep_sequences_keys == []:
                    for key in seq["sweep_list"].keys():
                        sweep_sequences_keys.append([key])
                else:

                    new_sweep_sequences_key = []
                    for sweep_seq_key in seq["sweep_list"].keys():
                        for sweep in sweep_sequences_keys:
                            temp_key = list(copy.copy(sweep))
                            temp_key.append(sweep_seq_key)
                            new_sweep_sequences_key.append(tuple((temp_key)))
                    
                    sweep_sequences_keys = new_sweep_sequences_key


                
                
                    
                    

                new_sweep_sequences = []
                for sweep_seq in seq["sweep_list"].values():
                    for sweep in sweep_sequences:
                        temp = copy.copy(sweep)
                        temp.append(sweep_seq)
                        new_sweep_sequences.append(temp)
                
                sweep_sequences = new_sweep_sequences
            else:
                for sweep in sweep_sequences:
                    sweep.append(seq["seq"])
        print(sweep_sequences)
        print(sweep_sequences_keys)

        final_sweep_sequences = []

        

        if sweep_sequences_keys:
            print("sweep_sequences_keys",sweep_sequences_keys)
            for sweep in sweep_sequences:
                main_sweep = sweep[0]
                for seq in sweep[1:]:
                    main_sweep = main_sweep.add_sequence(seq)   
                final_sweep_sequences.append(main_sweep)

            if len(sweep_sequences_keys[0]) <2:
                new_sweep_sequences_key = [tuple(s) for s in sweep_sequences_keys]
                sweep_sequences_keys= new_sweep_sequences_key
                
            final_dictionary = dict(zip(sweep_sequences_keys,final_sweep_sequences))
                    # clear the  seq["sweep_list"] from the main sequences 
            for seq in self.main_sequences.values():
                seq["sweep_list"] = OrderedDict()

            return final_dictionary
                # clear the  seq["sweep_list"] from the main sequences 
        for seq in self.main_sequences.values():
            seq["sweep_list"] = OrderedDict()

        return None
        # make a list of all the sweep sequences and compine them according to the index

        
    def to_json(self,file_name: Optional[str] = None) -> str:
        data = {
            "sequences": [],
            "sweep_list": []
        }
        
        # doing the sweep sequences first
        for sweep in self.to_be_swept:
            data["sweep_list"].append({
                "sequence_name": sweep["sequence_name"],
                "parameter": sweep["parameter"],
                "values": sweep["values"],
                "start_time": sweep["event_to_sweep"].start_time if sweep["event_to_sweep"] else sweep["start_time"],
                "channel_name": sweep["event_to_sweep"].channel.name if sweep["event_to_sweep"] else sweep["channel_name"],
            })


        #sort sequences by index before saving 
        self.sort_sequences()
        
        for seq_name, seq_data in self.main_sequences.items():
            data["sequences"].append({
                "name": seq_name,
                "index": seq_data["index"],
                "sequence": seq_data["seq"].to_json(),
                "sweep_list": {str(key): seq.to_json() for key, seq in seq_data["sweep_list"].items()}   
            })

        if file_name:
            with open(file_name, 'w') as file:
                print(data)
                json.dump(data, file, indent=4)
            
        return json.dumps(data, indent=4)
    
    @staticmethod
    def from_json( file_name: Optional[str] = None,json_input: Optional[str] = None) -> 'SequenceManager':
        
        if json_input is not None and file_name is not None:
            raise ValueError("Provide either a JSON string or a file name, not both.")

        if json_input is None and file_name is None:
            raise ValueError("Provide either a JSON string or a file name.")

        if file_name:
            with open(file_name, 'r') as file:
                json_str = file.read()
        else:
            json_str = json_input

        seq_manager = SequenceManager()

        data = json.loads(json_str)
        for seq_data in data["sequences"]:
            sequence = Sequence.from_json(json_input=seq_data["sequence"])
            seq_manager.main_sequences[seq_data["name"]] = {"index":seq_data["index"], "seq":sequence}
            #sweep_list
            seq_manager.main_sequences[seq_data["name"]]["sweep_list"] = {key: Sequence.from_json(json_input=seq) for key, seq in seq_data["sweep_list"].items()}
        # doing the sweep sequences 
        for sweep in data["sweep_list"]:
            seq_manager.main_sequences[sweep["sequence_name"]]["seq"].find_event_by_time_and_channel(sweep["start_time"],sweep["channel_name"]).is_sweept = True
            seq_manager.to_be_swept.append({"sequence_name":sweep["sequence_name"]
                                    ,"parameter":sweep["parameter"]
                                    ,"values":sweep["values"]
                                    ,"start_time":None
                                    ,"channel_name":None
                                    ,"event_to_sweep":seq_manager.main_sequences[sweep["sequence_name"]]["seq"].find_event_by_time_and_channel(sweep["start_time"],sweep["channel_name"])})
        print (seq_manager.to_be_swept)
        return seq_manager 
            






        

def create_test_sequence(name: str = "test"):
    sequence = Sequence(name)
    analog_channel = sequence.add_analog_channel("Analog1", 2, 1)
    analog_channel = sequence.add_analog_channel("Analog2", 2, 2)

    

    # Create events for testing
    event1 = sequence.add_event("Analog1", Jump(1.0), start_time=0)
    event2 = sequence.add_event("Analog1", Ramp(2, RampType.LINEAR, 1.0, 5.0), parent_event=event1, reference_time="end",relative_time=2)
    event3 = sequence.add_event("Analog1", Jump(0.0),  parent_event=event2, reference_time="end",relative_time=2)
    event4 = sequence.add_event("Analog1", Ramp(2, RampType.EXPONENTIAL, 5, 10), start_time=20)
    
# Create events for testing
    event1 = sequence.add_event("Analog2", Jump(1.0), start_time=1)
    event2 = sequence.add_event("Analog2", Ramp(2, RampType.LINEAR, 1.0, 5.0), parent_event=event1, reference_time="end",relative_time=2)
    event3 = sequence.add_event("Analog2", Jump(0.0),  start_time=8)
    event4 = sequence.add_event("Analog2", Ramp(2, RampType.EXPONENTIAL, 5, 10), start_time=15)
    

    return sequence


def create_test_seq_manager():
    seq_manager = SequenceManager()
    seq_manager.add_new_sequence("test")
    seq_manager.main_sequences["test"]["seq"] = create_test_sequence()

    seq_manager.add_new_sequence("test2")
    seq_manager.main_sequences["test2"]["seq"] = create_test_sequence("test2")


    # seq_manager.sweep_sequence("test","end_value", [2,3,4],start_time=2,channel_name= "Analog1")
    # # print(seq_manager.main_sequences)
    seq_manager.sweep_sequence("test","duration", [1,2,3],start_time=2,channel_name= "Analog1")
    # print(seq_manager.main_sequences)
    seq_manager.sweep_sequence("test2","end_value", [2,3,4],start_time=2,channel_name= "Analog1")
    # print(seq_manager.main_sequences)
    seq_manager.sweep_sequence("test2","duration", [1,2,3],start_time=2,channel_name= "Analog1")
    # print([str(k ) for k in seq_manager.get_sweep_sequences_main().keys()])
    return seq_manager

    
def test_camera_trigger():
    main_seq = Sequence("Camera Trigger")
    main_seq.add_analog_channel("Camera Trigger", 2, 2)
    t = 0
    main_seq.add_event("Camera Trigger", Jump(0), start_time=t)
    t = 1
    main_seq.add_event("Camera Trigger", Jump(3.3), start_time=t)
    t = 2
    main_seq.add_event("Camera Trigger", Jump(0), start_time=t)
    seq_manager = SequenceManager()
    seq_manager.load_sequence(main_seq)
    return seq_manager


if __name__ == '__main__':
    main_seq = Sequence("Camera Trigger")
    main_seq.add_analog_channel("Camera Trigger", 2, 2)
    t = 0
    main_seq.add_event("Camera Trigger", Jump(0), start_time=t)
    t = 1
    main_seq.add_event("Camera Trigger", Jump(3.3), start_time=t)
    t = 2
    event_2 =main_seq.add_event("Camera Trigger", Jump(0), start_time=t)
    
    sweeps =main_seq.sweep_event_parameters("jump_target_value", [1,2,3], event_to_sweep=event_2)
    seq_manager = SequenceManager()
    seq_manager.load_sequence(main_seq)
    seq_manager.sweep_sequence_temp("Camera Trigger","jump_target_value", [1,2,3], event_to_sweep=event_2)
    print(event_2)
    print(seq_manager.get_sweep_sequences_main())
    print(event_2)




    # print(seq_manager.main_sequences)
    # print(seq_manager.main_sequences["test"]["sweep_list"][('duration', 2)].all_events[0].reference_original_event.start_time)
    # print(seq_manager.main_sequences["test"]["sweep_list"].keys()) 
    
        # print(len(main_seq))
    # print(len(pram_list[0]))
    # print(pram_list[0])
    