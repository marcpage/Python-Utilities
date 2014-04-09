#!/usr/bin/env python -B

import re
import os.path
import xml.dom.minidom
import cu

kPreferencesPath= "Library/Preferences/SystemConfiguration/preferences.plist"
kSystemVersionPath= "System/Library/CoreServices/SystemVersion.plist"
def loadPlist(path):
	""" Loads plist xml from the given path
	"""
	x= xml.dom.minidom.parse(path)
	if x.documentElement.tagName != 'plist':
		raise SyntaxError("Invalid Plist: "+path)
	return x

def getDictKey(key, inXML):
	""" Gets the given key from a <dict> in a plist
		inXML is either the <dict> tag or the documentElement
		returns the xml.dom.minidom.Element right after the <key> tag that matches key
	"""
	kElementNode= 1
	nextDict= None
	if inXML.tagName != 'dict':
		for node in inXML.childNodes:
			if node.nodeType == kElementNode and node.tagName == 'dict':
				nextDict= node
	else:
		nextDict= inXML
	if nextDict:
		foundKey= False
		for node in nextDict.childNodes:
			if node.nodeType == kElementNode:
				if foundKey:
					return node
				foundKey= node.tagName == 'key' and len(node.childNodes) > 0
				foundKey= foundKey and key.lower() == node.childNodes[0].data.lower()
	return None

def getElementByPath(path, inXML):
	""" Walks a documentElement of XML to get dict in dict in dict ...
		path is a list of keys in the hierarchy
			for instance, ["computer", "hardware", "usb"]
			would get the usb key in the hardware dict in the computer dict
		inXML is the documentElement
	"""
	node= inXML
	for element in path:
		node= getDictKey(element, node)
	return node

kLocalHostNamePath= ["System", "Network", "HostNames", "LocalHostName"]
kComputerNamePath= ["System", "System", "ComputerName"]
def getMachineName():
	""" Gets the machine name, usually found in System Preferences, Sharing, Computer Name
	"""
	prefs= loadPlist(os.path.join("/", kPreferencesPath))
	machineName= getElementByPath(kLocalHostNamePath, prefs.documentElement).childNodes[0].data
	if machineName != getElementByPath(kComputerNamePath, prefs.documentElement).childNodes[0].data:
		raiseSyntaxError("Network and Machine Names DIFFER!")
	prefs.unlink()
	return machineName

def changeMachineName(root, newName):
	""" Changes the system preferences for the drive rooted at root to the newName
		root can be "/", "/Volumes/X", etc.
	"""
	prefsPath= os.path.join(root, kPreferencesPath)
	prefs= loadPlist(prefsPath)
	getElementByPath(kLocalHostNamePath, prefs.documentElement).childNodes[0].replaceWholeText(newName)
	getElementByPath(kComputerNamePath, prefs.documentElement).childNodes[0].replaceWholeText(newName)
	f= open(prefsPath, "w")
	prefs.writexml(f)
	prefs.unlink()
	f.close()

def getInstalledOSVersion(root):
	""" Reads the OS version from the system version plist for the given partition root
	"""
	version= loadPlist(os.path.join(root, kSystemVersionPath))
	osVersion= getDictKey("ProductUserVisibleVersion", version.documentElement).childNodes[0].data
	version.unlink()
	return osVersion

