#!/usr/bin/env python -B

import array

def stringToASCIIList(string):
	""" Converts a string to an array of ASCII values
	"""
	ascii= []
	for character in map(ord, string):
		ascii.append(character)
	return ascii

def ASCIIListToString(asciiList):
	""" Converts an array of ASCII values to a string
	"""
	string= ""
	for character in map(chr, asciiList):
		string+= character
	return string

def __rotate(block8x8):
	""" Rotates a list of integers by returning a list of integers
		composed of the bits of it's index, ie:
			result[0] bit 0 is block8x8[0] bit 0
			result[0] bit 1 is block8x8[1] bit 0
			result[0] bit 2 is block8x8[2] bit 0
			etc.
	"""
	blockRotated= []
	for bit in range(0, 8):
		bitValue= 0
		for index in range(0, 8):
			theBit= (block8x8[index] >> bit) & 0x01
			bitValue|= theBit << index
		blockRotated.append(bitValue)
	return blockRotated

def decimate(block):
	assert (len(block) & 7) == 0 # must be evenly divisble by 8
	bytes= len(block)/8
	blockBytes= array.array('B', block)
	bucketBytes= [0]*bytes
	buckets= (
		array.array('B'),array.array('B'),array.array('B'),array.array('B'),
		array.array('B'),array.array('B'),array.array('B'),array.array('B'),
	)
	for bucket in buckets:
		bucket.extend(bucketBytes)
	for byte in range(0, len(blockBytes)):
		value= blockBytes[byte]
		if value:
			byteDiv8= byte / 8
			byteMod8= byte % 8
			for bit in range(0, 8):
				if (value >> bit) & 1:
					buckets[bit][byteDiv8]|= 1 << byteMod8
	return (
		buckets[0].tostring(),buckets[1].tostring(),buckets[2].tostring(),
		buckets[3].tostring(),buckets[4].tostring(),buckets[5].tostring(),
		buckets[6].tostring(),buckets[7].tostring(),
	)

def decimate_deprecated(block):
	""" Takes a string that must be length multiple of 8
		and returns an array of strings of the zeroth bit, 1st bit, etc
		of each byte in the string. See interleave.
	"""
	assert (len(block) & 7) == 0 # must be evenly divisble by 8
	buckets= ([], [], [], [], [], [], [], [])
	asciiBlock= stringToASCIIList(block)
	for chunkIndex in range(0, len(block) >> 3):
		chunk= asciiBlock[chunkIndex * 8 : (chunkIndex + 1) * 8]
		rotatedChunk= __rotate(chunk)
		for index in range(0, 8):
			buckets[index].append(rotatedChunk[index])
	bucketsOfString= []
	for bucket in buckets:
		bucketsOfString.append(ASCIIListToString(bucket))
	return bucketsOfString

def interleave(buckets):
	""" Interleaves the bits from a list of 8 lists. See decimate.
	"""
	block= []
	bucketLength= len(buckets[0])
	asciiBuckets= []
	for i in range(0, 8):
		assert bucketLength == len(buckets[i])
		asciiBuckets.append(stringToASCIIList(buckets[i]))
	for chunkIndex in range(0, bucketLength):
		chunk= []
		for bucket in asciiBuckets:
			chunk.append(bucket[chunkIndex])
		block.extend(__rotate(chunk))
	return ASCIIListToString(block)

if __name__ == "__main__":
	import time
	testData= [
		[0, 1, 2, 3, 4, 5, 6, 7],
		[10, 11, 12, 13, 14, 15, 16, 17],
		[0, 10, 20, 30, 40, 50, 60, 70],
		[1, 2, 4, 8, 16, 32, 64, 128],
	]
	allData= []
	for data in testData:
		assert __rotate(__rotate(data)) == data
		allData.extend(data)
	assert allData == stringToASCIIList(interleave(decimate(ASCIIListToString(allData))))
	myself= open(__file__, "r")
	contents= myself.read()
	myself.close()
	div8paddedSize= ((len(contents) - 1) / 8 + 1) * 8
	contents+= (div8paddedSize - len(contents)) * "x"
	assert contents == interleave(decimate(contents))
	largeDataSet=(8 * 1024 * 1024)*[0xA5] # 8MB
	largeDataSetAsString= ASCIIListToString(largeDataSet)
	print "Timing 8MB"
	start= time.time()
	decimated= decimate(largeDataSetAsString)
	print "%0.3f seconds to decimate 8MB"%(time.time() - start)
	start= time.time()
	interleaved= interleave(decimated)
	print "%0.3f seconds to interleave 8MB"%(time.time() - start)
	assert largeDataSet == stringToASCIIList(interleaved)
