# -*- coding: utf-8 -*-
"""
Created on Mon Apr  7 16:11:05 2025

@author: jalom
"""

import cv2
import numpy as np
import pandas as pd
import os
from collections import OrderedDict
from filterpy.kalman import KalmanFilter
from pathlib import Path

# Create output directories: one for video results and one for CSV files
output_folder = ".\\Video_Analysis_Results"
myUSBpath = ".\\XIMEA_movement_files" #make filepath
csv_folder = os.path.join(output_folder, "csv")
os.makedirs(output_folder, exist_ok=True)
os.makedirs(csv_folder, exist_ok=True) 

# Video parameters
PIXELS_PER_MM = 162  # Scaling factor

def mm_per_min(pixels_per_frame, frame_rate):
    return (pixels_per_frame / PIXELS_PER_MM) * frame_rate * 60

# Kalman Tracker
class KalmanTracker:
    def __init__(self):
        self.trackers = {}
        self.next_id = 0
        self.positions = {}
        self.disappeared = {}
        self.max_disappeared = 20

    def create_kalman_filter(self, centroid):
        kf = KalmanFilter(dim_x=4, dim_z=2)
        kf.x[:2] = np.array([[centroid[0]], [centroid[1]]])
        kf.F = np.array([[1, 0, 1, 0],
                         [0, 1, 0, 1],
                         [0, 0, 1, 0],
                         [0, 0, 0, 1]])
        kf.H = np.array([[1, 0, 0, 0],
                         [0, 1, 0, 0]])
        kf.P *= 1000
        kf.R *= 10
        kf.Q = np.eye(4)
        return kf

    def register(self, centroid):
        kf = self.create_kalman_filter(centroid)
        self.trackers[self.next_id] = kf
        self.positions[self.next_id] = [centroid]
        self.disappeared[self.next_id] = 0
        self.next_id += 1

    def deregister(self, object_id):
        del self.trackers[object_id]
        del self.positions[object_id]
        del self.disappeared[object_id]

    def update(self, detections):
        updated_ids = set()
        to_deregister = []

        # Predict and mark disappearance
        for object_id, kf in list(self.trackers.items()):
            kf.predict()
            self.disappeared[object_id] += 1
            if self.disappeared[object_id] > self.max_disappeared:
                to_deregister.append(object_id)

        for object_id in to_deregister:
            self.deregister(object_id)

        # Process detections and update tracker
        for detection in detections:
            x, y, w, h = detection
            centroid = (int(x + w/2), int(y + h/2))

            min_dist = float('inf')
            best_id = None
            for object_id, kf in self.trackers.items():
                pred = kf.x[:2].flatten()
                dist = np.linalg.norm(np.array(centroid) - pred)
                if dist < min_dist and dist < 100:
                    min_dist = dist
                    best_id = object_id

            if best_id is not None:
                kf = self.trackers[best_id]
                kf.update(np.array([[centroid[0]], [centroid[1]]]))
                self.positions[best_id].append(centroid)
                self.disappeared[best_id] = 0
                updated_ids.add(best_id)
            else:
                self.register(centroid)

        return {
            object_id: (int(kf.x[0].item()), int(kf.x[1].item()))
            for object_id, kf in self.trackers.items() if object_id in self.positions
        }

# Iterate through all .avi files
for video_file in [f for f in os.listdir(myUSBpath) if f.endswith(".avi")]:
    #added in dir path
    input_video = os.path.join(myUSBpath, video_file)
    print("file exists?", os.path.exists(input_video), input_video) #used this to check code would run
    output_video = os.path.join(output_folder, f"{os.path.splitext(video_file)[0]}_output.mp4")
    # Save CSV files in the csv folder
    output_csv = os.path.join(csv_folder, f"{os.path.splitext(video_file)[0]}_speed_data.csv") #It should be ok to not edit this 
    #because all of them are going to be in the file regardless of where they were recorded
    # print(video_file) check if the code in here runs
    cap = cv2.VideoCapture(input_video)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, frame_rate, (frame_width, frame_height))

    fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows=False)
    start_line = int(frame_width * 0.2)
    end_line = int(frame_width * 0.8)
    tracker = KalmanTracker()
    speed_data = []
    cumulative_distance_mm = 0
    frame_count = 0
    completed_ids = set()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        roi = frame.copy()
        mask = fgbg.apply(roi)
        _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections = []

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if (70 <= w <= 130) and (70 <= h <= 130):
                detections.append((x, y, w, h))

        objects = tracker.update(detections)

        for object_id, (cX, cY) in objects.items():
            if object_id in completed_ids:
                continue

            positions = tracker.positions[object_id]
            if len(positions) >= 2:
                xs = [pos[0] for pos in positions]
                if min(xs) < start_line and max(xs) > end_line:
                    x_start = min(xs)
                    x_end = max(xs)
                    frames_taken = len(positions)
                    pixels_moved = x_end - x_start
                    distance_mm = pixels_moved / PIXELS_PER_MM
                    speed = mm_per_min(pixels_moved / frames_taken, frame_rate) if frames_taken > 0 else 0
                    timestamp_sec = frame_count / frame_rate

                    cumulative_distance_mm += distance_mm
                    speed_data.append([object_id, round(speed, 2), round(cumulative_distance_mm, 2), round(timestamp_sec, 2)])
                    completed_ids.add(object_id)

        for object_id, (cX, cY) in objects.items():
            cv2.putText(frame, f"ID {object_id}", (cX - 10, cY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        for (x, y, w, h) in detections:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.line(frame, (start_line, 0), (start_line, frame_height), (255, 0, 0), 2)
        cv2.line(frame, (end_line, 0), (end_line, frame_height), (0, 0, 255), 2)
        out.write(frame)

    cap.release()
    out.release()

    speed_df = pd.DataFrame(speed_data, columns=["Dot_ID", "Speed_mm_per_min", "Cumulative_Paper_Distance_mm", "Timestamp_sec"])
    print(speed_df)
    speed_df.to_csv(output_csv, index=False) 

print("Processing complete. Results saved in 'Video Analysis Results'.")
