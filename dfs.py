#!/usr/bin/env python -B

import sys
import re
import os.path
import os
import socket
import string
import threading
import Queue
import tempfile
import random
import shutil
import time
import CompactNumbers
import BaseHTTPServer
import fsTemplate
import rsa
import cPickle
import binaryXML
import array

class MetaData:
	def __init__(self, binary= None):
		if binary:
			self.__data= binaryXML.deserialize(binary)
		else:
			self.__data= []
		pass
	def serialize(self):
		return binaryXML.serialize(self.__data)
	def set(self, name, value, properties= None):
		if not properties:
			properties= []
		if value.__class__ is list:
			self.__data.append( (name, properties, value) )
		else:
			self.__data.append( (name, properties, [value]) )
	def get(self, itemName, trustList):
		pass # returns a list of tuples of trust score and data, in chronological order (latest first)
	def sign(self, publicKey, privateKey):
		flat= binaryXML.serialize(self.__data, format= 1)
		flatArray= array.array('B')
		flatArray.extend(flat)
		data= flatArray.toString()
		hash= md5.new(data).hexdigest()
		signed= rsa.sign(data, privateKey)
		key= "%s08x:%08x"%(publicKey['e'], publicKey['n'])
		self.__data= [("signed",[("key",key),("md5",hash),("signature",signed)],self.__data)]

class UIHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header('Content-type', 'text/html')
		self.end_headers()
		self.wfile.write("<html><head><title>Test GET</title><body><h1>Test GET</h1>")
		for member in self.__dict__.keys():
			self.wfile.write("<b>%s</b> = \"%s\"<br>\n"%(member, str(self.__dict__[member])))
		self.wfile.write("</body></html>")
	def do_POST(self):
		self.send_response(200)
		self.send_header('Content-type', 'text/html')
		self.end_headers()
		self.wfile.write("<html><head><title>Test POST</title><body><h1>Test POST</h1></body></html>")
	def log_message(self, format, *data):
		#print format%data
		pass

class InputStreamToQueue(threading.Thread):
	def __init__(self, inputStream, lineQueue, name):
		self.__in= inputStream
		self.__queue= lineQueue
		self.__name= name
		threading.Thread.__init__(self)
		self.start()
	def run(self):
		while True:
			try:
				line= self.__in.readline()
			except Exception, exception:
				self.__queue.put( ("exception", str(exception)) )
				break
			if len(line) == 0:
				break
			self.__queue.put( (self.__name, line) )
		self.__queue.put(None)

usage= "dfs.py -upload <path/to/directory> [-cache <path/to/directory>] [-port <number>] [-seed <server:port>]"
if __name__ == "__main__":
	parameters= {
		"-upload": "upload",
		"-cache": "cache",
		"-port": 8088,
		"-seed": None
	}
	next= None
	for arg in sys.argv[1:]:
		if next:
			parameters[next]= arg
			next= None
		elif parameters.has_key(arg):
			next= arg
		else:
			print usage
			print "Unknown argument: "+arg
			sys.exit(1)
	try:
		server = BaseHTTPServer.HTTPServer(('', int(parameters["-port"])), UIHandler)
		server.serve_forever()
	except KeyboardInterrupt:
		server.socket.close()


"""
	When a new file shows up:
		1. Calculate the md5 of the entire file and of the chunks
		2. Start blowing chunks
	Occassionally check file md5. If changes, treat it as a new file.
	When asked for a chunk of an uploaded file, check the md5 hash of the section to upload.
"""

"""
decrypt(cypher, key)
Decrypts a cypher with the private key 'key'
encrypt(message, key)
Encrypts a string 'message' with the public key 'key'
gen_pubpriv_keys(nbits)
Generates public and private keys, and returns them as (pub, priv). 

The public key consists of a dict {e: ..., , n: ....). The private key consists of a dict {d: ...., p: ...., q: ....).
sign(message, key)
Signs a string 'message' with the private key 'key'
verify(cypher, key)
Verifies a cypher with the public key 'key'
"""

"""
requestline = "GET /id/5435346564 HTTP/1.1"
wfile = ""
request = ""
raw_requestline = "GET /id/5435346564 HTTP/1.1 "
server = ""
headers = "User-Agent: Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-us) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16 Accept: application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5 Accept-Language: en-us Accept-Encoding: gzip, deflate Connection: keep-alive Host: localhost:8088 "
connection = ""
command = "GET"
rfile = ""
path = "/id/5435346564"
request_version = "HTTP/1.1"
client_address = "('127.0.0.1', 56675)"
close_connection = "1"
"""

"""
	/id/[md5hash]
	/meta/[md5hash]
	/files/path/to/resource
"""

"""d41d8cd98f00b204e9800998ecf8427e
	<signed key=d41d8cd98f00b204e9800998ecf8427e md5=d41d8cd98f00b204e9800998ecf8427e value=d41d8cd98f00b204e9800998ecf8427e>
		<name>Test.txt</name>
		<size>54677688</size>
		<path>documentation</path>
		<mime>text/plain</mime>
		<description>Test file to see if this mechanism works</description>
		<chunks size=4096>
			<chunk>d41d8cd98f00b204e9800998ecf8427e</chunk>
			<chunk>d41d8cd98f00b204e9800998ecf8427e</chunk>
			<chunk>d41d8cd98f00b204e9800998ecf8427e</chunk>
			<chunk>d41d8cd98f00b204e9800998ecf8427e</chunk>
			<chunk>d41d8cd98f00b204e9800998ecf8427e</chunk>
			<chunk>d41d8cd98f00b204e9800998ecf8427e</chunk>
		</chunks>
	</signed>
"""

"""
	test= [
		("signed",[("key","5k3e6y"),("md5","6m4d5"),("value","8v9a0l3u5e")], [
			("name",[],["test.txt"]),
			("signed",[("key","5k3e6y"),("md5","6m4d5"),("value","8v9a0l3u5e")],[
				("name",[],["Test.txt"]),
				("size",[],["543656547657"]),
				("path",[],["documentation"]),
				("mime",[],["text/plain"]),
				("description",[],["Original test document"]),
				("chunks",[("size","4096")],[
					("chunk",[],["54344563465"]),
					("chunk",[],["54344563465"]),
					("chunk",[],["54344563465"]),
					("chunk",[],["54344563465"]),
					("chunk",[],["54344563465"])
				])
			])
		])
	]
"""

