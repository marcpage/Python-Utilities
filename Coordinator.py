#!/usr/bin/env python

import os
import sys
import re
import cu
import p4
import bs
import fsSQL
import fsDB
import time
import Queue
import traceback
import threading
import socket

class Connection(threading.Thread):
	def __init__(self, socket):
		self.__socket= socket
		threading.Thread.__init__(self)
		self.start()
	def run(self):
		pass

class Incoming(threading.Thread):
	def __init__(self, port, manager):
		self.__socket= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.__socket.bind(('', port))
		self.__manager= manager
		threading.Thread.__init__(self)
		self.start()
	def run(self):
		while True:
			self.__socket.listen(5)
			(connection, address)= self.__socket.accept()
			manager.add(connection, address)

class Manager(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.start()
	def add(self, connection, address):
		pass
	def run(self):
		pass

if __name__ == "__main__":
	pass

""" http://docs.python.org/release/2.5.2/lib/socket-example.html
# Echo server program
import socket
import sys

HOST = ''                 # Symbolic name meaning the local host
PORT = 50007              # Arbitrary non-privileged port
s = None
for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
    af, socktype, proto, canonname, sa = res
    try:
		s = socket.socket(af, socktype, proto)
    except socket.error, msg:
		s = None
		continue
    try:
		s.bind(sa)
		s.listen(1)
    except socket.error, msg:
		s.close()
		s = None
		continue
    break
if s is None:
    print 'could not open socket'
    sys.exit(1)
conn, addr = s.accept()
print 'Connected by', addr
while 1:
    data = conn.recv(1024)
    if not data: break
    conn.send(data)
conn.close()

# Echo client program
import socket
import sys

HOST = 'daring.cwi.nl'    # The remote host
PORT = 50007              # The same port as used by the server
s = None
for res in socket.getaddrinfo(HOST, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM):
    af, socktype, proto, canonname, sa = res
    try:
		s = socket.socket(af, socktype, proto)
    except socket.error, msg:
		s = None
		continue
    try:
		s.connect(sa)
    except socket.error, msg:
		s.close()
		s = None
		continue
    break
if s is None:
    print 'could not open socket'
    sys.exit(1)
s.send('Hello, world')
data = s.recv(1024)
s.close()
print 'Received', repr(data)
"""
