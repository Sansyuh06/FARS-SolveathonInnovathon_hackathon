import subprocess
import time
import sys

try:
    import cv2
    import numpy as np
    import mss
except ImportError:
    print("Missing required libraries. Installing them now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-python", "mss", "numpy"])
    import cv2
    import numpy as np
    import mss

def record_demo():
    print("[FARS RECORDER] Launching FARS demo...")
    # Launch the FARS app as a subprocess
    process = subprocess.Popen([sys.executable, "fars_studio/launch_FARS.py"])

    # Give it a couple seconds to open the window
    time.sleep(2)

    with mss.mss() as sct:
        # Monitor 1 is usually the primary monitor
        monitor = sct.monitors[1]
        width, height = monitor["width"], monitor["height"]
        
        # Setup OpenCV Video Writer
        # 'mp4v' is a good cross-platform codec for mp4
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 24.0
        output_file = 'fars_demo_recording.mp4'
        out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

        print(f"[FARS RECORDER] Recording started! Capturing {width}x{height} at ~{fps} FPS.")
        print("[FARS RECORDER] Simply close the FARS window when you are done to stop recording and save the video.")

        # Record while the FARS process is still running
        while process.poll() is None:
            start_time = time.time()
            
            # Capture the screen
            img = np.array(sct.grab(monitor))
            
            # Convert BGRA to BGR (which OpenCV expects)
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            # Write frame to video
            out.write(frame)
            
            # Sleep to maintain the target FPS
            elapsed = time.time() - start_time
            sleep_time = max(1.0/fps - elapsed, 0)
            time.sleep(sleep_time)

        # Cleanup when the app is closed
        out.release()
        print(f"[FARS RECORDER] App closed. Video successfully saved to: {output_file}")

if __name__ == "__main__":
    record_demo()
