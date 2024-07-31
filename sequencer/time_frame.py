import copy
import numpy as np
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, List, Optional, Union,Tuple, Dict, Any 
import bisect
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
    def __init__(self, start_time_frame:'TimeFrame',end_time_frame:'TimeFrame', ramp_type: RampType = RampType.LINEAR, start_value: float = 0, end_value: float = 1, func: Optional[Callable[[float], float]] = None, resolution=0.001):
        if start_value == end_value:
            raise ValueError("start_value and end_value must be different")
        
        if start_time_frame.get_absolute_time() >= end_time_frame.get_absolute_time():
            raise ValueError("start_time_frame must be less than end_time_frame")
        
        
        self.start_time_frame = start_time_frame
        self.end_time_frame = end_time_frame

        
        if ramp_type == RampType.EXPONENTIAL and (start_value == 0 or end_value == 0):
            raise ValueError("For exponential ramp, start_value and end_value must be non-zero")

        if resolution < 0.000001:
            raise ValueError("resolution must be at least 0.000001")
        
        self.ramp_type = ramp_type
        self.start_value = start_value
        self.end_value = end_value
        self.resolution = resolution
        
        print (self.ramp_type)
        if func:
            self.func = func
        else:
            self._set_func()
    
    def get_duration(self):
        return self.end_time_frame.get_absolute_time() - self.start_time_frame.get_absolute_time()

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
        
    def edit_ramp(self, start_time_frame: Optional['TimeFrame'] = None,end_time_frame: Optional['TimeFrame'] = None, 
      ramp_type: Optional[RampType] = None, start_value: Optional[float] = None, end_value: Optional[float] = None, func: Optional[Callable[[float], float]] = None, resolution: Optional[float] = None):
        new_start_time_frame = start_time_frame if start_time_frame is not None else self.start_time_frame
        new_end_time_frame = end_time_frame if end_time_frame is not None else self.end_time_frame

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
        
        if new_start_time_frame.get_absolute_time() >= new_end_time_frame.get_absolute_time():
            raise ValueError("duration must be negative")
        
        if new_ramp_type == RampType.EXPONENTIAL and (new_start_value == 0 or new_end_value == 0):
            raise ValueError("For exponential ramp, start_value and end_value must be non-zero")
        
        if new_resolution < 0.000001:
            raise ValueError("resolution must be at least 0.000001")
        
        # Apply changes only after validation
        self.start_time_frame = new_start_time_frame
        self.end_time_frame = new_end_time_frame
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
    
class Event:
    def __init__(self, channel: Channel, behavior: EventBehavior,comment:str ="",start_time_frame: Optional['TimeFrame'] = None,end_time_frame: Optional['TimeFrame'] = None):


        self.channel = channel
        self.behavior = behavior
        self.comment= comment
        self.is_sweept = False
        self.sweep_type = None
        self.sweep_settings = dict()
        self.reference_original_event = self
        self.associated_parameters = []

        if start_time_frame is not None:
            self.start_time_frame = start_time_frame
        
        


        if isinstance(behavior, Ramp) and not isinstance(behavior, Jump):
            
            self.end_time_frame =  end_time_frame 
        else:
            self.end_time_frame = self.start_time_frame

        self.check_for_overlap(channel, behavior, self.start_time, self.end_time)

        self.children: List[Event] = []
        index = bisect.bisect_left([e.start_time for e in self.channel.events], self.start_time)
        self.channel.events.insert(index, self)

    def get_start_time(self):
        return self.start_time_frame.get_absolute_time()

    def get_end_time(self):
        return self.end_time_frame.get_absolute_time()
    
    

    def get_event_attributes(self):
        if isinstance(self.behavior, Jump):
            
                
            return {
                "jump_target_value": self.behavior.target_value,
                "start_time": self.get_start_time(),
                "relative_time": self.start_time_frame.relative_time,
                }

        elif isinstance(self.behavior, Ramp):
            return {
                "duration": self.behavior.duration,
                "ramp_type": self.behavior.ramp_type,
                "start_value": self.behavior.start_value,
                "end_value": self.behavior.end_value,
                "func": self.behavior.func,
                "resolution": self.behavior.resolution,
                "start_time": self.get_end_time(),
                "relative_time": self.start_time_frame.relative_time,
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



class TimeFrame:
    def __init__(self, name, parent=None, relative_time=0):
        self.name = name
        self.parent = parent
        self.relative_time = relative_time
        self.children = []
        self.events = []

        if parent:
            parent.children.append(self)

    def add_event(self, event):
        self.events.append(event)    
    def edit_parent(self, new_parent):
        self.parent.children.remove(self)
        self.parent = new_parent
        new_parent.children.append(self)
    def edit_name(self, new_name):
        if self.parent is None:
            raise Exception("Cannot change name of root time frame")
        # get the root time frame
        root = self.get_root()
        #  get all the children of the root
        all_children = root.get_all_children()
        # check if the name is unique
        for child in all_children:
            if child.name == new_name:
                raise Exception("Name already exists")
        self.name = new_name 
                    
    def edit_relative_time(self, new_relative_time):
        # we have to undate all the children's relative time as well
        time_diff = new_relative_time - self.relative_time
        self.relative_time = new_relative_time
        for child in self.children:
            child.edit_relative_time(child.relative_time + time_diff)
            

    def get_absolute_time(self):
        if self.parent is None:
            return self.relative_time
        return self.relative_time + self.parent.get_absolute_time()
    def add_child_time_frame(self, name, relative_time):
        return TimeFrame(name, parent=self, relative_time=relative_time)
    
    def delete_self(self):
        # assign all children of the child to the parent
        # check if I'm the root
        if self.parent is None:
            raise Exception("Cannot delete root time frame")
        
        
        for child in self.children:
            child.parent = self.parent
            self.parent.children.append(child)
        self.parent.children.remove(self)
        self.children = []

    
    def get_root(self):
        if self.parent is None:
            return self
        return self.parent.get_root()
    
    # make a recursive function to get all the children
    def get_all_children(self):
        children = []
        for child in self.children:
            children.append(child)
            children += child.get_all_children()
        return children

    def print_children(self, depth=0):
        print("  " * depth + str(self))
        for child in self.children:
            child.print_children(depth + 1)
    # return events strings indenting based on depth 
    # indentation = "  " * depth
    def get_events_string(self, depth=0):
        events_string = ""
        for event in self.events:
            events_string += "  " * depth + str(event) + "\n"
        for child in self.children:
            events_string += child.get_events_string(depth + 1)
        return events_string

    def create_a_deep_copy_of_all_frames(self):
        root = self.get_root()
        new_root = copy.deepcopy(root)
        return new_root

    def __str__(self):
        return f"TimeFrame(name={self.name}, absolute_time={self.get_absolute_time()}, events={self.events}), relative_time={self.relative_time}), children={self.children})"
    def __repr__(self):
        return f"TimeFrame(name={self.name}, absolute_time={self.get_absolute_time()}, events={self.events}), relative_time={self.relative_time}), children={self.children})"   




if __name__ == "__main__":

    # Example usage:
    root = TimeFrame(name="Root", relative_time=0)
    child1 = root.add_child_time_frame(name="Child1", relative_time=10)
    child2 = root.add_child_time_frame(name="Child2", relative_time=20)
    grandchild = child1.add_child_time_frame(name="Grandchild", relative_time=5)
    new = grandchild.create_a_deep_copy_of_all_frames()
    new.print_children()
    # print(root)
    # print(child1)
    # print(child2)
    # print(grandchild)
