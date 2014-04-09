#!/usr/bin/env python -B

import os
import threading
import Queue

Version= 1.1

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

def execute(command, interleave= False, stdin= None):
	makeStdIn, makeStdOut, makeStdErr= os.popen3(command)
	lines= Queue.Queue(0)
	if stdin:
		makeStdIn.write(stdin)
		makeStdIn.close()
	stdout= InputStreamToQueue(makeStdOut, lines, "out")
	stderr= InputStreamToQueue(makeStdErr, lines, "err")
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
	return ("".join(stdout), "".join(stderr), command)

class Message:
	def __init__(self, sender, subject, message, directRecipients, copiedRecipients= None, privateRecipients= None, otherHeaders= None):
		self.__sender= sender
		self.__subject= subject
		self.__message= message
		self.__to= self.__getList(directRecipients)
		self.__cc= self.__getList(copiedRecipients)
		self.__bcc= self.__getList(privateRecipients)
		self.__headers= otherHeaders
		if not self.__headers:
			self.__headers= {}
	def __getList(self, item):
		if type(item) is list:
			return item
		if not item:
			return []
		return [item]
	def addRecipient(self, recipient, copied= False, private= False):
		if not copied and not private:
			self.__to.append(recipient)
		elif not private:
			self.__cc.append(recipient)
		else:
			self.__bcc.append(recipient)
	def sendmailString(self):
		toString= ""
		ccString= ""
		bccString= ""
		headerString= ""
		if self.__to:
			toString= "To: "+", ".join(self.__to)+"\n"
		if self.__cc:
			ccString= "Cc: "+", ".join(self.__cc)+"\n"
		if self.__bcc:
			bccString= "Bcc: "+", ".join(self.__bcc)+"\n"
		for key in self.__headers.keys():
			headerString+= "%(key)s: %(value)s\n"%{"key": key, "value": self.__headers[key]}
		return "From: %(from)s\n%(to)s%(cc)s%(bcc)s%(headers)sSubject: %(subject)s\n\n%(body)s"%{
			"from": self.__sender,
			"to": toString,
			"cc": ccString,
			"bcc": bccString,
			"headers": headerString,
			"subject": self.__subject,
			"body": self.__message
		}
	def send(self, sendmailpath):
		results= execute(sendmailpath+" -t", stdin= self.sendmailString())
		if results[1]:
			raise RuntimeError("sendmail error\n"+results[1]+"\n"+results[0]+"\n"+results[2]+"\n"+self.sendmailString())
		return results
