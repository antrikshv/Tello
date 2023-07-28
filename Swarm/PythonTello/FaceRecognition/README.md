# Face Detection and Tracking with Dji Tello drone

Focuses on Face Detection and Tracking Alogrithm for the Tello Drone on OpenCV
> The flight movement and adjustment is not accurate in this file for the Tello Drone

Current implementation:

- Receive video feed from the drone to the computer and visualize the face detection carried out by the drone, amount of adjustment and the command sending function between the computer and the Tello Drone.
- Detect multiple faces at any given frame
- Position the user at the center of any shot by deciding the best movement based on the users x, y and z coordinates

**Note:** Current implementation allows only tracking of 1 user.

# Quick Start
1. On Tello drone and connect directly to its WIFI
2. Run Main.py which will cause the drone to take off and begin the face tracking

# Requirements

> - Python 3.8.0
> - OpenCV 4.7.0 
