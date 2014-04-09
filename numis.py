#!/usr/bin/env python -B

import sys
import re
import os.path
import os
import socket
import string
import threading
import Queue
import tempfile
import random
import shutil
import time
import hashlib
import cStringIO
import stat
import calendar
import cStringIO
import cPickle
import sqlite3
import fsDB
import zlib

schema= """
user
	id
	name[250]! search
	password[250]
tag
	id
	name[250]! search
	description[500]
	tax search
	transfers
transfer
	id
	date range search
	transaction_id search
	description_id
	fromcleared
	from_id(account) search
	tocleared
	to_id(account) search
	amount
	shares
	tags
transaction
	id
	description_id
	user_id
account
	id
	group_id
	type_id
	name[250]! search
	number[250]
	description[500]
type
	id
	name[250]! search
group
	id
	name[250]! search
	address[500]
	phone[250]
	fax[250]
	description[500]
description
	id
	description[500]!
balance
	account_id
	date
	cleared
	amount
	statement
	description
log
	transaction_id
	account_id
	user_id
	modification[500]
	description[500]
	date
"""
class Row(object):
	def __init__(self, table, fields, everything= False):
		self.__table= table
		self.__fields= fields
		self.__everything= everything
	def __getattribute__(self, name):
		if not self.__fields.has_key(name) and not self.__everything:
			self.__table.findFirst(search= self.__fields)
		if not self.__fields.has_key(name):
			raise AttributeError("Table: "+self.__table.name()+" Row: "+str(self.__fields)+" has no field "+name)
		return self.__fields[name]

class Table(object):
	def __init__(self, model, name, parameters, connection, cursor, dbType):
		"""parameters= {"fields": [], "relationships": [], "order": [], "columns": {}, "elements": {}}"""
		self.__model= model
		self.__name= name
		self.__parameters= parameters
		self.__connection= connection
		self.__cursor= cursor
		self.__dbType= dbType
		self.__db= fsDB.Database(name, cursor, dbType)
		self.__cache= []
	def name(self):
		return self.__name
	def add(self, **columns):
		return self.__add(columns)
	def find(self, *columns, **search):
		return self.__find(columns, search)
	def findFirst(self, *columns, **search):
		return self.__find(columns, search, 1)
	def update(self, *searchFor, **columns):
		if len(searchFor) == 1 and isinstance(searchFor[0], list):
			searchFor= searchFor[0]
		if len(columns.keys()) == 1 and columns.has_key("columns") and isinstance(columns["columns"], dict):
			columns= columns["columns"]
		updateFields= {}
		searchFields= {}
		for item in columns:
			if item in searchFor:
				searchFields[item]= columns[item]
			else:
				updateFields[item]= columns[item]
		return self.__db.updateRow(updateFields, searchFields, None)
	def delete(self, **searchFor):
		if len(searchFor.keys()) == 1 and searchFor.has_key("searchFor") and isinstance(searchFor["searchFor"], dict):
			searchFor= searchFor["searchFor"]
		where= []
		for item in searchFor:
			where.append("`%s` = '%s'"%(item, searchFor[item]))
		return self.__db.deleteWhere(" AND ".join(where))
	def __add(self, columns):
		if len(columns.keys()) == 1 and columns.has_key("columns") and isinstance(columns["columns"], dict):
			columns= columns["columns"]
		if not columns.keys():
			raise AttributeError("No columns specified in add")
		self.__db.addRow(columns)
		return self.__db.lastID()
	def __find(self, columns, search, limit= None):
		if len(columns) == 1 and isinstance(columns[0], list):
			columns= columns[0]
		if len(search.keys()) == 1 and search.has_key("search") and isinstance(search["search"], dict):
			search= search["search"]
		clause= []
		for item in search:
			clause.append("`%s` = '%s'"%(item, search[item]))
		return self.__db.findWhere(" AND ".join(clause), columns, limit= limit)

class Model(object):
	"""
	TODO:
		- add default values?
	tableName
	\t	id				(name == id is special, primary key integer auto increment, not null)
	\t	key[500]		(string of 500 characters max)
	\t	key				(if no length is indicated, then it is an INTEGER)
	\t	key search		(key field is searchable)
	\t	key?			(key can be NULL)
	\t	key!			(key must be unique)
	\t	table_id		(id of an item in table `table`)
	\t	some_id(table)	(use `table` as the table for the id, 'some' is the variable name)
	\t	tables			(if `table` has a [thisTableName]s entry then a many to many relationship is created)
	"""
	valuePattern= re.compile(r"^([a-zA-Z0-9_]+)(\[([0-9]+)\])?([?!])?( range)?( search)?$")
	idPattern= re.compile(r"^([a-zA-Z0-9_]+)_id([?!])?( range)?( search)?$")
	renamedIdPattern= re.compile(r"^([a-zA-Z0-9_]+)_id\(([a-zA-Z0-9_]+)\)([?!])?( range)?( search)?$")
	def __init__(self, schema, connection, dbType= "MySQL"):
		self.__schema= {}
		self.__connection= connection
		self.__cursor= connection.cursor()
		self.__parseSchema(schema)
		self.__interpretSchema()
		self.__defineRelationships()
		self.__createTables()
		self.__dbType= dbType
	def table(self, name):
		if self.__dict__.has_key(name) and isinstance(self.__dict__[name], Table):
			return self.__dict__[name]
		if self.__schema.has_key(name):
			self.__dict__[name]= Table(self, name, self.__schema[name], self.__connection, self.__cursor, self.__dbType)
			return self.__dict__[name]
		return None
	def __getattribute__(self, name):
		self.table(name)
		if not self.__dict__.has_key(name):
			raise AttributeError("Unknwon attribute "+str(name)+" in "+str(type(self)))
		return self.__dict__[name]
	def __parseSchema(self, schema):
		table= None
		while True:
			line= schema.readline()
			linestrip= line.strip()
			if not line:
				break
			if line[0] != "\t" and linestrip:
				table= linestrip
				self.__schema[table]= {
					"fields": []
				}
			elif linestrip:
				self.__schema[table]["fields"].append(linestrip)
	def __interpretSchema(self):
		for table in self.__schema:
			self.__interpretFields(table)
	def __defineRelationships(self):
		tables= self.__schema.keys()
		for table in tables:
			for relationship in self.__schema[table]["relationships"]:
				if not table in self.__schema[relationship]["relationships"]:
					raise Exception("%s says it relates to %s, but %s does not agree"%(table, relationship, relationship))
				if not self.__schema.has_key(relationship+"_"+table):
					related= table+"_"+relationship
					self.__schema[related]= {"fields": [table+"_id", relationship+"_id"]}
					self.__interpretFields(related)
	def __createTables(self):
		for table in self.__schema:
			command= ["CREATE TABLE `", table, "` ("]
			prefix= None
			for column in self.__schema[table]["order"]:
				if prefix:
					command.append(prefix)
				else:
					prefix= ", "
				command.extend(["`", column, "` ", self.__schema[table]["columns"][column]["properties"]])
			command.append(");")
			try:
				self.__cursor.execute("".join(command))
			except Exception,ex:
				pass
				#print "Create Table: "+str(ex)
	def __interpretFields(self, table):
		self.__fillInTable(table)
		for field in self.__schema[table]["fields"]:
			self.__interpretField(field, table)
	def __interpretField(self, field, table):
		name= None
		properties= None
		search= False
		unique= False
		range= False
		relatedTable= None
		canBeNULL= False
		column= None
		actionPerformed= False
		if field == "id": # its the primary key id
			name= field
			column= name
			properties= "INTEGER PRIMARY KEY AUTOINCREMENT"
			search= True
			range= False
		if field[-1] == "s":
			if self.__schema.has_key(field[:-1]):
				self.__schema[table]["relationships"].append(field[:-1])
				actionPerformed= True
		if not name and not actionPerformed: # its table_id
			isid= Model.idPattern.match(field)
			if isid:
				possibleTable= isid.group(1)
				if self.__schema.has_key(possibleTable):
					name= isid.group(1)
					column= name+"_id"
					relatedTable= possibleTable
					properties= "INTEGER"
					canBeNULL= isid.group(2)
					range= isid.group(3)
					search= isid.group(4) == "?"
					unique= isid.group(4) == "!"
		if not name and not actionPerformed: # its name_id(table)
			isid= Model.renamedIdPattern.match(field)
			if isid:
				possibleTable= isid.group(2)
				if self.__schema.has_key(possibleTable):
					name= "%s_id"%(isid.group(1))
					relatedTable= possibleTable
					canBeNULL= isid.group(3)
					range= isid.group(4)
					search= isid.group(5) == "?"
					unique= isid.group(5) == "!"
		if not name and not actionPerformed: # its a string or integer
			isValue= Model.valuePattern.match(field)
			if isValue:
				name= isValue.group(1)
				column= name
				if isValue.group(2):
					properties= "VARCHAR(%s)"%(isValue.group(3))
				else:
					properties= "INTEGER"
				canBeNULL= isValue.group(4)
				range= isValue.group(5)
				search= isValue.group(6) == "?"
				unique= isid.group(6) == "!"
		if unique:
			properties+= " UNIQUE"
		if canBeNULL:
			properties+= " NOT NULL"
		if name:
			self.__schema[table]["order"].append(column)
			self.__schema[table]["columns"][column]= {
				"table": relatedTable,
				"search": search,
				"unique": unique,
				"range": range,
				"name": name,
				"column": column,
				"properties": properties,
				"related": relatedTable,
				"null": canBeNULL
			}
			self.__schema[table]["elements"][name]= self.__schema[table]["columns"][column]
			actionPerformed= True
		if not actionPerformed:
			raise Exception("Invalid Field Format: Table: %s Field: %s"%(table, field))
	def __fillInTable(self, table):
		if not self.__schema[table].has_key("columns"):
			self.__schema[table]["columns"]= {}
		if not self.__schema[table].has_key("elements"):
			self.__schema[table]["elements"]= {}
		if not self.__schema[table].has_key("order"):
			self.__schema[table]["order"]= []
		if not self.__schema[table].has_key("relationships"):
			self.__schema[table]["relationships"]= []
					
			
def parseArgs(validArgs):
	nextIs= None
	for arg in sys.argv[1:]:
		if nextIs:
			if isinstance(validArgs[nextIs], list):
				validArgs[nextIs].append(arg)
			else:
				validArgs[nextIs]= arg
			nextIs= None
		elif arg in validArgs.keys():
			nextIs= arg
		else:
			raise SyntaxError("ERROR: Unknown parameter: "+arg+"\n")

class Tags:
	def __init__(self, connection, cursor, dbType):
		self.__connection= connection
		self.__cursor= cursor
		self.__db= fsDB.Database(cursor, "tag", dbType)
		self.__cache= {}
		try:
			self.__cursor.execute("""CREATE TABLE `tag` (
				`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
				`name` VARCHAR(250) NOT NULL,
				`description` VARCHAR(512) NOT NULL,
				`tax` INTEGER NOT NULL
			);""")
		except Exception,ex:
			pass # print "Create Table: "+str(ex)

class Users:
	def __init__(self, connection, cursor, dbType):
		self.__connection= connection
		self.__cursor= cursor
		self.__db= fsDB.Database(cursor, "user", dbType)
		self.__cache= {}
		try:
			self.__cursor.execute("""CREATE TABLE `user` (
				`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
				`name` VARCHAR(250) NOT NULL,
				`password` VARCHAR(250) NOT NULL
			);""")
		except Exception,ex:
			pass # print "Create Table: "+str(ex)
	def __findNameInCache(self,name):
		for id in self.__cache:
			if self.__cache[id]["name"] == name:
				return id
		return None
	def add(self, name, password):
		if self.__findNameInCache(name):
			raise Exception("user: name: %s already exists"%(name))
		results= self.__db.findWhere("`name` = '%s'"%(name), ["id"])
		if len(results) > 0:
			raise Exception("user: name: %s already exists, id=%d"%(name, int(results[0]["id"])))
		self.__db.addRow({"name": name, "password": password})
		id= self.__db.lastID()
		self.__cache[str(id)]= {"name": name, "password": password}
		id= int(self.__db.lastID())
		self.__connection.commit()
		return id
	def id(self, name):
		found= self.__findNameInCache(name)
		if found:
			return int(found)
		results= self.__db.findWhere("`name` = '%s'"%(name), ["id"])
		if len(results) > 0:
			return int(results[0]["id"])
		return None
	def name(self, id):
		if self.__cache.has_key(str(id)):
			return self.__cache[str(id)]["name"]
		results= self.__db.findWhere("`id` = '%d'"%(int(id)), ["name"])
		if len(results) > 0:
			return results[0]["name"]
		return None
	def password(self, nameOrID):
		if isinstance(nameOrID, basestring):
			found= self.__findNameInCache(nameOrID)
			if found:
				return self.__cache[found]["password"]
			results= self.__db.findWhere("`name` = '%s'"%(nameOrID), ["password"])
		else:
			if self.__cache.has_key(str(nameOrID)):
				return self.__cache[str(nameOrID)]["password"]
			results= self.__db.findWhere("`id` = '%d'"%(str(nameOrID)), ["password"])
		if len(results) > 0:
			return results[0]["password"]
		return None

def testUsers(db, cursor):
	"""Requires an empty database"""
	users= Users(db, cursor, dbType= "SQlite3")
	users.add("Marc", "password")
	users.add("Jamie", "drowssap")
	try:
		users.add("Marc", "test")
		print "We added a user twice!"
	except:
		pass
	try:
		users.add("Jamie", "test")
		print "We added a user twice!"
	except:
		pass
	if users.id("Marc") != 1:
		print "Marc id failed "+str(users.id("Marc"))
	if users.id("Jamie") != 2:
		print "Jamie id failed "+str(users.id("Jamie"))
	if users.name(1) != "Marc":
		print "user id 1 failed"
	if users.name(2) != "Jamie":
		print "user id 2 failed"
	if users.password("Marc") != "password":
		print "Marc password failed"
	if users.password("Jamie") != "drowssap":
		print "Jamie password failed"
	if users.password(1) != "password":
		print "1 password failed "+str(users.password(1))
	if users.password(2) != "drowssap":
		print "2 password failed"+str(users.password(2))

def testModel(model):
	marc= model.user.add(name="Marc", password="password")
	jamie= model.user.add(name="Jamie", password="drowssap")
	try:
		model.user.add(name="Marc", password="test")
		print "ERROR: Able to add Marc twice!"
	except:
		pass
	try:
		model.user.add(name="Jamie", password="test")
		print "ERROR: Able to add Jamie twice!"
	except:
		pass
	
	

if __name__ == "__main__":
	args= {
		"-db": None
	}
	parseArgs(args)
	db= sqlite3.connect(args["-db"])
	database= Model(cStringIO.StringIO(schema), db, "SQlite3")
	#cursor= db.cursor()
	#testUsers(db, cursor)
