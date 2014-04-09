#!/usr/bin/env python -B

import re
import sys
import traceback
import cStringIO

def unicodeToBuffer(string):
	result= ""
	for character in string:
		result+= chr(ord(character))
	return result

def tounicode(character):
	""" character is a hex unicode codepoint
	"""
	try:
		return unichr(int(character, 16))
	except:
		return character

class ini:
	""" As documented at:
		http://en.wikipedia.org/wiki/INI_file

		Supported:
			- comments as either ; or #, on their own line or after an item
			- whitespace is ignored, both blank lines as well as whitespace before and after keys and values
			- values can be quoted with single quotes (') or double quotes (")
			- only the first key encountered is used, other instances of the same name are ignored
			- changing a value changes it in place
			- removing a key removes the comment at the end of the line
			- key/value pairs can be delimited with either = or :
			- Hierarchical sections/keys are allowed with the following separators: dot (.), comma (,) and backslash (\)
			- When referencing keys in sections, you can either specify the section or use dot (.) notation (section.key)
	"""
	kEscapeTable= [ # unescaped, escaped
		('\\', '\\\\'),
		('\0', '\\0'),
		('\a', '\\a'),
		('\b', '\\b'),
		('\t', '\\t'),
		('\r', '\\r'),
		('\n', '\\n'),
		(';', '\\;'),
		('#', '\\#'),
		('=', '\\='),
		(':', '\\:'),
		("'", '\\x0027'),
		('"', '\\x0022'),
	]
	kSectionPattern= re.compile(r"^\s*\[\s*([^\]]+)\s*\]\s*([#;].*)?$")
	kSingleQuotedKeyValuePattern= re.compile(r"^\s*([^#;][^:=]+)\s*[:=]\s*'(.+)'\s*([#;].*)?(\s*)$")
	kDoubleQuotedKeyValuePattern= re.compile(r'^\s*([^#;][^:=]+)\s*[:=]\s*"(.+)"\s*([#;].*)?(\s*)$')
	kKeyValuePattern= re.compile(r"^\s*([^#;][^:=]+)\s*[:=]\s*(.+)\s*([#;].*)?(\s*)$")
	kUnicodePointPattern= re.compile(r"\\x([0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f])")
	def __replaceWithList(self, value, reverse= False):
		#print "__replaceWithList(",[value],",",reverse,")"
		result= ""
		if reverse:
			find=1
			replace=0
		else:
			find=0
			replace=1
		while len(value) > 0:
			bestOffset= len(value)
			bestFind= None
			bestReplace= None
			for item in self.kEscapeTable:
				offset= value.find(item[find])
				if offset >= 0 and offset < bestOffset:
					bestOffset= offset
					bestFind= item[find]
					bestReplace= item[replace]
			#print "\t","value",[value],"bestOffset",bestOffset,"bestFind",[bestFind],"bestReplace",[bestReplace]
			result+= value[:bestOffset]
			value= value[bestOffset:]
			if len(value) > 0:
				value= value[len(bestFind):]
				result+= bestReplace
			#print "\t","value",[value],"result",[result]
		return result
	def __escape(self, string):
		""" Handles escaping string for output to ini
		"""
		string= self.__replaceWithList(string)
		result= ""
		for character in string:
			if 32 > ord(character) or ord(character) >= 127:
				result+= "\\x%04x"%(ord(character))
			else:
				result+= character
		return result
	def __unescape(self, string):
		#print "__unescape(",[string],")"
		""" Handles getting the value of an escaped string
		"""
		result= self.kUnicodePointPattern.sub(lambda m: tounicode(m.group(1)),string)
		#print "\t",[result]
		return self.__replaceWithList(result, reverse= True)
	def __init__(self, source= None):
		""" If source is not a path, write must always have a path or file-like object passed to it
			source may be a path (which is remembered), a file object or the contents of an ini
		"""
		if isinstance(source, basestring):
			self.__path= source
		else:
			self.__path= None
		self.__keys= {}
		self.__modified= True
		self.__sections= {' global ': {'start': 1, 'end': 0}}
		self.__lines= []
		self.__lineEnding= "\n"
		currentSection= ' global '
		currentSectionPrefix= ""
		if None == source:
			return
		try:
			if isinstance(source, basestring):
				try:
					fileobject= open(source, "r")
				except:
					fileobject= cStringIO.StringIO(source)
					self.__path= None
			else:
				fileobject= source
			self.__lineEnding= None # get line ending from source
			while True:
				line= fileobject.readline()
				if not line:
					break
				if not self.__lineEnding:
					self.__lineEnding= line[-2:]
					if self.__lineEnding:
						if self.__lineEnding[0] != "\r":
							self.__lineEnding= self.__lineEnding[1:]
							#print "lineEnding: ",[self.__lineEnding]
				self.__lines.append(line)
				#print "lines", self.__lines
				line= line.strip()
				#print "line",line
				if not line:
					continue
				isSection= self.kSectionPattern.match(line)
				if isSection:
					#print "\t","isSection"
					if self.__sections.has_key(currentSection):
						self.__sections[currentSection]['end']= len(self.__lines) - 1
					currentSection= isSection.group(1).replace('\\', '.').replace(',', '.')
					currentSectionPrefix= currentSection+'.'
					#print "currentSection",currentSection,"currentSectionPrefix",currentSectionPrefix
					if not self.__sections.has_key(currentSection):
						self.__sections[currentSection]= {'start': len(self.__lines) - 1}
					#print "self.__sections",self.__sections
					continue
				keyValue= self.kSingleQuotedKeyValuePattern.match(line)
				if not keyValue:
					keyValue= self.kDoubleQuotedKeyValuePattern.match(line)
				if not keyValue:
					keyValue= self.kKeyValuePattern.match(line)
				if keyValue:
					fullKey= currentSectionPrefix + self.__unescape(keyValue.group(1)).replace('\\', '.').replace(',', '.')
					if not self.__keys.has_key(fullKey):
						self.__keys[fullKey]= {
							'line': len(self.__lines) - 1,
							'key': self.__unescape(keyValue.group(1)),
							'keyStart': keyValue.start(1),
							'keyEnd': keyValue.end(1),
							'value': self.__unescape(keyValue.group(2)),
							'valueStart': keyValue.start(2),
							'valueEnd': keyValue.end(2),
							'lineEnd': keyValue.end(4),
						}
			if self.__sections.has_key(currentSection):
				self.__sections[currentSection]['end']= len(self.__lines) - 1
			fileobject.close()
			self.__modified= False
		except:
			exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
			traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback, limit=5, file=sys.stderr)
			pass
		if not self.__lineEnding:
			self.__lineEnding= "\n"
	def __contains__(self, key):
		return key.replace('\\', '.').replace(',', '.') in self.__keys
	def __iter__(self):
		return self.__keys.__iter__()
	def __delitem__(self, key):
		self.remove(key)
	def __getitem__(self, key):
		return self.get(key)
	def __setitem__(self, key, value):
		self.set(key, value)
	def copy(self):
		""" Returns a full depth copy of itself
		"""
		new= ini()
		new.__path= self.__path
		new.__keys= dict(self.__path)
		new.__modified= True
		new.__sections= dict(self.__sections)
		new.__lines= list(self.__lines)
		new.__lineEnding= self.__lineEnding
		return new
	def remove(self, key, section= None):
		key= key.replace('\\', '.').replace(',', '.')
		if section:
			key= section.replace('\\', '.').replace(',', '.')+'.'+key
		if not self.__keys.has_key(key):
			raise KeyError(key+" does not exist to be removed")
		self.__lines[self.__keys[key]['line']]= self.__lines[self.__keys[key]['line']][self.__keys[key]['lineEnd']:]
	def get(self, key, section= None):
		#print "get(",key,",",section,")"
		key= key.replace('\\', '.').replace(',', '.')
		if section:
			key= section.replace('\\', '.').replace(',', '.')+'.'+key
		#print "\t","keys",self.__keys[key]
		return self.__keys[key]['value']
	def set(self, key, value, section= None):
		key= key.replace('\\', '.').replace(',', '.')
		if section:
			fullKey= section.replace('\\', '.').replace(',', '.')+'.'+key
		else:
			fullKey= key
		if self.__keys.has_key(fullKey):
			self.__keys[fullKey]['value']= value
			oldStart= self.__keys[fullKey]['valueStart']
			oldEnd= self.__keys[fullKey]['valueEnd']
			lineValuePrefix= self.__lines[self.__keys[fullKey]['line']][:oldStart]
			lineValueSuffix= self.__lines[self.__keys[fullKey]['line']][oldEnd:]
			self.__lines[self.__keys[fullKey]['line']]= lineValuePrefix+value+lineValueSuffix
			self.__keys[fullKey]['lineEnd']+= (oldEnd - oldStart) - len(value)
		else:
			if section and not self.__sections.has_key(section):
				if len(self.__lines) > 0 and self.__lines[-1].strip():
					self.__lines.append(self.__lineEnding)
				self.__sections[section]= {
					'start': len(self.__lines),
					'end': len(self.__lines) + 1,
				}
				self.__lines.append("[%s]%s"%(self.__escape(section), self.__lineEnding))
				insertionPoint= len(self.__lines)
			else:
				if not section:
					sections= list(self.__sections.keys())
					sections.sort(lambda x,y: len(y) - len(x))
					for evaluatedSection in sections:
						if key.find(evaluatedSection+'.') == 0:
							section= evaluatedSection
							key= key[len(evaluatedSection) + 1:]
							break
				if not section:
					section= ' global '
				insertionPoint= self.__sections[section]['end']
				if insertionPoint > 0 and len(self.__lines[insertionPoint].strip()) != 0:
					insertionPoint+= 1
				for updatedSection in self.__sections:
					if self.__sections[updatedSection]['start'] >= insertionPoint:
						self.__sections[updatedSection]['start']+= 1
					if self.__sections[updatedSection]['end'] >= insertionPoint:
						self.__sections[updatedSection]['end']+= 1
				for updatedKey in self.__keys:
					if self.__keys[updatedKey]['line'] >= insertionPoint:
						self.__keys[updatedKey]['line']+= 1
			escapedKey= self.__escape(key)
			escapedValue= self.__escape(value)
			self.__lines.insert(insertionPoint, "%s='%s'%s"%(escapedKey, escapedValue, self.__lineEnding))
			self.__keys[fullKey]= {
				'line': insertionPoint,
				'key': key,
				'keyStart': 0,
				'keyEnd': len(escapedKey),
				'value': value,
				'valueStart': len(escapedKey) + 2,
				'valueEnd': len(escapedKey) + 2 + len(escapedValue),
				'lineEnd': len(escapedKey) + 2 + len(escapedValue) + 1,
			}
	def iterkeys(self):
		return self.__keys.iterkeys()
	def update(self, other):
		for key in other:
			set(key, other[key])
	def has_key(self, key, section= None):
		#print "has_key(",key,",",section,")"
		if section:
			section= section.replace('\\', '.').replace(',', '.')+'.'
		else:
			section= ''
		fullKey= section + key
		#print "\t","fullKey",fullKey
		return self.__keys.has_key(fullKey)
	def keys(self, section= None):
		if not section:
			return self.__keys.keys()
		section= section.replace('\\', '.').replace(',', '.')
		sectionKeys= []
		section+= '.'
		for key in self.__keys:
			if key.find(section) ==0:
				sectionKeys.append(key)
		return sectionKeys
	def values(self, section= None):
		if section:
			section= section.replace('\\', '.').replace(',', '.')+'.'
		else:
			section= ''
		values= []
		for key in self.__keys:
			if key.find(section) == 0:
				values.append(keys[key]['value'])
		return values
	def write(self, destination= None):
		""" destination may be a file object or a path
		"""
		if destination or self.__modified:
			if not destination:
				destination= self.__path
			if isinstance(destination, basestring):
				outfile= open(destination, "w")
			else:
				outfile= destination
			for line in self.__lines:
				outfile.write(line)
			outfile.close()
	def sections(self):
		sections= list(self.__sections.keys())
		if ' global ' in sections:
			sections.remove(' global ')
		return sections
	def __repr__(self):
		return "ini.ini(%s)"%(self.__str__().__repr__())
	def __str__(self):
		return "".join(self.__lines)

if __name__ == "__main__":
	slashTest= ini("[FILE]\nxattr_com.apple.FinderInfo=';\\x00f0\\#\\x009cB\\x0084&~\\x001e\\\\x?\\x00c7\\x00a4i5\\x00b1\\r\\x00e1\\x00f87\\x00a0C@'\n")
	print [slashTest['FILE.xattr_com.apple.FinderInfo'], unicodeToBuffer(slashTest['FILE.xattr_com.apple.FinderInfo'])]
	slashTest2= ini(str(slashTest))
	print [slashTest2['FILE.xattr_com.apple.FinderInfo'], unicodeToBuffer(slashTest2['FILE.xattr_com.apple.FinderInfo'])]

	if slashTest['FILE.xattr_com.apple.FinderInfo'] != slashTest2['FILE.xattr_com.apple.FinderInfo']:
		raise SyntaxError("Failure!")
	i= ini()
	i.set('test', 'true', 'main.db')
	i['main.db.debug']= 'false'
	i['test']= 'false'
	i['main.db.test']= 'maybe'
	i.set('test', 'casually', 'main.db.gone')
	i['main.db.gone.test']= 'eventually'
	i.write("/tmp/test_ini_py.ini")
	source= "[DIRECTORY]\nname='templates'\nbackslash='\\\\a'\ngroup='staff'\nuser='marcp'\nflags='0'\nmeta_data_modified='2010/12/20@19\\:06\\:26.000000'\ncreated='2010/12/20@19\\:06\\:11.000000'\nmodified='2010/12/20@19\\:06\\:26.000000'\n"
	print "------- source --------"
	print source
	print "------- source --------"
	t= ini(source)
	print "------- str --------"
	print str(t)
	print "------- str --------"
	u= ini(str(t))
	print "------- str.ini.str --------"
	print str(u)
	print "------- str.ini.str --------"
	print [u.get('DIRECTORY.backslash')]
	t.set('binary', "Testing\0\0\0\0'me\"now\\\1\2\3\4\5\6\7\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x20")
	testBackslashString= "\\\\test\\me\\\\"
	t.set('backslash',testBackslashString)
	if t.get('backslash') != testBackslashString:
		print "What?",t.get('backslash'),testBackslashString
	print "binary",[t.get('binary')]
	print "sections:",t.sections()
	t.write(sys.stdout)
