#!/usr/bin/env python


'''
    pygnad - shows bandwith utilisation in a SysTray Icon, eg. in lxpanel
    Copyright (C) 2011 Florian Streibelt

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''

import gtk, gobject, os, sys, pyinotify 
from pyinotify import WatchManager, Notifier, ProcessEvent, EventsCodes
from collections import deque
import time
import random
import getopt

class StatusIcc():
	w=18
	h=18

	pixbuf=None;

	# activate callback
	def activate( self, widget, data=None):
		global pygnad
		dialog = gtk.MessageDialog(
		parent         = None,
		flags          = gtk.DIALOG_DESTROY_WITH_PARENT,
		type           = gtk.MESSAGE_INFO,
		buttons        = gtk.BUTTONS_OK,
		message_format = pygnad)
		dialog.set_title('Status of PyGNAD')
		dialog.connect('response', self.show_hide)
		dialog.show()
   
	# Show_Hide callback
	def  show_hide(self, widget,response_id, data= None):
		if response_id == gtk.RESPONSE_YES:
			widget.hide()
		else:
			widget.hide()
           

	# destroyer callback
	def  destroyer(self, widget,response_id, data= None):
		if response_id == gtk.RESPONSE_OK:
			gtk.main_quit()
			#sys.exit(1)
		else:
			widget.hide()

	# popup callback
	def popup(self, button, widget, data=None):
		global pygnad
		dialog = gtk.MessageDialog(
		parent         = None,
		flags          = gtk.DIALOG_DESTROY_WITH_PARENT,
		type           = gtk.MESSAGE_INFO,
		buttons        = gtk.BUTTONS_OK_CANCEL,
		message_format = "Close the PyGNAD tray icon?")
		dialog.set_title('Status of PyGNAD')
		dialog.connect('response', self.destroyer)
		dialog.show()
     
	def appendValue(self,value=0):
		print("got new value to add: %s \n" %value)
		self.myqueue.popleft()
		self.myqueue.append(value)
		self.draw_graph()


	def draw_graph(self):
		w=self.w
		h=self.h
		pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, w, h)
		#w,h = pixbuf.get_width(), pixbuf.get_height()
		drawable = gtk.gdk.Pixmap( None, w, h, 24)
		gc = drawable.new_gc()
		drawable.draw_pixbuf(gc, pixbuf, 0,0,0,0,-1,-1)

		#---ACTUAL DRAWING CODE---
		pixmap,mask = pixbuf.render_pixmap_and_mask() # Function call
		cm = pixmap.get_colormap()
		red = cm.alloc_color(self.fgcolor)
		green = cm.alloc_color(self.bgcolor)
		black = cm.alloc_color('black')

		gc.set_foreground(black)
		drawable.draw_rectangle(gc, True, 0, 0, w, h)

		maxvalue=0
		for i in range(w):
			v=self.myqueue[i]
			if (v>maxvalue):
				maxvalue=v
		print("max value in queue: %i \n" %maxvalue)

		#drawable.draw_line(gc, 0, 0, w,h)
		for i in range(w):
			if (maxvalue>0):
				value =h-int( (self.myqueue[i] / float(maxvalue) )*h)
			else:
				value = h
			#print(" %i " % value)
			gc.set_foreground(red)
			drawable.draw_line(gc,i,h,i,value)
			#gc.set_foreground(green)
			#drawable.draw_line(gc,i,0,i,value)
		print("\n")

		#-------------------------

		pb=pixbuf.get_from_drawable(drawable,cm,0,0,0,0,w,h)

		self.staticon.set_from_pixbuf(pb)

	def timer_update(self):
		print("tick\n")
		#/sys/class/net/wlan0/statistics/tx_bytes
		#value_t1 = int(open("/sys/class/net/wlan0/statistics/tx_bytes","r").read())
		#value_r1 = int(open("/sys/class/net/wlan0/statistics/rx_bytes","r").read())

		#value_t2 = int(open("/sys/class/net/eth0/statistics/tx_bytes","r").read())
		#value_r2 = int(open("/sys/class/net/eth0/statistics/rx_bytes","r").read())

		#value=value_t1 + value_r1  + value_t2 + value_r2
		try:
			value_t = int(open("/sys/class/net/%s/statistics/tx_bytes" % self.nic ,"r").read())
			value_r = int(open("/sys/class/net/%s/statistics/rx_bytes" % self.nic ,"r").read())
			value=value_r + value_t
		except IOError:
			value=0

		if (self.lastvalue==None):
			self.lastvalue=value

		delta=value - self.lastvalue
		print("delta = %i on nic %s \n" % (delta,self.nic))

		self.appendValue(delta);

		self.lastvalue=value
		return True


	def __init__(self,nic,fg,bg,ival):
		
		gtk.gdk.threads_init()

		self.myqueue=deque()
		self.lastvalue=None
		self.fgcolor=fg
		self.bgcolor=bg
		self.nic=nic

		for i in range(self.w):
			self.myqueue.append(20)

		print("icon init started\n")
		# create a new Status Icon
		self.staticon = gtk.StatusIcon()

		#self.draw_graph()
	
		gobject.timeout_add_seconds(ival, self.timer_update)

		self.staticon.connect("activate", self.activate)
		self.staticon.connect("popup_menu", self.popup)
		self.staticon.set_visible(True)
		print("icon init finished\n")


		# register a  timer
		#gobject.timeout_add_seconds(10, self.timer_callback)
		#self.timer_callback()

def usage(name):
	print("usage: %s -n nic -f fgcolor -b bgcolor [-h] \n" % name)


def main(argv=None):
	if argv is None:
		argv = sys.argv


	nic = "eth0"
	fgcolor = "red"
	bgcolor = "black"
	ival = 5

	try:                                
		opts, args = getopt.getopt(argv[1:], "hn:f:b:i:", ["help","nic=", "fgcolor=","bgcolor=","interval="])
	except getopt.GetoptError:
		usage(argv[0])
		sys.exit(2)


	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage(argv[0])
			sys.exit()                  
		elif opt in ("-n", "--nic"):
			nic = arg
		elif opt in ("-f", "--fgcolor"):
			fgcolor = arg
		elif opt in ("-b", "--bgcolor"):
			bgcolor = arg
		elif opt in ("-i", "--interval"):
			ival = int(arg)

	statusicon = StatusIcc(nic,fgcolor,bgcolor,ival)

	try:
		gtk.main()
	except KeyboardInterrupt:
		pass



if __name__ == "__main__":
    sys.exit(main())
