# Tello Drone Swarm Showcase

This Project implements and modifies tools from external Swarm Showcase to display a pre planned routine for multiple drones with AI face Tracking and Gesture Control Capabilities

The details on this project can be found in the External Source

External Source: https://tello.oneoffcoder.com/swarm.html

## Modifications

1. Connection Method to Drones, instead of dynamic planning uses a predetermined set of addresses based from the configuration files
2. Added the function Display video that will process the video stream received from the main drone that is connected directly to the Computer WIFI 

**Note:** Implementation of Modification is same as that in Autonomous Swarm (refer to [Autonomous Swarm Overview](../AutonomousSwarm/README.md))

# Requirements

> - Python 3.8.0
> - OpenCV 4.7.0 
> - TensorFlow
> - cvzone