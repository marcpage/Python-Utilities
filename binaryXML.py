#!/usr/bin/env python -B
# -*- coding: utf-8 -*-

import CompactNumbers

"""
	TODO: print out data structure as string at point of exception
	TODO: format 2 gets all the strings and creates a dictionary up front and just uses numbers for the strings throughout
	
	<test prop=value>
		<value prop=value>value</value>
	</test>
	(
		"test"
		[(prop,value)]
		[
			("value",[(prop,value)],["value"])
		]
	)
	tag is tuple of name, properties and items
	item can be a tag or a string
	[format:]count:
		type:tag/text
"""
bestCompressionFormat=1
latestFormat=1
mostReadableFormat=1
allFormats= [1]

_StringItem= 1
_IntegerItem= 2
_TagItem= 3

def deserialize(binary, format=None):
	if not format:
		format= CompactNumbers.decodeUnsignedInteger(binary)
		if not format in allFormats:
			raise SyntaxError("Unknown format: "+str(format))
	count= CompactNumbers.decodeUnsignedInteger(binary)
	items= []
	for item in range(0, count):
		type= CompactNumbers.decodeUnsignedInteger(binary)
		if _StringItem == type:
			items.append(CompactNumbers.decodeString(binary))
		elif _TagItem == type:
			items.append(CompactNumbers.decodeSignedInteger(binary))
		elif _TagItem == type:
			tagName= CompactNumbers.decodeString(binary)
			propertyCount= CompactNumbers.decodeUnsignedInteger(binary)
			properties= []
			for property in range(0, propertyCount):
				key= CompactNumbers.decodeString(binary)
				value= CompactNumbers.decodeString(binary)
				properties.append( (key, value) )
			contents= deserialize(binary, format)
			items.append( (tagName, properties, contents) )
		else:
			raise SyntaxError("Corrupted Stream: item type: "+str(type))
	return items

def serialize(data, container= None, format= latestFormat):
	if not container:
		container= []
	if format:
		CompactNumbers.encodeUnsignedInteger(format, container)
	if not data.__class__ is list:
		raise SyntaxError("serialize takes an array of elements")
	CompactNumbers.encodeUnsignedInteger(len(data), container)
	for item in data:
		if isinstance(item, basestring):
			CompactNumbers.encodeUnsignedInteger(_StringItem, container)
			CompactNumbers.encodeString(item, container)
		elif isinstance(item, (int, long)):
			CompactNumbers.encodeUnsignedInteger(_IntegerItem, container)
			CompactNumbers.encodeSignedInteger(item, container)
		elif isinstance(item, tuple):
			CompactNumbers.encodeUnsignedInteger(_TagItem, container)
			if not item[0].__class__ is str and not item[0].__class__ is unicode:
				raise SyntaxError("serialize: tag name (1st tuple element) should be string or unicode")
			CompactNumbers.encodeString(item[0], container)
			if item[1] and not item[1].__class__ is list:
				raise SyntaxError("serialize: properites (2nd tuple element) should be list")
			CompactNumbers.encodeUnsignedInteger(len(item[1]), container)
			for property in item[1]:
				if not property.__class__ is tuple:
					raise SyntaxError("serialize: property is not a tuple")
				if not property[0].__class__ is str and not property[0].__class__ is unicode:
					raise SyntaxError("serialize: property name (1st tuple element) should be string or unicode")					
				if not property[1].__class__ is str and not property[1].__class__ is unicode:
					raise SyntaxError("serialize: property valie (2nd tuple element) should be string or unicode")					
				CompactNumbers.encodeString(property[0], container)
				CompactNumbers.encodeString(property[1], container)
			if item[2] and not item[2].__class__ is list:
				raise SyntaxError("serialize: contents (3rd tuple element) should be list")
			serialize(item[2], container, None)
		else:
			raise SyntaxError("serialize: Unknown element type")
	return container
			

if __name__ == "__main__":
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
	print test
	binary= serialize(test)
	test2= deserialize(binary)
	print test2
	if test != test2:
		print "FAILED"
