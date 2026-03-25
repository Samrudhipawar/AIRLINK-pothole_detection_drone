import streamlit as st
st.set_page_config(page_title="Pothole AI Analyzer", layout="wide")

import cv2
import torch
import numpy as np
from PIL import Image
from ultralytics import YOLO 
from torchvision.transforms import Compose, Resize, ToTensor, Normalize

# Now everything else can happen
st.title("🚧 Drone-Based Pothole Detection & Depth Analysis")
st.write("Upload a road image to detect potholes and get AI-powered repair suggestions.")

@st.cache_resource
def load_models():
    yolo = YOLO('yolov8n.pt') 
    midas = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
    return yolo, midas

yolo, midas = load_models()

uploaded_file = st.file_uploader("Choose an image...", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    # Convert uploaded file to OpenCV format
    img = Image.open(uploaded_file).convert('RGB')
    frame = np.array(img)
    
    # 2. Run YOLO Detection
    results = yolo(frame)
    
    # 3. Run Depth Estimation
    transform = Compose([
        Resize((256, 256)), 
        ToTensor(), 
        Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    input_batch = transform(img).unsqueeze(0)

    with torch.no_grad():
        prediction = midas(input_batch)
        depth_map = prediction.squeeze().cpu().numpy()
        # Scale to 0-15cm for demo realism
        depth_cm_map = cv2.normalize(depth_map, None, 0, 15, cv2.NORM_MINMAX)

    # 4. Layout: Display Image
    st.image(results[0].plot(), caption="Processed Detection Frame", use_container_width=True)

    # 5. Measurement & Suggestion Logic
    if len(results[0].boxes) > 0:
        # Get coordinates of the first pothole detected
        box = results[0].boxes[0].xyxy[0].cpu().numpy()
        center_x = int((box[0] + box[2]) / 2)
        center_y = int((box[1] + box[3]) / 2)
        
        # Calculate Depth at center
        h, w = depth_cm_map.shape
        scaled_x = int(center_x * (w / frame.shape[1]))
        scaled_y = int(center_y * (h / frame.shape[0]))
        pothole_depth = float(depth_cm_map[scaled_y, scaled_x])

        # Material Selection Logic
        if pothole_depth < 4:
            material = "Cold Mix Asphalt"
            desc = "Best for minor surface repairs. Quick application."
        elif pothole_depth < 8:
            material = "Hot Mix Asphalt (HMA)"
            desc = "Standard permanent repair. High durability."
        else:
            material = "Epoxy-Modified Bitumen"
            desc = "Deep structural repair for high-traffic zones."

        # Display Metrics
        st.divider()
        st.subheader("📊 AI Analysis Report")
        c1, c2, c3 = st.columns(3)
        c1.metric("Estimated Depth", f"{pothole_depth:.2f} cm")
        c2.metric("Severity Level", "High" if pothole_depth > 7 else "Moderate")
        c3.metric("Recommended Material", material)
        
        st.info(f"**Technician Note:** {desc}")
    else:
        st.warning("No potholes detected in this frame.")