'''
**********************************************************************
* Filename    : views
* Description : views for server
* Author      : Cavon
* Brand       : SunFounder
* E-mail      : service@sunfounder.com
* Website     : www.sunfounder.com
* Update      : Cavon    2016-09-13    New release
**********************************************************************
'''

import os
import subprocess
from inspect import signature
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError
from django.shortcuts import render

is_setup = False
fw = None
bw = None
cam = None
SPEED = int(os.environ.get("PICAR_DEFAULT_SPEED", "60"))
bw_status = 0


def get_config_path():
	config_path = os.environ.get("PICAR_CONFIG_PATH")
	if config_path:
		return config_path
	return str(Path(settings.BASE_DIR) / "remote_control" / "driver" / "config")


def get_i2c_bus_number():
	return int(os.environ.get("PICAR_I2C_BUS", "1"))


def get_stream_port():
	return int(os.environ.get("PICAR_STREAM_PORT", "8765"))


def make_driver(driver_class, *, debug, bus_number, db):
	driver_signature = signature(driver_class)
	kwargs = {"debug": debug, "db": db}
	if "bus_number" in driver_signature.parameters:
		kwargs["bus_number"] = bus_number
	return driver_class(**kwargs)

def setup():
	global fw, bw, cam, SPEED, bw_status, is_setup
	if is_setup == True:
		return
	import picar
	from picar import back_wheels, front_wheels
	from .driver import camera
	from .picar_v_video_stream import Vilib

	bus_number = get_i2c_bus_number()
	picar.setup()
	db_file = get_config_path()
	fw = make_driver(front_wheels.Front_Wheels, debug=False, bus_number=bus_number, db=db_file)
	bw = make_driver(back_wheels.Back_Wheels, debug=False, bus_number=bus_number, db=db_file)
	cam = make_driver(camera.Camera, debug=False, bus_number=bus_number, db=db_file)
	cam.ready()
	bw.ready()
	fw.ready()
	
	Vilib.camera_start()

	SPEED = 60
	bw_status = 0
	is_setup = True

#test.start()
#print(stream.start())
def run_command(cmd):
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = p.stdout.read().decode('utf-8')
    status = p.poll()
    return status, result


def get_ip():
    _, result = run_command(["hostname", "-I"])
    ip = result.split(" ")
    return ip[0]


def home(request):
	return render(request, "base.html")


def ensure_setup():
	if is_setup:
		return None
	try:
		setup()
	except Exception as exc:
		return HttpResponseServerError("PiCar setup failed: {0}".format(exc))
	return None

def run(request):
	global SPEED, bw_status
	debug = ''
	if 'action' in request.GET:
		action = request.GET['action']
		if action == 'setup':
			error_response = ensure_setup()
			if error_response:
				return error_response
		# ============== Back wheels =============
		elif action == 'bwready':
			error_response = ensure_setup()
			if error_response:
				return error_response
			bw.ready()
			bw_status = 0
		elif action == 'forward':
			error_response = ensure_setup()
			if error_response:
				return error_response
			bw.speed = SPEED
			bw.forward()
			bw_status = 1
			debug = "speed =", SPEED
		elif action == 'backward':
			error_response = ensure_setup()
			if error_response:
				return error_response
			bw.speed = SPEED
			bw.backward()
			bw_status = -1
		elif action == 'stop':
			error_response = ensure_setup()
			if error_response:
				return error_response
			bw.stop()
			bw_status = 0

		# ============== Front wheels =============
		elif action == 'fwready':
			error_response = ensure_setup()
			if error_response:
				return error_response
			fw.ready()
		elif action == 'fwleft':
			error_response = ensure_setup()
			if error_response:
				return error_response
			fw.turn_left()
		elif action == 'fwright':
			error_response = ensure_setup()
			if error_response:
				return error_response
			fw.turn_right()
		elif action == 'fwstraight':
			error_response = ensure_setup()
			if error_response:
				return error_response
			fw.turn_straight()
		elif 'fwturn' in action:
			error_response = ensure_setup()
			if error_response:
				return error_response
			print("turn %s" % action)
			fw.turn(int(action.split(':')[1]))

		# ================ Camera =================
		elif action == 'camready':
			error_response = ensure_setup()
			if error_response:
				return error_response
			cam.ready()
		elif action == "camleft":
			error_response = ensure_setup()
			if error_response:
				return error_response
			cam.turn_left(40)
		elif action == 'camright':
			error_response = ensure_setup()
			if error_response:
				return error_response
			cam.turn_right(40)
		elif action == 'camup':
			error_response = ensure_setup()
			if error_response:
				return error_response
			cam.turn_up(20)
		elif action == 'camdown':
			error_response = ensure_setup()
			if error_response:
				return error_response
			cam.turn_down(20)
		else:
			return HttpResponseBadRequest("Unknown action: {0}".format(action))
	if 'speed' in request.GET:
		error_response = ensure_setup()
		if error_response:
			return error_response
		speed = int(request.GET['speed'])
		if speed < 0:
			speed = 0
		if speed > 100:
			speed = 100
		SPEED = speed
		if bw_status != 0:
			bw.speed = SPEED
		debug = "speed =", speed
	#host = stream.get_host().decode('utf-8').split(' ')[0]
	host = get_ip()
	return render(request, "run.html", {'host': host, 'stream_port': get_stream_port()})

def cali(request):
	error_response = ensure_setup()
	if error_response:
		return error_response
	if 'action' in request.GET:
		action = request.GET['action']
		# ========== Camera calibration =========
		if action == 'camcali':
			print('"%s" command received' % action)
			cam.calibration()
		elif action == 'camcaliup':
			print('"%s" command received' % action)
			cam.cali_up()
		elif action == 'camcalidown':
			print('"%s" command received' % action)
			cam.cali_down()
		elif action == 'camcalileft':
			print('"%s" command received' % action)
			cam.cali_left()
		elif action == 'camcaliright':
			print('"%s" command received' % action)
			cam.cali_right()
		elif action == 'camcaliok':
			print('"%s" command received' % action)
			cam.cali_ok()

		# ========= Front wheel cali ===========
		elif action == 'fwcali':
			print('"%s" command received' % action)
			fw.calibration()
		elif action == 'fwcalileft':
			print('"%s" command received' % action)
			fw.cali_left()
		elif action == 'fwcaliright':
			print('"%s" command received' % action)
			fw.cali_right()
		elif action == 'fwcaliok':
			print('"%s" command received' % action)
			fw.cali_ok()

		# ========= Back wheel cali ===========
		elif action == 'bwcali':
			print('"%s" command received' % action)
			bw.calibration()
		elif action == 'bwcalileft':
			print('"%s" command received' % action)
			bw.cali_left()
		elif action == 'bwcaliright':
			print('"%s" command received' % action)
			bw.cali_right()
		elif action == 'bwcaliok':
			print('"%s" command received' % action)
			bw.cali_ok()
		else:
			print('command error, error command "%s" received' % action)
	return render(request, "cali.html")

def connection_test(request):
	return HttpResponse('OK')
