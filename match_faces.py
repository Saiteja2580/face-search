import cv2
import face_recognition
import numpy as np
import os
import shutil
import time

# --- Config ---
FRAME_INTERVAL = 2          # Use 1 frame every N
CAPTURE_DURATION = 5        # seconds
MATCH_THRESHOLD = 0.45      # Lower = more strict match
GALLERY_FOLDER = "static/gallery"
MATCHED_FOLDER = "static/matched"

# --- Prepare matched_faces folder ---
if os.path.exists(MATCHED_FOLDER):
    shutil.rmtree(MATCHED_FOLDER)
os.makedirs(MATCHED_FOLDER)

# --- Step 1: Capture Video from Webcam ---
print("📷 Starting 5-second face capture. Look at the camera...")

cap = cv2.VideoCapture(0)
start_time = time.time()
captured_frames = []
frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    elapsed = time.time() - start_time
    if elapsed > CAPTURE_DURATION:
        break

    if frame_count % FRAME_INTERVAL == 0:
        captured_frames.append(frame.copy())

    # 👇 Show the live camera feed
    cv2.imshow("Capturing Face (Look at the Camera)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    frame_count += 1

cap.release()
cv2.destroyAllWindows()
cv2.waitKey(1)

print(f"✅ Captured {len(captured_frames)} frames.\n")

# --- Step 2: Extract ALL Face Encodings from Captured Frames ---
ref_encodings = []
for frame in captured_frames:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = face_recognition.face_encodings(rgb)
    ref_encodings.extend(faces)  # Add all encodings, not just one

if not ref_encodings:
    print("❌ No face detected in captured video. Try again.")
    exit()

print(f"🧠 Stored {len(ref_encodings)} reference encodings.\n")

# --- Step 3: Match Against Group Photos ---
match_count = 0

for filename in os.listdir(GALLERY_FOLDER):
    path = os.path.join(GALLERY_FOLDER, filename)
    img_bgr = cv2.imread(path)
    if img_bgr is None:
        continue

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(img_rgb)
    face_encodings = face_recognition.face_encodings(img_rgb, face_locations)

    matched = False

    for i, enc in enumerate(face_encodings):
        distances = [np.linalg.norm(enc - ref) for ref in ref_encodings]
        min_dist = min(distances)
        if min_dist < MATCH_THRESHOLD:
            matched = True
            top, right, bottom, left = face_locations[i]
            cv2.rectangle(img_bgr, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(img_bgr, f"{min_dist:.2f}", (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    if matched:
        # Save clean version (without rectangles)
        out_clean_path = os.path.join(MATCHED_FOLDER, f"clean_{filename}")
        cv2.imwrite(out_clean_path, img_rgb[:, :, ::-1])  # RGB -> BGR

        # Save version with rectangles
        out_path = os.path.join(MATCHED_FOLDER, filename)
        cv2.imwrite(out_path, img_bgr)
        match_count += 1

print(f"\n🎯 {match_count} group image(s) with at least one match saved to '{MATCHED_FOLDER}'.")

if match_count == 0:
    print("🚫 No perfect matches found.")