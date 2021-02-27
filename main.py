
from flask import Flask, render_template, Response, request
from camera import VideoCamera
import time
import os
from pyserial_connection_arduino import connect_to_arduino, list_available_ports
import numpy as np

app = Flask(__name__)
#app = Flask(__name__, template_folder='/var/www/html/templates')

comport = 'COM3'
motor0_enable = 0
motor0_direction = 0
motor0_position = 0
motor1_enable = 0
motor1_direction = 0
motor1_position = 0
motor2_enable = 0
motor2_direction = 0
motor2_position = 0
motor3_enable = 0
motor3_direction = 0
motor3_position = 0

#background process happening without any refreshing
@app.route('/left')
def left():
    print ("Left")
    results = np.array(connect_to_arduino(comport,motor0_enable,motor0_direction,0,
        motor1_enable,motor1_direction,motor1_position,motor2_enable,motor2_direction,motor2_position,motor3_enable,motor3_direction,motor3_position))
    print(f"Received values: {results}")
    return ("nothing")

@app.route('/center')
def center():
    print ("Center")
    results = np.array(connect_to_arduino(comport,motor0_enable,motor0_direction,1600,
        motor1_enable,motor1_direction,motor1_position,motor2_enable,motor2_direction,motor2_position,motor3_enable,motor3_direction,motor3_position))
    print(f"Received values: {results}")
    return ("nothing")

@app.route('/right')
def right():
    print ("Right")
    results = np.array(connect_to_arduino(comport,motor0_enable,motor0_direction,3200,
        motor1_enable,motor1_direction,motor1_position,motor2_enable,motor2_direction,motor2_position,motor3_enable,motor3_direction,motor3_position))
    print(f"Received values: {results}")
    return ("nothing")

@app.route('/fourth')
def fourth():
    print("Fourth")
    results = np.array(connect_to_arduino(comport,motor0_enable,motor0_direction,4800,
        motor1_enable,motor1_direction,motor1_position,motor2_enable,motor2_direction,motor2_position,motor3_enable,motor3_direction,motor3_position))
    print(f"Received values: {results}")
    return ("nothing")

@app.route('/', methods=['GET', 'POST'])
def move():
    result = ""
    if request.method == 'POST':
        
        return render_template('index.html', res_str=result)
                        
    return render_template('index.html')


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)
