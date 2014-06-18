#!/usr/bin/env python -B

import time
import calendar

Version= 1.2

"""
	1.2
		Added interpretResults and fetchAll to handle interpretting results from external execute commands

	1.1
		Added SpecialValue class to pass functions in
		Made zero length strings go up as NULL (use SpecialValue('""') to set an empty string)

	1.0
		Initial Version
"""

kTimeFormatString= "%Y-%m-%d %H:%M:%S"

def secondsAgo(dbDateTimeString):
	return time.mktime(time.strptime(dbDateTimeString, kTimeFormatString))

def secondsFromNow(seconds):
	return time.strftime(kTimeFormatString, time.localtime(seconds + time.time()))

def interpretResults(fetchallResults, cursorDescription):
		results= []
		for columns in fetchallResults:
			result= {}
			for columnIndex in range(0, len(cursorDescription)):
				#cursor.description[column] -> name, type_code, display_size, internal_size, precision, scale, null_ok
				result[cursorDescription[columnIndex][0]]= columns[columnIndex]
			results.append(result)
		return results

def fetchAll(cursor):
	return interpretResults(cursor.fetchall(), cursor.description)

class SpecialValue:
	def __init__(self, specialValue):
		self.__value= specialValue
	def __repr__(self):
		return "SpecialValue(\"%s\")"%(self.__value)
	def __str__(self):
		return self.__value

def createTable(cursor, name, fields, dbType= "MySQL", ifNotExists= True):
	try: # support passing an fsSQL as the cursor
		dbType= cursor.type().lower()
		database= cursor
		cursor= cursor.cursor()
	except AttributeError:
		dbType= dbType.lower()
		database= cursor
	fieldsString= ""
	separator= ""
	primary= None
	index= []
	if isinstance(fields, list):
		originalFields= fields
		fields= {}
		order= []
		for item in originalFields:
			fields[item[0]]= item[1]
			order.append(item[0])
	elif fields.has_key(''):
		order= fields['']
		for field in fields:
			if field not in order and len(field) > 0:
				order.append(field)
	else:
		order= fields.keys()
		order.sort()
	for field in order:
		if fields[field].has_key('size'):
			size= "( %s )"%(str(fields[field]['size']))
		else:
			size= ""
		if fields[field].has_key('null') and not fields[field]['null']:
			flags= " NOT NULL"
		else:
			flags= ""
		if fields[field].has_key('unique') and fields[field]['unique']:
			flags+= " UNIQUE"
		if fields[field].has_key('default'):
			defaultValue= fields[field]['default']
			if None == defaultValue:
				defaultValue= "NULL"
			else:
				defaultValue= "'%s'"%(defaultValue)
			flags+=" DEFAULT %s"%(defaultValue)
		if fields[field].has_key('primary') and fields[field]['primary']:
			if primary:
				raise SyntaxError("Trying to set more than one primary key! "+primary+" vs "+field)
			primary= field
		if fields[field].has_key('index') and fields[field]['index']:
			index.append(field)
		fieldsString+= "%s`%s` %s%s%s"%(separator, field, fields[field]['type'], size, flags)
		separator= ", "
	if primary:
		fieldsString+= ", PRIMARY KEY ( `%s` )"%(primary)
	if len(index) > 0 and dbType == "mysql":
		fieldsString+= ", INDEX ( "
		separator= ""
		for item in index:
			fieldsString+= "%s`%s`"%(separator, item)
			separator= ", "
		fieldsString+= ")"
	if ifNotExists:
		existsClause= "IF NOT EXISTS "
	else:
		existsClause= ""
	command= "CREATE TABLE %s`%s` (%s);"%(existsClause, name, fieldsString)
	cursor.execute(command)
	try:
		database.commit()
	except Exception,exception:
		pass
		#print exception
		#print command
	return Database(database, name, dbType)

class Database:
	"""
		database= MySQLdb.Connect(host=server, port=port, user=dbusername, passwd=dbpassword, db=dbname)
		dbTable= fsDB.Database(database.cursor(), table)
	"""
	def __init__(self, cursor, db, dbType= "MySQL"):
		"""dbType can be: MySQL or SQlite3, if cursor is an fsSQL, then dbType is ignored"""
		try: # support passing an fsSQL as the cursor
			self.__type= cursor.type().lower()
			self.__cursor= cursor.cursor()
			self.__database= cursor
		except AttributeError:
			self.__cursor= cursor
			self.__type= dbType.lower()
			self.__database= None
		self.__db= db
	def execute(self, command, doCommit= True):
		try:
			self.__cursor.execute(command)
		except Exception,exception:
			print exception
			print command
			raise exception
		if doCommit:
			try:
				self.__database.commit()
			except Exception,exception:
				pass
				print exception
				print command
		return fetchAll(self.__cursor)
	def db(self):
		return self.__db
	def list(self, columns= None, sorting= None, limit= None):
		(show, orderClause, limit)= self.__prepareSelect(columns, sorting, limit)
		return self.execute("SELECT %s FROM `%s`%s%s;"%(show, self.__db, orderClause, limit), doCommit= False)
	def findWhere(self, whereClause, columns= None, sorting= None, limit= None):
		(show, orderClause, limit)= self.__prepareSelect(columns, sorting, limit)
		return self.execute("SELECT %s FROM `%s` WHERE %s%s%s;"%(show, self.__db, whereClause, orderClause, limit), doCommit= False)
	def uniqueColumn(self, column, sortColumn= None):
		if sortColumn:
			display= "%s , %s"%(sortColumn, column)
		else:
			sortColumn= column
			display= column
		return self.execute("SELECT COUNT( * ) AS  Rows , %(display)s FROM `%(db)s` GROUP BY %(column)s ORDER BY %(sort)s;"\
								%{"db": self.__db, "column": column, "display": display, "sort": sortColumn}, doCommit= False)
	def __prepareSelect(self, columns, sorting, limit):
		if sorting:
			if not isinstance(sorting, list):
				sorting= [sorting]
			sortingFields= []
			for field in sorting:
				if field[0] == "-":
					field= field[1:]+" DESC"
				elif field[0] == "+":
					field= field[1:]
				sortingFields.append(field)
			orderClause= " ORDER BY "+", ".join(sortingFields)
		else:
			orderClause= ""
		if not columns:
			show= "*"
		elif isinstance(columns, list):
			show= "`"+"`, `".join(columns)+"`"
		else:
			show= "`%s`"%(columns)
		if limit:
			limit= " LIMIT %s"%(str(limit))
		else:
			limit= ""
		return (show, orderClause, limit)
	def __interpretFields(self, fields):
		values= []
		keys= []
		for key in fields.keys():
			keys.append("`"+key+"`")
			if None == fields[key]:
				values.append("NULL")
			elif isinstance(fields[key], SpecialValue):
				values.append(str(fields[key]))
			elif len(str(fields[key])) == 0:
				values.append("NULL")
			else:
				values.append("'%s'"%(str(fields[key]).replace("'", "''")))
		return (keys, values)
	def addRow(self, fields, doCommit= True):
		(keys, values)= self.__interpretFields(fields)
		return self.execute("INSERT INTO `%s` ( %s ) VALUES (%s);"%(self.__db, ", ".join(keys), ", ".join(values)), doCommit)
	def updateRow(self, updatedFields, id, idField= "id", doCommit= True):
		(keys, values)= self.__interpretFields(updatedFields)
		changes= []
		for change in zip(keys, values):
			changes.append("%s = %s"%(change[0], change[1]))
		if not idField and isinstance(id, dict):
			wheres= []
			for key in id:
				wheres.append("`%s` = '%s'"%(key, id[key]))
			whereClause= " AND ".join(wheres)
		else:
			whereClause= "`%s` = '%s'"%(idField, id)
		return self.execute("UPDATE `%s` SET %s WHERE %s;"%(self.__db, ", ".join(changes), whereClause), doCommit)
	def lastID(self, idField= "id"):
		if self.__type == "sqlite3":
			return self.execute("SELECT last_insert_rowid() AS `%s`;"%(idField),
																	doCommit= False)[0][idField]
		return self.execute("SELECT LAST_INSERT_ID();", doCommit= False)[0]['LAST_INSERT_ID()']
	def deleteWhere(self, whereClause, doCommit= True):
		return self.execute("DELETE FROM `%s` WHERE %s;"%(self.__db, whereClause), doCommit)



"""

DELETE FROM `groups` WHERE `group_id` = 21 AND `person_id` = 30 LIMIT 1

UPDATE `person` SET `name` = 'Marco', `fullname` = 'Marco Page' WHERE `id` =1 LIMIT 1 ;

INSERT INTO `person` ( `id` , `name` , `fullname` , `email` , `password` , `group_id` )
VALUES (
NULL , 'Marc', 'Marc Page', 'marcallenpage@gmail.com', '', '1'
), (
NULL , '', '', '', '', ''
);

UPDATE `person` SET `fullname` = 'Marc Allen Page' WHERE `id` =1 LIMIT 1 ;

CREATE TABLE `message` (
`id` INT NOT NULL ,
`person_id` INT NOT NULL ,
`body` LONGTEXT NOT NULL ,
`subject` VARCHAR( 250 ) NOT NULL ,
`to_id` INT NOT NULL ,
`cc_id` INT NOT NULL ,
`bcc_id` INT NOT NULL ,
`time` DATETIME NOT NULL ,
`complete` TINYINT NOT NULL DEFAULT '0',
PRIMARY KEY ( `id` ) ,
INDEX ( `person_id` , `time` , `complete` )
) ENGINE = MYISAM ;

INSERT INTO `group` ( `id` , `person_id` , `name` )
VALUES (
'1', '1', 'All'
);

"""
