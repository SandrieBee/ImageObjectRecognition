import customtkinter as ctk
from tkinter import Label, filedialog, messagebox
from PIL import Image, ImageTk
import threading
from detect import run  
from pathlib import Path# Ensure this module is implemented
import os
import cv2

# Global variables for the live feed control
stop_live_detection = threading.Event()
cancel_button = None  # Reference to dynamically create/destroy the button

# Function to handle image upload and detection
def detect_image():
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpeg*.jpg;*.png")])
    if file_path:
        try:
            # Run YOLOv5 detection on the selected image
            run(
                source=file_path,          # Path to the selected image
                weights="yolov5s.pt",      # Path to your YOLOv5 weights
                conf_thres=0.25,           # Confidence threshold
                iou_thres=0.45,            # IOU threshold
                nosave=False,              # Ensure results are saved
                save_txt=False,            # Do not save results as text
                save_conf=False,           # Do not save confidence
                view_img=False,            # Do not show OpenCV window
                project="runs/detect",     # Folder to save results
                name="image_results",      # Subfolder name
                exist_ok=True              # Overwrite existing results
            )

            # Load and display the resulting image with detections
            result_image_path = f"runs/detect/image_results/{Path(file_path).name}"  # Path to saved result
            if os.path.exists(result_image_path):
                img = Image.open(result_image_path).resize((600, 480))
                img_tk = ImageTk.PhotoImage(img)
                image_label.configure(image=img_tk)
                image_label.image = img_tk
                result_label.configure(text="Detection complete. Results displayed.")
            else:
                result_label.configure(text="Error: Result image not found.")

        except Exception as e:
            result_label.configure(text=f"Error during detection: {e}")
    else:
        image_label.configure(image=None)
        image_label.image = None
        result_label.configure(text="No image selected.")




# Function to handle video upload and detection
def detect_video():
    file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4;*.avi")])
    if file_path:
        try:
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                result_label.configure(text="Error: Could not open video.")
                return

            # Prepare for saving the output video
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            output_path = f"runs/detect/video_results/{Path(file_path).stem}.mp4"
            out = cv2.VideoWriter(output_path, fourcc, cap.get(cv2.CAP_PROP_FPS),
                                  (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                                   int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))

            # Process each frame recursively
            def process_frame():
                ret, frame = cap.read()
                if ret:
                    # Perform detection on each frame
                    results = run(source=frame, weights="yolov5s.pt", conf_thres=0.25, iou_thres=0.45, nosave=True)

                    # Draw results on the frame
                    if results and len(results.xyxy[0]) > 0:
                        for box in results.xyxy[0]:
                            x1, y1, x2, y2, conf, cls = box
                            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                            cv2.putText(frame, f"{results.names[int(cls)]} {conf:.2f}", 
                                        (int(x1), int(y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    # Convert to RGB and display in the GUI
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    img_tk = ImageTk.PhotoImage(image=img)
                    image_label.configure(image=img_tk)
                    image_label.image = img_tk

                    # Write the frame to output video
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    out.write(frame)

                    # Continue processing the next frame after 30 ms
                    app.after(30, process_frame)
                else:
                    # End of video
                    cap.release()
                    out.release()
                    messagebox.showinfo("Video Detection", f"Detection complete! Video saved at {output_path}")
                    result_label.configure(text=f"Detection complete. Video saved at {output_path}")

            process_frame()  # Start processing the first frame

        except Exception as e:
            result_label.configure(text=f"Error processing video: {e}")
    else:
        result_label.configure(text="No video selected.")


# Live detection logic
def live_detection():
    global stop_live_detection, cancel_button
    stop_live_detection.clear()

    def process_live_feed():
        try:
            run(source=0, weights="yolov5s.pt", view_img=True, nosave=True)
        except Exception as e:
            result_label.configure(text=f"Error during live detection: {e}")
        finally:
            stop_live_detection.set()
            hide_cancel_button()


    def stop_detection():
        stop_live_detection.set()#-
        cv2.destroyAllWindows()#-
        hide_cancel_button()#-
        result_label.configure(text="Live detection stopped.")#-
        try:#+
            stop_live_detection.set()#+
            cv2.destroyAllWindows()#+
            hide_cancel_button()#+
            # Use app.after to ensure GUI updates are done on the main thread#+
            app.after(0, lambda: result_label.configure(text="Live detection stopped."))#+
        except Exception as e:#+
            # Log the exception or show an error message#+
            app.after(0, lambda: result_label.configure(text=f"Error stopping detection: {e}"))#+


    def show_cancel_button():
        global cancel_button
        cancel_button = ctk.CTkButton(
            app, text="Cancel", command=stop_detection,
            width=100, height=30, fg_color="red", hover_color="#C82333", text_color="white"
        )
        cancel_button.pack(pady=10)

    def hide_cancel_button():
        global cancel_button
        if cancel_button:
            cancel_button.destroy()
            cancel_button = None

    threading.Thread(target=process_live_feed).start()
    show_cancel_button()
    result_label.configure(text="Running live detection... Press 'Cancel' to stop.")



# Initialize the app
app = ctk.CTk()
app.title("IMAGE AND OBJECT RECOGNITION")
app.geometry("600x480")
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")



# Header
header_label = ctk.CTkLabel(app, text="IMAGE AND OBJECT RECOGNITION", font=ctk.CTkFont(size=20, weight="bold"))
header_label.pack(pady=20)

# Buttons
button_frame = ctk.CTkFrame(app)
button_frame.pack(pady=20)

button_font = ctk.CTkFont(size=14, weight="bold")

image_button = ctk.CTkButton(button_frame, text="Upload Image to Detect", command=detect_image, width=250, height=40,
                             font=button_font, fg_color="#3B8ED0", hover_color="#2B6FA3", text_color="white")
image_button.pack(pady=20)

video_button = ctk.CTkButton(button_frame, text="Upload Video to Detect", command=detect_video, width=250, height=40,
                             font=button_font, fg_color="#3B8ED0", hover_color="#2B6FA3", text_color="white")
video_button.pack(pady=20)

live_button = ctk.CTkButton(app, text="Live Camera Detection", command=live_detection, width=200, height=40, font=button_font,
                            fg_color="#3B8ED0", hover_color="#2B6FA3", text_color="white")
live_button.pack(pady=20)

# Image display
image_label = ctk.CTkLabel(app, text="")
image_label.pack(pady=15)

# Detection result label
result_label = ctk.CTkLabel(app, text="Detection Result: None", font=ctk.CTkFont(size=14))
result_label.pack(pady=20)

# Run the app
app.mainloop()
