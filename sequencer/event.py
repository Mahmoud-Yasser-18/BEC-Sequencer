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

class RampType(Enum):
    LINEAR = 'linear'
    QUADRATIC = 'quadratic'
    EXPONENTIAL = 'exponential'
    LOGARITHMIC = 'logarithmic'
    GENERIC = 'generic'
    MINIMUM_JERK = 5


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

    def edit_ramp(self, duration: Optional[float] = None, ramp_type: Optional[RampType] = None, start_value: Optional[float] = None, end_value: Optional[float] = None, func: Optional[Callable[[float], float]] = None, resolution: Optional[float] = None):
        new_duration = duration if duration is not None else self.duration
        new_ramp_type = ramp_type if ramp_type is not None else self.ramp_type
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

    # add a new event to the sequence
    def add_event(self, channel_name: str, behavior: EventBehavior, start_time: Optional[float] = None, relative_time: Optional[float] = None, reference_time: str = "start", parent_event: Optional[Event] = None) -> Event:
        if start_time is not None and relative_time is not None:
            raise ValueError("Provide either start_time or relative_time, not both.")

        channel = self.find_channel_by_name(channel_name)
        if channel is None:
            raise ValueError(f"Channel {channel_name} not found")

        if isinstance(channel, Digital_Channel) and isinstance(behavior, Ramp):
            raise ValueError("Ramp behavior cannot be added to a digital channel.")

        if parent_event is None:
            if start_time is None:
                raise ValueError("Root event must have start_time specified.")
            event = Event(channel, behavior, start_time=start_time)
        else:
            if relative_time is None:
                raise ValueError("Child event must have relative_time specified.")
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
    def print_sequence(self):
        for event in self.all_events:
            print(f"Event: {event.behavior} on {event.channel.name} at {event.start_time}")

    # update the absolute time of an event
    def update_event_absolute_time(self, start_time: float, channel_name: str, new_start_time: float):
        temp_sequence = copy.deepcopy(self)
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
    def delete_event(self, start_time: float, channel_name: str):
        temp_sequence = copy.deepcopy(self)
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
        
        if (edited_event is not None) and (start_time is not  None) and (channel_name is not None):
            raise ValueError("Provide either edited_event or start_time and channel_name, not both.")
        
        if edited_event is None and (start_time is None or channel_name is None):
            raise ValueError("Provide either edited_event or start_time and channel_name.")
        

        if edited_event is None:
            event = temp_sequence.find_event_by_time_and_channel(start_time, channel_name)
        else:
            event = temp_sequence.find_event_by_time_and_channel(edited_event.start_time, edited_event.channel.name)    

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
            event = edited_event    


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
                print("delta_duration",delta_duration)
                event.update_times_end(delta_duration)

        elif isinstance(event.behavior, Jump):
            event.behavior.edit_jump(jump_target_value)

        
        temp_sequence.all_events.sort(key=lambda event: event.start_time)

        for channel in temp_sequence.channels:
            channel.events.sort(key=lambda event: event.start_time)
            channel.check_for_overlapping_events()


    def sweep_event_parameters(self, parameter: str, values: List[float],start_time: Optional[float]=None, channel_name: Optional[str]=None, edited_event: Optional[Event] = None):
        # Find the event to sweep
        if edited_event is not None and start_time is not  None and channel_name is not None:
            raise ValueError("Provide either edited_event or start_time and channel_name, not both.")
        
        if edited_event is None and (start_time is None or channel_name is None):
            raise ValueError("Provide either edited_event or start_time and channel_name.")
        


        
        list_of_sequences=dict()
        # know which parameter to sweep
        if parameter == "duration":
            for value in values:
                temp_sequence = copy.deepcopy(self)
                try:
                    temp_sequence.edit_event( edited_event=edited_event, start_time=start_time, channel_name=channel_name, duration=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "ramp_type":
            for value in values:
                temp_sequence = copy.deepcopy(self)
                try:
                    temp_sequence.edit_event( edited_event=edited_event, start_time=start_time, channel_name=channel_name, ramp_type=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "start_value":
            for value in values:
                temp_sequence = copy.deepcopy(self)
                try:
                    temp_sequence.edit_event( edited_event=edited_event, start_time=start_time, channel_name=channel_name, start_value=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "end_value":
            for value in values:
                temp_sequence = copy.deepcopy(self)
                try:
                    temp_sequence.edit_event( edited_event=edited_event, start_time=start_time, channel_name=channel_name, end_value=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "func":
            for value in values:
                temp_sequence = copy.deepcopy(self)
                try:
                    temp_sequence.edit_event( edited_event=edited_event, start_time=start_time, channel_name=channel_name, func=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "resolution":
            for value in values:
                temp_sequence = copy.deepcopy(self)
                try:
                    temp_sequence.edit_event( edited_event=edited_event, start_time=start_time, channel_name=channel_name, resolution=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "jump_target_value":
            for value in values:
                temp_sequence = copy.deepcopy(self)
                try:
                    temp_sequence.edit_event( edited_event=edited_event, start_time=start_time, channel_name=channel_name, jump_target_value=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "start_time":
            for value in values:
                temp_sequence = copy.deepcopy(self)
                try:
                    temp_sequence.edit_event( edited_event=edited_event, start_time=start_time, channel_name=channel_name, new_start_time=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "relative_time":
            for value in values:
                temp_sequence = copy.deepcopy(self)
                try:
                    temp_sequence.edit_event( edited_event=edited_event, start_time=start_time, channel_name=channel_name, new_relative_time=value)
                    list_of_sequences[tuple((parameter,value))]=temp_sequence
                except ValueError as e:
                    print(e)
                
        elif parameter == "reference_time":
            for value in values:
                temp_sequence = copy.deepcopy(self)
                try:
                    temp_sequence.edit_event( edited_event=edited_event, start_time=start_time, channel_name=channel_name, new_reference_time=value)
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

    def to_json(self, filename: str) -> str:
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
    def add_sequence(self, new_sequence: 'Sequence', time_difference: float = 0.0):
        temp_original_sequence = copy.deepcopy(self)
        temp_new_sequence = copy.deepcopy(new_sequence)


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

        return temp_original_sequence




class SequenceManager:
    def __init__(self,) -> None:
        self.main_sequences = dict()


    def add_new_sequence(self,  sequence_name: str,index: Optional[int] = None):
        
        if index is None:
            index = len(self.main_sequences)
        self.main_sequences[sequence_name] = {"index":index, "seq":Sequence('sequence_name'),"sweep_list":dict()}
    
    def change_sequence_name(self, old_name: str, new_name: str):
        if old_name not in self.main_sequences:
            raise ValueError(f"Sequence with name {old_name} not found.")
        
        if new_name in self.main_sequences:
            raise ValueError(f"Sequence with name {new_name} already exists.")
        
        self.main_sequences[new_name] = self.main_sequences.pop(old_name)
        self.main_sequences[new_name]["seq"].sequence_name = new_name
        if self.main_sequences[new_name]["spweep_list"]:
            for key, seq in self.main_sequences[new_name]["sweep_list"]:
                seq.sequence_name = new_name

    def change_sequence_index(self, sequence_name: str, new_index: int):
        if sequence_name not in self.main_sequences:
            raise ValueError(f"Sequence with name {sequence_name} not found.")
        
        if new_index in (seq["index"] for seq in self.main_sequences.values()):
            raise ValueError(f"Sequence with index {new_index} already exists.")
        
        self.main_sequences[sequence_name]["index"] = new_index

    def delete_sequence(self, sequence_name: str):
        if sequence_name not in self.main_sequences:
            raise ValueError(f"Sequence with name {sequence_name} not found.")
        
        self.main_sequences.pop(sequence_name)
    
    def sort_sequences(self):
        self.main_sequences = dict(sorted(self.main_sequences.items(), key=lambda item: item[1]["index"]))


    def load_sequence_json(self, json: str, index):
        if index in self.main_sequences:
            raise ValueError(f"Sequence with index {index} already exists.")
        
        sequence = Sequence.from_json(json)
        if sequence.sequence_name in self.main_sequences:
            raise ValueError(f"Sequence with name {sequence.sequence_name} already exists.")
        
        self.main_sequences[sequence.sequence_name] = {"index":index, "seq":sequence}
    
    
     
     

    def sweep_sequence(self,sequence_name: str,parameter: str, values: List[float],start_time: Optional[float]=None, channel_name: Optional[str]=None, edited_event: Optional[Event] = None):
        if sequence_name not in self.main_sequences:
            raise ValueError(f"Sequence with name {sequence_name} not found.")

        new_sweep_dict = dict()
        if  len(self.main_sequences[sequence_name]["sweep_list"])!=0:
            # print("sweep_list is not empty")
            # print(self.main_sequences[sequence_name])
            for old_key, old_seq in self.main_sequences[sequence_name]["sweep_list"].items():

                temp_sweep = old_seq.sweep_event_parameters(parameter=parameter, values=values, start_time=start_time, channel_name=channel_name, edited_event=edited_event)
                for new_key, new_seq in temp_sweep.items():

                    new_sweep_dict[(new_key,old_key)] = new_seq
            self.main_sequences[sequence_name]["sweep_list"]= new_sweep_dict
                
        else:
            print("else")
            new_sweep_dict = self.main_sequences[sequence_name]["seq"].sweep_event_parameters(parameter=parameter, values=values, start_time=start_time, channel_name=channel_name, edited_event=edited_event)
            self.main_sequences[sequence_name]["sweep_list"]= new_sweep_dict



        

def create_test_sequence():
    sequence = Sequence("test")
    analog_channel = sequence.add_analog_channel("Analog1", 2, 1)
    

    # Create events for testing
    event1 = sequence.add_event("Analog1", Jump(1.0), start_time=0)
    event2 = sequence.add_event("Analog1", Ramp(2, RampType.LINEAR, 1.0, 5.0), parent_event=event1, reference_time="end",relative_time=2)
    event3 = sequence.add_event("Analog1", Jump(0.0),  start_time=17)
    event4 = sequence.add_event("Analog1", Ramp(2, RampType.EXPONENTIAL, 5, 10), start_time=20)
    
    return sequence




if __name__ == '__main__':

    sequence1 = create_test_sequence()
    
    # list_of_seqs = sequence1.sweep_event_parameters("duration", [1,2,3,4,5,6,16],start_time=2,channel_name= "Analog1")

    # for key, seq in list_of_seqs.items():
    #     seq.plot()
    
    seq_manager = SequenceManager()
    seq_manager.add_new_sequence("test")
    seq_manager.main_sequences["test"]["seq"] = sequence1


    seq_manager.sweep_sequence("test","end_value", [1,2,3,4,5,6,16],start_time=2,channel_name= "Analog1")
    print(seq_manager.main_sequences)
    seq_manager.sweep_sequence("test","duration", [1,2,3,4,5,6,16],start_time=2,channel_name= "Analog1")
    print(seq_manager.main_sequences)

    for key, seq in seq_manager.main_sequences["test"]["sweep_list"].items():
        print(key)
        seq.plot()

    
