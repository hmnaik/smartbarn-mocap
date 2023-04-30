# smartbarn-mocap
The repo is deisgned to use the 3D tracking data of mocap system. 

The given file function is doing following tasks 

1. Reading 3D information of the mocap system.
2. Projecting mocap information on the video images.
3. Calibration alignment between the acoustic and the mocap 3D data. 
4. Reading realtime information using the vicon SDK

Special python package needs: 
ViconDataStreamSDK_1.11 is used in the development. ViconDataStreamSDK_1.12 is available but we have not tested it with the new library as of 30/04/2023. 
The software needs one custom installation, i.e. python library that provides access to online data. 
This is not requited if the user plans to work with offline data only. 
Unfortunately, this is a bottleneck from the manufacturers side because their code development is done with focus on their business clients.  

https://docs.vicon.com/display/DSSDK112/Vicon+DataStream+SDK+Quick+Start+Guide+for+Python#ViconDataStreamSDKQuickStartGuideforPython-Installthesoftware
