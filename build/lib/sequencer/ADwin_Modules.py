#! /usr/bin/python3
# -*- coding: cp1252 -*-
import ADwin
import sys
import os





def calculate_seq(seq):

    microsecond=10**3
    period =1000*microsecond
    updatelist = [1,-period,1,-period]*30000
    chnum =[45,45,45,45,45,45]*30000
    chval = [0,6.5,0,1,0,8]*30000




    return updatelist,chnum,chval





class ADwin_Driver:
    def __init__(self, process_file="transfer_seq_data.TC1", absolute_path=0):
        self.PROCESSORTYPE = "12"
        self.DEVICENUMBER = 0x1
        self.RAISE_EXCEPTIONS = 1 
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

    def update_temp_parameters(self,updatelist,chnum,chval):
        self.updatelist=updatelist 
        self.chnum=chnum
        self.chval=chval



    def load_ADwin_Data(self):
        self.adw.Set_Par(Index=1,Value=len(self.updatelist))
        self.adw.Set_Par(Index=2,Value=self.processdelay)
        self.adw.Set_Par(Index=3,Value= max(self.updatelist))
        self.adw.SetData_Double(Data=self.updatelist,DataNo=1,Startindex=1,Count=len(self.updatelist))
        self.adw.SetData_Double(Data=self.chnum,DataNo=2,Startindex=1,Count=len(self.chnum))
        self.adw.SetData_Double(Data=self.chval,DataNo=3,Startindex=1,Count=len(self.chval))
      
    def start_process(self, process_number):
        self.adw.Start_Process(process_number)

    def initiate_experiment(self,process_number=1):
        self.load_ADwin_Data()
        self.start_process(process_number)


if __name__ == "__main__":
    adw = ADwin_Driver()
    adw.update_temp_parameters(*calculate_seq(1))
    adw.initiate_experiment()

