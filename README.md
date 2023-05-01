# smartbarn-mocap
The repo is deisgned to use the 3D tracking data of mocap system. 

The given file function is doing following tasks, in module 2.  

1. accessPhoneCam : The code in this file allows us to stream the camera footage from the phone connected to the same WLAN network with the computer. Requires users to have active connection with VICON system and in the same network.  

2. acousticVICONCalibration: Computers the rotation and translation between the VICON coordinate system and the acoustic coordinate system. This can be considered as a pose of acoustic sensors w.r.t vicon just like other bodies that are tracked. 

3. annotateSequence: The file is created to start your own annotation sequence for computing 3D position of custom features. The code follows following 3 steps.
1. First selection of frames for annotation (Implemented in AnnotationFrameSelector.Py explained below)
2. Opens annotating tool to capture 2D positions
3. 2D positions from different images are triangulated and 3D positions w.r.t corresponding 6-DOF pattern  are saved in separate file.
Example data: 20190620_PigeonPostureDataset4\settings_session07.xml (provided with sample data)

4. annotationFrameSelector: The file allows for selection of frames for annotation based on projection of the markers on the image.
The projections are VICON markers transferred to image space from 3D space.
Using the rotation and translation data provided by the tracker software.
The image projection indicate accuracy of the marker tracking.
Example data: 20190620_PigeonPostureDataset4\settings_session07.xml (provided with sample data)

5. automaticAnnotationTool: The automatic annotation tool works in following way. It takes custom 3D feature information of given 6DOF VICON objects
(i.e. marker position of marker patterns and virtual features prepared through annotation protocol) and projects them on the image.
The final projected points are stored in the .csv file to create a database for the image annotations.
Example data: 20190620_PigeonPostureDataset4\settings_session07.xml (provided with sample data)

6. createFeaturesUsingAnnotation: This file shows an example of using the custom 2D annotations and triangulating them to create 3D annotations on images. A separate version purely for annotation of bird 3D posture is now pulished with https://doi.org/10.48550/arXiv.2303.13174 at https://github.com/alexhang212/dataset-3dpop. 
Example data: 20190620_PigeonPostureDataset4\settings_session07.xml (provided with sample data)

7. customCameraProjection: The file is created to show an example of adding custom camera to the module, the example shows how new cameras can be added to the existing workflow and used for projecting 3D information on the image space. [not tested 100%] 
Example data: 20190620_PigeonPostureDataset4\settings_session07.xml (provided with sample data)

8. exampleNexusProjectionToImage: 
Example code: Data visualization on images directly using output of vicon nexus. 
The example shows the method to read data directly from the Nexus output (3D points in vicon space) and project them directly on the image space.
Example data: 20190620_PigeonPostureDataset4\settings_session07.xml (provided with sample data)

9. imageProjectionExample: [Deprecated]

10. livePoseComputationFromStream : 
Example code: Closed loop application
The file is designed show an example of how to read the vicon datastream and compute the pose of the object from the 3D position of markers, The script also compares the pose with the results computed by the tracker software.
Use case : The script is useful to learn how to computer pose of pattern from marker positions and error. A valid comparioson with vicon pose is possible. If the object is defined well it should result in similar results both in vicon and custom pose compuration. Vicon does do some additional tricks and optimizations that we do not know and pose may differ. However, on good datasets it should not differ a lot.

11. rwStreamOverNetwork: 
Example code: Closed-loop applications [ Requires active connection with VICON over network or their simulator ]
The file can be used to print the stream from remote computer using the VICON system.
The script provides and example on how to use the stream and extract data.
The advantage is that the computer does not need to have vicon datastream wrapper installed.
Note: The computer has to be connected to the live system via VPN i.e. both computers must be on the same network follow documentation on VICON Datastream SDK for latest information
Input file: Path to \\ViconDataStreamSDK_CPPTest, usually stored in program files depending on x64 or x32 installation.  
Input : IP information of the computer with live VICON connection. 

12. viconDataStreamReader: 
Example code: Closed loop applications [ Requires active connection with VICON over network or their simulator ]
The file is supposed to read the information coming from the vicon software through their customized datastream SDK. According to the website the it is supported for windows OS. The vicon package must be installed. Follow documentation on VICON Datastream SDK for latest information
Input : IP information of the computer with live VICON connection. 

Overview of the coded : 
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
