# from flask import Flask, request, render_template, send_file, redirect, url_for, flash
# import os
# from PIL import Image
# import torch
# import uuid
# from fpdf import FPDF
# from datetime import datetime
# import cv2  # For video processing
#
# app = Flask(__name__)
# app.secret_key = 'your_secret_key_here'  # Required for flashing messages
#
# # Directories
# UPLOAD_FOLDER = 'uploads'
# RESULT_FOLDER = 'static/results'
# REPORT_FOLDER = 'reports'
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# os.makedirs(RESULT_FOLDER, exist_ok=True)
# os.makedirs(REPORT_FOLDER, exist_ok=True)
#
# # YOLO Model
# try:
#     print("Loading YOLO model...")
#     model = torch.hub.load('ultralytics/yolov5', 'yolov5s')  # Load YOLOv5 small model
#     print("Model loaded successfully.")
# except Exception as e:
#     print(f"Error loading model: {e}")
#     model = None
#
# @app.route('/')
# def home():
#     return render_template('index.html')
#
# @app.route('/upload', methods=['POST'])
# def upload_file():
#     result_image = None
#     result_video = None
#     detections = []
#     report_path = None
#     error = None
#
#     if 'file' not in request.files:
#         flash("No file part. Please upload an image or video.", 'error')
#         return redirect(url_for('home'))
#
#     file = request.files['file']
#
#     if file.filename == '':
#         flash("No selected file. Please choose an image or video.", 'error')
#         return redirect(url_for('home'))
#
#     try:
#         # Save the uploaded file
#         ext = os.path.splitext(file.filename)[1]
#         unique_filename = f"{uuid.uuid4().hex}{ext}"
#         file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
#         file.save(file_path)
#         print(f"File saved at: {file_path}")
#
#         # Perform detection
#         if model is None:
#             flash("Model not loaded. Please check the server logs.", 'error')
#             return redirect(url_for('home'))
#
#         # Flash message: Detection started
#         flash("Detection started. Please wait...", 'info')
#
#         # Check if the file is a video
#         if ext.lower() in ['.mp4', '.avi', '.mov']:
#             # Process video
#             result_video = process_video(file_path, unique_filename)
#             detections = []  # Video detections are not displayed in a table
#         else:
#             # Process image
#             img = Image.open(file_path).convert("RGB")
#             results = model(img)
#             print("Detection results:", results.pandas().xyxy[0])
#
#             # Save the detection result with bounding boxes and labels
#             result_path = os.path.join(RESULT_FOLDER, unique_filename)
#             results.render()  # Overlay bounding boxes and labels on the image
#             for img in results.ims:
#                 img_base = Image.fromarray(img)
#                 img_base.save(result_path)
#
#             # Fix backslashes in file path (for Windows compatibility)
#             result_path = result_path.replace("\\", "/")
#
#             # Verify the result file exists
#             if not os.path.exists(result_path):
#                 raise FileNotFoundError(f"Result file not found: {result_path}")
#
#             result_image = f'/static/results/{unique_filename}'
#
#             # Prepare detections for rendering
#             detections = results.pandas().xyxy[0].to_dict(orient="records")
#
#         # Generate the PDF report (for images only)
#         if result_image:
#             report_path = generate_report(file_path, result_image, detections)
#             report_path = f'/reports/{os.path.basename(report_path)}'
#
#         # Flash message: Detection completed
#         flash("Detection completed successfully!", 'success')
#         return render_template(
#             'index.html',
#             result_image=result_image,
#             result_video=result_video,
#             detections=detections,
#             report_path=report_path
#         )
#
#     except Exception as e:
#         print(f"Error: {e}")
#         flash(f"An error occurred during processing: {e}", 'error')
#         return redirect(url_for('home'))
#
# def process_video(video_path, unique_filename):
#     try:
#         # Open the video file
#         cap = cv2.VideoCapture(video_path)
#         if not cap.isOpened():
#             raise Exception("Could not open video file.")
#
#         # Get video properties
#         frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#         frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#         fps = int(cap.get(cv2.CAP_PROP_FPS))
#
#         # Define the codec and create a VideoWriter object
#         result_path = os.path.join(RESULT_FOLDER, unique_filename)
#         fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for .mp4
#         out = cv2.VideoWriter(result_path, fourcc, fps, (frame_width, frame_height))
#
#         # Process each frame
#         while cap.isOpened():
#             ret, frame = cap.read()
#             if not ret:
#                 break
#
#             # Perform detection on the frame
#             results = model(frame)
#
#             # Render bounding boxes and labels on the frame
#             results.render()
#
#             # Write the frame with detections to the output video
#             out.write(results.ims[0])
#
#         # Release resources
#         cap.release()
#         out.release()
#
#         # Fix backslashes in file path (for Windows compatibility)
#         result_path = result_path.replace("\\", "/")
#
#         # Verify the result file exists
#         if not os.path.exists(result_path):
#             raise FileNotFoundError(f"Result video not found: {result_path}")
#
#         return f'/static/results/{unique_filename}'
#     except Exception as e:
#         print(f"Error processing video: {e}")
#         raise
#
# @app.route('/download_report/<filename>')
# def download_report(filename):
#     try:
#         return send_file(os.path.join(REPORT_FOLDER, filename), as_attachment=True)
#     except Exception as e:
#         print(f"Error downloading report: {e}")
#         flash("Error downloading report. Please try again.", 'error')
#         return redirect(url_for('home'))
#
# @app.route('/download_video/<filename>')
# def download_video(filename):
#     try:
#         return send_file(os.path.join(RESULT_FOLDER, filename), as_attachment=True)
#     except Exception as e:
#         print(f"Error downloading video: {e}")
#         flash("Error downloading video. Please try again.", 'error')
#         return redirect(url_for('home'))
#
# def generate_report(input_image_path, output_image_path, detections):
#     try:
#         # Create a PDF report
#         pdf = FPDF()
#         pdf.add_page()
#         pdf.set_font("Arial", size=12)
#
#         # Add title
#         pdf.set_font("Arial", 'B', 16)
#         pdf.cell(200, 10, txt="Object Detection Report", ln=True, align="C")
#         pdf.ln(10)
#
#         # Add input image
#         pdf.set_font("Arial", 'B', 12)
#         pdf.cell(200, 10, txt="Input Image", ln=True)
#         pdf.image(input_image_path, x=10, y=40, w=90)
#         pdf.ln(100)
#
#         # Add output image (if available)
#         if output_image_path and os.path.exists(output_image_path):
#             pdf.cell(200, 10, txt="Output Image", ln=True)
#             pdf.image(output_image_path, x=10, y=150, w=90)
#             pdf.ln(100)
#         else:
#             pdf.cell(200, 10, txt="Output Image: Not available", ln=True)
#             pdf.ln(100)
#
#         # Add detection results table
#         pdf.set_font("Arial", 'B', 12)
#         pdf.cell(200, 10, txt="Detection Results", ln=True)
#         pdf.ln(10)
#
#         # Table header
#         pdf.set_font("Arial", 'B', 10)
#         pdf.cell(60, 10, txt="Object", border=1)
#         pdf.cell(40, 10, txt="Confidence", border=1)
#         pdf.cell(40, 10, txt="Bounding Box", border=1)
#         pdf.ln()
#
#         # Table rows
#         pdf.set_font("Arial", size=10)
#         for detection in detections:
#             pdf.cell(60, 10, txt=detection['name'], border=1)
#             pdf.cell(40, 10, txt=f"{detection['confidence']:.2f}", border=1)
#             pdf.cell(40, 10, txt=f"({detection['xmin']}, {detection['ymin']}, {detection['xmax']}, {detection['ymax']})", border=1)
#             pdf.ln()
#
#         # Save the PDF
#         report_filename = f"report_{uuid.uuid4().hex}.pdf"
#         report_path = os.path.join(REPORT_FOLDER, report_filename)
#         pdf.output(report_path)
#         print(f"Report saved at: {report_path}")
#
#         return report_path
#     except Exception as e:
#         print(f"Error generating report: {e}")
#         raise
#
# if __name__ == '__main__':
#     app.run(debug=True)






# from flask import Flask, request, render_template, send_file, redirect, url_for, flash
# import os
# from PIL import Image
# import torch
# import uuid
# from fpdf import FPDF
# from datetime import datetime
# import cv2  # For video processing
#
# app = Flask(__name__)
# app.secret_key = 'your_secret_key_here'  # Required for flashing messages
#
# # Directories
# UPLOAD_FOLDER = 'uploads'
# RESULT_FOLDER = 'static/results'
# REPORT_FOLDER = 'reports'
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# os.makedirs(RESULT_FOLDER, exist_ok=True)
# os.makedirs(REPORT_FOLDER, exist_ok=True)
#
# # YOLO Model
# try:
#     print("Loading YOLO model...")
#     model = torch.hub.load('ultralytics/yolov5', 'yolov5s')  # Load YOLOv5 small model
#     print("Model loaded successfully.")
# except Exception as e:
#     print(f"Error loading model: {e}")
#     model = None
#
# @app.route('/')
# def home():
#     return render_template('index.html')
#
# @app.route('/upload', methods=['POST'])
# def upload_file():
#     result_image = None
#     result_video = None
#     detections = []
#     report_path = None
#     error = None
#
#     if 'file' not in request.files:
#         flash("No file part. Please upload an image or video.", 'error')
#         return redirect(url_for('home'))
#
#     file = request.files['file']
#
#     if file.filename == '':
#         flash("No selected file. Please choose an image or video.", 'error')
#         return redirect(url_for('home'))
#
#     try:
#         # Save the uploaded file
#         ext = os.path.splitext(file.filename)[1]
#         unique_filename = f"{uuid.uuid4().hex}{ext}"
#         file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
#         file.save(file_path)
#         print(f"File saved at: {file_path}")
#
#         # Perform detection
#         if model is None:
#             flash("Model not loaded. Please check the server logs.", 'error')
#             return redirect(url_for('home'))
#
#         # Flash message: Detection started
#         flash("Detection started. Please wait...", 'info')
#
#         # Check if the file is a video
#         if ext.lower() in ['.mp4', '.avi', '.mov']:
#             # Process video
#             result_video = process_video(file_path, unique_filename)
#             detections = []  # Video detections are not displayed in a table
#         else:
#             # Process image
#             img = Image.open(file_path).convert("RGB")
#             results = model(img)
#             print("Detection results:", results.pandas().xyxy[0])
#
#             # Save the detection result with bounding boxes and labels
#             result_path = os.path.join(RESULT_FOLDER, unique_filename)
#             results.render()  # Overlay bounding boxes and labels on the image
#             for img in results.ims:
#                 img_base = Image.fromarray(img)
#                 img_base.save(result_path)
#
#             # Fix backslashes in file path (for Windows compatibility)
#             result_path = result_path.replace("\\", "/")
#
#             # Verify the result file exists
#             if not os.path.exists(result_path):
#                 raise FileNotFoundError(f"Result file not found: {result_path}")
#
#             result_image = f'/static/results/{unique_filename}'
#
#             # Prepare detections for rendering
#             detections = results.pandas().xyxy[0].to_dict(orient="records")
#
#         # Generate the PDF report (for images only)
#         if result_image:
#             report_path = generate_report(file_path, result_image, detections)
#             report_path = f'/reports/{os.path.basename(report_path)}'
#
#         # Flash message: Detection completed
#         flash("Detection completed successfully!", 'success')
#         return render_template(
#             'index.html',
#             result_image=result_image,
#             result_video=result_video,
#             detections=detections,
#             report_path=report_path
#         )
#
#     except Exception as e:
#         print(f"Error: {e}")
#         flash(f"An error occurred during processing: {e}", 'error')
#         return redirect(url_for('home'))
#
# def process_video(video_path, unique_filename):
#     try:
#         # Open the video file
#         cap = cv2.VideoCapture(video_path)
#         if not cap.isOpened():
#             raise Exception("Could not open video file.")
#
#         # Get video properties
#         frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#         frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#         fps = int(cap.get(cv2.CAP_PROP_FPS))
#
#         # Define the codec and create a VideoWriter object
#         result_path = os.path.join(RESULT_FOLDER, unique_filename)
#         fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for .mp4
#         out = cv2.VideoWriter(result_path, fourcc, fps, (frame_width, frame_height))
#
#         # Process each frame
#         while cap.isOpened():
#             ret, frame = cap.read()
#             if not ret:
#                 break
#
#             # Perform detection on the frame
#             results = model(frame)
#
#             # Render bounding boxes and labels on the frame
#             results.render()
#
#             # Write the frame with detections to the output video
#             out.write(results.ims[0])
#
#         # Release resources
#         cap.release()
#         out.release()
#
#         # Fix backslashes in file path (for Windows compatibility)
#         result_path = result_path.replace("\\", "/")
#
#         # Verify the result file exists
#         if not os.path.exists(result_path):
#             raise FileNotFoundError(f"Result video not found: {result_path}")
#
#         return f'/static/results/{unique_filename}'
#     except Exception as e:
#         print(f"Error processing video: {e}")
#         raise
#
# @app.route('/download_report/<filename>')
# def download_report(filename):
#     try:
#         return send_file(os.path.join(REPORT_FOLDER, filename), as_attachment=True)
#     except Exception as e:
#         print(f"Error downloading report: {e}")
#         flash("Error downloading report. Please try again.", 'error')
#         return redirect(url_for('home'))
#
# @app.route('/download_video/<filename>')
# def download_video(filename):
#     try:
#         return send_file(os.path.join(RESULT_FOLDER, filename), as_attachment=True)
#     except Exception as e:
#         print(f"Error downloading video: {e}")
#         flash("Error downloading video. Please try again.", 'error')
#         return redirect(url_for('home'))
#
# def generate_report(input_image_path, output_image_path, detections):
#     try:
#         # Create a PDF report
#         pdf = FPDF()
#         pdf.add_page()
#         pdf.set_font("Arial", size=12)
#
#         # Add title
#         pdf.set_font("Arial", 'B', 16)
#         pdf.cell(200, 10, txt="Object Detection Report", ln=True, align="C")
#         pdf.ln(10)
#
#         # Add input image
#         pdf.set_font("Arial", 'B', 12)
#         pdf.cell(200, 10, txt="Input Image", ln=True)
#         pdf.image(input_image_path, x=10, y=40, w=90)
#         pdf.ln(100)
#
#         # Add output image (if available)
#         if output_image_path and os.path.exists(output_image_path):
#             pdf.cell(200, 10, txt="Output Image", ln=True)
#             pdf.image(output_image_path, x=10, y=150, w=90)
#             pdf.ln(100)
#         else:
#             pdf.cell(200, 10, txt="Output Image: Not available", ln=True)
#             pdf.ln(100)
#
#         # Add detection results table
#         pdf.set_font("Arial", 'B', 12)
#         pdf.cell(200, 10, txt="Detection Results", ln=True)
#         pdf.ln(10)
#
#         # Table header
#         pdf.set_font("Arial", 'B', 10)
#         pdf.cell(60, 10, txt="Object", border=1)
#         pdf.cell(40, 10, txt="Confidence", border=1)
#         pdf.cell(40, 10, txt="Bounding Box", border=1)
#         pdf.ln()
#
#         # Table rows
#         pdf.set_font("Arial", size=10)
#         for detection in detections:
#             pdf.cell(60, 10, txt=detection['name'], border=1)
#             pdf.cell(40, 10, txt=f"{detection['confidence']:.2f}", border=1)
#             pdf.cell(40, 10, txt=f"({detection['xmin']}, {detection['ymin']}, {detection['xmax']}, {detection['ymax']})", border=1)
#             pdf.ln()
#
#         # Save the PDF
#         report_filename = f"report_{uuid.uuid4().hex}.pdf"
#         report_path = os.path.join(REPORT_FOLDER, report_filename)
#         pdf.output(report_path)
#         print(f"Report saved at: {report_path}")
#
#         return report_path
#     except Exception as e:
#         print(f"Error generating report: {e}")
#         raise
#
# if __name__ == '__main__':
#     app.run(debug=True)




from flask import Flask, request, render_template, send_file, redirect, url_for, flash
import os
from PIL import Image
import torch
import uuid
from fpdf import FPDF
import cv2  # For video processing

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flashing messages

# Directories
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'static/results'
REPORT_FOLDER = 'reports'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

# YOLO Model
try:
    print("Loading YOLO model...")
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s')  # Load YOLOv5 small model
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    result_image = None
    result_video = None
    detections = []
    report_path = None

    if 'file' not in request.files:
        flash("No file part. Please upload an image or video.", 'error')
        return redirect(url_for('home'))

    file = request.files['file']

    if file.filename == '':
        flash("No selected file. Please choose an image or video.", 'error')
        return redirect(url_for('home'))

    try:
        # Save the uploaded file
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        print(f"File saved at: {file_path}")

        # Perform detection
        if model is None:
            flash("Model not loaded. Please check the server logs.", 'error')
            return redirect(url_for('home'))

        # Flash message: Detection started
        flash("Detection started. Please wait...", 'info')

        # Check if the file is a video
        if ext.lower() in ['.mp4', '.avi', '.mov']:
            # Process video
            result_video = process_video(file_path, unique_filename)
            detections = []  # Video detections are not displayed in a table
        else:
            # Process image
            img = Image.open(file_path).convert("RGB")
            results = model(img)
            print("Detection results:", results.pandas().xyxy[0])

            # Save the detection result with bounding boxes and labels
            result_path = os.path.join(RESULT_FOLDER, unique_filename)
            results.render()  # Overlay bounding boxes and labels on the image
            for img in results.ims:
                img_base = Image.fromarray(img)
                img_base.save(result_path)

            # Fix backslashes in file path (for Windows compatibility)
            result_path = result_path.replace("\\", "/")

            # Verify the result file exists
            if not os.path.exists(result_path):
                raise FileNotFoundError(f"Result file not found: {result_path}")

            result_image = f'/static/results/{unique_filename}'

            # Prepare detections for rendering
            detections = results.pandas().xyxy[0].to_dict(orient="records")

        # Generate the PDF report (for images only)
        if result_image:
            report_path = generate_report(file_path, result_image, detections)
            report_path = f'/reports/{os.path.basename(report_path)}'

        # Flash message: Detection completed
        flash("Detection completed successfully!", 'success')
        return render_template(
            'index.html',
            result_image=result_image,
            result_video=result_video,
            detections=detections,
            report_path=report_path
        )

    except Exception as e:
        print(f"Error: {e}")
        flash(f"An error occurred during processing: {e}", 'error')
        return redirect(url_for('home'))

def process_video(video_path, unique_filename):
    try:
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception("Could not open video file.")

        # Get video properties
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Video Properties: {frame_width}x{frame_height}, {fps} FPS, {total_frames} frames")

        # Define the codec and create a VideoWriter object
        result_path = os.path.join(RESULT_FOLDER, unique_filename)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for .mp4
        out = cv2.VideoWriter(result_path, fourcc, fps, (frame_width, frame_height))

        # Process each frame
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Perform detection on the frame
            results = model(frame)

            # Render bounding boxes and labels on the frame
            results.render()

            # Write the frame with detections to the output video
            out.write(results.ims[0])

            frame_count += 1
            print(f"Processed frame {frame_count}/{total_frames}")

        # Release resources
        cap.release()
        out.release()

        # Fix backslashes in file path (for Windows compatibility)
        result_path = result_path.replace("\\", "/")

        # Verify the result file exists
        if not os.path.exists(result_path):
            raise FileNotFoundError(f"Result video not found: {result_path}")

        return f'/static/results/{unique_filename}'
    except Exception as e:
        print(f"Error processing video: {e}")
        raise

@app.route('/download_report/<filename>')
def download_report(filename):
    try:
        return send_file(os.path.join(REPORT_FOLDER, filename), as_attachment=True)
    except Exception as e:
        print(f"Error downloading report: {e}")
        flash("Error downloading report. Please try again.", 'error')
        return redirect(url_for('home'))

@app.route('/download_video/<filename>')
def download_video(filename):
    try:
        return send_file(os.path.join(RESULT_FOLDER, filename), as_attachment=True)
    except Exception as e:
        print(f"Error downloading video: {e}")
        flash("Error downloading video. Please try again.", 'error')
        return redirect(url_for('home'))

def generate_report(input_image_path, output_image_path, detections):
    try:
        # Create a PDF report
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Add title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Object Detection Report", ln=True, align="C")
        pdf.ln(10)

        # Add input image
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Input Image", ln=True)
        pdf.image(input_image_path, x=10, y=40, w=90)
        pdf.ln(100)

        # Add output image (if available)
        if output_image_path and os.path.exists(output_image_path):
            pdf.cell(200, 10, txt="Output Image", ln=True)
            pdf.image(output_image_path, x=10, y=150, w=90)
            pdf.ln(100)
        else:
            pdf.cell(200, 10, txt="Output Image: Not available", ln=True)
            pdf.ln(100)

        # Add detection results table
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Detection Results", ln=True)
        pdf.ln(10)

        # Table header
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(60, 10, txt="Object", border=1)
        pdf.cell(40, 10, txt="Confidence", border=1)
        pdf.cell(40, 10, txt="Bounding Box", border=1)
        pdf.ln()

        # Table rows
        pdf.set_font("Arial", size=10)
        for detection in detections:
            pdf.cell(60, 10, txt=detection['name'], border=1)
            pdf.cell(40, 10, txt=f"{detection['confidence']:.2f}", border=1)
            pdf.cell(40, 10, txt=f"({detection['xmin']}, {detection['ymin']}, {detection['xmax']}, {detection['ymax']})", border=1)
            pdf.ln()

        # Save the PDF
        report_filename = f"report_{uuid.uuid4().hex}.pdf"
        report_path = os.path.join(REPORT_FOLDER, report_filename)
        pdf.output(report_path)
        print(f"Report saved at: {report_path}")

        return report_path
    except Exception as e:
        print(f"Error generating report: {e}")
        raise

if __name__ == '__main__':
    app.run(debug=True)