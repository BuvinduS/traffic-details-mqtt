import cvzone
from ultralytics import YOLO
import cv2

import time

# Dimensions for resizing
max_width = 900
max_height = 900
LINE_DISTANCE_IN_METERS = 20

def run_detection(on_update=None, update_interval=2):
    # For Videos
    cap = cv2.VideoCapture("Videos/footage.mp4")

    if not cap.isOpened():
        print("Video Error")

    # Chose the model YOLO-weight needed, if not already available will be downloaded to the path
    model = YOLO("YOLO-weights/yolov8n.pt")

    fps = cap.get(cv2.CAP_PROP_FPS)

    # ---- STATE (all local) ----
    count = 0
    counted = {}
    prev_centers = {}
    line1_times = {}
    line2_times = {}
    speed_by_id = {}

    frame_number = 0
    last_update_frame = 0
    update_interval_frames = int(fps * update_interval)

    while True:
        success, img = cap.read()
        if not success:
            break

        frame_number += 1

        height, width = img.shape[:2]

        if height > width:
            scale = max_height / height
        else:
            scale = max_width / width

        width_new = int(width * scale)
        height_new = int(height * scale)

        img = cv2.resize(img, (width_new, height_new))

        # Counting line
        line_y = int(img.shape[0] * 3 / 4)
        cv2.line(img, (0, line_y), (img.shape[1], line_y), (0, 255, 0), 2)

        # Lines for two line speed calculation
        line_start_y = int(img.shape[0]*1/3)
        line_end_y = int(img.shape[0]*1/2)

        cv2.line(img, (0, line_start_y), (img.shape[1], line_start_y), (0, 0, 255), 2)
        cv2.line(img, (0, line_end_y), (img.shape[1], line_end_y), (255, 0, 0), 2)

        results = model.track(img, persist=True, tracker="botsort.yaml", classes=[2], conf=0.5) #iou == intersection over union, 2 is the class of car

        r = results[0]
        boxes = r.boxes

        for box in boxes:
            if box.id is None:  # occasionally (first frame, edge cases), BoT-SORT may not have assigned an ID yet.
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            w, h = x2 - x1, y2 - y1

            # Center of the bounding box
            cX, cY = int(x1 + w / 2), int(y1 + h / 2)

            track_id = int(box.id[0])

            # Speed estimation (Two line method)
            if track_id in prev_centers:
                prevY = prev_centers[track_id]
                # Crossing first line
                if track_id not in line1_times and prevY < line_start_y <= cY:
                    line1_times[track_id] = frame_number

                # Crossing second line
                if track_id in line1_times and track_id not in line2_times and prevY < line_end_y <= cY:
                    line2_times[track_id] = frame_number

                    # Speed calculation
                    dt = (line2_times[track_id] - line1_times[track_id]) / fps
                    if dt > 0:
                        speed_mps = LINE_DISTANCE_IN_METERS / dt
                        speed_by_id[track_id] = round((speed_mps * (3600 / 1000)), 1)  # in kmph

            prev_centers[track_id] = cY

            # Counting
            if track_id not in counted:  # not yet counted
                counted[track_id] = False

            if not counted[track_id] and cY > line_y:
                counted[track_id] = True
                count += 1

            cvzone.cornerRect(img, (x1, y1, w, h), l=15)
            instantaneous_val_colorR = (235, 152, 116)
            instantaneous_val_colorT = (0, 0, 0)
            if track_id in speed_by_id:
                # speed_kmph = speed_by_id[track_id]
                instantaneous_val_colorR = (0, 255, 0)
                cvzone.putTextRect(img, f'{speed_by_id[track_id]} kmph', (max(0, x1), max(35, y1)), scale=1.3, thickness=2,
                                   offset=10, colorR=(0, 0, 0), colorT=(255, 255, 255))

            cvzone.putTextRect(img, f'Id : {track_id}', (max(0, x2), max(35, y2)), scale=1, thickness=1, offset=10,
                               colorR=instantaneous_val_colorR, colorT=instantaneous_val_colorT)
            cv2.circle(img, (cX, cY), 5, (123, 255, 24), cv2.FILLED)

        # ---- MQTT / CALLBACK UPDATE (rate-limited) ----
        if on_update and frame_number - last_update_frame >= update_interval_frames:
            on_update({
                "vehicle_count": count,
                "active_vehicles": len(prev_centers),
                "timestamp": time.time()
            })
            last_update_frame = frame_number

        cv2.putText(img, f'Count: {count}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)

        cv2.imshow("Image", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()