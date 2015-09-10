function [  ] = collect_data_buffer( s,~,signal,last )
%UNTITLED Summary of this function goes here
%   Detailed explanation goes here

global index;

while index<=last
    bytes = get(s,'BytesAvailable');
    if (bytes>0)        %Most likely unnecessary
        command = fgets(s);
        if strcmp(command(1),'s')
            fwrite(s,signal(index,1));  % Send direction
            fwrite(s,signal(index,2));  % Send pwm
            disp(signal(index,2))
            index = index+1;
        elseif strcmp(command(1),'t')
            % Read the LINE that you want to save in the file
            data_received = fgets(s);
            % Creare and open the data file
            fileID = fopen('input_output_data.txt','a');
            % Add the line
            fprintf(fileID,'%s',data_received);
        end
%     if (strcmp(command(1:4),'dir'))
%         fprintf(s,signal(index,1:end));
%         display(num2str(index));
%         index = index + 1;
%     elseif (strcmp(command(1:4),'dat'))
%         fprintf(s,signal(index,1:end));
%         display(num2str(index));
%         index = index + 1;
%     elseif (strcmp(command(1:4),'file'))
%         % Read the LINE that you want to save in the file
%         data_received = fgets(s);
%         % Creare and open the data file
%         fileID = fopen('input_output_data.txt','a');
%         % Add the line
%         fprintf(fileID,'%s',data_received);
%         % REMEMBER IN THE MAIN PROGRAM TO DELETE THE FILE
%     end
%     disp(signal(index,1:end));
    end

end %while
if index>=last
    fclose(s);
end

