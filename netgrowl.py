#!/usr/bin/env python

"""Growl 0.6 Network Protocol Client for Python"""
__version__ = "0.6.3"
__author__ = "Rui Carmo (http://the.taoofmac.com)"
__copyright__ = "(C) 2004 Rui Carmo. Code under BSD License."
__contributors__ = "Ingmar J Stein (Growl Team), John Morrissey (hashlib patch)"

try:
	import hashlib
	md5_constructor = hashlib.md5
except ImportError:
	import md5
	md5_constructor = md5.new

import struct
import socket
import cu
import time

GROWL_UDP_PORT=9887
GROWL_PROTOCOL_VERSION=1
GROWL_TYPE_REGISTRATION=0
GROWL_TYPE_NOTIFICATION=1

class GrowlRegistrationPacket:
	"""Builds a Growl Network Registration packet.
		 Defaults to emulating the command-line growlnotify utility."""

	def __init__(self, application="growlnotify", password = None ):
		self.notifications = []
		self.defaults = [] # array of indexes into notifications
		self.application = application.encode("utf-8")
		self.password = password
	# end def


	def addNotification(self, notification="Command-Line Growl Notification", enabled=True):
		"""Adds a notification type and sets whether it is enabled on the GUI"""
		self.notifications.append(notification)
		if enabled:
			self.defaults.append(len(self.notifications)-1)
	# end def


	def payload(self):
		"""Returns the packet payload."""
		self.data = struct.pack( "!BBH",
								 GROWL_PROTOCOL_VERSION,
								 GROWL_TYPE_REGISTRATION,
								 len(self.application)
					)
		self.data += struct.pack( "BB",
									len(self.notifications),
									len(self.defaults)
					)
		self.data += self.application
		for notification in self.notifications:
			encoded = notification.encode("utf-8")
			self.data += struct.pack("!H", len(encoded))
			self.data += encoded
		for default in self.defaults:
			self.data += struct.pack("B", default)
		self.checksum = md5_constructor()
		self.checksum.update(self.data)
		if self.password:
			 self.checksum.update(self.password)
		self.data += self.checksum.digest()
		return self.data
	# end def
# end class


class GrowlNotificationPacket:
	"""Builds a Growl Network Notification packet.
		 Defaults to emulating the command-line growlnotify utility."""

	def __init__(self, application="growlnotify",
				 notification="Command-Line Growl Notification", title="Title",
				 description="Description", priority = 0, sticky = False, password = None ):
		self.application	= application.encode("utf-8")
		self.notification = notification.encode("utf-8")
		self.title				= title.encode("utf-8")
		self.description	= description.encode("utf-8")
		flags = (priority & 0x07) * 2
		if priority < 0:
			flags |= 0x08
		if sticky:
			flags = flags | 0x0100
		self.data = struct.pack( "!BBHHHHH",
								 GROWL_PROTOCOL_VERSION,
								 GROWL_TYPE_NOTIFICATION,
								 flags,
								 len(self.notification),
								 len(self.title),
								 len(self.description),
								 len(self.application)
					)
		self.data += self.notification
		self.data += self.title
		self.data += self.description
		self.data += self.application
		self.checksum = md5_constructor()
		self.checksum.update(self.data)
		if password:
			 self.checksum.update(password)
		self.data += self.checksum.digest()
	# end def

	def payload(self):
		"""Returns the packet payload."""
		return self.data
	# end def
# end class


if __name__ == '__main__':
	args= {
		'-application': "pyGrowl",
		'-password': None,
		'-machine': "localhost",
		'-port': str(GROWL_UDP_PORT),
		'-types': [], # type1, -disabledType1, type2, -disabledType2
		'-noreg': 0,
		'-debug': 0,
		'': [], # +high:type1:Sticky:This is a sticky notification, low:type2:Not Sticky:This is not sticky
	}
	cu.parseArgs(args)
	if len(args['-types']) == 0:
		args['-types']= ['Notification']
	
	address= (args['-machine'], int(args['-port']))
	connection= socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	
	if args['-noreg'] == 0:
		# Sending registration
		registration= GrowlRegistrationPacket(application= args['-application'], password= args['-password'])
		for type in args['-types']:
			enabled= not type.startswith('-')
			if not enabled:
				type= type[1:]
			registration.addNotification(notification= type, enabled= enabled)
		payload= registration.payload()
		if args['-debug']:
			hex= "0123456789abcdef"
			for b in payload:
				n= ord(b)
				print hex[n >> 4]+hex[n&0x0f]
		connection.sendto(payload, address)
	
	for message in args['']:
		# [+]priority:type:title:message
		priorities= ['low', 'moderate', 'normal', 'high', 'emergency']
		sticky= message.startswith('+')
		if sticky:
			message= message[1:]
		parts= message.split(':',4)
		priority= priorities.index(parts[0]) - 2
		notification= GrowlNotificationPacket(
						application= args['-application'],
						notification= parts[1],
						title= parts[2],
						description= parts[3],
						priority= priority,
						sticky= sticky,
						password= args['-password']
					)
		payload= notification.payload()
		if args['-debug']:
			print
			hex= "0123456789abcdef"
			for b in payload:
				n= ord(b)
				print hex[n >> 4]+hex[n&0x0f]
		connection.sendto(payload, address)
		time.sleep(0.2)
	connection.close()
