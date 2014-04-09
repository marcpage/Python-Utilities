#!/usr/bin/env python -B

import MySQLdb

Version= 1.2

"""
	Need to handle null vs empty string
"""

class Column:
	def __init__(self, database, table, columnInfo):
		self.__database= database
		self.__table= table
		self.__info= columnInfo
	def required(self):
		return self.__info["Null"] == "NO"
	def primary(self):
		return self.__info["Key"] == "PRI"
	def type(self):
		typeInfo= self.__info["Type"]
		parenStart= typeInfo.find("(")
		if parentStart > 0:
			return typeInfo[:parenStart]
		return typeInfo
	def size(self):
		typeInfo= self.__info["Type"]
		parenStart= typeInfo.find("(")
		if parenStart > 0:
			parenEnd= typeInfo.find(")")
			if parenEnd > 0:
				return typeInfo[parenStart + 1:parenEnd]
		return typeInfo
	def default(self):
		return self.__info["Default"]
	def comment(self):
		return self.__info["Comment"]
	def unique(self):
		results= self.__database.execute("SELECT COUNT ( * ) AS `Rows` , `%(column)s` FROM `%(table)s` GROUP BY `%(column)s`"
						%{"column": self.__info["Field"], self.__table}
		values= []
		for info in results:
			values.append(info[self.__info["Field"]])
		return values

class Table:
	def __init__(self, database, name):
		self.__database= database
		self.__name= name
		self.__columnInfoCache= None
	def columns(self):
		self.__cacheColumnInfo()
		names= []
		for column in self.__columnInfoCache:
			names.append(column["Field"])
		return names
	def primary(self):
		self.__cacheColumnInfo()
		names= []
		for column in self.__columnInfoCache:
			if column["Key"] == "PRI":
				return column["Field"]
		return None
	def __getitem__(self, key):
		self.__cacheColumnInfo()
		names= []
		for column in self.__columnInfoCache:
			if column["Field"] == key:
				return Column(self.__database, self.__name, key, column)
		raise KeyError("%(key)s is not a valid column name (%(column)s)"%{"key": key, "column", ",".join(self.columns())})
	def __cacheColumnInfo(self):
		if not self.__columnInfoCache:
			self.__columnInfoCache= self.__database._table_columns(self.__name)

class Database:
	def __init__(self, name, username, password, server, port= 3306):
		self.__name= name
		self.__username= username
		self.__password= password
		self.__server= server
		self.__port= port
		self.__db= MySQLdb.Connect(host=server, port= port, user= username, passwd= password, db= name)
		self.__cursor= self.__db.cursor()
		self.__tableNameCache= None
	def close(self):
		self.__db.close()
	def execute(self, command):
		self.__cursor.execute(command)
		return self.__interpret_results()
	def tables(self):
		if self.__tableNameCache:
			return self.__tableNameCache
		tableList= self.execute("SHOW TABLE STATUS FROM `%(database)s`"%{"database": self.__name})
		self.__tableNameCache= []
		for table in tableList:
			self.__tableNameCache.append(table["Name"])
		return self.__tableNameCache
	def _table_columns(self, tableName):
		return self.execute("SHOW FULL COLUMNS FROM `%(table)s` FROM `%(database)s`":{"database": self.__name, "table": tableName})
	def __interpret_results(self):
		resultsList= []
		results= self.__cursor.fetchall()
		for row in results:
			rowInfo= {}
			for column in range(0, len(self.__cursor.description)):
				rowInfo[self.__cursor.description[column][0]]= row[column]
			resultsList.append(rowInfo)
		return resultsList
	def __getitem__(self, key):
		columnNames= self.tables()
		for name in columnNames:
			if name == key:
				return Table(self, key)
		raise KeyError("%(key)s is not a valid table name (%(tables)s)"%{"key": key, "tables", ",".join(tableNames)})


test= Database("freeman", "freeman", "fr33M4n", "freeman.startlogicmysql.com")
print test.tables()

"""
SHOW TABLE STATUS FROM `db`
self.__cursor.description
Description: (('Name', 253, 6, 64, 64, 0, 0), ('Engine', 253, 6, 64, 64, 0, 1), ('Version', 8, 2, 21, 21, 0, 1), ('Row_format', 253, 7, 10, 10, 0, 1), ('Rows', 8, 1, 21, 21, 0, 1), ('Avg_row_length', 8, 2, 21, 21, 0, 1), ('Data_length', 8, 2, 21, 21, 0, 1), ('Max_data_length', 8, 15, 21, 21, 0, 1), ('Index_length', 8, 4, 21, 21, 0, 1), ('Data_free', 8, 1, 21, 21, 0, 1), ('Auto_increment', 8, 1, 21, 21, 0, 1), ('Create_time', 12, 19, 19, 19, 0, 1), ('Update_time', 12, 19, 19, 19, 0, 1), ('Check_time', 12, 19, 19, 19, 0, 1), ('Collation', 253, 17, 64, 64, 0, 1), ('Checksum', 8, 0, 21, 21, 0, 1), ('Create_options', 253, 0, 255, 255, 0, 1), ('Comment', 253, 0, 80, 80, 0, 0))
"""
