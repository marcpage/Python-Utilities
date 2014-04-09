#!/usr/bin/env python -B

import ini
import os
import sys
import stat
import datetime
import calendar
import traceback
try:
	import xattr
	kXattrAvailable= True
except:
	exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
	traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback, limit=5, file=sys.stderr)
	kXattrAvailable= False
try:
	import pwd
	import grp
	kPWDAvailable= True
except:
	exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
	traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback, limit=5, file=sys.stderr)
	kPWDAvailable= False

#kBetterDateFormat= "%Y/%m/%d@%H:%M:%S.%f" # not supported in 2.5.1 (Mac OS X 10.5/ppc)
kReliableDateFormat= "%Y/%m/%d@%H:%M:%S"
def __formatDate(timestamp):
	dt= datetime.datetime.utcfromtimestamp(timestamp)
	return dt.strftime(kReliableDateFormat)

def __parseDate(timestampString):
	dt= datetime.datetime.strptime(timestampString, kReliableDateFormat)
	return calendar.timegm(dt.timetuple())

kXattrPrefix= 'xattr_'
kChmodMask= stat.S_ISUID|stat.S_ISGID|stat.S_ENFMT|stat.S_ISVTX|stat.S_IREAD|stat.S_IWRITE|stat.S_IEXEC|stat.S_IRWXU|stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR|stat.S_IRWXG|stat.S_IRGRP|stat.S_IWGRP|stat.S_IXGRP|stat.S_IRWXO|stat.S_IROTH|stat.S_IWOTH|stat.S_IXOTH
def apply(path, info, skipAttributes= None):
	#print">apply(",path,",",info,")"
	somethingChanged= False
	if None == skipAttributes:
		skipAttributes= []
	stats= os.lstat(path)
	#print "info"
	#print info
	#print "sections",info.sections()
	kind= info.sections()[0]
	if "DIRECTORY" == kind:
		if not stat.S_ISDIR(stats.st_mode):
			raise SyntaxError(path+" was expected to be a directory")
	elif "FILE" == kind:
		if not stat.S_ISREG(stats.st_mode):
			raise SyntaxError(path+" was expected to be a file")
		if str(stats.st_size) != info['FILE.size']:
			raise SyntaxError(path+" is expected to be "+info['FILE.size']+" but is "+str(stats.st_size))
	elif "LINK" == kind:
		if not stat.S_ISREG(stats.st_mode):
			raise SyntaxError(path+" was expected to be a link")
		if os.readlink(path) != info['LINK.target']:
			#print "\t","changing link from",os.readlink(path),"to",info['LINK.target']
			os.remove(path)
			os.symlink(path, info['LINK.target'])
			somethingChanged= True
	else:
		raise SyntaxError("Unknown type: "+kind)
	#print "\t","kind",kind
	outpath= os.path.join(os.path.split(path)[0], info[kind+'.name'])
	if path != outpath:
		os.rename(path, outpath)
		somethingChanged= True
		#print"\t","renaming",path,"to",outpath
	if info.has_key(kind+'.mode'):
		mode= int(info[kind+'.mode'])
		if mode&kChmodMask != stats.st_mode&kChmodMask:
			os.chmod(outpath, stats.st_mode&~kChmodMask | mode&kChmodMask)
			somethingChanged= True
			#print "\t","changing mode from","%o"%(stats.st_mode),"to","%o"%(mode)
	if kXattrAvailable:
		infoAttr= {}
		for key in info:
			#print "\t","Examinging",key,"to see if it starts with",kind+"."+kXattrPrefix,key.find(kind+"."+kXattrPrefix)
			if key.find(kind+"."+kXattrPrefix) == 0:
				#print "\t","looking for attr",key[len(kind+"."+kXattrPrefix):]
				infoAttr[key[len(kind+"."+kXattrPrefix):]]= info[key]
		try:
			attrs= xattr.listxattr(outpath)
			for attr in attrs:
				if attr not in skipAttributes and infoAttr.has_key(attr):
					try:
						value= xattr.getxattr(outpath, attr)
						if value != bIni.unicodeToBuffer(infoAttr[attr]):
							xattr.setxattr(outpath, attr, bIni.unicodeToBuffer(infoAttr[attr]), xattr.XATTR_REPLACE, True)
							somethingChanged= True
							#print "\t","Replacing attribute",attr
						del infoAttr[attr]
					except:
						exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
						traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback, limit=5, file=sys.stderr)
						pass
			for attr in infoAttr:
				try:
					xattr.setxattr(outpath, attr, bIni.unicodeToBuffer(infoAttr[attr]), xattr.XATTR_CREATE, True)
					somethingChanged= True
					#print "\t","Setting attribute",attr
				except:
					exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
					traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback, limit=5, file=sys.stderr)
					pass
		except:
			exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
			traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback, limit=5, file=sys.stderr)
			pass
	setTimes= False
	if info.has_key(kind+'.access'):
		atime= __parseDate(info[kind+'.access'])
		if abs(atime - stats.st_atime) > 1:
			setTimes= True
	else:
		atime= stats.st_atime
	if info.has_key(kind+'.modified'):
		mtime= __parseDate(info[kind+'.modified'])
		#print "\t","mtime",mtime,"stats.st_mtime",stats.st_mtime
		if abs(mtime - stats.st_mtime) > 1:
			setTimes= True
	else:
		mtime= stats.st_mtime
	if setTimes:
		os.utime(outpath, (atime, mtime))
		somethingChanged= True
		#print "\t","changing times ",stats.st_atime,stats.st_mtime,"to",atime,mtime
	#print"<apply(",path,",",info,") -> ",outpath,somethingChanged
	return (outpath, somethingChanged)

def info(path, skipAttributes= None):
	if None == skipAttributes:
		skipAttributes= []
	results= bIni.ini()
	stats= os.lstat(path)
	if stat.S_ISDIR(stats.st_mode):
		section= 'DIRECTORY'
	elif stat.S_ISLNK(stats.st_mode):
		section= 'LINK'
		results.set('target', os.readlink(path), section)
	elif stat.S_ISREG(stats.st_mode):
		section= 'FILE'
		results.set('size', str(stats.st_size), section)
		try:
			results.set('mac_type', str(stats.st_type), section)
			results.set('mac_creator', str(stats.st_creator), section)
			results.set('mac_resource_size', str(stats.st_rsize), section)
		except:
			pass # only works on Mac
	else:
		return None # not a regular file, directory or link
	results.set('name', os.path.split(path)[1], section)
	results.set('modified', __formatDate(stats.st_mtime), section)
	#results.set('accessed', __formatDate(stats.st_atime), section)
	try:
		results.set('created', __formatDate(stats.st_birthtime), section)
		results.set('meta_data_modified', __formatDate(stats.st_ctime), section)
	except:
		#exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
		#traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback, limit=5, file=sys.stderr)
		results.set('created', __formatDate(stats.st_ctime), section)
	results.set('mode', str(stats.st_mode), section)
	if kPWDAvailable:
		try:
			results.set('user', pwd.getpwuid(stats.st_uid).pw_name, section)
		except:
			exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
			traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback, limit=5, file=sys.stderr)
			results.set('uid', str(stats.st_uid), section)
		try:
			results.set('group', grp.getgrgid(stats.st_gid).gr_name, section)
		except:
			exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
			traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback, limit=5, file=sys.stderr)
			results.set('gid', str(stats.st_gid), section)
	if kXattrAvailable:
		try:
			attrs= xattr.listxattr(path)
			for attr in attrs:
				if attr not in skipAttributes:
					try:
						value= xattr.getxattr(path, attr, True)
						results.set(kXattrPrefix+attr, value, section)
					except:
						exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
						traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback, limit=5, file=sys.stderr)
						pass
		except:
			exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
			traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback, limit=5, file=sys.stderr)
			pass
	return results

if __name__ == "__main__":
	for root, dirs, files in os.walk(os.getcwd()):
		for dir in dirs:
			print info(os.path.join(root, dir))
		for file in files:
			print info(os.path.join(root, file))
