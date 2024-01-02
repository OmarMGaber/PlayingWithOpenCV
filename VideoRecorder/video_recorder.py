import cv2
import os

def main():
    # Define constants for button key codes
    CONTINUE_BUTTON = ord('c')
    PAUSE_BUTTON = ord('p')
    START_RECORDING_BUTTON = ord('r')
    STOP_RECORDING_BUTTON = ord('s')
    QUIT_BUTTON = ord('q')

    # Create a directory for storing recordings if it doesn't exist
    if not os.path.exists('recordings'):
        os.makedirs('recordings')

    web_cam = cv2.VideoCapture(0)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')

    # declaring variables for recording state
    current_video = None
    filename = None
    is_recording = False
    is_paused = False
    video_count = -1
    text = ""

    while web_cam.isOpened():
        is_good_capture, frame = web_cam.read()

        if not is_good_capture:
            print('An error occurred while capturing the video.')
            break

        # Let the current video write the frame
        if is_recording and not is_paused:
            current_video.write(frame)

        # Set the current state text on the frame
        if is_paused:
            text = "Recording is paused. Press 'c' to continue recording. Or 's' to stop recording"
        elif is_recording:
            text = "Recording. Press 'p' to pause recording. Or 's' to stop recording"
        else:
            text = "Press 'r' to start recording."

        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, "Press 'q' to quit", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Show the current frame to the user
        cv2.imshow('Main Webcam Window', frame)

        # Read the user event key and make a decision
        key = cv2.waitKey(1)
        if key == START_RECORDING_BUTTON:
            if is_recording:
                print('A video is already being recorded.')
            else:
                is_recording = True
                video_count += 1
                filename = f"recordings/video_{video_count}.avi"
                current_video = cv2.VideoWriter(filename, fourcc, 20.0, (frame.shape[1], frame.shape[0]))

        if key == STOP_RECORDING_BUTTON:
            if current_video is None or not is_recording:
                print('There is no video recording in progress.')
            else:
                is_recording = False
                is_paused = False
                current_video.release()
                current_video = None
                print(f"Recording saved as {filename}")

        if key == PAUSE_BUTTON:
            is_paused = True

        if key == CONTINUE_BUTTON:
            is_paused = False

        if key == QUIT_BUTTON:
            break

    # Release the webCam and VideoWriter objects
    web_cam.release()
    if current_video is not None:
        current_video.release()
        print(f"Recording saved as {filename}")

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
