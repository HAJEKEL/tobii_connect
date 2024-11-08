from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import os
import json
from tobiiglassesctrl import TobiiGlassesController

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://frontend-example.ngrok-free.app"],  # Replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tobii setup
ipv4_address = "192.168.71.50"
tobiiglasses = TobiiGlassesController(ipv4_address, video_scene=True)
project_id = tobiiglasses.create_project("Test live_scene_and_gaze.py")
participant_id = tobiiglasses.create_participant(project_id, "participant_test")
calibration_id = tobiiglasses.create_calibration(project_id, participant_id)
is_calibrated = False  # Flag to track calibration status

@app.get("/calibrate")
async def calibrate():
    global is_calibrated

    # Start a fresh calibration process
    calibration_id = tobiiglasses.create_calibration(project_id, participant_id)
    print(f"[DEBUG]: Created new calibration with ID: {calibration_id}")

    tobiiglasses.start_calibration(calibration_id)
    print("[DEBUG]: Calibration started")

    # Wait for calibration to complete
    result = tobiiglasses.wait_until_calibration_is_done(calibration_id)
    if result:
        is_calibrated = True
        print("[DEBUG]: Calibration successful")
        return {"status": "Calibration successful!"}
    else:
        print("[DEBUG]: Calibration failed")
        raise HTTPException(status_code=500, detail="Calibration failed! Please try again.")

@app.get("/capture_snapshot")
def capture_snapshot():
    global is_calibrated
    if not is_calibrated:
        raise HTTPException(status_code=400, detail="Device is not calibrated. Please call /calibrate first.")

    # Start streaming if it’s not already started
    tobiiglasses.start_streaming()
    
    cap = cv2.VideoCapture(f"rtsp://{ipv4_address}:8554/live/scene")
    ret, frame = cap.read()
    if ret:
        # Get gaze data
        data_gp = tobiiglasses.get_data().get('gp')
        
        # Check if gaze data is valid
        if data_gp and data_gp['ts'] > 0:
            height, width = frame.shape[:2]
            gaze_x = int(data_gp['gp'][0] * width)
            gaze_y = int(data_gp['gp'][1] * height)
            cv2.circle(frame, (gaze_x, gaze_y), 60, (0, 0, 255), 5)
            print(f"[DEBUG] Gaze point drawn at: ({gaze_x}, {gaze_y})")
        else:
            print("[DEBUG] No valid gaze data found.")

        # Save frame as image file
        file_path = "snapshot.jpg"
        cv2.imwrite(file_path, frame)
        cap.release()
        return FileResponse(file_path, media_type="image/jpeg")

    cap.release()
    return {"error": "Failed to capture snapshot"}

@app.on_event("shutdown")
def shutdown_event():
    tobiiglasses.stop_streaming()
    tobiiglasses.close()
