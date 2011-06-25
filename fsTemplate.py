#!/usr/bin/python

"""
Python Templated Output
(C) 2007 The Freeman Society

This code may be freely used in any project, commercial or otherwise, with no restrictions on
use other than including this copyright statement. We do not provide any guarantee of this
code or its usefulness in for particular use.

TODO
	Add %{else}%
	Add %{else if:}%
	Add %{with:expression}%
	Add for loop magic (index, step, begin, end)
	Add allowing list[index]variable
	Add expression functions:
		replace
		escape (for URL)
			
%$#!+% === Name ===

%{variable}%
%{include:exp}%
%{begin if:exp}%
%{end if}%
%{begin loop:list setting=expr}%
	begin, end, step, row, column
%{end loop}%

%$#!+% === Name ===

Usage:

import fsTemplate
import sys

class StringWriter:
	def __init__(self):
		self.__contents= ""
	def write(self, contents):
		self.__contents= self.__contents + contents
	def get(self):
		return self.__contents

contents= StringWriter()
variables= {"AUTHENTICATED": None, "NOT_AUTHENTICATED": "True", "NAME": "Marc", "surname": "Page", "family": [ {"name": "Jamie", "surname": "Ingram"}, {"name": "Michael", "surname": "Page"}, {"name": "Kenneth", "surname": "Page"}, {"name": "Amy", "surname": "Page"}, {"name": "Rebekah", "surname": "Page"}]}
library= fsTemplate.File(sys.argv[1])
library.write("Home", variables, contents)
print contents.get()

1.46
	Added reverse command

1.45
	Added hex command
	Added upper command
	Added lower command

1.44
	Added pad command

1.43
	Added htmlize and urlize commands

1.42
	Fixed even and odd commands
	Improved not command
	Added equals command (alias of equal command)

1.41
	Fixed evaluateBoolean when item was unicode instead of str

1.4
	Added commands: less, greater, lessorequal, greaterorequal, equal
1.3
	Added full, recursive expressions: not, and, nand, or, nor, xor, nxor, add, subtract, multiply, divide, remainder, odd, even, concatenate
1.2
	More flexible
	added one level unary operator not(x)
	added one level binary operators and(x,y), or(x,y), xor(x,y), nand(x,y), nor(x,y), nxor(x,y)
	end statements can have an optional comment after :
		%{end loop[:comment]}% %{end if[:comment]}%
		comment is ignored
1.1
	Better error checking
1.0
	First Version
	
"""

import re

Version= 1.41

falseMatch= re.compile(r"(f|n|off|0)", re.IGNORECASE)
def evaluateBoolean(item):
	if item and (isinstance(item, str) or isinstance(item, unicode)):
		item= not falseMatch.match(item)
	if item:
		return True
	return False
def evaluateNumeric(item):
	if isinstance(item, list):
		return len(item)
	return int(item)

def notCommand(args):
	if len(args) == 0:
		return True
	return not evaluateBoolean(args[0])
def andCommand(args):
	result= True
	for arg in args:
		result= result and arg
	return result
def nandCommand(args):
	return not andCommand(args)
def orCommand(args):
	result= False
	for arg in args:
		result= result or arg
	return result
def norCommand(args):
	return not orCommand(args)
def xorCommand(args):
	result= False
	for arg in args:
		result= (result and (not arg)) or ( (not result) and arg)
	return result
def nxorCommand(args):
	return not xorCommand(args)
def addCommand(args):
	result= 0
	for arg in args:
		result= result + evaluateNumeric(arg)
	return str(result)
def subtractCommand(args):
	result= evaluateNumeric(args[0])
	for arg in args[1:]:
		result= result - evaluateNumeric(arg)
	return str(result)
def multiplyCommand(args):
	result= 0
	for arg in args:
		result= result * evaluateNumeric(arg)
	return str(result)
def divideCommand(args):
	result= evaluateNumeric(args[0])
	for arg in args[1:]:
		result= result / evaluateNumeric(arg)
	return str(result)
def remainderCommand(args):
	result= evaluateNumeric(args[0])
	for arg in args[1:]:
		result= result % evaluateNumeric(arg)
	return str(result)
def oddCommand(args):
	result= True
	for arg in args:
		if int(arg) % 2 == 0:
			result= False
	return str(result)
def evenCommand(args):
	result= True
	for arg in args:
		if int(arg) % 2 == 1:
			result= False
	return str(result)
def concatenateCommand(args):
	result= ""
	for arg in args:
		if isinstance(arg, list):
			arg= "".join(arg)
		result= result + str(arg)
	return result
def htmlizeCommand(args):
	#print "INPUT: ["+args[0]+"]"
	result= args[0].replace(
				"&", "&amp;").replace(
				"<", "&lt;").replace(
				">", "&gt;").replace(
				"\t", "&nbsp;&nbsp;&nbsp;").replace(
				"\r\n", "\n").replace(
				"\r", "\n").replace(
				"\n", "<br>").replace(
				" ", "&nbsp;")
	#print "OUTPUT: ["+result+"]"
	return result
def padCommand(args):
	value= args[0]
	width= int(args[1])
	if len(args) > 2:
		pad= args[2]
	else:
		pad= ' '
	if len(args) > 3:
		side= args[3]
	else:
		side= 'L'
	while(len(value) < width):
		if side == 'l' or side == 'L':
			value= pad + value
		else:
			value+= pad
	return value
def urlizeCommand(args):
	return args[0].replace(
		"%", "%25").replace(
		"+", "%2B").replace(
		" ", "+").replace(
		"?", "%3F").replace(
		"&", "%26")
def countCommand(args):
	count= 0
	for arg in args:
		if isinstance(arg, list):
			count+= len(arg)
		else:
			count+= 1
	return str(count)
def reverseCommand(args):
	if len(args) != 1:
		raise SyntaxError("reverse takes 1 and only 1 parameter")
	if not isinstance(args[0], list):
		raise SyntaxError("reverse takes a list")
	result= list(args[0])
	result.reverse()
	return result
def lessThanCommand(args):
	if len(args) != 2:
		raise SyntaxError("lessthan takes 2 and only 2 parameters")
	return args[0] < args[1]
def greaterThanCommand(args):
	if len(args) != 2:
		raise SyntaxError("greaterthan takes 2 and only 2 parameters")
	return args[0] > args[1]
def lessThanOrEqualCommand(args):
	if len(args) != 2:
		raise SyntaxError("lessthanorequal takes 2 and only 2 parameters")
	return args[0] <= args[1]
def greaterThanOrEqualCommand(args):
	if len(args) != 2:
		raise SyntaxError("greaterthanorequal takes 2 and only 2 parameters")
	return args[0] >= args[1]
def equalsCommand(args):
	if len(args) != 2:
		raise SyntaxError("equals takes 2 and only 2 parameters")
	#print "equalsCommand: \""+args[0]+"\" vs \""+args[1]+"\""
	if args[0] == args[1]:
		pass #print "True"
	else:
		pass #print "False"
	return args[0] == args[1]
def hexCommand(args):
	if len(args) != 1:
		raise SyntaxError("hex takes 1 and only 1 parameter")
	return "%x"%(long(args[0]))
def upperCommand(args):
	if len(args) != 1:
		raise SyntaxError("upper takes 1 and only 1 parameter")
	return str(args[0]).upper()
def lowerCommand(args):
	if len(args) != 1:
		raise SyntaxError("upper takes 1 and only 1 parameter")
	return str(args[0]).lower()

supportedCommands= {
	"not": notCommand,
	"and": andCommand,
	"nand": nandCommand,
	"or": orCommand,
	"nor": norCommand,
	"xor": xorCommand,
	"nxor": nxorCommand,
	"add": addCommand,
	"subtract": subtractCommand,
	"multiply": multiplyCommand,
	"divide": divideCommand,
	"remainder": remainderCommand,
	"odd": oddCommand,
	"even": evenCommand,
	"less": lessThanCommand,
	"greater": greaterThanCommand,
	"lessorequal": lessThanOrEqualCommand,
	"greaterorequal": greaterThanOrEqualCommand,
	"equal": equalsCommand,
	"equals": equalsCommand,
	"concatenate": concatenateCommand,
	"count": countCommand,
	"reverse": reverseCommand,
	"htmlize": htmlizeCommand,
	"pad": padCommand,
	"hex": hexCommand,
	"upper": upperCommand,
	"lower": lowerCommand,
}

class Environment:
	__numeric= re.compile(r"\s*([0-9]+)\s*")
	__quotedItem= re.compile(r"\s*\"")
	__commandItem= re.compile(r"\s*([^\s,()]+)\s*\(\s*")
	__singleItem= re.compile(r"\s*([^\s,()]+)(\s*)[,)]?")
	def __init__(self, variables, blocks, parent= None):
		if not isinstance(variables, dict):
			self.__variables= {"value": variables}
		elif variables:
			self.__variables= variables
		else:
			self.__variables= {}
		self.__parent= parent
		self.__blocks= blocks
		self.__variables["__internal__ERRORS__"]= ""
	def __parseQuotedString(self, string, argsList):
		value= ""
		while 1:
			backslashPosition= string.find("\\")
			quotePosition= string.find("\"")
			if quotePosition >= 0:
				if backslashPosition > 0 and backslashPosition < quotePosition:
					value= value + string[0:backslashPosition] + string[backslashPosition + 1:backslashPosition + 2]
					string= string[backslashPosition + 2:]
				else:
					argsList.append(value + string[0:quotePosition])
					return string[quotePosition + 1:]
			else:
				self.appendError("missing quote in string")
	def __parseItems(self, originalString, argsList):
		while 1:
			quotedItem= self.__quotedItem.match(originalString)
			commandItem= self.__commandItem.match(originalString)
			singleItem= self.__singleItem.match(originalString)
			if quotedItem:
				originalString= self.__parseQuotedString(originalString[quotedItem.end():], argsList)
			elif commandItem:
				commandArgs= []
				originalString= self.__parseItems(originalString[commandItem.end():], commandArgs)
				if supportedCommands.has_key(commandItem.group(1)):
					value= supportedCommands[commandItem.group(1)](commandArgs)
					argsList.append(value)
				else:
					self.appendError("Command \"%s\" is not supported"%(commandItem.group(1)))
			elif singleItem:
				isNumeric= self.__numeric.match(singleItem.group(1))
				if isNumeric:
					argsList.append(isNumeric.group(1))
				else:
					argsList.append(self.get(singleItem.group(1)))
				originalString= originalString[singleItem.end(2):]
			else:
				self.appendError("We are completely lost \"%s\""%(originalString))
			if originalString[0:1] == ")":
				return originalString[1:]
			if originalString[0:1] == ",":
				originalString= originalString[1:]
			if len(originalString) == 0:
				return originalString
	def getBlocks(self):
		return self.__blocks
	def get(self, name):
		if self.__variables.has_key(name):
			return self.__variables[name]
		elif None == self.__parent:
			return None
		else:
			return self.__parent.get(name)
	def evaluate(self, expression):
		results= []
		self.__parseItems(expression, results)
		if len(results) == 1:
			return results[0]
		else:
			return results
		self.appendError("We didn't get any results \"%s\""%(expression))
		return ""
	def set(self, name, value):
		self.__variables[name]= value
	def appendError(self, message):
		if self.__parent:
			self.__parent.appendError(message)
		elif self.__variables["__internal__ERRORS__"]:
			self.__variables["__internal__ERRORS__"].append(message+"\n")

class Text:
	def __init__(self, text):
		self.__text= text
	def write(self, out, env):
		out.write(self.__text)

class Variable:
	def __init__(self, name):
		if name:
			self.__name= name
		else:
			raise SyntaxError("Variable has no name")
	def write(self, out, env):
		value= env.get(self.__name)
		if value:
			out.write(str(env.get(self.__name)))
		else:
			env.appendError("Variable not found '%s'"%(self.__name))

class Include:
	def __init__(self, name):
		self.__name= name
	def write(self, out, env):
		env.getBlocks()[self.__name].write(out, env)

class Assignment:
	def __init__(self, variable, expression):
		self.__variable= variable
		self.__expression= expression
	def write(self, out, env):
		env.set(self.__variable, env.evaluate(self.__expression))

class Block:
	def __init__(self, parent= None):
		self.__elements= []
		self.__parent= parent
	def append(self, block):
		self.__elements.append(block)
	def parent(self):
		return self.__parent
	def __iter__(self):
		return self.__elements.__iter__()
	def write(self, out, env):
		for element in self.__elements:
			element.write(out, env)

class IfBlock:
	def __init__(self, condition, parent):
		self.__elements= []
		self.__parent= parent
		self.__condition= condition
	def append(self, block):
		self.__elements.append(block)
	def parent(self):
		return self.__parent
	def __iter__(self):
		return self.__iter__()
	def write(self, out, env):
		if evaluateBoolean(env.evaluate(self.__condition)):
			for element in self.__elements:
				element.write(out, env)

class LoopBlock:
	__startPattern= re.compile(r"begin=(.*);?")
	__endPattern= re.compile(r"end=(.*);?")
	__countPattern= re.compile(r"count=(.*);?")
	__stepPattern= re.compile(r"step=(.*);?")
	__rowPattern= re.compile(r"row=(.*);?")
	__columnPattern= re.compile(r"column=(.*);?")
	__variablePattern= re.compile(r"^(.*);?")
	def __init__(self, conditions, parent):
		self.__elements= []
		self.__parent= parent
		variableMatch= self.__variablePattern.match(conditions)
		if not variableMatch:
			raise SyntaxError("Could not find list variable in loop declaration")
		self.__variable= variableMatch.group(1)
		self.__start= 0
		self.__end= None
		self.__count= None
		self.__step= 1
		self.__row= None
		self.__column= None
		# get other parts here
	def append(self, block):
		self.__elements.append(block)
	def parent(self):
		return self.__parent
	def write(self, out, env):
		subEnvironments= env.get(self.__variable)
		if subEnvironments:
			if None == self.__end:
				if None == self.__count:
					end= len(subEnvironments)
				else:
					end= self.__start + self.__count
			else:
				end= self.__end
			# handle row, column and step
			for index in range(self.__start, end):
				subEnvironment= Environment(subEnvironments[index], env.getBlocks(), env)
				for element in self.__elements:
					element.write(out, subEnvironment)
	def variable(self):
		return self.__variable

class InnerBlock:
	def __init__(self, parent):
		self.__parent= parent
	def append(self, block):
		self.__elements.append(block)
	def parent(self):
		return self.__parent
	def write(self, out, indexes, env):
		raise SyntaxError("Inner loop blocks not supported yet")
		# finish

class StringWriter:
	def __init__(self):
		self.__contents= ""
	def write(self, contents):
		self.__contents= self.__contents + contents
	def get(self):
		return self.__contents

class File:
	__code= re.compile(r"%{([^}]*)}%")
	__ifCode= re.compile(r"^begin if:(.*)$")
	__loopCode= re.compile(r"^begin loop:(.*)$")
	__innerCode= re.compile(r"^begin inner$")
	__endInnerCode= re.compile(r"^end inner(:.*)?$")
	__endIfCode= re.compile(r"^end if(:.*)?$")
	__endLoopCode= re.compile(r"^end loop(:.*)?$")
	__includeCode= re.compile(r"^include:(.*)$")
	__assignCode= re.compile(r"^([^=]+)=(.*)$")
	__blockDivider= re.compile(r"%\$#!\+%\s+=+\s+(\S+)\s+=+(\r\n|\r|\n)", re.MULTILINE)
	__blockDividerNameIndex= 1
	def __init__(self, path= None, contents= None):
		if path:
			file= open(path, "r")
			contents= file.read()
			file.close()
		self.__blocks= {}
		while True:
			while True:
				start= self.__blockDivider.search(contents)
				if not start:
					break
				if start.start() == 0 or contents[start.start()-1] == "\r" or contents[start.start()-1] == "\n":
					break
			if not start:
				break
			contents= contents[start.end():]
			while True:
				end= self.__blockDivider.search(contents)
				if not end:
					break
				if end.start() > 0 and (contents[end.start()-1] == "\r" or contents[end.start()-1] == "\n"):
					break
			if not end:
				raise SyntaxError("No end block found for '%s'"%(start.group(self.__blockDividerNameIndex)))
			if start.group(self.__blockDividerNameIndex) != end.group(self.__blockDividerNameIndex):
				raise SyntaxError("Block started '%s', but next block ('%s') started before it ended"%(start.group(self.__blockDividerNameIndex), end.group(self.__blockDividerNameIndex)))
			endOfBlock= end.start()
			# consume last end of line in block
			if contents[endOfBlock - 1 : endOfBlock] == "\n":
				endOfBlock= endOfBlock - 1
			if contents[endOfBlock - 1 : endOfBlock] == "\r":
				endOfBlock= endOfBlock - 1
			self.__parseBlock(start.group(self.__blockDividerNameIndex), contents[:endOfBlock])
			contents= contents[end.end():]
	def __parseBlock(self, name, contents):
		self.__blocks[name]= Block()
		currentNode= self.__blocks[name]
		while 1:
			nextCode= self.__code.search(contents)
			if None == nextCode:
				if None != currentNode.parent():
					raise SyntaxError("Missing end code(s)")
				break
			if nextCode.start() > 0:
				currentNode.append(Text(contents[:nextCode.start()]))
				contents= contents[nextCode.start():]
			matchFound= None
			match= self.__ifCode.match(nextCode.group(1))
			if match:
				currentNode= IfBlock(match.group(1), currentNode)
				currentNode.parent().append(currentNode)
				matchFound= True
			else:
				match= self.__loopCode.match(nextCode.group(1))
			if not matchFound and match:
				currentNode= LoopBlock(match.group(1), currentNode)
				currentNode.parent().append(currentNode)
				matchFound= True
			else:
				match= self.__innerCode.match(nextCode.group(1))
			if not matchFound and match:
				currentNode= InnerBlock(currentNode)
				currentNode.parent().append(currentNode)
				matchFound= True
			else:
				match= self.__includeCode.match(nextCode.group(1))
			if not matchFound and match:
				currentNode.append(Include(match.group(1)))
				matchFound= True
			else:
				match= self.__assignCode.match(nextCode.group(1))
			if not matchFound and match:
				currentNode.append(Assignment(match.group(1), match.group(2)))
				matchFound= True
			else:
				match= self.__endInnerCode.match(nextCode.group(1))
			if not matchFound and match:
				if not isinstance(currentNode, LoopBlock):
					raise SyntaxError("Found '%s' in %s"%(nextCode.group(1), currentNode.__class__))
				currentNode= currentNode.parent()
				if None == currentNode:
					raise SyntaxError("Unexpected 'end inner', but how were we in an if block at root?")
				matchFound= True
			else:
				match= self.__endIfCode.match(nextCode.group(1))
			if not matchFound and match:
				if not isinstance(currentNode, IfBlock):
					raise SyntaxError("Found '%s' in %s"%(nextCode.group(1), currentNode.__class__))
				currentNode= currentNode.parent()
				if None == currentNode:
					raise SyntaxError("Unexpected 'end if', but how were we in an if block at root?")
				matchFound= True
			else:
				match= self.__endLoopCode.match(nextCode.group(1))
			if not matchFound and match:
				if not isinstance(currentNode, LoopBlock):
					raise SyntaxError("Found '%s' in %s"%(nextCode.group(1), currentNode.__class__))
				currentNode= currentNode.parent()
				if None == currentNode:
					raise SyntaxError("Unexpected end loop, but how were we in a loop block at root?")
			elif not matchFound:
				currentNode.append(Variable(nextCode.group(1)))
			contents= contents[len(nextCode.group()):]
		if len(contents) > 0:
			currentNode.append(Text(contents))
	def write(self, name, variables, out):
		if not self.__blocks.has_key(name):
			raise SyntaxError("Template does not have a block named \"%s\""%(name))
		if not variables:
			variables= {}
		env= Environment(variables, self.__blocks)
		self.__blocks[name].write(out, env)
	def get(self, name, variables= None):
		contents= StringWriter()
		self.write(name, variables, contents)
		return contents.get()

def __formatKey(key, value, results):
	if isinstance(value, list):
		results.append(key+__getCommonInformation(value))
	else:
		results.append(key)

def __getCommonInformation(templateDataList):
	keys= []
	results= []
	for item in templateDataList:
		for key in item:
			if key not in keys:
				__formatKey(key, item[key], results)
				keys.append(key)
	return "[ "+", ".join(results)+" ]"

def dictionaryToTemplateData(dictionary, templateData= None, prefix= "", keyset= None):
	if None == templateData:
		templateData= []
	if None == keyset:
		keyset= dictionary.keys()
	for key in keyset:
		if dictionary.has_key(key):
			templateData[prefix + key]= dictionary[key]

def describeTemplateData(templateData):
	results= []
	for key in templateData:
		__formatKey(key, templateData[key], results)
	return ", ".join(results)

def dictionaryToTemplateList(dictionary):
	results= []
	for key in dictionary:
		results.append({"key": key, "value": dictionary[key]})
	return results

if __name__ == "__main__":
	data= {
		'list': [
			{'name': 'John', 'id': 5},
			{'name': 'Fred', 'id': 3},
			{'name': 'George', 'id': 1},
			{'name': 'Harry', 'id': 2},
			{'name': 'Sally', 'id': 4},
		]
	}
	template= """ Test Data
%$#!+% === Test1 ===
%{TITLE="Test1"}%%{include:TestInclude}%
%{begin loop:list}%
	#%{id}%. %{name}%%{end loop:list}%
%{begin if:greater(count(list),4)}%
Lot's of items, huh?
%{end if:greater(count(list),4)}%
%{begin if:less(count(list),4)}%
Not many items, huh?
%{end if:less(count(list),4)}%
%$#!+% === Test1 ===

%$#!+% === TestInclude ===
%{TITLE}%%{TEST=concatenate(TITLE,"2")}%
%{include:TestInclude2}%
%$#!+% === TestInclude ===

%$#!+% === TestInclude2 ===
%{TEST}%
%$#!+% === TestInclude2 ===

"""
	templates= File(contents=template)
	out= StringWriter()
	templates.write("Test1", data, out)
	print out.get()
