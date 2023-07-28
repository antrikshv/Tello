# Gesture Control with Tello Drone

Focuses on Hand Gesture detection and identification from a Video feed namely in this case for the Tello Drone, focusing on the machine learning model and its accuracy as well as preparing the data sets and the keras model to be implemented in the actual implementation
> The flight movement and adjustment is not accurate in this file for the Tello Drone

Current implementation:

test.py
- Receive video feed from the drone to the computer and visualize the hand detection carried out by the drone and the identification of the hand gesture resulting in gesture specfic movement for the Tello Drone.
- Detect Single Hand at any given fram (Can be changed using cvzone instantiation)

dataCollection.py
- Receive video feed from the drone to the computer and visualize the hand detection carried out by the drone and the identification of the hand gesture resulting in gesture specfic movement for the Tello Drone.
- Edits and saves every single frame when key "s" is pressed down

**Note:** Current implementation allows only tracking of 1 hand, and contains no flight for the Tello Drone.

# Quick Start
1. On Tello drone and connect directly to its WIFI
2. Run test.py or dataCollection.py depending on the requirement

**Note:** Current implementation has a prebuilt model for specific use Cases

# Requirements

> - Python 3.8.0
> - OpenCV 4.7.0 
> - TensorFlow
> - cvzone