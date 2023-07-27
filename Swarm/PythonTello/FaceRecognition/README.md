# Face Detection and Tracking with Dji Tello drone

The current implementation allows the user to:

- Launch the drone through the command line using `python main.py`
- Receive video feed from the drone to the computer and visualize the face detection carried out by the drone

It allows the drone to:

- Detect multiple faces at any given frame
- Position the user at the center of any shot by deciding the best movement based on the users x, y and z coordinates

**Note:** Current implementation allows only tracking of 1 user.

## Quick Start

To initialize your drone and get it up and running, simply clone the repository and download its dependencies with:

```bash
pip install -r requirements.txt
```

Afterwards, connect to the drones wifi and run:

```bash
python main.py
```

This will make the drone take off and initialize a video feed directly from the drone to your computer.

