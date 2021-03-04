
from flask import Flask, render_template, Response, request
from camera import VideoCamera
import time
import os
from pyserial_connection_arduino import connect_to_arduino, list_available_ports
import numpy as np

# how to schedule
# https://stackoverflow.com/questions/21214270/how-to-schedule-a-function-to-run-every-hour-on-flask
# from apscheduler.schedulers.background import BackgroundScheduler

from flask_apscheduler import APScheduler
# set configuration values
class Config(object):
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
#app = Flask(__name__, template_folder='/var/www/html/templates')

app.config.from_object(Config())
# initialize scheduler
scheduler = APScheduler()
# if you don't wanna use a config, you can set options here:
# scheduler.api_enabled = True
scheduler.init_app(app)
scheduler.start()

comport = 'COM6'
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

def motor_position(position_in_degree):
    print("motor_position")
    # 4800 steps are 270°, 360 should never be possible since = 0°
    # degrees are divided by 90 and multiplied by 1600
    # only send int values to arduino!
    step_position_arduino = int(position_in_degree/90*1600)
    try:
        results = np.array(connect_to_arduino(comport,motor0_enable,motor0_direction,step_position_arduino,
            motor1_enable,motor1_direction,motor1_position,motor2_enable,motor2_direction,motor2_position,motor3_enable,motor3_direction,motor3_position))
        print(f"Received values: {results}")
    except:
        print("Microcontroller not found or not connected")

@app.route('/deg_0')
def deg_0():
    print ("Moving to 0°")
    motor_position(0)
    return ("nothing")

@app.route('/deg_90')
def deg_90():
    print ("Moving to 90°")
    motor_position(90)
    return ("nothing")

@app.route('/deg_180')
def deg_180():
    print ("Moving to 180°")
    motor_position(180)
    return ("nothing")

@app.route('/deg_270')
def deg_270():
    print("Moving to 270°")
    motor_position(270)
    return ("nothing")

# not yet implemented
# https://fontawesome.com/v4.7.0/examples/

# @app.route('/automatic')
#def automatic():

# @scheduler.task('interval', id='automatic_pictures', seconds=60, misfire_grace_time=900)

@app.route('/automatic_start')
def run_tasks():
    for i in range(0, 180, 90):
        app.apscheduler.add_job(func=scheduled_task, trigger='date', args=[i], id='j'+str(i))
        time.sleep(10)
        # app.apscheduler.add_job(func=scheduled_task, seconds=30, misfire_grace_time=900, args=[i], id='j'+str(i))
        # time.sleep(10)
        # time.sleep(15)
        # send motor values
        # wait for motor values ??????????
        # time.sleep(18)
        # take picture

 
    return 'Scheduled several long running tasks.', 200
 
def scheduled_task(task_id):
    task_iterations = 2
    for i in range(task_iterations):
        print("start of task")
        # send motor to position in degree
        motor_position(task_id)
        run_every_something_seconds = 20
        time.sleep(run_every_something_seconds)
        print(f'Task {task_id} running iteration {i}')

        # WAIT!!!!!!!!!!
        # take image
        import cv2
        filename = f"Position{task_id}_Cycle{i}.jpg"
        print(filename)
        # frame = take_image(VideoCamera())
        # this used the created global object
        frame = gen_frame(global_video_cam)

        cv2.imwrite(filename, frame)
        print("end of task")


@app.route('/automatic_stop')
def automatic_stop():
    # https://github.com/viniciuschiele/flask-apscheduler
    # scheduler.pause()
    print("Removing all jobs")
    # scheduler.remove_job(j0)
    scheduler.remove_all_jobs()
    # job names:
    # j0
    # j90
    # j180
    # j270
    return ("nothing")
    # this does nothing right now


# @app.route('/settings')
# def automatic():
#     print("settings")
#     return ("nothing")

@app.route('/', methods=['GET', 'POST'])
def move():
    result = ""
    if request.method == 'POST':
        
        return render_template('index.html', res_str=result)
                        
    return render_template('index.html')


def gen(camera):
    while True:
        frame, frame2 = camera.get_frame()
        # this is executed every frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def gen_frame(camera):
    frame, frame2 = camera.get_frame()
    # frame 2 is an image, frame is a jpeg stream in bytes
    # not sure when this is needed??
    return frame2

@app.route('/video_feed')
def video_feed():
    global global_video_cam
    global_video_cam = VideoCamera()
    return Response(gen(global_video_cam),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
    #app.run(host='0.0.0.0', debug=True, threaded=True)
