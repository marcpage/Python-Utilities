#!/usr/bin/env python -B

import sys
import Queue
import os
import re
import os.path
import tempfile
import random
import smtplib
import threading
try:
	import subprocess
	kUseSubProcess= True
except:
	kUseSubProcess= False


global ShellEscapePattern
ShellEscapePattern= re.compile(r"[^A-Za-z0-9./,-]")
def shellEscape(path):
	global ShellEscapePattern
	return ShellEscapePattern.sub(lambda m:"\\"+m.group(0), path)

kShortLabels= ["B", "kiB", "MiB", "GiB", "TiB"]
kLongLabels= ["bytes", "kibibytes", "mebibytes", "gibibytes", "tebibytes"]
def formatDiskSize(size, format="%(size)0.1f %(label)s", labels= None):
	if size < 0:
		prefix= "-"
		size*= -1
	else:
		prefix= ""
	if None == labels:
		labels= list(kShortLabels)
	else:
		labels= list(labels)
	while size > 1024.0 and len(labels) > 1:
		size/= 1024.0
		labels.pop(0)
	return prefix+format%{'size': size, 'label': labels[0]}

def parseDiskSize(value):
	unit= value[-1].lower()
	multiplier= 1
	base= value[:-1].strip()
	if unit == 't':
		multiplier= 1024 * 1024 * 1024 * 1024
	elif unit == 'g':
		multiplier= 1024 * 1024 * 1024
	elif unit == 'm':
		multiplier= 1024 * 1024
	elif unit == 'k':
		multiplier= 1024
	else:
		base= value
	return long(base) * multiplier

def sendEmail(sender, recipients, subject, body, smtpServer):
	if not isinstance(recipients, list):
		recipients= [recipients]
	server= smtplib.SMTP(smtpServer)
	message= "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s"%(
		sender,
		", ".join(recipients),
		subject,
		body
	)
	server.sendmail(sender, recipients, message)
	server.quit()
	return message

def diskUsage():
	columns= {
		'Filesystem': {'format':'s'},
		'1024-blocks': {'format':'i'},
		'Used': {'format':'i'},
		'Available': {'format':'i'},
		'Capacity': {'format':'%'},
		'iused': {'format':'i'},
		'ifree': {'format':'i'},
		'%iused': {'format':'%'},
		'Mounted on': {'format':'/'},
	}
	o= execute("df -k")[0]
	o= o.strip().replace("\r\n", "\n").replace("\r", "\n")
	lines= o.split("\n")
	header= lines.pop(0)
	for column in columns:
		columns[column]['offset']= header.lower().find(column.lower())
	columnOrder= filter(lambda x:columns[x]['offset'] >= 0, columns.keys())
	columnOrder.sort(key=lambda x:columns[x]['offset'])
	numberPattern= re.compile(r"\b([0-9%]+)\s+")
	disks= {}
	for line in lines:
		numbers= []
		for number in numberPattern.finditer(line):
			value= number.group(1)
			type= ''
			if value[-1] == '%':
				value= value[:-1]
				type= '%'
			numbers.append( (number.start(), number.end(), long(value), type) )
		if columnOrder[-1].lower() != "mounted on":
			raise SyntaxError("Expected last column to be 'Mounted on', but it was "+columnOrder[-1])
		if columnOrder[0].lower() != "filesystem":
			raise SyntaxError("Expected first column to be 'Filesystem', but it was "+columnOrder[0])
		headers= list(columnOrder)
		mountHeader= headers.pop()
		filesystemHeader= headers.pop(0)
		mount= line[numbers[-1][1]:].strip()
		filesystem= line[:numbers[0][0]].strip()
		if(len(headers) != len(numbers)):
			raise SyntaxError("Number of columns and numbers do not match: headers "+str(len(headers))+" numbers "+str(len(numbers)))
		disks[mount]= {filesystemHeader.lower():filesystem,mountHeader.lower():mount}
		for column in zip(headers,numbers):
			disks[mount][column[0].lower()]= column[1][2]
		disks[mount]['__line__']= line
		disks[mount]['size']= disks[mount]['1024-blocks'] * 1024
		if 'available' in disks[mount]:
			disks[mount]['free']= disks[mount]['available'] * 1024
	return disks

def temporaryFile(prefix= None, extension=None, access= "w", temporaryDir= None, justPath= False):
	""" Creates a unique file
		if prefix is given the file will start with this, otherwise it will start with "tempfile"
		if extension is given (with leading .) it will be used, otherwise ".temp" will be used
		if access is given, it will be used to open the resulting file, otherwise "w" will be used
		if temporaryDir is given, it will be the directory to create the file in,
			otherwise the system temp directory will be used
		if justPath is True, only the path to the just created file is returned
		if justPath is False, or not specified, then a tuple of (fileObj, path) is returned
	"""
	if None == temporaryDir:
		temporaryDir= tempfile.gettempdir()
	if None == prefix:
		prefix= "tempfile"
	if None == extension:
		extension= ".temp"
	file_name= os.path.join(temporaryDir, prefix+extension)
	while 1:
		try:
			fd = os.open(file_name, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
			if justPath:
				os.fdopen(fd, access).close()
				return file_name
			return (os.fdopen(fd, access), file_name)
		except OSError:
			pass
		file_name= os.path.join(temporaryDir, prefix+'_'+str(random.randint(0,1000000000))+extension)

def temporaryDirectory(name= None):
	""" Creates a folder with a unique name
		if name is given, it is used for the base name (may have numbers appended if not unique)
		returns the path to the newly created directory
	"""
	temp= temporaryFile(name, extension= "", justPath= True)
	os.remove(temp)
	os.mkdir(temp)
	return temp

class InputStreamToQueue(threading.Thread):
	""" Continuously calls readline() from an inputStream in another thread
		and puts each line (with an optional name) into a queue
		until an empty string is returned
	"""
	def __init__(self, inputStream, lineQueue, name= None):
		""" inputStream must support readline() and return empty string when stream ends
			lineQueue must support put(item)
			name, if given, will be the first item in the tuple
				and the line being the second item put into the queue
			if name is given, put into queue (name, line)
			if name is not given, queue the line (no tuple)
			if an exception is raised in lineQueue.readline(), a tuple (always a tuple)
				of ("exception", str(exception)) will be put in the queue
				followed by None put in the queue
			when end of stream is reached (readline() returns an empty string)
				None is put in the queue
			This thread is self-starting
		"""
		self.__in= inputStream
		self.__queue= lineQueue
		self.__name= name
		threading.Thread.__init__(self)
		self.start()
	def run(self):
		""" Runs until end of stream or an exception is encountered """
		try:
			while True:
				try:
					line= self.__in.readline()
				except Exception, exception:
					self.__queue.put( ("exception", str(exception)) )
					break
				if len(line) == 0:
					break
				if None == self.__name:
					self.__queue.put(line)
				else:
					self.__queue.put( (self.__name, line) )
		except Exception, exception:
			try:
				self.__queue.put( ("exception", str(exception)) )
			except Exception:
				pass
		self.__queue.put(None)

class PopenCompatability:
	def __init__(self, command):
		(self.stdin, self.stdout, self.stderr)= os.popen3(command)
		self.returncode= 0
	def kill(self):
		sys.stderr.write("ERROR: Unable to kill process after timeout\r\n") # Figure out how to kill the process

def popen(command):
	""" bridges the gap between subprocess and popen3
		popen3 is deprecated but subprocess is not in some earlier versions of Python
		returns Popen like type
	"""
	if kUseSubProcess:
		#print "command",command
		return subprocess.Popen(	command,
								shell=False, # needs to be True for Windows? needs to be False on UNIX
								stdin=subprocess.PIPE,
								stdout=subprocess.PIPE,
								stderr=subprocess.PIPE,
								close_fds=True
		)
	return PopenCompatability(command)

def popen3compatability(command, shell= True):
	""" bridges the gap between subprocess and popen3
		popen3 is deprecated but subprocess is not in some earlier versions of Python
		drop in replacement for popen3(command)
	"""
	if kUseSubProcess:
		p= subprocess.Popen(	command,
								shell= shell,
								stdin=subprocess.PIPE,
								stdout=subprocess.PIPE,
								stderr=subprocess.PIPE,
								close_fds=True
		)
		return (p.stdin, p.stdout, p.stderr)
	else:
		return os.popen3(command)

def startProcess(command, stdin= None, shell= True):
	""" starts a command runnings and returns a queue the receives the output
		if stdin is a string, it will be written to the stdin
		the queue returned will receive a queue of tuples, or None
			each touple is (type, line) where type is "stderr", "stdout" or "exception"
			When two None's are returned (one for stderr one for stdout)
				all process output has been received
	"""
	(makeStdIn, makeStdOut, makeStdErr)= popen3compatability(command, shell= shell)
	lines= Queue.Queue(0)
	if stdin:
		makeStdIn.write(stdin)
		makeStdIn.close()
	stdout= InputStreamToQueue(makeStdOut, lines, "out")
	stderr= InputStreamToQueue(makeStdErr, lines, "err")
	return lines

def execute(command, interleave= False, stdin= None, debugLevel= 0, shell= True):
	""" executes a command in the shell
		command is the command to execute
		if interleave is true, then stderr will be interleaved with stdout
		if stdin is a string, it will be written to the stdin before any output is read
		if debugLevel >= 2, the command will be printed
		if debugLevel >= 3, the stdout and stderr will be printed upon completion
		if debugLevel >= 4, each line (as well as it's type) will be printed as it is received
		returns tuple of (stdout, stderr, command)
		if interleave is True, stderr will be empty string
	"""
	if debugLevel >= 2:
		print command
	lines= startProcess(command, stdin, shell= shell)
	streamCount= 2
	stdout= []
	stderr= []
	while streamCount > 0:
		line= lines.get()
		if None == line:
			streamCount-= 1
		elif interleave or line[0] == "out":
			stdout.append(line[1])
		else:
			stderr.append(line[1])
			if line[0] == "exception" and debugLevel >= 1:
				print line[1]
		if debugLevel >= 4:
			if None != line:
				print line
	if debugLevel == 3:
		print "STDOUT"
		print "".join(stdout)
		print "STDERR"
		print "".join(stderr)
	return ("".join(stdout), "".join(stderr), command)

def parseArgs(validArgs):
	""" Parse the command line arguments and return them.
		validArgs is a dictionary with key being the switches for the command line
		if the value for a given key is an integer, the integer will be incremented each time the switch is encountered
			integer value switches cannot have a field after it
		if the value for a given key is a list, the argument after the given key on the command line will be appended to the list
		otherwise, the value will be assigned the argument after the given key
		if one of the keys is empty string, it's value should be a list
			empty string key will get all arguments that are not part of a switch, usually used for file paths
		if there is no emptry string key, and a switch is encountered that is not a key, a SyntexError is raised
	"""
	nextIs= None
	for arg in sys.argv[1:]:
		if None == nextIs and not arg in validArgs.keys() and "" in validArgs.keys():
			nextIs= ""
		if None != nextIs:
			if isinstance(validArgs[nextIs], list):
				validArgs[nextIs].append(arg)
			else:
				validArgs[nextIs]= arg
			nextIs= None
		elif arg in validArgs.keys():
			if isinstance(validArgs[arg], int):
				validArgs[arg]+= 1
			else:
				nextIs= arg
		else:
			raise SyntaxError(
				"ERROR: Unknown parameter: "+arg+"\nValid Args: "+", ".join(validArgs.keys())+"\n"
			)

def mounts():
	mountInfo= {}
	global MountsPattern
	locations= execute("mount")[0].replace("\r\n","\n").replace("\r","\n").split("\n")
	for line in locations:
		if line:
			(identifier,remainder)= line.split(" on ",1)
			(path,remainder)= remainder.split('(',1)
			(parameters,remainder)= remainder.split(')',1)
			mountInfo[path.strip()]= (identifier.strip(),map(lambda x:x.strip(),parameters.split(',')))
	return mountInfo

def localMountPoints(mounted):
	locals= filter(lambda x:'local' in mounted[x][1],mounted)
	locals= filter(lambda x:'nodev' not in mounted[x][1],locals)
	locals= filter(lambda x:'nobrowse' not in mounted[x][1],locals)
	return locals

def localMounts():
	mounted= mounts()
	locals= localMountPoints(mounted)
	notLocals= filter(lambda x:x not in locals, mounted)
	for item in notLocals:
		del mounted[item]
	return mounted

def notLocalMounts():
	mounted= mounts()
	locals= localMountPoints(mounted)
	for item in locals:
		del mounted[item]
	return mounted
