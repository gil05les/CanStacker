CAN STACKER

Authors: Lola Jo Ackermann, Gilles Harder, Sarah Wehrli

A robotics project enabling the Cherrybot to autonomously detect, grasp, and stack cans into a tower format.

⸻

Running the System

Start the main program:

python main.py

All commands below are entered in the terminal after running the program.

⸻

1. Calibration Procedure (Required after positioning the iPhone above the cans)

Step 1 — Enter calibration mode

config

Step 2 — Detect calibration points

detect

A preview window opens. Confirm or reject each detection:
	•	Press y to accept
	•	Press n to retry

Once accepted, calibration points are saved into:
detected_coords.txt

These points then need to be added to the coordination_transformation_camera_to_robot.py

Calibration is now complete.

⸻

2. Detect Cans for Stacking

After calibration, run:

detect

Confirm detections with y/n. These coordinates are used for stacking and again saved into the detected_coords.txt

⸻

3. Start Can Stacking

Run:

stack

The robot will:
	1.	Transform detected pixels into robot coordinates
	2.	Choose 3-can or 6-can stacking
	3.	Pick and place cans in the stacking formation

⸻

4. Ending Can Stacking

Run:

exit

This enables the robot to get to it's starting position.

⸻

Commands Overview

Command	Description
config	Start calibration mode
detect	Detect calibration points or cans
stack	Run the stacking sequence
quit	Exit the program

⸻

Project Structure

main.py
robot_client.py
detect_single_frame.py
coordination_transformation_camera_to_robot.py
config.py
detected_coords.txt
