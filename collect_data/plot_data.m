% clear all, close all
% 
%Load data
% Example: exp1
% load exp1
%% Output (in sensor ticks -range 0:4096)
out1 = load('input_output_data.txt');
% 
% data = out1; % !!!!depends on the experiment you loaded!!!!!

% Correct the overflow issue
abs_pos = 0;
prev_pos = 0;
ovf = 0;
out_abs(:,1) = zeros(length(out1),1);
for i = 1:length(out1)
    abs_pos = out1(i,1);
    
    if (abs_pos > 3900)
        if ((prev_pos - abs_pos< 0) && (abs_pos - prev_pos >3000))
            ovf = ovf - 1;
        end
    end
    
    if (abs_pos < 200)
        if ((abs_pos - prev_pos < 0) && (prev_pos - abs_pos > 3000))
            ovf = ovf + 1;
        end
    end
    prev_pos = abs_pos;
    out_abs(i,1) = abs_pos + 4098*ovf;
end
% Relative outputs
out_rel(:,1) = out_abs - out1(1,1);
out_rel_deg(:,1) = out_rel(:,1)*360/4098;
% Time stamp
t(:,1) = 1:length(out1);
% Plot
figure,
subplot(3,1,1); plot(out_abs); title('absolute position'); legend('ticks'); grid on;
subplot(3,1,2); plot(out_rel); title('relative position'); legend('ticks'); grid on;
subplot(3,1,3); plot(out_rel_deg); title('relative position'); legend('degrees');
grid on;