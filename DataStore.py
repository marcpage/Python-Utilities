#!/usr/bin/env python -B

import sys
import hashlib
import BaseHTTPServer
import cgi
import cgitb; cgitb.enable(display=0, logdir="/tmp")
import os
import os.path
import SocketServer
import re

StreamBufferSize= 4096
StoragePath= "/tmp"
IdUrlPrefix= "/md5"

def temporaryFile(prefix= None, extension=None, directory= None):
	if not directory:
		directory= tempfile.gettempdir()
	if not prefix:
		prefix= "tempfile"
	if not extension:
		extension= ".temp"
	file_name= os.path.join(directory, prefix+extension)
	while 1:
		try:
			fd = os.open(file_name, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
			return (os.fdopen(fd, "w"), file_name)
		except OSError:
			pass
		file_name= os.path.join(directory, prefix+'_'+str(random.randint(0,1000000000))+extension)

def streamFile(source, directory):
	(filestream, filename)= temporaryFile(directory= directory)
	hashmd5= hashlib.md5()
	hashsha1= hashlib.sha1()
	while True:
		chunk= source.read(StreamBufferSize)
		filestream.write(chunk)
		hashmd5.update(chunk)
		hashsha1.update(chunk)
		if len(chunk) != StreamBufferSize:
			break
	filestream.close()
	hashmd5= hashmd5.hexdigest()
	hashsha1= hashsha1.hexdigest()
	newName= os.path.join(os.path.dirname(filename), hashmd5+".cache")
	if os.path.exists(newName):
		os.remove(filename)
	else:
		os.rename(filename, newName)
	return (newName, hashmd5, hashsha1)

def streamData(source, destination):
	while True:
		chunk= source.read(StreamBufferSize)
		destination.write(chunk)
		if len(chunk) != StreamBufferSize:
			break

#Accept: application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5
def acceptsMIMETypeExactly(acceptHeader, type):
	fields= (field.rstrip().lstrip() for field in acceptHeader.split(","))
	for field in fields:
		parts= (part.rstrip().lstrip() for part in field.split(";"))
		if parts[0] == type:
			return True
	return None
	
class UIHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_GET(self):
		downloadContentType= "application/octet-stream"
		if self.path == IdUrlPrefix or self.path == IdUrlPrefix+"/":
			self.send_response(200)
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			listing= (filename for filename in os.listdir(StoragePath) if os.path.splitext(filename)[1] == ".cache")
			self.wfile.write("<html><head><title>Cache Contents</title><body><h1>Cache Contents</h1>")
			self.wfile.write("<ul>")
			for item in listing:
				self.wfile.write("<li><a href=\"%(url)s/%(md5)s\">%(md5)s</a>"%{"md5": os.path.splitext(item)[0], "url": IdUrlPrefix})
			self.wfile.write("</ul>")
			self.wfile.write("</body></html>")
		elif self.path.startswith(IdUrlPrefix+"/"):
			pathParts= self.path.split("/")
			item= os.path.join(StoragePath, pathParts[2]+".cache")
			if os.path.isfile(item):
				self.send_response(200)
				self.send_header('Content-type', downloadContentType)
				self.end_headers()
				sourceFile= open(item, "rb")
				streamData(sourceFile, self.wfile)
				sourceFile.close()
			else: # really we want to search and provide an answer here?
				self.send_response(404)
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				self.wfile.write("<html><head><title>Not Found</title><body><h1>Not Found</h1>")
				self.wfile.write("%s is not in the cache"%(pathParts[2]))
				self.wfile.write("</body></html>")
		else:
			self.send_response(200)
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			self.wfile.write("<html><head><title>Test GET</title><body><h1>Test GET</h1>")
			for member in self.__dict__.keys():
				self.wfile.write("<b>%s</b> = \"%s\"<br>\n"%(member, str(self.__dict__[member])))
			self.wfile.write("<form action=. method=POST enctype=multipart/form-data>")
			self.wfile.write("<input type=HIDDEN name=test value=30>")
			self.wfile.write("<input type=FILE name=file1 size=40>")
			self.wfile.write("<input type=FILE name=file2 size=40>")
			self.wfile.write("<input type=FILE name=file3 size=40>")
			self.wfile.write("<input type=SUBMIT value=Add>")
			self.wfile.write("</form>")
			self.wfile.write("</body></html>")
	def do_POST(self):
		self.send_response(200)
		self.send_header('Content-type', 'text/html')
		self.end_headers()
		self.wfile.write("<html><head><title>Test POST</title><body><h1>Test POST</h1>")
		print str(self.headers)
		while True:
			sys.stdout.write(self.rfile.read(1))
		"""
		request= cgi.FieldStorage(
					fp=self.rfile,
					headers=self.headers,
					keep_blank_values= True,
					strict_parsing= True,
					environ={
							'REQUEST_METHOD':'POST',
							'CONTENT_TYPE':self.headers['Content-Type']
							}
					)
		for info in request.keys():
			if request[info].filename:
				(filepath, md5hash, sha1hash)= streamFile(request[info].file, StoragePath)
				self.wfile.write("<b>%s</b> => \"%s\" (%s, %s)<br>\n"%(info, str(request[info].filename), filepath, md5hash))
			else:
				self.wfile.write("<b>%s</b> => \"%s\"<br>\n"%(info, str(request[info].value)))
		for member in self.__dict__.keys():
			self.wfile.write("<b>%s</b> = \"%s\"<br>\n"%(member, str(self.__dict__[member])))
		self.wfile.write(str(request))
		"""
		self.wfile.write("</body></html>")
	def log_message(self, format, *data):
		#print format%data
		pass

class ThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == "__main__":
	parameters= {
		"-port": 8088,
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
		server = ThreadedHTTPServer(('', int(parameters["-port"])), UIHandler)
		server.serve_forever()
	except KeyboardInterrupt:
		server.socket.close()

