# Tello Drone Video Streaming and Standalone

Focuses only on Receiving the video stream from the Tello Drone and displaying it. Also Can be used to allow the user to control the Tello Drone using Command Line Interface (CLI).

These programs are tools used to test the drone itself and Unity based connection

UpVideoStream.py:
- Connects to the Tello Drone and Displays the Video Footage
- Using the [Tello SDK](https://dl-cdn.ryzerobotics.com/downloads/Tello/Tello%20SDK%202.0%20User%20Guide.pdf) and CLI based user inputs to control the drone
- directly input the Tello SDK based command into the prompt for the drone to move accordingly

MidVideoStream.py:
- Connects to external Unity Simulation and Displays Video Footage.
- Cannot be controlled directly from CLI only through Unity SImulation


**Note:** Mainly developed and used for VOC

# Requirements

> - Python 3.8.0
> - OpenCV 4.7.0 