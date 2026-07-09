import cv2
import os

# Folder where images will be saved
save_folder = 'CapturedImages'
os.makedirs(save_folder, exist_ok=True)

def capture_image():
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam (tried index 1 and 0).")
        return

    print("Press 'c' to capture an image or 'q' to quit.")
    
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        if not ret:
            print("Failed to grab frame.")
            break

        # Display the resulting frame
        cv2.imshow('Webcam', frame)

        # Wait for key press
        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            # Save the captured frame
            image_name = os.path.join(save_folder, 'captured_image.jpg')
            cv2.imwrite(image_name, frame)
            print(f"Image saved as {image_name}")
        elif key == ord('q'):
            # Quit the loop
            break

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_image()
