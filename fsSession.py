#!/usr/bin/python

import Cookie
import hashlib
import os
import time

Version= 1.2

"""
	1.2
		Removed need for including fsSettings
		
	1.1
		Added hashPassword function
	
	1.0
		Initial Version
"""

def hashPassword(password):
	return hashlib.md5(password).hexdigest()

def sessionAuthenticationCode(hashedPassword):
	return hashPassword(os.environ["HTTP_USER_AGENT"]+hashedPassword+os.environ["REMOTE_ADDR"])

def formatCookies(cookies):
	cookie= Cookie.SimpleCookie()
	for requestedCookie in cookies:
		cookie[requestedCookie["cookie"]]= requestedCookie["value"]
		if requestedCookie.has_key("path") and requestedCookie["path"]:
			cookie[requestedCookie["cookie"]]['path']= requestedCookie["path"]
		else:
			cookie[requestedCookie["cookie"]]['path']= "/"
		expirationTime= 2 * 365 * 24 * 60 * 60 # defaults to 2 years
		if requestedCookie.has_key("expiration") and requestedCookie["expiration"]:
			if requestedCookie["expiration"] == "session":
				expirationTime= None
			else:
				expirationTime= int(requestedCookie["expiration"])
		if expirationTime:
			expirationValue= time.strftime('%a %d %b %Y %H:%M:%S GMT', time.gmtime(time.time() + expirationTime))
			cookie[requestedCookie["cookie"]]['expires']= expirationValue
	return str(cookie)

def setCookies(templateData, username, usernameExpiration, userCookie, hashedPassword, passwordExpiration, authenticationCookie, cookieKey):
	cookies= [
		{"cookie": userCookie,
			"value": username,
			"expiration": userExpiration},
		{"cookie": authenticationCookie,
			"value": sessionAuthenticationCode(hashedPassword),
			"expiration": passwordExpiration}
	]
	if username or hashedPassword:
		templateData[cookieKey]= templateData[cookieKey] + formatCookies(cookies) + "\n"

def setAuthenticationCookies(templateData, username, hashedPassword, userCookie, authenticationCookie, cookieKey):
	twoYears= 2*(60*60*24*365)
	setCookies(templateData, username, twoYears, userCookie, hashedPassword, twoYears, authenticationCookie, cookieKey)

def deauthenticate(templateData, authenticationCookie, cookieKey):
	oneSecond= 1
	setCookies(templateData, None, None, None, "expired", None, authenticationCookie, cookieKey)
	
def authenticate(templateData, cookieData, requestData, userInfo, passwordParamKey, userCookie, authenticationCookie, cookieKey, usernameFromRequest,
					dbUsersUsername, dbUsersPassword, userTemplateDataPrefix):
	authenticated= False
	username= userInfo[dbUsersUsername]
	for key in userInfo:
		if key != dbUsersPassword:
			templateData["%s%s"%(userTemplateDataPrefix, key)]= userInfo[key]
	password= requestData.getfirst(passwordParamKey)
	if password:
		hashedPassword= hashPassword(password)
		if password == userInfo[dbUsersPassword] or password == hashedPassword:
			setAuthenticationCookies(templateData, username, hashedPassword, userCookie, authenticationCookie, cookieKey)
			authenticated= True
	elif cookieData.has_key(authenticationCookie) and not usernameFromRequest:
		authenticationCode= cookieData[authenticationCookie].value
		if authenticationCode != "expired" and authenticationCode != sessionAuthenticationCode("expired"):
			hashedPassword= hashPassword(userInfo[dbUsersPassword])
			expectedAuthentication= sessionAuthenticationCode(hashedPassword)
			authenticated= expectedAuthentication == authenticationCode
			if not authenticated:
				expectedUnhashedAuthentication= sessionAuthenticationCode(userInfo[dbUsersPassword])
				authenticated= expectedUnhashedAuthentication == authenticationCode
			if authenticated:
				setAuthenticationCookies(templateData, username, hashedPassword, userCookie, authenticationCookie, cookieKey)
	return authenticated
