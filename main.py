
from flask import Flask, render_template, Response, request
from camera import VideoCamera
import time
import os
from pyserial_connection_arduino import connect_to_arduino, list_available_ports
import numpy as np
# icons from:
# https://fontawesome.com/v4.7.0/examples/
# how to schedule
# https://stackoverflow.com/questions/21214270/how-to-schedule-a-function-to-run-every-hour-on-flask
# from apscheduler.schedulers.background import BackgroundScheduler
# how to handle querys:
# https://www.digitalocean.com/community/tutorials/processing-incoming-request-data-in-flask
from flask_apscheduler import APScheduler
import cv2
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

comport = '/dev/ttyACM0' # this should be set to the standard address of the microcontroller
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
        return

@app.route('/move_deg')
def move_deg():
    degree = 0
    degree = int(request.args.get('degree'))
    if(degree >= 280):
        degree = 270
    print(f"Moving to {degree}°")
    motor_position(degree)
    return '''<h1>Moving to: {}</h1>'''.format(degree)
    # return ("nothing")

from datetime import datetime, timedelta
# https://stackoverflow.com/questions/6871016/adding-days-to-a-date-in-python

@app.route('/automatic_start')
def run_tasks():
    schedule_start = datetime.today()
    print(f"starting scheduling {schedule_start}")
    moving_time = 5
    task_seperation_increase = moving_time*2
    task_seperation = 1
    for i in range(0, 360, 90):
        schedule_time_movement = schedule_start + timedelta(seconds=task_seperation)
        schedule_time_picture = schedule_start + timedelta(seconds=moving_time+task_seperation)
        scheduler.add_job(func=motor_task_creator, trigger='date', run_date=schedule_time_movement, args=[i], id='move_start'+str(i))
        print(f"created moving job {i} running at {schedule_time_movement}")
        scheduler.add_job(func=picture_task_creator, trigger='date', run_date=schedule_time_picture, args=[i], id='picture_start'+str(i))
        print(f"created picture job {i} running at {schedule_time_picture}")
        task_seperation = task_seperation + task_seperation_increase
    print(scheduler.get_jobs())
    return 'Scheduled several long running tasks.', 200

def motor_task_creator(task_id):
    print(f"start of motor task creator {task_id}")
    # creating motor task that runs every minute
    scheduler.add_job(func=motor_task, trigger='interval', minutes=1, args=[task_id], id='move'+str(task_id))

def picture_task_creator(task_id):
    print(f"start of picture task creator {task_id}")
    # creating picture task that runs every minute
    scheduler.add_job(func=picture_task, trigger='interval', minutes=1, args=[task_id], id='picture'+str(task_id))

def motor_task(task_id):
    # send to motor position
    print(f"moving to position {task_id}")
    motor_position(task_id)
#-------------------------------------------------------------------------------------

def picture_task(task_position):
    print(f"start of picture task {task_position}")
    filename = f'position{task_position}_{datetime.now().strftime("%Y%m%d-%H%M%S")}.jpg'
    print(filename)
    frame = gen_frame(global_video_cam)
    # writing image
    cv2.imwrite(filename, frame)

@app.route('/automatic_stop')
def automatic_stop():
    # https://github.com/viniciuschiele/flask-apscheduler
    # scheduler.pause()
    print(scheduler.get_jobs())
    print("Removing all jobs")
    # scheduler.remove_job(j0)
    scheduler.remove_all_jobs()
    print(scheduler.get_jobs())
    return ("nothing")

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
