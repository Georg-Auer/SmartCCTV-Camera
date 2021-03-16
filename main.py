# SPOC lab CAM²: hetcam-webcam
# icons from:
# https://fontawesome.com/v4.7.0/examples/
# how to schedule:
# https://stackoverflow.com/questions/21214270/how-to-schedule-a-function-to-run-every-hour-on-flask
# https://apscheduler.readthedocs.io/en/stable/modules/triggers/date.html#module-apscheduler.triggers.date
# alternatively to flask_apscheduler: from apscheduler.schedulers.background import BackgroundScheduler
# how to handle querys:
# https://www.digitalocean.com/community/tutorials/processing-incoming-request-data-in-flask
from flask import Flask, render_template, Response, request
from camera import VideoCamera
import time
import os
from pyserial_connection_arduino import connect_to_arduino, list_available_ports
import numpy as np
from flask_apscheduler import APScheduler
import cv2
from datetime import datetime, timedelta
# https://stackoverflow.com/questions/6871016/adding-days-to-a-date-in-python
class Config(object):
    SCHEDULER_API_ENABLED = True

app = Flask(__name__)
#app = Flask(__name__, template_folder='/var/www/html/templates')

app.config.from_object(Config())

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

def motor_task_creator(task_id):
    print(f"start of motor task creator {task_id}")
    # creating motor task that runs every minute
    scheduler.add_job(func=motor_task, trigger='interval', minutes=60, args=[task_id], id='move'+str(task_id))

def picture_task_creator(task_id):
    print(f"start of picture task creator {task_id}")
    # creating picture task that runs every minute
    scheduler.add_job(func=picture_task, trigger='interval', minutes=60, args=[task_id], id='picture'+str(task_id))

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

@app.route('/get_toggled_status') 
def toggled_status():
    current_status = request.args.get('status')
    # instead of if, create a list, send list and do for items in list
    # this way, only in activated positions are scheduled
    if(scheduler.get_jobs()):
        print(bool(scheduler.get_jobs()))
        print("jobs scheduled")
        # current_status = 'Automatic On'
    else:
        print(bool(scheduler.get_jobs()))
        print("no jobs scheduled")
    #     current_status = 'Automatic On'

    # if Automatic On was sent and no jobs are scheduled
    if(current_status == 'Automatic Off') and not(scheduler.get_jobs()):
        print("Switching On")
        schedule_start = datetime.today()
        print(f"starting scheduling {schedule_start}")
        moving_time = 10
        print(f"moving time is assumed {moving_time} seconds") 
        task_seperation_increase = moving_time*2
        task_seperation = 1
        for i in range(0, 180, 90): # starting angle, stop angle and step angle in degrees
            schedule_time_movement = schedule_start + timedelta(seconds=task_seperation)
            schedule_time_picture = schedule_start + timedelta(seconds=moving_time+task_seperation)
            scheduler.add_job(func=motor_task_creator, trigger='date', run_date=schedule_time_movement, args=[i], id='move_start'+str(i))
            print(f"created moving job {i} running at {schedule_time_movement}")
            scheduler.add_job(func=picture_task_creator, trigger='date', run_date=schedule_time_picture, args=[i], id='picture_start'+str(i))
            print(f"created picture job {i} running at {schedule_time_picture}")
            task_seperation = task_seperation + task_seperation_increase
        print(scheduler.get_jobs())

    else:
        print("Switching Off")
        print(scheduler.get_jobs())
        print("Removing all scheduled jobs")
        # scheduler.remove_job(j0)
        scheduler.remove_all_jobs()
        print(scheduler.get_jobs())

    return 'Automatic On' if current_status == 'Automatic Off' else 'Automatic Off'

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

@app.route('/picture')
def picture(pos_name = "custom"):
    picture_task(pos_name)
    return ("nothing")

@app.route('/settings')
def automatic():
    print("settings")
    return ("nothing")

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
    try:
        object_methods = [method_name for method_name in dir(camera)
                  if callable(getattr(camera, method_name))]
        print(object_methods)
        frame, frame2 = camera.get_frame_resolution()
        print("picture with custom resolution")
    except:
        frame, frame2 = camera.get_frame()
        print("picture with standard resolution, custom did not work")

    # frame 2 is an image, frame is a jpeg stream in bytes
    return frame2

@app.route('/video_feed')
def video_feed():
    global global_video_cam
    global_video_cam = VideoCamera()
    return Response(gen(global_video_cam),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# gallery-------------------------------

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

@app.route("/gallery")
def gallery():
    images = os.listdir('./images')
    return render_template("index_gallery.html", images=images)

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload", methods=["GET","POST"])
def upload_file():
    if request.method=="GET":
        return render_template('upload.html')
    target = os.path.join(APP_ROOT, 'images/')
    print(target)
    if not os.path.isdir(target):
        os.mkdir(target)
    for file in request.files.getlist("file"):
        print(file)
        filename = file.filename
        destination = "/".join([target, filename])
        print(destination)
        file.save(destination)
    return render_template("uploaded.html")

@app.route('/upload/<filename>')
def send_image(filename):
    return send_from_directory("images", filename)

def send_image_for_filter(image):
    return render_template('filter.html', image=image)

@app.route("/filters")
def filter():
    return render_template('filters.html')

@app.url_defaults
def hashed_url_for_static_file(endpoint, values):
    if 'static' == endpoint or endpoint.endswith('.static'):
        filename = values.get('filename')
        if filename:
            if '.' in endpoint:  # has higher priority
                blueprint = endpoint.rsplit('.', 1)[0]
            else:
                blueprint = request.blueprint  # can be None too
            if blueprint:
                static_folder = app.blueprints[blueprint].static_folder
            else:
                static_folder = app.static_folder
            param_name = 'h'
            while param_name in values:
                param_name = '_' + param_name
            values[param_name] = static_file_hash(os.path.join(static_folder, filename))

def static_file_hash(filename):
    return int(os.stat(filename).st_mtime)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
    #app.run(host='0.0.0.0', debug=True, threaded=True)
    # app.run(port=5000)
