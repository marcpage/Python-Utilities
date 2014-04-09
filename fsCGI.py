#!/usr/bin/env python -B

import os
import Cookie
import cgi
import fsTemplate
import time

Version= 1.2

"""
	1.21
		Added setCookie, setScriptURL, cookiesToDict and defaultTemplateData
		
	1.2
		Added addEnvironment and addCookies to cgiToDict
	
	1.1
		Made remap parameter of cgiToDict optional
	
	1.0
		Initial Version
"""

def defaultTemplateData(templateData= None, importList= None, remap= None, env= "__os_environ__", cookies= "__cookies__", scriptURL= "__script_url__", requestURL= "__request_url__", request= "__request__", fieldStorage= None):
	if not importList:
		importList= []
	if not remap:
		remap= {}
	if not templateData:
		templateData= {}
	if not fieldStorage and (len(importList) > 0 or request):
		fieldStorage= cgi.FieldStorage()
	dictionaries= [cookiesToDict(), cgiToDict(fieldStorage), os.environ]
	for dictionary in dictionaries:
		for key in dictionary:
			if key in importList:
				useKey= key
				if remap.has_key(key):
					useKey= remap[key]
				templateData[useKey]= dictionary[key]
	if env:
		templateData[env]= fsTemplate.dictionaryToTemplateList(dictionaries[2])
	if request:
		templateData[request]= fsTemplate.dictionaryToTemplateList(dictionaries[1])
	if cookies:
		templateData[cookies]= fsTemplate.dictionaryToTemplateList(dictionaries[0])
	if scriptURL:
		setScriptURL(templateData, scriptURL)
	if requestURL:
		setRequestURL(templateData, requestURL)
	return templateData

def setCookie(templateData, cookieName, value, expirationFromNowInSeconds= None, path="/", cookiesName= "COOKIES"):
	cookie= Cookie.SimpleCookie()
	cookie[cookieName]= value
	cookie[cookieName]["path"]= path
	if expirationFromNowInSeconds:
		cookie[cookieName]["expires"]= time.strftime('%a %d %b %Y %H:%M:%S GMT', time.gmtime(time.time() + expirationFromNowInSeconds))
	templateData[cookiesName]+= str(cookie)+"\n"

def setRequestURL(dictionary, key):
	if os.environ.has_key("SCRIPT_URI"):
		if os.environ.has_key("REQUEST_URI") and os.environ["REQUEST_URI"].find("?") >= 0:
			dictionary[key]= os.environ["SCRIPT_URI"]+os.environ["REQUEST_URI"][os.environ["REQUEST_URI"].find("?"):]
		else:
			dictionary[key]= os.environ["SCRIPT_URI"]
	
def setScriptURL(dictionary, key):
	if os.environ.has_key("SCRIPT_URI"):
		if os.environ.has_key("PATH_INFO"):
			dictionary[key]= os.environ["SCRIPT_URI"][:os.environ["SCRIPT_URI"].rfind(os.environ["PATH_INFO"])]
		else:
			dictionary[key]= os.environ["SCRIPT_URI"]

def cgiToDict(formData, remap= None, addEnvironment= False, addCookies= False):
	results= {}
	if not remap:
		remap= {}
	if addEnvironment:
		for env in os.environ:
			key= env
			if remap.has_key(key):
				key= remap[key]
			results[key]= os.environ[env]
		scriptUrlKey= "__script_url__"
		if remap.has_key(scriptUrlKey):
			scriptUrlKey= remap[scriptUrlKey]
		setScriptURL(results, scriptUrlKey)
	if addCookies:
		cookies= cookiesToDict()
		for cookie in cookies:
			cookieKey= cookie
			if remap.has_key(cookieKey):
				cookieKey= remap[cookieKey]
			results[cookieKey]= cookies[cookie]
	for key in formData:
		result= None
		if formData[key].file:
			pass # ignore files
		elif isinstance(formData[key], list):
			result= []
			for element in formData[key]:
				result.append(element.value)
		else:
			result= formData[key].value
		if result:
			if remap.has_key(key):
				results[remap[key]]= result
			elif not remap:
				results[key]= result
	return results

def cookiesToDict():
	results= {}
	if os.environ.has_key("HTTP_COOKIE"):
		cookies= Cookie.SimpleCookie(os.environ["HTTP_COOKIE"])
		for cookie in cookies:
			results[cookie]= cookies[cookie].value
	return results
