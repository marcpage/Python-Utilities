#!/usr/bin/python

import rsa
import binaryXML
import array
import md5

""" Format:
	<block hash=543536546>
		<date>543534543</date>
		<name>John</name>
		<size>5345354</size>
		<path>documentation</path>
		<mime>text/plain</mime>
		<description>Original test document</description>
		<chunks size=1024>
			<chunk>54363645645</chunk>
			<chunk>436546456456</chunk>
			<chunk>534645674564</chunk>
			<chunk>564364564</chunk>
		</chunks>
	</block>
	<sign key=543534533 hash=543536546>53456345354</sign>
"""
class Packet:
	def __init__(self, binary= None):
		if binary:
			self.__data= binaryXML.deserialize(binary)
		else:
			self.__data= []
	def serialize(self):
		return binaryXML.serialize(self.__data)
	def set(self, name, value, properties= None):
		if not properties:
			properties= []
		if not value.__class__ is list:
			value= [value]
		alreadyExists= self.__findNamedItem(name, self.__data)
		if alreadyExists:
			self.__data.remove(item)
		self.__data.append( (name, properties, value) )
	def get(self, itemName):
		return self.__find(itemName)
	def sign(self, publicKey, privateKey):
		flat= binaryXML.serialize(self.__data, format= 1)
		flatArray= array.array('B')
		flatArray.extend(flat)
		data= flatArray.tostring()
		hash= md5.new(data).hexdigest()
		self.__data= [ ("block",[("hash",hash)],self.__data) ]
		self.__signBlocks(publicKey, privateKey)
	def __signBlocks(self, publicKey, privateKey): # we want to be able to mask out fields we disagree with
		signatures= []
		publicKeyString= rsa.keystring(publicKey)
		for item in self.__data:
			if item[0] is "block":
				hash= self.__findNamedItem("hash", item[1])
				if hash and hash[1]:
					signed= rsa.sign(hash, privateKey)
					signatures.append( ("sign", [ ("key", publicKeyString), ("hash", hash[1])], [signed]) )
			elif not item[0] is "sign":
				raise SyntaxError("We have a top level item that is not 'sign' and is not 'block'")
		self.__data.extend(signatures)
	def __repr__(self):
		return self.__data.__repr__()
	def __str__(self):
		return self.__data.__str__()
	def __findNamedItem(name, list):
		for item in list:
			if item[0] is name:
				return item
		return None
	def __find(self, itemName, data= None, results= None, hashes= None):
		if not data:
			data= self.__data
		if not results:
			results= []
		if not hashes:
			hashes= []
		for element in data:
			if element[0] is itemName:
				results.append( (element[2], element[1], hashes) )
			elif element[0] is "block": # TODO: need to validate hash here
				blockHash= __findNamedItem("hash", element[1])
				if blockHash:
					hashes= list(hashes)
					hashes.append(blockHash[2])
				results.extend(self.__find(itemName, element[2], results, hashes))
		return results

if __name__ == "__main__":
	x= Packet()
	x.set("name", "test.txt")
	x.set("size", "2235")
	x.set("path", "documentation")
	x.set("mime", "text/plain")
	x.set("description", "Original test document")
	x.set("chunks", properties= [("size","1024")], value= [
		("chunk", [], ["5435364567457"]),
		("chunk", [], ["6547756785678"]),
		("chunk", [], ["4346547658565"]),
		("chunk", [], ["4578758768675"]),
		("chunk", [], ["6677658585756"])
	])
	print x.get("name")
	print "Generating first key"
	(publicKey, privateKey)= rsa.gen_pubpriv_keys(128)
	trust= {rsa.keystring(publicKey): {"good": 3, "bad": 1}}
	print "signing first data"
	x.sign(publicKey, privateKey)
	print x.get("name", trust)
	x.set("name", "Test.txt")
	print x.get("name", trust)
	print "Generating second key"
	(publicKey2, privateKey2)= rsa.gen_pubpriv_keys(128)
	trust[rsa.keystring(publicKey2)]= {"good": 1, "bad": 2}
	print "signing second data"
	x.sign(publicKey2, privateKey2)
	print x.get("name", trust)
	x.sign(publicKey, privateKey)
	print x.get("name", trust)
	print x
