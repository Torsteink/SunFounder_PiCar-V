import numpy as np
import cv2
import os
from flask import Flask, Response
from multiprocessing import Manager, Process
from threading import Lock
import time



app = Flask(__name__)
@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

def gen():
    """Video streaming generator function."""
    while True:  
        img = Vilib.img_array[0]
        if img is None or not hasattr(img, "size") or img.size == 0:
            time.sleep(0.05)
            continue

        ok, encoded = cv2.imencode('.jpg', img)
        if not ok:
            time.sleep(0.05)
            continue
        frame = encoded.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        

@app.route('/mjpg')
def video_feed():
    # from camera import Camera
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame') 

def web_camera_start():
    port = int(os.environ.get("PICAR_STREAM_PORT", "8765"))
    app.run(host='0.0.0.0', port=port, threaded=True, use_reloader=False)


class Vilib(object): 

    video_source = os.environ.get("PICAR_CAMERA_SOURCE", "0")
    reconnect_delay = float(os.environ.get("PICAR_CAMERA_RECONNECT_DELAY", "0.5"))
    max_reconnect_delay = float(os.environ.get("PICAR_CAMERA_MAX_RECONNECT_DELAY", "5"))
    read_failure_limit = int(os.environ.get("PICAR_CAMERA_READ_FAILURE_LIMIT", "3"))

    detect_obj_parameter = Manager().dict()
    img_array = Manager().list(range(2))
    rt_img = np.ones((320,240),np.uint8)     
    img_array[0] = rt_img
    _start_lock = Lock()
    _camera_process = None
    _web_process = None


    @staticmethod
    def camera_start(web_func = True):
        with Vilib._start_lock:
            if web_func and (
                    Vilib._web_process is None or
                    not Vilib._web_process.is_alive()):
                Vilib._web_process = Process(
                    name='PiCar video web server', target=web_camera_start)
                Vilib._web_process.daemon = True
                Vilib._web_process.start()

            if (Vilib._camera_process is None or
                    not Vilib._camera_process.is_alive()):
                Vilib._camera_process = Process(
                    name='PiCar camera capture', target=Vilib.camera_clone)
                Vilib._camera_process.daemon = True
                Vilib._camera_process.start()

    
    @staticmethod
    def camera_clone():
        Vilib.camera()     

    @staticmethod
    def _video_source():
        video_source = Vilib.video_source
        if isinstance(video_source, str) and video_source.isdigit():
            video_source = int(video_source)
        return video_source

    @staticmethod
    def _open_camera(video_source):
        # Open local Linux cameras through V4L2 directly. OpenCV otherwise
        # commonly selects GStreamer, whose failed pipeline cannot recover
        # after a transient USB camera disconnect.
        is_local_camera = (
            isinstance(video_source, int) or
            (isinstance(video_source, str) and
             video_source.startswith(("/dev/video", "/dev/v4l/")))
        )
        try:
            if is_local_camera and hasattr(cv2, "CAP_V4L2"):
                camera = cv2.VideoCapture(video_source, cv2.CAP_V4L2)
            else:
                camera = cv2.VideoCapture(video_source)
        except cv2.error as exc:
            print("Unable to create camera capture: {0}".format(exc), flush=True)
            return None

        if not camera.isOpened():
            camera.release()
            return None

        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return camera

    @staticmethod
    def camera():
        video_source = Vilib._video_source()
        cv2.setUseOptimized(True)
        retry_delay = Vilib.reconnect_delay

        while True:
            camera = Vilib._open_camera(video_source)
            if camera is None:
                print(
                    "Unable to open camera source {0}; retrying in {1:.1f}s".format(
                        Vilib.video_source, retry_delay),
                    flush=True,
                )
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, Vilib.max_reconnect_delay)
                continue

            print("Camera source {0} opened".format(Vilib.video_source), flush=True)
            retry_delay = Vilib.reconnect_delay
            consecutive_failures = 0
            try:
                while consecutive_failures < Vilib.read_failure_limit:
                    try:
                        ok, img = camera.read()
                    except cv2.error as exc:
                        print("Camera read failed: {0}".format(exc), flush=True)
                        break
                    if not ok or img is None:
                        consecutive_failures += 1
                        time.sleep(0.05)
                        continue

                    consecutive_failures = 0
                    Vilib.img_array[0] = img
            finally:
                camera.release()

            print(
                "Camera source {0} stopped responding; reopening".format(
                    Vilib.video_source),
                flush=True,
            )
            time.sleep(Vilib.reconnect_delay)

if __name__ == "__main__":
    Vilib.camera_start()
    while True:
        pass
