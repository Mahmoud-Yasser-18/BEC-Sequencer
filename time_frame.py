import copy

from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, List, Optional, Union,Tuple, Dict, Any 


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
