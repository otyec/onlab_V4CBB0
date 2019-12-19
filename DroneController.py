import socket, time, threading, re, math
from pynput.keyboard import Key, Listener
from tkinter import *
from random import *

def draw_line(x1,y1,x2,y2):
	my_canvas.create_line(x1,y1,x2,y2,width=2)

def delete_lines():
	my_canvas.delete('all')

my_window=Tk()
my_canvas=Canvas(my_window, width=300, height=300)

#communication with the motion controller
leap_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
leap_socket.connect(("127.0.0.1", 3223))

host = ''
port = 9000
locaddr = (host,port)
tello_address = ('192.168.10.1', 8889)
tello_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tello_sock.bind(locaddr)
tello_sock.sendto("command".encode('utf-8'), tello_address)
"""
def recv():
    while True: 
        try:
            data, server = sock.recvfrom(1518)
            print(data.decode(encoding="utf-8"))
        except Exception:
            print ('\nExit . . .\n')
            break
recvThread = threading.Thread(target=recv)
recvThread.start()
"""
key_w = False # rc l-r, forward, 0, rotate  
key_c = False # rc with up-down
key_k = False # kalibrálás
l_r_Min = l_r_Max = l_r_Origo = 0
f_b_Min = f_b_Max = f_b_Origo = 0
twist_Min = twist_Max = twist_Origo = 0
twist_Scale = l_r_Scale = f_b_Scale = 1
vertical_y0 = 300
current_palm_y = 0
l_r = f_b = twist = 0

def on_press(key):
    # print('{0} pressed'.format(key))
    global key_w
    global key_c
    global key_k
    global l_r_Min
    global l_r_Max
    global f_b_Min
    global f_b_Max
    global twist_Min
    global twist_Max
    global l_r_Origo
    global f_b_Origo
    global twist_Origo
    global vertical_y0
    if hasattr(key,'char'):
        if key.char == 'k' and not key_k:
            key_k=True
            l_r_Min = l_r_Max = 0
            f_b_Min = f_b_Max = 0
            twist_Min = twist_Max = 0
        # move
        if key.char == 'w' and not key_w:
            key_w=True
            l_r_Origo = l_r
            f_b_Origo = f_b
            twist_Origo = twist
        if key.char == 'c' and not key_c:
            key_c=True
            vertical_y0 = current_palm_y
        # takeoff
        if key.char == 't':
            print("takeoff")
            tello_sock.sendto("takeoff".encode('utf-8'), tello_address)
        # land
        if key.char == 'l':
            print("land")
            tello_sock.sendto("land".encode('utf-8'), tello_address)

    if key == Key.space:
       print("stop")
       tello_sock.sendto("stop".encode('utf-8'), tello_address)
        

def on_release(key):
    global key_w
    global key_c
    global key_k
    global l_r_Scale
    global f_b_Scale
    global twist_Scale
    global l_r_Min
    global l_r_Max
    global f_b_Min
    global f_b_Max
    global twist_Min
    global twist_Max
    if hasattr(key,'char'):
        if key.char == 'k':
            key_c = False
            l_r_Scale = (200/(abs(l_r_Min)+abs(l_r_Max)))
            f_b_Scale = (200/(abs(f_b_Min)+abs(f_b_Max)))
            twist_Scale = (200/(abs(twist_Min)+abs(twist_Max)))
            print(l_r_Scale)
        if key.char == "w":
            key_w=False
            tello_sock.sendto("rc 0 0 0 0".encode('utf-8'), tello_address)
        if key.char == "c":
            key_c=False
    if key == Key.esc:
        # Stop listener
        return False

#Collect events until released
listener = Listener(
        on_press=on_press,
        on_release=on_release)
listener.start()

while True:
	try:	
		msg=leap_socket.recv(128)
		param_list = re.split('\s+', msg.decode("utf-8"))
		if param_list[0] == "1":# 1: palm normal vec degrees
			if key_k == True:
				l_r_deg = int(param_list[1])
				f_b_deg = int(param_list[2])
				twist_deg = int(param_list[4])
				if l_r_deg < l_r_Min:
					l_r_Min = l_r_deg
				elif l_r_deg > l_r_Max:
					l_r_Max = l_r_deg
				if f_b_deg < f_b_Min:
					f_b_Min = f_b_deg
				elif f_b_deg > f_b_Max:
					f_b_Max = f_b_deg
				if twist_deg < twist_Min:
					twist_Min = twist_deg
				elif twist_deg > twist_Max:
					twist_Max = twist_deg
			l_r = int(int(param_list[1])*l_r_Scale/2)
			f_b = int(int(param_list[2])*f_b_Scale/2)
			twist = int(int(param_list[4])*twist_Scale/2)
			if key_w == True:
				
				current_palm_y = int(param_list[3])
				vertical_speed = 0
				if key_c:
					vertical_speed = int((current_palm_y - vertical_y0)/2)
				msg = "rc "+str(l_r-l_r_Origo)+' '+str(f_b-f_b_Origo)+' '+str(vertical_speed)+' '+str(twist-twist_Origo)
				delete_lines()
				draw_line(150, 150, 150+math.cos(int(param_list[4])*0.01745)*100,150+math.sin(int(param_list[4])*0.01745)*30)
				draw_line(150, 150, 150+math.sin(int(param_list[1])*0.01745)*100,150-math.cos(int(param_list[1])*0.01745)*100+abs(f_b))
				draw_line(147,50,153,50)
				draw_line(255,147,255,153)
				my_canvas.pack()
				my_window.update()
				print(msg)
				tello_sock.sendto(msg.encode('utf-8'), tello_address)
			
	except KeyboardInterrupt:
		tello_sock.sendto("stop".encode('utf-8'), tello_address)
		tello_sock.sendto("land".encode('utf-8'), tello_address)
		tello_sock.close()
		leap_socket.close()
		listener.stop
		break

