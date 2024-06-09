
'June 28th 2021
'This file takes the results of the sequences coded in Matlab and transfers them to the ADwin channels at the set times.
'Once compiled, the ADwin reads the binary file, which is essentially a list of channels, times and voltages/states.

#include adwinpro_all.inc

#define SIZE 500000 'size of the data arrays

#define d_io 1 'the digital I/O card is set to module number 1
#define a_out1 2'one of the analog outs is module 2
#define a_out2 3 'one of the analog outs is module 3
#define a_out3 4
#define a_out4 5

#define MAX_EVENT_COUNT Par_1 'controls when the looping stops; assigned to Par_1 in E3_load_seq.m
#define MAX_UPDATES Par_3 'max number of updates per EVENT run
#define DELAY Par_2 'the base delay

'For mapping analog voltage values to a bit pattern:
#define LIMIT 65535 'at most can have 16 bit value written to DAC
#define RANGE 20
#define OFFSET 10



'these arrays are predefined globals in ADbasic, but they must be declared before use
dim Data_1[SIZE] as long 'this array is used to step through Data_2 and Data_3; it indicates how many channels are to be updated per run of the EVENT section
'negative values indicate a wait/hold of the signal value (delay before changing)?
dim Data_2[SIZE] as long 'indicates the channels to be updated
dim Data_3[SIZE] as float 'indicates the values of the channels; in a 1:1 correspondence with Data_2
'Data_4 will be used for reset to zero stuff?

'reset to zero stuff?

'declaration of local variables
dim i as long 'loop index
dim curr_delay as long 'delay to hold a voltage/state until the appropriate time to change
dim event_count as long 'tracks number of runs of the EVENT loop
dim num_updates as long 'tracks running total of number of updates to signal values
dim ch as long 'the channel to be updated
dim state as long 'the updated value

'Note that the output voltage range of the DACs for the AOUT8/16 modules is set to ±10V bipolar and can't be
'changed (ADwin Pro II hardware manual, page 96)
'8 output channels, 16 bit resolution, < 3 us settling time

'***************************************************
'convert continuous voltage value in specified range to an n bit value, where LIMIT = 2^n - 1
function discretize(val) as float
  
  discretize = (val + OFFSET)/RANGE * LIMIT
  
endfunction




INIT:
  'Processdelay is a predefined ADbasic variable that correponds to the number of cycles that the EVENT section takes
  'For the Pro II T12, Processdelay is in units of 1 ns e.g. if Processdelay is 1000 clock cycles then that corresponds to an EVENT length 1 us.
  'Note that the ProCPUT12 has a clk rate of 1000 MHz (1 GHz)
  Processdelay = DELAY 
    
  event_count = 1
  num_updates = 1
        


  'set the necessary digital channels to be output channels
  'DigProg sets the channels of the module specified in the first param to inputs or outputs
  'Does so in groups of 8 (each bit in second param corresponds to an octet of channels)
  'Note that on power up all channels are at first configured as inputs
  'Bit = 0 --> input
  'Bit = 1 --> output
  P2_DigProg(d_io, 1111b)
    
  'configure the channels of each modules for sycnhronous output: this helps to make sure that all updates that are meant to be
  'simultaneous occur at the same time in the EVENT loop, not one after the other
  'for revision E digital cards, just need to set one bit to enable all channels
  P2_Sync_Enable(d_io, 01b)
  
  'This is for analog channels; 0FFh corresponds to 11111111b and since our analog 
  'cards have 8 channels we sync enable all 8 of them
  P2_SYNC_ENABLE(a_out1,0FFh)
  P2_SYNC_ENABLE(a_out2,0FFh)
  



EVENT:
  'works with SYNC_ENABLE to ensure simultaneous updates are indeed simultaneous
  P2_SYNC_ALL(0111b) 
    
  'update Processdelay... should do at beginning of EVENT section!
  'a negative value in Data_1 indicates we should hold values for the absolute value of Data_1[event_count] number of base delays
  'we update Processdelay accordingly
  'If Data_1[event_count] is positive, the value controls the update channel loop
  curr_delay = DELAY
  if(Data_1[event_count] < 0) then
    curr_delay = DELAY*(-1*Data_1[event_count])
  endif
  Processdelay = curr_delay
 
  'only need to update if Data_1 value is positive
  if((Data_1[event_count] <= MAX_UPDATES) and (Data_1[event_count] > 0)) then
    for i = 1 to Data_1[event_count] 'loop over the number of updates at this time instance
       
      'get the channel number: corresponds to analog or digital outs    
      ch = Data_2[num_updates]
      
      if((ch >= 1) AND (ch <= 32)) then 'we have a digital channel
        'write to corresponding channel
        ch = ch - 1 'numbering starts at 0 for dig card
        state = Data_3[num_updates] 'get the value to be written
            
        'write the 32 bit code to the digital card
        P2_Dig_Write_Latch(d_io, state)

      endif
         
      if((ch >=33) AND (ch <=47)) then 'we have an analog channel
        'check if out of of range although this should have been done in matlab
        if(discretize(Data_3[num_updates]) > LIMIT) then
          P2_Set_LED(a_out1,1);
        else
          analog_write(ch, Data_3[num_updates]) 
        endif
      
      endif
      
      Inc(num_updates)
      
    next i
  endif
    
  Inc(event_count)
  
  if(event_count > (MAX_EVENT_COUNT + 1)) then end 'go to FINISH block

FINISH:
  
  'set to default stuff
  '  P2_Digout(d_io, 0, 1) '3D MOT single pass MOGlabs; leave on
  '  P2_Digout(d_io, 1, 0) 'camera trigger
  '  P2_Digout(d_io, 2, 0) 'just testing for now
  P2_Dig_Write_Latch(d_io, 000b)
  
  'reset to default values; hard coded ch vals just for now for testing/until we know desired "end state" signal behaviour
  'analog_write(33, 0)  '3D mot coils are active low; this leaves them off when we finish
  'analog_write(45, 0)   '3D MOT single pass MOGlabs; keep on
    
  'analog_write(37, 0) 'Crystal Tech 3D MOT single pass; leave on
  'analog_write(40, 0) 'off; note that nominal 3D repump freq is 6.8 V
  'analog_write(39, 0) 'nominal 3D trap freq
  
  'channel tests
  'analog_write(38, 0)   'analog card 1 ch 6
  'analog_write(47, 0)   'analog card 1 ch 7
  
  P2_SYNC_ALL(0111b) 
  
  '***************************************************
  'should check if analog value is between -10 and 10 V in matlab code before writing to final list
sub analog_write(achannel, avalue) 
  ' if statement for each module i.e. analog card
  if((achannel>=33) AND (achannel<=40)) then
    'write the channel value; the sync functions called above actually start the D/A conversion process
    P2_Write_DAC(a_out1,achannel-32,discretize(avalue))
  endif
  'analog card 2 with channels 41-48 (this is OUR numbering choice, not the device's -  must convert)   
  if((achannel>=41) AND (achannel<=48)) then
    'subtract since module/card designates channels with numbers 1-8.
    P2_Write_DAC(a_out2,achannel-40,discretize(avalue))
  endif 
  'analog card 3 with channels 49-56
  if((achannel>=49) AND (achannel<=56)) then
    P2_Write_DAC(a_out3,achannel-48,discretize(avalue)) 'subtract since module/card designates channels with numbers 1-8.
  endif
  'analog card 4 with channels 57-64
  if((achannel>=57) AND (achannel<=64)) then
    P2_Write_DAC(a_out4,achannel-56,discretize(avalue)) 'subtract since module/card designates channels with numbers 1-8.
  endif  
 
endsub