% Description: Matlab is running the simulink model "simulink_signal_generator"
% to create the input data to send to arduino to drive the motor. Then it
% collects the output (position) data from arduino and save them to the
% text file "input_output_data.txt"

% Arduino file: "collect_data_v1_0"
% Matlab callback function: "collect_data_buffer"

% Notes: To create different input signals you have to open the simulink
% model.

% Author: Dimitris Zervas

%
% clear all, close all
% fclose(s);
flag = 0;

global index;   % global  variable to pass the counter in the callback function
index = 1;
load_system('simulink_signal_generator');
sim('simulink_signal_generator');
%% Delete the previous file (you append data)
delete('input_output_data.txt');    % First time you run, it will through a warning.
%% Choose the input data set, you want to apply
inp = input3;
%% Translate volts to pwm_duty
inp = round(inp.*(255/5));
% Set direction
for i=1:length(inp)
    if (inp(i) > 0)
        dir(i,1) = 1;
    else
        dir(i,1) = 0;
    end
end
signal(:,1) = dir;
signal(:,2) = abs(inp);
last = length(signal);
% Add 0 in the end to stop the motor
signal(last+1,1) = signal(last,1);
signal(last+1,2) = 2;
last = last + 1;

%% Serial port creation
%Create a serial port object 
s = serial('/dev/ttyACM0'); % *java.boots file*

% Set/Change BaudRate (Default: 9600)
set(s,'BaudRate',115200);

s.BytesAvailableFcnMode = 'terminator';
s.BytesAvailableFcn = {@collect_data_buffer,signal,last}; 
% then you create a function function mycallback(obj,event)
% You pass additional parameters to the callback function by including 
% both the callback function and the parameters as elements of a cell 
% array. For example, to pass the MATLAB variable time to mycallback:
% time = datestr(now,0);
% s.BytesAvailableFcnMode = 'terminator';
% s.BytesAvailableFcn = {@mycallback,time};
% The corresponding function header is:
% function mycallback(obj,event,time)

% To verify the number of values read from the device-including 
% the terminator, use the ValuesReceived property.
% s.ValuesReceived;
% 
% 
% Connect the serial port object to the device
fopen(s);