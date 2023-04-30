# smartbarn-mocap
The repo is deisgned to use the 3D tracking data of mocap system. 

The given file function is doing following tasks 

1. Reading 3D information of the mocap system.
2. Projecting mocap information on the video images.
3. Calibration alignment between the acoustic and the mocap 3D data. 
4. Reading realtime information using the vicon SDK


Code overview: 
The code has following modules: 
1. VICON Data: Documentations for the SDK provided by vicon. 
2. VICON Application Examples: Each file is example of a specific task, each of these tasks are designed in a way that user learns to use the helper functions developed to access and process VICON data. Each file has comments in the beginning to explain the task. 
3. VICON Drawing Operations : Drawing operations on the images, Annotation tool related files. 
4. VICON File Operations: Each file is made for specific operation with the data. e.g. c3dReader : Functions to acess data in the c3d file.  
5. VICON Math : Each file is collection of functions for specific math operations with the data. Multiplication of 3D points or computing 3D points from traiangulation of image annotations. 
6. VICON System : Each file is a specific class system that works in the background supporting the modules explained above (3,4,5). Module 2 uses these classes to use and manipuate the data. The classes help in creating modular structure that can be modified or arranged in sequence for various data manipulation tasks. 

Code style : 
Each module has a *.py file. The ideas is to build a library around the VICON data strucures. Each file in module 1,3,4,5 is a set of *.py files that work as a set of helper functions and classes that have specific tasks. Module 2 is the most important module to learn how to combine the library. The code could be organized better but currently we have done extensive commenting for replicating the work. One main advantage of the current design is that most *.py files in helper functions (module 3,4,5,6) can be accessed directly within the file. Each file has a test case written for each function and this means that even if all packages are not downloaded user can run each and every file individually as long as the locally required package were installed in the python environment. 

Special python package needs: 
ViconDataStreamSDK_1.11 is used in the development. ViconDataStreamSDK_1.12 is available but we have not tested it with the new library as of 30/04/2023. 
The software needs one custom installation, i.e. python library that provides access to online data. 
This is not requited if the user plans to work with offline data only. 
Unfortunately, this is a bottleneck from the manufacturers side because their code development is done with focus on their business clients.  

https://docs.vicon.com/display/DSSDK112/Vicon+DataStream+SDK+Quick+Start+Guide+for+Python#ViconDataStreamSDKQuickStartGuideforPython-Installthesoftware
