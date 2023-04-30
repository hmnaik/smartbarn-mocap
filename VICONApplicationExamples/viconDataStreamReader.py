"""
 Example code: Closed loop applications
 The file is supposed to read the information coming from the vicon software through the datastream SDK
 According to the website the it is supported for windows OS
 The vicon package must be installed.
 Follow documentation on VICON Datastream SDK for latest information
"""

from vicon_dssdk import ViconDataStream

def main(**kwargs):
    #call for the client

    client = ViconDataStream.Client()

    print('Connecting')
    while not client.IsConnected():
        print('.')
        if kwargs and kwargs['IP']:
            remoteAddress = kwargs['IP']
            client.Connect(remoteAddress + ':801')
        else:
            client.Connect('localhost:801')

    i = 0

    try:
        while client.IsConnected() and i < 10:

            client.EnableMarkerData()
            client.EnableUnlabeledMarkerData()
            client.EnableSegmentData()
            if client.GetFrame():
                # store data here
                frame = client.GetFrameNumber()
                print(frame)
                subjects = client.GetSubjectNames()
                print('Subjects: ', subjects)
                for subject in subjects:
                    segments = client.GetSegmentNames(subject)
                    print(' Subject {}: Segment {}'.format(subject, segments))
                    for segment in segments:
                        """
                        Important: Note that the R/t is not streamed with Nexus, It is only streamed with Tracker 
                        """
                        rotation, occlusion = client.GetSegmentGlobalRotationQuaternion(subject,segment)
                        translation, occlusion = client.GetSegmentGlobalTranslation(subject,segment)
                        print("Rotation: ",rotation)
                        print("Translation: ", translation)

                    """
                    Important: Not that marker names are in sequence and useful for computer R/t without the help of 
                    the Nexus or tracker, could be useful when Nexus is used for streaming. 
                    """
                    markerNames = client.GetMarkerNames(subject)
                    for markerName, parentSegment in markerNames:
                        point, occlusion = client.GetMarkerGlobalTranslation(subject, markerName)
                        print(markerName, 'has parent segment', parentSegment, 'position',
                             point, ' and occlusion', occlusion )

                    try:
                        print('Object Quality', client.GetObjectQuality(subject)) # ONLY for Tracker
                    except ViconDataStream.DataStreamException as e:
                        print('Not present', e)
                # End- loop for subject related information
                """
                Important: All labelled points are printed, without information but can be matched using trajectories probably.  
                """
                # Get marker position for the subject and the trajectory id
                labelledMarkers = client.GetLabeledMarkers()
                print(" Labelled Count:", len(labelledMarkers))

                for marker , trajectoryID in labelledMarkers:
                    print('Marker data:{} - Trajectory ID - {}'.format(marker,trajectoryID))

                """
                Important: All unlabelle points are printed, this could also include some ghost points that are calculated by multiple
                cameras and rejected as labelled markers.   
                """
                unlabelledMarkers = client.GetUnlabeledMarkers()
                print("Unlabelled Count:", len(unlabelledMarkers))

                if unlabelledMarkers:
                    print('Direct print', unlabelledMarkers[0])
                for marker, trajectoryID in unlabelledMarkers:
                    print('Unlabelled Marker data:{} - Trajectory ID - {}'.format(marker, trajectoryID))

                i+=1

    except ViconDataStream.DataStreamException as e:
        print('Error', e)

    print('client disconnected')
    client.Disconnect()


if __name__ == '__main__':
    # Send the
    main(IP = '10.0.21.11')
    #main()

