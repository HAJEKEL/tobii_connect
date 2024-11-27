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
    allow_origins=["https://frontend-example.ngrok-free.app","http://localhost:5174"],  # Replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tobii setup
#ipv4_address = "192.168.71.50192"
ipv4_address = "192.168.71.50"

tobiiglasses = TobiiGlassesController(ipv4_address, video_scene=True)
project_id = tobiiglasses.create_project("Test live_scene_and_gaze.py")
participant_id = tobiiglasses.create_participant(project_id, "participant_test")
calibration_id = tobiiglasses.create_calibration(project_id, participant_id)
is_calibrated = False  # Flag to track calibration status


from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def read_root():
    """
    Root endpoint describing the API functionality in Markdown-style rendered HTML.
    """
    markdown_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tobii Glasses 2 API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 20px;
                padding: 0;
                background-color: #f9f9f9;
                color: #333;
            }
            h1 {
                color: #4CAF50;
            }
            pre {
                background-color: #f4f4f4;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                overflow-x: auto;
            }
            img {
                max-width: 100%;
                height: auto;
            }
            a {
                color: #4CAF50;
            }
        </style>
    </head>
    <body>
        <h1>Welcome to the Tobii Glasses 2 API Server</h1>
        <p>This server interfaces with the Tobii Glasses 2 for calibration and gaze tracking.</p>
        <img src="https://example.com/tobii-glasses-image.jpg" alt="Tobii Glasses 2" />
        
        <h2>Available Endpoints</h2>
        <ul>
            <li>
                <strong><code>/calibrate</code></strong> (POST) - Endpoint to calibrate the Tobii glasses.
                <pre>
Example Request Body:
{
    "calibration_point_count": 5,
    "participant_id": "12345"
}
                </pre>
            </li>
            <li>
                <strong><code>/capture_snapshot</code></strong> (GET) - Captures a snapshot with gaze point overlay.
                <pre>
Example Response:
{
    "status": "success",
    "image_url": "http://example.com/snapshot.jpg"
}
                </pre>
            </li>
        </ul>

        <h2>Usage Instructions</h2>
        <p>Use the endpoints as described above to interact with the Tobii Glasses 2 API.</p>
    </body>
    </html>
    """
    return markdown_content


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
