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
import itertools



from sympy import symbols
from sympy.parsing.sympy_parser import parse_expr
from sympy.utilities.lambdify import lambdify


def tuple_to_string(tuple_input):
    """
    Convert a tuple of three strings to one string.
    
    Args:
    tuple_input (tuple): A tuple containing three strings.
    
    Returns:
    str: A single string combining the three input strings.
    """
    if len(tuple_input) != 3:
        raise ValueError("Input tuple must contain exactly three strings.")
    
    return "|".join(tuple_input)

def string_to_tuple(string_input):
    """
    Convert one string to a tuple of three strings.
    
    Args:
    string_input (str): A string containing three parts separated by '|'.
    
    Returns:
    tuple: A tuple containing three strings.
    """
    parts = string_input.split("|")
    
    if len(parts) != 3:
        raise ValueError("Input string must contain exactly two '|' separators.")
    
    return tuple(parts)



def exp_to_func(exp_str):
    x = symbols('t')
    expr = parse_expr(exp_str)
    return lambdify(x, expr)
def find_min_max(func, start, end, step=0.000001):
    """
    Find the minimum and maximum values of a function within a given range using NumPy.
    
    Args:
    func (callable): The function to evaluate
    start (float): The start of the range
    end (float): The end of the range
    step (float): The step size for the range (default is 1)
    
    Returns:
    tuple: (min_value, max_value, t_min, t_max)
    """
    t_range = np.arange(start, end + step, step)
    values = func(t_range)
    
    max_value = np.max(values)
    min_value = np.min(values)
    
    t_max = t_range[np.argmax(values)]
    t_min = t_range[np.argmin(values)]
    
    return min_value, max_value, t_min, t_max


class Parameter:
    def __init__(self, name: str,event: 'Event',parameter_origin):
        self.name = name
        self.event = event
        self.parameter_origin = parameter_origin
    def get_value(self): 
        return self.event.get_event_attributes()[self.parameter_origin]

        
        



class RampType(Enum):
    LINEAR = 'Linear'
    QUADRATIC = 'Quadratic'
    EXPONENTIAL = 'Exponential'
    LOGARITHMIC = 'Logarithmic'
    GENERIC = 'Generic'
    MINIMUM_JERK = 'Minimum Jerk'

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
    def __init__(self, start_time_instance:'TimeInstance',end_time_instance:'TimeInstance', ramp_type: RampType = RampType.LINEAR, start_value: float = 0, end_value: float = 1, func_text: str = None, resolution=0.001):
        # if start_value == end_value:
        #     raise ValueError("start_value and end_value must be different")
        
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
        self.func_text = func_text
        if self.ramp_type == RampType.GENERIC:
            if func_text:
                self.func = exp_to_func(func_text)
            else:
                raise ValueError("func can only be provided for generic ramp type, not for other ramp types")
        else:
            self._set_func()
    
    def get_duration(self):
        return self.end_time_instance.get_absolute_time() - self.start_time_instance.get_absolute_time()

    def _set_func(self):
        if self.end_time_instance == "temp":
            return
        
        duration = self.get_duration()
        if self.ramp_type == RampType.LINEAR:
            self.func = lambda t: self.start_value + (self.end_value - self.start_value) * (t / duration)
        elif self.ramp_type == RampType.QUADRATIC:
            self.func = lambda t: self.start_value + (self.end_value - self.start_value) * (t / duration)**2
        elif self.ramp_type == RampType.EXPONENTIAL:
            self.func = lambda t: self.start_value * (self.end_value / self.start_value) ** (t / duration)
        elif self.ramp_type == RampType.LOGARITHMIC:
            self.func = lambda t: self.start_value + (self.end_value - self.start_value) * (np.log10(t + 1) / np.log10(duration + 1))
        elif self.ramp_type == RampType.MINIMUM_JERK:
            self.func = lambda t: self.start_value + (self.end_value - self.start_value) * (10 * (t/duration)**3 - 15 * (t/duration)**4 + 6 * (t/duration)**5)
        else:
            raise ValueError("Invalid ramp type")
    def get_start_value(self):
        return self.func(0)

    def get_end_value(self):
        return self.func(self.get_duration())
    def edit_ramp(self, 
                        start_time_instance: Optional['TimeInstance'] = None,
                        end_time_instance: Optional['TimeInstance'] = None, 
                        ramp_type: Optional[RampType] = None,
                        start_value: Optional[float] = None,
                        end_value: Optional[float] = None,
                        func_text: str = None,
                        resolution: Optional[float] = None):
        
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
        
        # if new_start_value == new_end_value:
        #     raise ValueError("start_value and end_value must be different")
        
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

        if func_text:
            self.func_text = func_text
            self.func = exp_to_func(func_text)
        else:
            self._set_func()


    def get_value_at_time(self, t: float) -> float:
        if 0 <= t <= self.get_duration():
            return self.func(t)
        else:
            return self.func(self.get_duration())
    
    def __repr__(self) -> str:
        return f"Ramp({self.get_duration()}, {self.ramp_type.value}, {self.get_start_value()}, {self.get_end_value()})"
class Digital(EventBehavior):
    def __init__(self, target_value: float):
        if target_value not in [0, 1]:
            raise ValueError("target_value must be 0 or 1")
        self.target_value = target_value

    def edit_digital(self, target_value: float):
        if target_value not in [0, 1]:
            raise ValueError("target_value must be 0 or 1")
        self.target_value = target_value

    def get_value_at_time(self, t: float) -> float:
        return self.target_value
    
    def __repr__(self) -> str:
        return f"Digital({self.target_value})"
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

    def detect_a_ramp(self,time_instance:'TimeInstance'):
        # check if the time instance between two time instances has a ramp
        # get all the ramps in the channel: 
        for event in time_instance.events:
            if event.channel == self:
                return None
        for event in time_instance.ending_ramps:
            if event.channel == self:
                return None
        ramps = [event for event in self.events if isinstance(event.behavior, Ramp)] 
        for ramp in ramps:
            if ramp.start_time_instance.get_absolute_time() < time_instance.get_absolute_time() < ramp.end_time_instance.get_absolute_time():
                value = ramp.behavior.get_value_at_time(time_instance.get_absolute_time() - ramp.start_time_instance.get_absolute_time())
                return ramp, value
        return None
    
    def get_event_by_time_instance(self,time_instance:'TimeInstance'):
        for event in self.events:
            if event.start_time_instance == time_instance:
                return (event,"start")
        for event in self.events:
            if event.end_time_instance == time_instance:
                return (event,"end")
        return None
    

             
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
    def __init__(self, channel: Optional[Union[Digital_Channel, Analog_Channel]] , behavior: EventBehavior,comment:str ="",start_time_instance: Optional['TimeInstance'] = None,end_time_instance: Optional['TimeInstance'] = None):


        self.channel = channel
        self.behavior = behavior
        self.comment= comment
        self.is_sweept = False
        self.sweep_type = None
        self.sweep_settings = dict()
        self.reference_original_event = self
        self.associated_parameters = []
        # check if the start_time_instance and channels already have events, raise an error if there is already an event at the same time and channel
        for event in start_time_instance.events:
            if event.channel == channel:
                raise ValueError(f"Event already exists on channel {channel.name} at time instance {start_time_instance.name}")
        if end_time_instance and end_time_instance != "temp":
            for event in end_time_instance.events:
                if event.channel == channel:
                    raise ValueError(f"Event already exists on channel {channel.name} at time instance {end_time_instance.name}")
            
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
                    self.end_time_instance = end_time_instance
        else:
            self.end_time_instance = self.start_time_instance

            
        
        


        if isinstance(behavior, Ramp) and not isinstance(behavior, Jump):
            
            self.end_time_instance =  end_time_instance 
        else:
            self.end_time_instance = self.start_time_instance

        if end_time_instance != "temp":
            self.check_for_overlap(channel, behavior, self.get_start_time(), self.get_end_time())
            self.check_if_generic_ramp_is_valid()
        


        self.children: List[Event] = []
        index = bisect.bisect_left([e.get_start_time() for e in self.channel.events], self.get_start_time())
        self.channel.events.insert(index, self)
        self.start_time_instance.add_event(self)
        if self.end_time_instance != "temp":
            if isinstance(behavior, Ramp) and not isinstance(behavior, Jump) and self.end_time_instance != self.start_time_instance:
                self.end_time_instance.add_ending_ramp(self)
    
    def check_if_generic_ramp_is_valid(self):
        if isinstance(self.behavior, Ramp) and self.behavior.ramp_type == RampType.GENERIC:
            # get the min and max values of the function
            min_value, max_value, _, _ = find_min_max(self.behavior.func, 0, self.behavior.get_duration())
            if min_value < self.channel.min_voltage or max_value > self.channel.max_voltage:
                raise ValueError(f"Generic ramp values are out of range for channel {self.channel.name} with min voltage {self.channel.min_voltage} and max voltage {self.channel.max_voltage}")
        else:
            return
            
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
                "ramp_type": self.behavior.ramp_type.value,
                "start_value": self.behavior.start_value,
                "end_value": self.behavior.end_value,
                "func": self.behavior.func_text,
                "resolution": self.behavior.resolution,
                "channel_name": self.channel.name,
                "comment":self.comment,
                "start_time_instance":self.start_time_instance.name,
                "end_time_instance":self.end_time_instance.name
                }   
        elif isinstance(self.behavior, Digital):
            return {
                "type": "digital",
                "target_value": self.behavior.target_value,
                "start_time": self.get_start_time(),
                "channel_name": self.channel.name,
                "comment":self.comment,
                "start_time_instance":self.start_time_instance.name,
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
                    raise ValueError(f"Events on channel {channel.name} overlap with existing event {event.behavior} from {event.get_start_time()} to {event.get_end_time()}.")

class TimeInstance:
    def __init__(self, name: str, parent: Optional['TimeInstance'] = None, relative_time: int = 0):
        self.name: str = name
        self.parent: Optional['TimeInstance'] = parent
        self.relative_time: int = relative_time
        self.children: List['TimeInstance'] = []
        self.events: List[Event] = []
        self.ending_ramps: List[Event] = []
        self.is_sweept = False
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

    def get_child_time_instance_by_name(self, name: str) -> Optional['TimeInstance']:
        for child in self.children:
            if child.name == name:
                return child
        return
    def get_descendant_by_name(self, name: str) -> Optional['TimeInstance']:
        for child in self.children:
            if child.name == name:
                return child
            descendant = child.get_descendant_by_name(name)
            if descendant:
                return descendant
        return None
    
    
    def edit_parent(self, new_parent_name: str) -> None:
        # check if the new parent is not the current time instance
        if self.name == new_parent_name:
            raise ValueError("Cannot set the parent to self")
        # check if the parent is not a descendant of the current time instance
        new_parent = self.get_time_instance_by_name(new_parent_name)
        
        if self == new_parent:
            raise ValueError("Cannot set the parent to self")
        # check if the parent is not a descendant of the current time instance
        if new_parent in self.get_all_children():
            raise ValueError("Cannot set the parent to a descendant")
        # check the parent belongs to the same sequence
        if self.get_root() != new_parent.get_root():
            raise ValueError("Cannot set the parent to a time instance from a different sequence")
        # check if editing the parent will result in negative absolute time
        if new_parent.get_absolute_time() + self.relative_time < 0: 
            raise ValueError("new relative time will result in negative absolute time")
        
        if self.parent:
            self.parent.children.remove(self)
        self.parent = new_parent
        new_parent.children.append(self)

    def edit_name(self, new_name: str) -> None:
        
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
    def get_all_time_instances(self) -> List['TimeInstance']:
        time_instances: List['TimeInstance'] = []
        time_instances.append(self)
        time_instances += self.get_all_children()
        return time_instances
    
    def get_all_time_instances_after_me(self) -> List['TimeInstance']:
        # get root time instance
        root = self.get_root()
        # get all time instances in the sequence
        all_time_instances = root.get_all_time_instances()
        sort_time_instances = sorted(all_time_instances, key=lambda x: x.get_absolute_time())
        index = sort_time_instances.index(self)
        return sort_time_instances[index + 1:]
    

    
    def get_time_instance_by_name(self, name: str) -> Optional['TimeInstance']:
        if self.name == name:
            return self
        # get all children of the current time instance
        children = self.get_root().get_all_children()
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
        self.sweep_dict = {}
        self.sweep_values = []

        
        
        # list of all channels in the sequence 
        self.channels: List[Channel] = []

    # adding a time instance to the sequence 
    def add_time_instance(self, name: str, parent: TimeInstance, relative_time: int) -> TimeInstance:
        return parent.add_child_time_instance(name, relative_time)
    
    def get_all_time_instances(self) -> List[TimeInstance]:
        return self.root_time_instance.get_all_time_instances()
    
    def change_channel_order(self, channel, new_index):
        index = self.channels.index(channel)
        self.channels.pop(index)
        self.channels.insert(new_index, channel)
            
    # adding an event to the sequence by providing the channel, behavior, start_time_instance and end_time_instance (in case of ramp)
    def add_event(self, channel_name: str, behavior: EventBehavior,start_time_instance: TimeInstance, end_time_instance: Optional[TimeInstance] = None,comment:str="",) -> Event:
        # check if the channel is already in the sequence
        channel = self.find_channel_by_name(channel_name)
        # check if the start_time_instance already has an event on the channel
        for event in start_time_instance.events + start_time_instance.ending_ramps:
            if event.channel == channel:
                raise ValueError(f"Event already exists on channel {channel_name} at time instance {start_time_instance.name}")
        # check if the end_time_instance already has an event on the channel
        if end_time_instance:
            for event in end_time_instance.events + end_time_instance.ending_ramps:
                if event.channel == channel:
                    raise ValueError(f"Event already exists on channel {channel_name} at time instance {end_time_instance.name}")
        # check if the start_time_instance is less than end_time_instance
        if isinstance(behavior, Ramp):
            if start_time_instance.get_absolute_time() >= end_time_instance.get_absolute_time():
                raise ValueError("start_time_instance must be less than end_time_instance")
        # check if the behavior is a jump and is not within the max min range of the channel

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
    def delete_event(self, time_instance_name: str, channel_name: str) -> None:
        event = self.find_event_by_time_and_channel(time_instance_name, channel_name)
        if event is None:
            raise ValueError(f"Event at time instance {time_instance_name} not found on channel {channel_name}")
        event.channel.events.remove(event)
        if event.end_time_instance != event.start_time_instance:
            event.end_time_instance.ending_ramps.remove(event)
        event.start_time_instance.events.remove(event)
        
        
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
    
    def edit_event_behavior(self, edited_event: Event, start_value: Optional[float] = None, end_value: Optional[float] = None, target_value: Optional[float] = None, ramp_type: Optional[RampType] = None, func_text: str = None, comment: Optional[str] = None) -> Event:
        if isinstance(edited_event.behavior, Jump):
            if target_value > edited_event.channel.max_voltage or target_value < edited_event.channel.min_voltage:
                raise ValueError(f"Jump value {target_value} is out of range for channel {edited_event.channel.name} with min voltage {edited_event.channel.min_voltage} and max voltage {edited_event.channel.max_voltage}")
        if isinstance(edited_event.behavior, Ramp):
            if start_value is not None and (start_value > edited_event.channel.max_voltage or start_value < edited_event.channel.min_voltage):
                raise ValueError(f"Ramp start value {start_value} is out of range for channel {edited_event.channel.name} with min voltage {edited_event.channel.min_voltage} and max voltage {edited_event.channel.max_voltage}")
            if end_value is not None and (end_value > edited_event.channel.max_voltage or end_value < edited_event.channel.min_voltage):
                raise ValueError(f"Ramp end value {end_value} is out of range for channel {edited_event.channel.name} with min voltage {edited_event.channel.min_voltage} and max voltage {edited_event.channel.max_voltage}")
        if isinstance(edited_event.behavior, Digital):
            if target_value not in [0, 1]:
                raise ValueError("target_value must be 0 or 1")
            edited_event.behavior.edit_digital(target_value)


        if isinstance(edited_event.behavior, Jump):
            edited_event.behavior.edit_jump(target_value)
        elif isinstance(edited_event.behavior, Ramp):
            if func_text:
                # make a deep copy of the event
                copy_event = copy.deepcopy(edited_event)
                # edit the ramp
                copy_event.behavior.edit_ramp(ramp_type=ramp_type, func_text=func_text)
                copy_event.check_if_generic_ramp_is_valid()
                # check if the new ramp is valid
                edited_event.behavior.edit_ramp(ramp_type=ramp_type, func_text=func_text)
            else:
                edited_event.behavior.edit_ramp(start_value=start_value, end_value=end_value, ramp_type=ramp_type)
        if comment:
            edited_event.comment = comment
        return edited_event
    

    def edit_time_instance(self, edited_time_instance: TimeInstance, new_name: Optional[str] = None, new_relative_time: Optional[int] = None, new_parent_name:str = None):
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
        if new_parent_name is not None:
            time_instance.edit_parent(new_parent_name)

        # check for overlapping events
        for channel in temp_sequence.channels:
            channel.check_for_overlapping_events()
        
        # apply the changes to the original sequence
        time_instance = edited_time_instance
        if new_name is not None:
            time_instance.edit_name(new_name)
        if new_relative_time is not None:
            time_instance.edit_relative_time(new_relative_time)
        if new_parent_name is not None:
            time_instance.edit_parent(new_parent_name)
        
        return time_instance



    def get_all_events(self) -> List[Event]:
        all_events: List[Event] = []
        for channel in self.channels:
            all_events += channel.events
        return all_events
    
    
    def get_all_events2(self) -> List[Event]:
        # should be equivalent to the above function
        all_events: List[Event] = []
        for time_instance in self.get_all_time_instances():
            all_events += time_instance.events
        return all_events
    
    def check_for_overlapping_events(self):
        for channel in self.channels:
            channel.check_for_overlapping_events()
    
    def add_analog_channel(self, name: str, card_number: int, channel_number: int, reset: bool = False, reset_value: float = 0, default_voltage_func: Callable[[float], float] = lambda a: a, max_voltage: float = 10, min_voltage: float = -10,index= None) -> Analog_Channel:
        for channel in self.channels:
            if channel.name == name:
                raise ValueError(f"Channel name '{name}' is already in use.")

        # Ensure combination of card_number and channel_number is unique
        for channel in self.channels:
            if channel.card_number == card_number and channel.channel_number == channel_number:
                raise ValueError(f"Card number {card_number} and channel number {channel_number} combination is already in use.")

        channel = Analog_Channel(name, card_number, channel_number, reset, reset_value, default_voltage_func, max_voltage, min_voltage)
        if index is not None:
            self.channels.insert(index,channel)
        else:
            self.channels.append(channel)
        return channel

    # add a new digital channel to the sequence
    def add_digital_channel(self, name: str, card_number: int, channel_number: int, reset: bool = False, reset_value: float = 0,index=None) -> Digital_Channel:
        for channel in self.channels:
            if channel.name == name:
                raise ValueError(f"Channel name '{name}' is already in use.")

        # Ensure combination of card_number and channel_number is unique
        for channel in self.channels:
            if channel.card_number == card_number and channel.channel_number == channel_number:
                raise ValueError(f"Card number {card_number} and channel number {channel_number} combination is already in use.")
                    
        channel = Digital_Channel(name, card_number, channel_number, reset, reset_value)
        if index is not None:
            self.channels.insert(index,channel)
        else:
            self.channels.append(channel)
        return channel
    def find_TimeInstance_by_name(self, name: str) -> Optional[TimeInstance]:
        return self.root_time_instance.get_time_instance_by_name(name)
    
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
            temp_sequence.sweep_values.append( {"sweep_type":"time_instance_relative_time",
                                                "time_instance_name":sweep_time_instance.name,
                                                "relative_time":relative_time})
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
            temp_sequence.sweep_values.append( {"sweep_type":"event_behavior",
                                                "event_time_instance":sweep_event.start_time_instance.name,
                                                "channel_name":sweep_event.channel.name,
                                                "parameter_name":parameter_name,
                                                "value":value})
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


        # use tuple_to_string to convert the sweep_dict to string
        new_sweep_dict = {}
        for key in self.sweep_dict:
            if isinstance(key,tuple):
                new_sweep_dict[tuple_to_string(key)] = self.sweep_dict[key]
            else:
                new_sweep_dict[key] = self.sweep_dict[key]


        data = {
            "name": self.sequence_name,
            "sweep_dict": new_sweep_dict,
            "sweep_values": self.sweep_values,
            "channels": [channel.get_channel_attributes() for channel in self.channels],
            "root_time_instance": root_data,
            
        }
        if filename:
            with open(filename, 'w') as file:
                json.dump(data, file, indent=4)

        return json.dumps(data, indent=4)

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
        sequence = Sequence(data["name"])
        for channel_data in data["channels"]:
            if channel_data["type"] == "analog":
                channel = Analog_Channel(channel_data["name"], channel_data["card_number"], channel_data["channel_number"], channel_data["reset"], channel_data["reset_value"], max_voltage=channel_data["max_voltage"], min_voltage=channel_data["min_voltage"])
            else:
                channel = Digital_Channel(channel_data["name"], channel_data["card_number"], channel_data["channel_number"], channel_data["reset"], channel_data["reset_value"])
            sequence.channels.append(channel)

        def deserialize_TimeInstances(TimeInstance_data: dict, parent: TimeInstance) -> TimeInstance:
            
            TimeInstance_new = TimeInstance(TimeInstance_data["name"], parent, TimeInstance_data["relative_time"])
            for event_data in TimeInstance_data["events"]:
                channel = sequence.find_channel_by_name(event_data["channel_name"])
                if event_data["type"] == "jump":
                    behavior = Jump(event_data["jump_target_value"])
                elif event_data["type"] == "ramp":
                    behavior = Ramp(TimeInstance_new,"temp", RampType(event_data["ramp_type"]), event_data["start_value"], event_data["end_value"],event_data["func"] ,event_data["resolution"])
                else:
                    behavior = Digital(event_data["target_value"])
                Event(channel, behavior, event_data["comment"],TimeInstance_new,"temp")
            for event_data in TimeInstance_data["ending_ramps"]:
                event = sequence.find_event_by_time_and_channel(event_data["start_time_instance"], event_data["channel_name"])
                event.end_time_instance = TimeInstance_new
                event.behavior.end_time_instance = TimeInstance_new
                if event.behavior.ramp_type != RampType.GENERIC:
                    event.behavior._set_func()
                TimeInstance_new.ending_ramps.append(event)
            for child_data in TimeInstance_data["children"]:
                deserialize_TimeInstances(child_data, TimeInstance_new)


            return TimeInstance_new
        
        root = deserialize_TimeInstances(data["root_time_instance"], None)
        sequence.root_time_instance = root

        sweep_dict_temp = data["sweep_dict"]
        # loop through the sweep_dict and convert the keys to tuple if they are strings and contain | character
        sweep_dict = {}
        for key in sweep_dict_temp:
            if "|" in key:
                sweep_dict[string_to_tuple(key)] = sweep_dict_temp[key]
            else:
                sweep_dict[key] = sweep_dict_temp[key]
        sequence.sweep_dict = sweep_dict

        sequence.sweep_values = data["sweep_values"]

        return sequence
    def find_sequence_dauation(self):
        all_events = self.get_all_events()
        return max(
            (event.get_start_time() + (event.behavior.get_duration() if isinstance(event.behavior, Ramp) else 0))
            for event in all_events
        )

    

    def plot(self, channels_to_plot: Optional[List[str]] = None, resolution: float = 0.1, start_time: Optional[float] = None, end_time: Optional[float] = None, plot_now: bool =True):
        all_events = self.get_all_events()


        if channels_to_plot is None:
            channels_to_plot = [channel.name for channel in self.channels]
        else:
            invalid_channels = [name for name in channels_to_plot if not any(channel.name == name for channel in self.channels)]
            if invalid_channels:
                raise ValueError(f"Invalid channel names: {', '.join(invalid_channels)}")
        
        if start_time is None or end_time is None:
            all_time_points = sorted(set(event.get_start_time() for event in all_events) | set(event.get_end_time() for event in all_events))
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
            events = sorted(channel.events, key=lambda event: event.get_start_time())
            
            time_points: List[float] = []
            values: List[float] = []
            last_value = channel.reset_value
            
            for event in events:
                if event.get_start_time() > end_time:
                    break
                if event.get_end_time() < start_time:
                    continue
                
                if event.get_start_time() > start_time and (not time_points or time_points[-1] < start_time):
                    time_points.append(start_time)
                    values.append(last_value)
                
                if time_points and event.get_start_time() > time_points[-1]:
                    time_points.append(event.get_start_time())
                    values.append(last_value)
                
                current_time = max(start_time, event.get_start_time())
                while current_time <= min(end_time, event.get_end_time()):                    
                    time_points.append(current_time)
                    last_value = event.behavior.get_value_at_time(current_time - event.get_start_time())
                    values.append(last_value)
                    current_time += resolution
                
                if current_time > event.get_end_time():
                    last_value = event.behavior.get_value_at_time(event.get_end_time() - event.get_start_time())
                    time_points.append(event.get_end_time())
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
        original_sequence_channels_number = [(ch.card_number, ch.channel_number) for ch in temp_original_sequence.channels]
        new_sequence_channels_numbers = [(ch.card_number, ch.channel_number) for ch in temp_new_sequence.channels]
        intersection_channels_numbers = list(set(original_sequence_channels_number) & set(new_sequence_channels_numbers))
        for channel in intersection_channels_numbers:
            if  temp_original_sequence.find_channel_by_channel_and_card_number(channel[0], channel[1])== temp_new_sequence.find_channel_by_channel_and_card_number(channel[0], channel[1]):
                pass
            else:
                raise ValueError(f"Channel {channel} already exists in the original sequence but with different properties")
        # all channels are unique and do not conflict with the original sequence 
        
        # add the events of the overlapping channels to the original sequence
        for channel_name in intersection_channels_name:
            channel = temp_new_sequence.find_channel_by_name(channel_name)
            for event in channel.events:
                new_channel = temp_original_sequence.find_channel_by_name(channel_name)
                event.channel = new_channel
                new_channel.events.append(event)

        
        new_sequence_channels = [channel for channel in temp_new_sequence.channels if channel.name not in intersection_channels_name]
        
        for channel in new_sequence_channels:
            temp_original_sequence.channels.append(channel)

        original_sequence_channels_duration = temp_original_sequence.find_sequence_dauation()
        temp_new_sequence.root_time_instance.relative_time += original_sequence_channels_duration + time_difference
        temp_original_sequence.root_time_instance.children.append(temp_new_sequence.root_time_instance)
        temp_new_sequence.root_time_instance.parent = temp_original_sequence.root_time_instance
        # add the events of the overlapping channels to the original sequence
        # adding the sweep values and the sweep dict
        temp_original_sequence.sweep_values+=temp_new_sequence.sweep_values
        temp_original_sequence.sweep_dict.update(temp_new_sequence.sweep_dict)


        return temp_original_sequence
    
    def stack_sweep_paramter(self,target, values: List[float], parameter: str):
        # get event to sweep from start time and channel name
        if isinstance(target,Event):
            key = (target.start_time_instance.name, target.channel.name,parameter)
            if key not in self.sweep_dict:
                self.sweep_dict[key] = values
                target.is_sweept = True
            else:
                return ValueError(f"Parameter {parameter} already swept on {target.start_time_instance.name} at {target.channel.name}")
        elif isinstance(target,TimeInstance):
            key = target.name
            if key not in self.sweep_dict:
                self.sweep_dict[key] = values
                target.is_sweept = True
            else:
                return ValueError(f"Parameter relative time already swept on {target.name}")
    def unstuck_sweep_parameter(self,target,parameter:str):
        if isinstance(target,Event):
            key = (target.start_time_instance.name, target.channel.name,parameter)
            if key in self.sweep_dict:
                del self.sweep_dict[key]
                target.is_sweept = False
            else:
                return ValueError(f"Parameter {parameter} not found on {target.start_time_instance.name} at {target.channel.name}")
        elif isinstance(target,TimeInstance):
            key = target.name
            if key in self.sweep_dict:
                del self.sweep_dict[key]
                target.is_sweept = False
            else:
                return ValueError(f"Parameter relative time not found on {target.name}")
    def unstuck_all_sweep_parameters(self):
        self.sweep_dict = {}
        for channel in self.channels:
            for event in channel.events:
                event.is_sweept = False

        for time_instance in self.get_all_time_instances():
            time_instance.is_sweept = False

    def sweep(self) -> List['Sequence']:
        # check if the sweep dict is empty
        if not self.sweep_dict:
            return [self]
        
        # get all the keys from the sweep dict
        first_key = list(self.sweep_dict.keys())[0]
        if isinstance(first_key,tuple):
            generated_sequences = self.sweep_event_behavior(self.find_event_by_time_and_channel(first_key[0], first_key[1]), self.sweep_dict[first_key],first_key[2])
        elif isinstance(first_key,str): 
            generated_sequences = self.sweep_time_instance_relative_time(self.find_TimeInstance_by_name(first_key), self.sweep_dict[first_key])
        
        for key in list(self.sweep_dict.keys())[1:]:
            if isinstance(key,tuple):
                temp_list = []
                for s in generated_sequences:
                    temp_list+=s.sweep_event_behavior(s.find_event_by_time_and_channel(key[0], key[1]), self.sweep_dict[key],key[2])
                generated_sequences = temp_list
            elif isinstance(key,str):
                temp_list = []
                for s in generated_sequences:
                    temp_list+=s.sweep_time_instance_relative_time(s.find_TimeInstance_by_name(key), self.sweep_dict[key])
                generated_sequences = temp_list        
                    
        return generated_sequences


from collections import OrderedDict
from typing import Dict, Any


class SequenceManager:
    def __init__(self) -> None:

        self.main_sequences : OrderedDict[int,Sequence]= OrderedDict()
    
    def find_sequence_by_name(self, sequence_name: str) -> Optional[Sequence]:
        for sequence in self.main_sequences.values():
            if sequence.sequence_name == sequence_name:
                return sequence
        return None


    def get_all_channels_names(self): 
        all_channels_names = []
        all_channels_references = []
        for sequence in self.main_sequences.values():
            for channel in sequence.channels:
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
            )
        return new_channel
    def add_existing_channel_to_sequence(self, sequence_name, channel_name): 
        sequence = self.find_sequence_by_name(sequence_name)
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
        if self.find_sequence_by_name(sequence_name) is not None:
            raise ValueError(f"Sequence with name {sequence_name} already exists.")
        
        if index in self.main_sequences.keys():
            raise ValueError(f"Sequence with index {index} already exists.")
        
        if index is None:
            index = len(self.main_sequences)
        self.main_sequences[index] = Sequence(sequence_name)
    
    def load_sequence(self,  sequence: Sequence,index: Optional[int] = None):
        if self.find_sequence_by_name(sequence.sequence_name) is not None:
            raise ValueError(f"Sequence with name {sequence.sequence_name} already exists.")
        if index in self.main_sequences.keys():
            raise ValueError(f"Sequence with index {index} already exists.")
                
        if index is None:
            index = len(self.main_sequences)

        self.main_sequences[index] = sequence

    def change_sequence_name(self, old_name: str, new_name: str):
        
        if self.find_sequence_by_name(old_name) is None:
            raise ValueError(f"Sequence with name {old_name} not found.")
        
        
        if self.find_sequence_by_name(new_name) is not None:
            raise ValueError(f"Sequence with name {new_name} already exists.")
        
        sequence = self.find_sequence_by_name(old_name)
        sequence.sequence_name = new_name

    def get_all_sequence_names(self):
        return [sequence.sequence_name for sequence in self.main_sequences.values()]
    
    def find_sequence_by_index(self, index: int) -> Optional[Sequence]:
        if index not in self.main_sequences.keys():
            return None
        return self.main_sequences[index]
    
    def find_index_by_name(self, sequence_name: str) -> Optional[int]:
        for index, sequence in self.main_sequences.items():
            if sequence.sequence_name == sequence_name:
                return index
        return None
        
    def change_sequence_index(self, sequence_name: str, new_index: int):
        if self.find_sequence_by_name(sequence_name) is None:
            raise ValueError(f"Sequence with name {sequence_name} not found.")
        
        
        if new_index in self.main_sequences.keys():
            raise ValueError(f"Sequence with index {new_index} already exists.")
        
        index = self.find_index_by_name(sequence_name)
        self.main_sequences[new_index] = self.main_sequences.pop(index)
        
        
    def swap_sequence_index(self, sequence_name1: str, sequence_name2: str):
        
        if self.find_sequence_by_name(sequence_name1) is None:
            raise ValueError(f"Sequence with name {sequence_name1} not found.")
        
        if self.find_sequence_by_name(sequence_name2) is None:
            raise ValueError(f"Sequence with name {sequence_name2} not found.")
        
        index1 = self.find_index_by_name(sequence_name1)
        index2 = self.find_index_by_name(sequence_name2)
        # swap the indexes
        self.main_sequences[index1], self.main_sequences[index2] = self.main_sequences[index2], self.main_sequences[index1]

    
    def move_sequence_to_index(self, sequence_name: str, new_index: int):
        if self.find_sequence_by_name(sequence_name) is None:
            raise ValueError(f"Sequence with name {sequence_name} not found.")
        
        current_index = self.find_index_by_name(sequence_name)
        if current_index == new_index:
            return
        

        if new_index not in self.main_sequences.keys():
            raise ValueError(f" can not exchange index with {new_index} as it does not exist.")

        # use the swap function to move the sequence to incermentally to the new index
        # if the new index is greater than the current index, move the sequence to the right
        # if the new index is less than the current index, move the sequence to the left
        # if the new index is equal to the current index, do nothing
        while current_index!=new_index:
            if new_index>current_index:
                self.swap_sequence_index(sequence_name, self.find_sequence_by_index(current_index+1).sequence_name)
                current_index+=1
            elif new_index<current_index:
                self.swap_sequence_index(sequence_name, self.find_sequence_by_index(current_index-1).sequence_name)
                current_index-=1
 

    def sort_sequences(self):
        self.main_sequences = OrderedDict(sorted(self.main_sequences.items(), key=lambda item: item[0]))        

    def delete_sequence(self, sequence_name: str):
        if self.find_sequence_by_name(sequence_name) is None:
            raise ValueError(f"Sequence with name {sequence_name} not found.")
        
        index = self.find_index_by_name(sequence_name)
        self.main_sequences.pop(index)
        self.sort_sequences()
    


    def load_sequence_json(self, json: str, index):
        if index in self.main_sequences.keys():
            raise ValueError(f"Sequence with index {index} already exists.")
        
        sequence = Sequence.from_json(json)
        if self.find_sequence_by_name(sequence.sequence_name) is not None:
            raise ValueError(f"Sequence with name {sequence.sequence_name} already exists.")
        
        self.main_sequences[index] = sequence
            

    def get_main_sequence(self ):
     
        # put all sequences in a list and sort them by the index
        self.sort_sequences()
        
        seq_list = list(self.main_sequences.values())

        # Run the sequences in order
        main_sequence = seq_list[0]
        for seq in seq_list[1:]:
            main_sequence = main_sequence.add_sequence(seq)

        return main_sequence

    def get_sweep_sequences_main(self) -> List[Sequence]:
        # put all sequences in a list and sort them by the index
    
        self.sort_sequences()
        seq_list = [[s for s in  seq.sweep()] for seq in self.main_sequences.values()]

        sweep_sequences = [[s] for s in seq_list[0]]



        for seq in seq_list[1:]:
            # loop through each sequence in the sweep_sequences and add the sequences from sweep_sequences_list to it 
            new_sweep_sequences = []
            for sweep in seq:
                for sweep_seq in sweep_sequences:
                    # make a copy of the sweep_seq
                    temp = copy.copy(sweep_seq)
                    temp.append(sweep)
                    new_sweep_sequences.append(temp)
            sweep_sequences = new_sweep_sequences
        
        # loop through the sweep_sequences and add the sequences to the main sequence
        final_sweep_sequences = []
        
        for sweep in sweep_sequences: 
            main_sweep = sweep[0]
            for seq in sweep[1:]:
                main_sweep = main_sweep.add_sequence(seq)
            final_sweep_sequences.append(main_sweep)
        
        return final_sweep_sequences
    

    def get_custom_sequence(self, sequence_name: List[str]) -> Sequence:
        seq_list = [self.find_sequence_by_name(seq_name) for seq_name in sequence_name]
        custom_sequence = seq_list[0]
        for seq in seq_list[1:]:
            custom_sequence = custom_sequence.add_sequence(seq)
        return custom_sequence
    

    def get_sweep_sequences_custom(self, sequence_name: List[str]):
        seq_list_names = [self.find_sequence_by_name(seq_name) for seq_name in sequence_name]
        seq_list = [[s for s in  seq.sweep()] for seq in seq_list_names]

        sweep_sequences = [[s] for s in seq_list[0]]



        for seq in seq_list[1:]:
            # loop through each sequence in the sweep_sequences and add the sequences from sweep_sequences_list to it 
            new_sweep_sequences = []
            for sweep in seq:
                for sweep_seq in sweep_sequences:
                    # make a copy of the sweep_seq
                    temp = copy.copy(sweep_seq)
                    temp.append(sweep)
                    new_sweep_sequences.append(temp)
            sweep_sequences = new_sweep_sequences
        
        # loop through the sweep_sequences and add the sequences to the main sequence
        final_sweep_sequences = []
        
        for sweep in sweep_sequences: 
            main_sweep = sweep[0]
            for seq in sweep[1:]:
                main_sweep = main_sweep.add_sequence(seq)
            final_sweep_sequences.append(main_sweep)
        
        return final_sweep_sequences

        # make a list of all the sweep sequences and compine them according to the index

        
    def to_json(self,file_name: Optional[str] = None) -> str:

        # convert the main sequences to json
        data = dict()
        for index, sequence in self.main_sequences.items():
            data[index] = sequence.to_json()

        if file_name:
            with open(file_name, 'w') as file:
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
        for index, sequence_json in data.items():
            sequence = Sequence.from_json(json_input=sequence_json)
            seq_manager.main_sequences[int(index)] = sequence
            
        return seq_manager 
def create_test_e(n=1,t="t",ch="ch",c=4):
    seq = Sequence(f"test{n}")
    seq.add_analog_channel("ch1", 1, 1)
    seq.add_analog_channel("ch2", 1, 2)
    seq.add_digital_channel("ch3", 1, 3)
    seq.add_digital_channel(f"{ch}4", 1, c)
    
    root = seq.root_time_instance
    t1 = TimeInstance(f"{t}1", root, 1)
    t2 = TimeInstance(f"{t}2", t1, 2)
    t3 = TimeInstance(f"{t}3", t2, 3)
    t4 = TimeInstance(f"{t}4", t3, 4)

    # add events
    seq.add_event("ch1", Jump(1),root,comment="jump1")
    seq.add_event("ch2", Jump(2),root,comment="jump2")
    seq.add_event("ch3", Digital(1),root,comment="digital1")
    seq.add_event(f"{ch}4", Digital(0),root,comment="digital2")

    seq.add_event("ch1", Jump(3),t1,comment="jump3")
    Event_ramp = seq.add_event("ch2", Ramp(t2,t4,RampType.LINEAR,1,2,resolution=0.1),t2,t4,comment="ramp1")
    seq.add_event("ch3", Digital(0),t1,comment="digital3")
    seq.add_event(f"{ch}4", Digital(1),t1,comment="digital4")


    Event_Jump = seq.add_event("ch1", Jump(5),t2,comment="jump5")
    seq.add_event("ch3", Digital(1),t2,comment="digital5")
    seq.add_event(f"{ch}4", Digital(0),t2,comment="digital6")


    seq.add_event("ch1", Jump(7),t3,comment="jump7")
    seq.add_event("ch3", Digital(0),t3,comment="digital7")
    seq.add_event(f"{ch}4", Digital(1),t3,comment="digital8")


    seq.add_event("ch1", Jump(9),t4,comment="jump9")
    seq.add_event("ch3", Digital(1),t4,comment="digital9")
    seq.add_event(f"{ch}4", Digital(0),t4,comment="digital10")

    # test sweep sweeping t2 and Event_ramp start value and Event_Jump target value
    seq.stack_sweep_paramter(t2, [2,3,4],"relative_time")
    seq.stack_sweep_paramter(Event_ramp, [1,2,3],"start_value")
    seq.stack_sweep_paramter(Event_Jump, [5,6,7],"target_value")  
    return seq

if __name__ == "__main__":
    # test sweep 
    
    # seq.to_json("test_sweep.json")

    # seq2 = Sequence.from_json("test_sweep.json")
    # seq2.to_json("test_sweep2.json")

    # generated_sequences = seq.sweep()
    # for x,s in enumerate(generated_sequences):
    #     print(s.to_json(f"test_sweep_generated_{x}.json"))
    seq1 = create_test_e("t")
    seq2 = create_test_e(n=2,t="k",ch="cx",c=5)
    
    seq_manager = SequenceManager()
    seq_manager.load_sequence(seq1,0)
    seq_manager.load_sequence(seq2,1)

    seq_manager.to_json("test_sweep_Seq_manager.json")
    seq_manager2 = SequenceManager.from_json(file_name="test_sweep_Seq_manager.json")
    seq_manager2.to_json("test_sweep_Seq_manager2.json")
    seq_manager2.get_main_sequence().plot()
    for s in seq_manager2.get_sweep_sequences_main()[:3]:
        print(s.sweep_dict)
        print(s.sweep_values)

        




    

    exit() 



def creat_test():
    DFM_ToF = Sequence("test")

    DFM_ToF.add_analog_channel("MOT Coils", 2,1)
    DFM_ToF.add_analog_channel("Camera Trigger", 2, 2)
    DFM_ToF.add_analog_channel("Trap TTL", 2, 3)
    DFM_ToF.add_analog_channel("Trap FM", 2, 4)
    DFM_ToF.add_analog_channel("Trap AM", 2, 5)
    DFM_ToF.add_analog_channel("Repump TTL", 2, 6)
    DFM_ToF.add_analog_channel("Repump FM", 2, 7)
    DFM_ToF.add_analog_channel("Repump AM", 2, 8)
    DFM_ToF.add_digital_channel("Digital", 5, 8)
    DFM_ToF.add_analog_channel("D1 AOM FM", 3,1)
    DFM_ToF.add_analog_channel("D1 AOM AM", 3,2)
    DFM_ToF.add_analog_channel("D1 EOM FM", 3,3)
    DFM_ToF.add_analog_channel("D1 EOM AM", 3,4)
    DFM_ToF.add_analog_channel("Absorption Imaging FM", 3,5)
    DFM_ToF.add_analog_channel("Absorption Imaging TTL", 3,6)

    
    
    Dump_MOT = DFM_ToF.root_time_instance
    Dump_MOT.edit_name("Dump MOT")
    
    
    DFM_ToF.add_event("Digital", Digital(1), Dump_MOT, comment = 'Coils Off') # Coils Off
    DFM_ToF.add_event("MOT Coils", Jump(3.3), Dump_MOT, comment = 'Coils Off') # Coils Off
    DFM_ToF.add_event("Camera Trigger", Jump(0), Dump_MOT, comment = 'Cam Trigger Low') # Cam Trigger Low
    DFM_ToF.add_event("Trap TTL", Jump(0), Dump_MOT, comment = 'Trap Beam Off') # Trap Beam Off
    DFM_ToF.add_event("Trap FM", Jump(2.5), Dump_MOT, comment = 'Default Trap FM') # Default Trap FM
    DFM_ToF.add_event("Trap AM", Jump(1.5), Dump_MOT, comment = 'Default Trap AM') # Default Trap AM
    DFM_ToF.add_event("Repump TTL", Jump(0), Dump_MOT, comment = 'Repump Beam Off') # Repump Beam Off
    DFM_ToF.add_event("Repump FM", Jump(1.9), Dump_MOT, comment = 'Default Repump FM') # Default Repump FM
    DFM_ToF.add_event("Repump AM", Jump(0.5), Dump_MOT, comment = 'Default Rempump AM') # Default Rempump AM
    DFM_ToF.add_event("D1 AOM FM", Jump(0), Dump_MOT, comment = 'Default D1 Cooling FM') # Default D1 Cooling FM
    DFM_ToF.add_event("D1 AOM AM", Jump(0), Dump_MOT, comment = 'D1 AOM Off') # D1 AOM Off
    DFM_ToF.add_event("D1 EOM FM", Jump(0), Dump_MOT, comment = 'D1 EOM FM, N/A') # D1 EOM FM, N/A
    DFM_ToF.add_event("D1 EOM AM", Jump(0), Dump_MOT, comment = 'D1 EOM AM, N/A') # D1 EOM AM, N/A
    DFM_ToF.add_event("Absorption Imaging FM", Jump(7.5), Dump_MOT, comment = 'Defauly Abs Beam Detuning') # Defauly Abs Beam Detuning
    DFM_ToF.add_event("Absorption Imaging TTL", Jump(0), Dump_MOT, comment = 'Absorption Beam Off') # Absorption Beam Off



    Initiate_MOT =DFM_ToF.add_time_instance(f"Initiate_MOT", Dump_MOT, 1)


    DFM_ToF.add_event("Trap TTL", Jump(3.3), Initiate_MOT, comment='Trap Beam On') # Trap Beam On
    DFM_ToF.add_event("Repump TTL", Jump(3.3), Initiate_MOT, comment='Repump Beam On') # Repump Beam On

    DFM_ToF.add_event("Trap FM", Jump(2.5), Initiate_MOT, comment='Trap FM') # Trap FM
    DFM_ToF.add_event("Repump FM", Jump(1.9), Initiate_MOT, comment='Repump FM') # Repump FM

    DFM_ToF.add_event("Trap AM", Jump(1.5), Initiate_MOT, comment='Trap AM') # Trap AM
    DFM_ToF.add_event("Repump AM", Jump(0.5), Initiate_MOT, comment='Rempump AM') # Rempump AM


    ### Creat a Dual-Frequency MOT by additionally doing Gray Molasses
    t_load = 5 # MOT Load Time
    Initiate_DFM =DFM_ToF.add_time_instance(f"Initiate_DFM", Initiate_MOT, t_load)
    
    # Turn off the D2 Trap Beam
    DFM_ToF.add_event("Trap TTL", Jump(0), Initiate_DFM, comment= "End MOT Load, Initiate DFM, Trap Off") # Trap Beam Off

    # Bring the D2 Repump Beam Close to Resonance and Lower its Power
    DFM_ToF.add_event("Repump FM", Jump(2.5), Initiate_DFM, comment='Repump FM ~ -2Gamma') # Bring the D2 Repump Closer to Resonance
    DFM_ToF.add_event("Repump AM", Jump(2.5),  Initiate_DFM, comment= "Repump AM Low Power") # Lower the D2 Repump Power

    # Turn On the D1 Cooling Beam (but keep the D1 Repump Beam Off)
    DFM_ToF.add_event("D1 AOM AM", Jump(10), Initiate_DFM, comment= "D1 AOM On") # D1 AOM On
    DFM_ToF.add_event("D1 AOM FM", Jump(0), Initiate_DFM, comment= "Set the Detuning of the D1 Beam") # Set the Detuning of the D1 Beam
    DFM_ToF.add_event("D1 EOM FM", Jump(0), Initiate_DFM, comment= "D1 EOM FM (Should be AM, Unavailable)") # D1 EOM FM (We have a resonant EOM, this creates an RF signal away from the EOM's resonance.)

    ### Image the MOT after the CMOT Stage
    DFM_Time = 20
    Initiate_ToF =DFM_ToF.add_time_instance(f"Initiate_ToF", Initiate_MOT, DFM_Time)
    
    
    # DFM_ToF.add_event("MOT Coils", Ramp(Initiate_MOT,Initiate_ToF,RampType.LINEAR,start_value=3.3,end_value=0), Initiate_MOT,Initiate_ToF, comment = 'Initiate MOT, Coils On') # Coils On
    DFM_ToF.add_event("MOT Coils", Ramp(Initiate_MOT,Initiate_ToF,RampType.GENERIC,func_text="2*cos(2*pi*t)"), Initiate_MOT,Initiate_ToF, comment = 'Initiate MOT, Coils On') # Coils On

### Image the MOT after the CMOT Stage

# Turn off the MOT Beams and bring the MOT Beams on Resonance for ToF Imaging

    # DFM_ToF.add_event("MOT Coils", Jump(3.3), Initiate_ToF, comment= "End DFM, Initiate ToF, Coils Off")
    DFM_ToF.add_event("Trap TTL", Jump(0), Initiate_ToF, comment= "Trap Beam Off")
    DFM_ToF.add_event("Repump TTL", Jump(0), Initiate_ToF, comment= "Repump Beam Off")
    DFM_ToF.add_event("D1 AOM AM", Jump(0), Initiate_ToF, comment= "D1 Beams Off")

    DFM_ToF.add_event("Trap FM", Jump(0),  Initiate_ToF, comment= "Trap FM Res")
    DFM_ToF.add_event("Repump FM", Jump(4),  Initiate_ToF, comment= "Repump FM Res")

    ToF_Time = -0.2e-3

    Trig_High_IWA =DFM_ToF.add_time_instance(f"Trig_High_IWA", Initiate_ToF, ToF_Time)


    DFM_ToF.add_event("Camera Trigger", Jump(3.3), Trig_High_IWA, comment= "End ToF, Cam Trig High")
    DFM_ToF.add_event("Repump AM", Jump(0.5),  Trig_High_IWA, comment= "Repump AM High Power") # D1 AM Low Power
    DFM_ToF.add_event("Trap TTL", Jump(3.3), Trig_High_IWA,comment= "Trap Beam On")
    DFM_ToF.add_event("Repump TTL", Jump(3.3), Trig_High_IWA,comment= "Repump Beam On")
    
    t_exp = 64e-6
    Trig_Low_IWA =DFM_ToF.add_time_instance(f"Trig_Low_IWA", Trig_High_IWA, t_exp)

    DFM_ToF.add_event("Camera Trigger", Jump(0), Trig_Low_IWA, comment= "Cam Trigger Low")

    DFM_ToF.stack_sweep_paramter(Trig_High_IWA,"Trap FM", [0,1,2,3,4,5,6,7,8,9,10])


    return DFM_ToF

def create_test_time_instance():
    root = TimeInstance("root", relative_time=0)
    child1 = TimeInstance("child1", root, 1)
    child2 = TimeInstance("child2", root, 2)
    subchild1 = TimeInstance("subchild1", child1, 1)
    subchild2 = TimeInstance("subchild2", child1, 2)
    subchild3 = TimeInstance("subchild3", child2, 1)
    return root

if __name__ == '__main__':
    test = creat_test()
    test.plot()
