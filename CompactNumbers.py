#!/usr/bin/env python -B
# -*- coding: utf-8 -*-

import struct

bits= 7
moreBit= 1 << bits
maxValue= moreBit - 1
infinite= 1e100000 # python rounds it to infinite
#DBL_EPSILON= 2.2204460492503131e-016 # arbitrarily picked from a search for DBL_EPSILON on the web
#range 1.0e308 to 1.0e-323

"""
	We currently have issues with Real, in that this assumption fails:
		ASSUME: real > 1.0, real * 2.0 is not lossy
"""

class AppendableString:
	def __init__(self):
		self.__string= []
	def append(self, byte):
		self.__string.append(struct.pack("B", byte))
	def __str__(self):
		return "".join(self.__string)

class PoppableString:
	def __init__(self, string, offset= 0):
		self.__string= string
		self.__offset= offset
	def pop(offset):
		if offset != 0:
			raise SyntaxError("pop(offset!=0) not supported")
		value= struct.unpack_from("B", self.__string, self.__offset)[0]
		self.__offset+= 1
		return value

class AppendableWritable:
	def __init__(self, writable):
		self.__writable= writable
	def append(self, byte):
		self.__writable.write(struct.pack("B", byte))

class PoppableReadable:
	def __init__(self, readable):
		self.__readable= readable
	def pop(offset):
		if offset != 0:
			raise SyntaxError("pop(offset!=0) not supported")
		return struct.unpack("B", self.__readable.read(1))

def encodeUnsignedInteger(number, appendable):
	base= 0
	lastBase= 0
	bytes= 0
	while True:
		lastBase= base
		bytes+= 1
		base= (base << bits) | moreBit
		if base > number:
			break
	number-= lastBase
	notLast= moreBit
	for byte in range(0,bytes):
		if byte == bytes - 1:
			notLast= 0
		value= (number & maxValue) | notLast
		number= number >> bits
		appendable.append(value)

def decodeUnsignedInteger(poppable):
	value= 0
	base= 0
	shift= 0
	
	while True:
		nextByte= poppable.pop(0)
		value= value | ( (nextByte & maxValue) << shift )
		if nextByte > maxValue:
			base= (base << bits) | moreBit
		else:
			break
		shift+= bits
	return base + value

def encodeSignedInteger(number, appendable):
	negative= number < 0
	if negative:
		number= -1
	number= number << 1
	if negative:
		number= number | 1
	return encodeUnsignedInteger(number, appendable)

def decodeSignedInteger(poppable):
	number= decodeUnsignedInteger(poppable)
	negative= (number & 1) != 0
	if negative:
		number-= 1
	number= number >> 1
	if negative:
		number= -number
	return number

def encodeReal(number, appendable):
	negative= number < 0
	print "1 negative="+str(negative)
	shifts= 0
	print "2 shifts="+str(shifts)
	if negative:
		number= -number
		print "3 number="+str(number)
	if number == infinite:
		number= 0
		print "4 number="+str(number)
		if negative:
			shifts= -1 # 0 x 2 ^ -1 == -inf
		else:
			shifts= 1 # 0 x 2 ^ 1 == inf
		print "5 shifts="+str(shifts)
	elif number != 0.0:
		while long(number) != number:
			number*= 2
			shifts-= 1
			print "6 number="+str(number)
			print "7 shifts="+str(shifts)
		while long(number) == number:
			number/= 2
			shifts+= 1
			print "8 number="+str(number)
			print "9 shifts="+str(shifts)
		number*= 2
		shifts-= 1
		print "a number="+str(number)
		print "b shifts="+str(shifts)
	number= long(number)
	print "c number="+str(number)
	if negative:
		number= -number
		print "d number="+str(number)
	encodeSignedInteger(number, appendable)
	encodeSignedInteger(shifts, appendable)
	
def decodeReal(poppable):
	value= decodeSignedInteger(poppable)
	shifts= decodeSignedInteger(poppable)
	if value == 0 and shifts == 1:
		return infinite
	elif value == 0 and shifts == -1:
		return -infinite
	return value * 2.0**shifts

def encodeString(string, appendable):
	utf8= unicode(string).encode("utf8")
	encodeUnsignedInteger(len(utf8), appendable)
	for byte in range(0, len(utf8)):
		appendable.append(struct.unpack_from("B", utf8, byte)[0])

def decodeString(poppable):
	length= decodeUnsignedInteger(poppable)
	string= []
	for byte in range(0, length):
		string.append(struct.pack("B", poppable.pop(0)))
	return "".join(string).decode("utf8")

if __name__ == "__main__":
	stream= []
	originalValues= []
	value= 0
	for x in range(0, 1000):
		originalValues.append(value)
		encodeUnsignedInteger(value, stream)
		value= 3 * value + 1
	good= True
	for value in originalValues:
		streamed= decodeUnsignedInteger(stream)
		if streamed != value:
			print "%d did not come out right, it came out: %s"%(value, streamed)
			good= False
			break
	strings= [u"Résumé", u"©2009"]
	stream= []
	for string in strings:
		encodeString(string, stream)
	for string in strings:
		decoded= decodeString(stream)
		if decoded != string:
			print "expected \"%s\" but got \"%s\""%(string, decoded)
			good= False
			break
	numbers= [2.2204460492503131e-016] #, 2.2204460492503131e+016, 1.0e308, 1.0e-323, 0.0, 1.0, -1.0, 2.0, -2.0
	dataset= []
	stream= []
	for number in numbers:
		for othernumber in numbers:
			dataset.append(number * othernumber)
	for number in dataset:
		encodeReal(number, stream)
	for number in dataset:
		value= decodeReal(stream)
		if value != number:
			print "Expected %s but got %s"%(str(number), str(value))
			good= False
			break
	if good:
		print "Test passed"
