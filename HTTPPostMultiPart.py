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

class MultiPart:
	def __init__(self, hash= None):
		self.__storage= hash
		if not self.__storage:
			self.__storage= {}
		self.__boundary= None
	def __randomString(self):
		characters= "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
		values= []
		for x in range(0, 16):
			values.append(characters[random.randrange(0, len(characters))])
		return "".join(values)
	def __ensureBoundary(self):
		while self.__validateBoundary():
			self.__boundary= "----PythonHTTPPostMultiPartBoundary"+self.__randomString()
		return self.__boundary
	def __validateBoundary(self, field= None):
		if not self.__boundary:
			return True
		if field:
			if isinstance(self.__storage[field], tuple):
				pass # TODO FIX HERE
			elif self.__boundary in field or self.__boundary in self.__storage[field]:
				self._boundary= None
				return True
		else:
			for field in self.__storage.keys():
				return self.__validateBoundary(field)
		return False
	def __getitem__(self, key):
		self.__storage[key]
	def __setitem__(self, key, value):
		self.__storage[key]= value
	def __delitem__(self, key):
		del self.__storage[key]
	def __contains__(self, item):
		return self.has_key(item)
	def __repr__(self):
		return "HTTPPostMultiPart.MultiPart("+self.__storage.__repr__+")"
	def __str__(self):
		return self.encoded()
	def has_key(self, key):
		return self.__storage.has_key(key)
	def addFile(self, key, filename, path, contentType):
		self.__storage[key]= (filename, path, contentType)
	def contentType(self):
		return "multipart/form-data; boundary="+self.__ensureBoundary()
	def contentLength(self):
		return 0
	def encoded(self):
		return ""
	

if __name__ == "__main__":
	
"""
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryHtGwju1NUp96Suqo
Content-Length: 12499

------WebKitFormBoundaryHtGwju1NUp96Suqo
Content-Disposition: form-data; name="test"

30
------WebKitFormBoundaryHtGwju1NUp96Suqo
Content-Disposition: form-data; name="file1"; filename="DataStore.py"
Content-Type: text/x-python-script

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


------WebKitFormBoundaryHtGwju1NUp96Suqo
Content-Disposition: form-data; name="file2"; filename=""


------WebKitFormBoundaryHtGwju1NUp96Suqo
Content-Disposition: form-data; name="file3"; filename=""


------WebKitFormBoundaryHtGwju1NUp96Suqo--
"""
