#!/usr/bin/Python3

"""
Example code: Closed-loop applications
The file can be used to print the stream from remote computer using the VICON system.
The script provides and example on how to use the stream and extract data.
The advantage is that the computer does not need to have vicon datastream wrapper installed.
Note: The computer has to be connected to the live system via VPN i.e. both computers must be on the same network
Follow documentation on VICON Datastream SDK for latest information
"""


from subprocess import Popen, PIPE
from shlex import split
from sys import platform

def run_command(cmd, **kwargs):
    process = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    labeled = 0
    framenumber = 0

    #Check if object tracking enabled
    if kwargs['objectTrackingEnabled']:
        objectName = kwargs['objectName']
        noOfObjectToTrack = len(objectName)
        print("Object Tracking is Enabled, Object to track:{},{} ".format(noOfObjectToTrack,objectName) )

    #start reading stream
    while True:
        output = process.stdout.readline()
        if platform == 'win32':
            output = str(output,'utf-8')
        if output == '' and process.poll() is not None:
            break
        if kwargs['enableStreamPrint']:
            print(output)

        if output:
            text = output.strip()
            if text.startswith('Hardware Frame Number:'):
                words = text.split()
                framenumber = int(words[3])
            elif text.startswith('Labeled'):
                labeled = 1
            elif text.startswith('Unlabeled'):
                labeled = 0
            # print and find markers based on the name, only show 1st marker of the pattern
            elif text.startswith('Marker #0: '+objectName[0]) and labeled:
                words = text.split()
                if words[6].startswith('False'):
                    print('Marker ', words[6], framenumber, text)
                    # print all lines
                    # print('output ',output.strip())

if __name__  == '__main__':
    # Here specify the location of the ViconDataStreamSDK (In your system)
    pathToVicon = 'C:\Program Files\Vicon\DataStream SDK\Win64\CPP\ViconDataStreamSDK_CPPTest'
    #remote IP : If Nexus or Tracker stream is being read from another computer
    IP = '10.0.21.11'
    if platform == 'linux' or platform == 'linux2': #for Linux distribution
        cmd = pathToVicon + ' ' + IP
    elif platform == 'win32': # for Windows distribution
        cmd = [pathToVicon,IP]
    elif platform == "darwin" :
        print('It may not work, have not checked on the MAC OS')
        cmd = pathToVicon + ' ' + IP
    else:
        print("OS not supported for the current distribution for remote reading")

run_command(cmd, enableStreamPrint = False, objectTrackingEnabled= True, objectName = ['cat'])