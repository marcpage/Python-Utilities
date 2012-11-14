#!/usr/bin/env python

import re

kValidNumberPattern= re.compile(r"^-?[1-9][0-9]*$")
def decode(readable, typecode= None):
	if None == typecode:
		typecode= readable.read(1)
	if 'i' == typecode:
		integer= ""
		while True:
			byte= readable.read(1)
			if 'e' == byte:
				break
			integer+= byte
		if not kValidNumberPattern.match(integer):
			raise SyntaxError("invalid integer: "+integer)
		return int(integer)
	if '0' <= typecode and typecode <= '9':
		string= ""
		byte= typecode
		while ':' != byte:
			if byte < '0' or '9' < byte:
				raise SyntaxError("invalid string length: "+byte)
			string+= byte
			byte= readable.read(1)
		return string
	if 'l' == typecode:
		array= []
		typecode= readable.read(1)
		while 'e' != typecode:
			array.append(decode(readable, typecode))
			typecode= readable.read(1)
		return array
	if 'd' == typecode:
		dictionary= {}
		typecode= readable.read(1)
		while 'e' != typecode:
			dictionary[decode(readable, typecode)]= decode(readable)
			typecode= readable.read(1)
		return dictionary
	raise SyntaxError("invalid typecode: "+typecode)

def encode(object, writable):
	keys= None
	isString= False
	isInteger= False
	try: # is it a dictionary?
		keys= object.keys()
	except:
		isString= isinstance(object, basestring)
		if not isString:
			isInteger= isinstance(object , (int, long))
	if None != keys:
		keys.sort()
		writable.write('d')
		for key in keys:
			encode(key, writable)
			encode(object[key], writable)
		writable.write('e')
	elif isString:
		writable.write("%d:%s"%(len(object),object))
	elif isInteger:
		writable.write("i%de"%(object))
	else:
		writeable.write('l')
		for element in object:
			encode(writable, element)
		writable.write('e')

if __name__ == "__main__":
	pass
