import numpy as np
import cv2
import os
from flask import Flask, Response
from multiprocessing import Manager
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

    detect_obj_parameter = Manager().dict()
    img_array = Manager().list(range(2))
    rt_img = np.ones((320,240),np.uint8)     
    img_array[0] = rt_img


    @staticmethod
    def camera_start(web_func = True):
        from multiprocessing import Process
       
        worker_2 = Process(name='worker 2',target=Vilib.camera_clone)
        if web_func == True:
            worker_1 = Process(name='worker 1',target=web_camera_start)
            worker_1.start()
        worker_2.start()

    
    @staticmethod
    def camera_clone():
        Vilib.camera()     

    @staticmethod
    def camera():
        video_source = Vilib.video_source
        if isinstance(video_source, str) and video_source.isdigit():
            video_source = int(video_source)

        camera = cv2.VideoCapture(video_source)
        if not camera.isOpened():
            print("Unable to open camera source: {0}".format(Vilib.video_source))
            return

        camera.set(3,320)
        camera.set(4,240)
        camera.set(cv2.CAP_PROP_BUFFERSIZE,1)
        cv2.setUseOptimized(True)
 

        while True:
            ok, img = camera.read()
            if not ok or img is None:
                time.sleep(0.05)
                continue

            Vilib.img_array[0] = img

if __name__ == "__main__":
    Vilib.camera_start()
    while True:
        pass
