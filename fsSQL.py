#!/usr/bin/python -B

try:
	import sqlite3
	sqlite3_available= True
except:
	sqlite3_available= False
try:
	import MySQLdb
	mysql_available= True
except:
	mysql_available= False

class Sqlite3:
	"""Connection to a sqlite3 database file"""
	def __init__(self, path):
		if not sqlite3_available:
			raise SyntaxError("sqlite3 not available")
		self.__path= path
		self.__connection= sqlite3.connect(self.__path)
	def cursor(self):
		return self.__connection.cursor()
	def type(self):
		return "sqlite3"
	def commit(self):
		self.__connection.commit()

class MySQL:
	"""Connection to a sqlite3 database file"""
	def __init__(self, host, port, user, password, database):
		if not mysql_available:
			raise SyntaxError("MySQL not available")
		self.__host= host
		self.__port= port
		self.__user= user
		self.__password= password
		self.__database= database
		self.__connection= MySQLdb.Connect(
								host= self.__host,
								port= self.__port,
								user= self.__user,
								passwd= self.__password,
								db= self.__database
							)
	def cursor(self):
		return self.__connection.cursor()
	def type(self):
		return "mysql"
	def commit(self):
		self.__connection.commit()
