#!/usr/bin/python

import re
import sys
import urllib2
import traceback
import datetime

kKnownNotHandledTags= [
	"channel:admin:generatoragent", "channel:atom10:link", "channel:atom:id",
	"channel:atom:link", "channel:author", "channel:category", "channel:category",
	"channel:channel", "channel:cloud", "channel:copyright",
	"channel:creativecommons:license", "channel:dc:creator", "channel:dc:date",
	"channel:dc:language", "channel:dc:publisher", "channel:dc:rights",
	"channel:dc:subject", "channel:dc:subject", "channel:docs", "channel:email",
	"channel:feed", "channel:feedburner:browserfriendly",
	"channel:feedburner:emailserviceid", "channel:feedburner:feedburnerhostname",
	"channel:feedburner:feedflare", "channel:feedburner:info", "channel:generator",
	"channel:geo:lat", "channel:geo:long", "channel:height", "channel:icon",
	"channel:id", "channel:image", "channel:items", "channel:itunes:author",
	"channel:itunes:category", "channel:itunes:email", "channel:itunes:explicit",
	"channel:itunes:image", "channel:itunes:keywords", "channel:itunes:name",
	"channel:itunes:owner", "channel:itunes:subtitle", "channel:itunes:summary",
	"channel:language", "channel:lastbuilddate", "channel:lj:journal",
	"channel:lj:journalid", "channel:lj:journaltype", "channel:logo",
	"channel:managingeditor", "channel:media:category", "channel:media:copyright",
	"channel:media:credit", "channel:media:description", "channel:media:keywords",
	"channel:media:rating", "channel:media:thumbnail", "channel:name",
	"channel:opensearch:itemsperpage", "channel:opensearch:startindex",
	"channel:opensearch:totalresults", "channel:pubdate", "channel:rdf:li",
	"channel:rdf:rdf", "channel:rdf:seq", "channel:rights", "channel:rss",
	"channel:sy:updatebase", "channel:sy:updatefrequency",
	"channel:sy:updateperiod", "channel:syn:updatebase",
	"channel:syn:updatefrequency", "channel:syn:updateperiod",
	"channel:textinput", "channel:topix:rsslink", "channel:ttl",
	"channel:updated", "channel:uri", "channel:url", "channel:webmaster",
	"channel:width", "item:a", "item:a10:author", "item:a10:name",
	"item:a10:updated", "item:a10:uri", "item:app:edited", "item:atom:updated",
	"item:author", "item:br", "item:comments", "item:created", "item:dc:creator",
	"item:dc:subject", "item:description", "item:div", "item:ece:source",
	"item:em", "item:email", "item:enclosure", "item:ent:cloud", "item:ent:topic",
	"item:feedburner:origenclosurelink", "item:fieldset", "item:font",
	"item:gd:extendedproperty", "item:georss:point", "item:go:thumbnail",
	"item:h3", "item:h4", "item:img", "item:issued", "item:itunes:author",
	"item:itunes:duration", "item:itunes:explicit", "item:itunes:image",
	"item:itunes:keywords", "item:itunes:subtitle", "item:itunes:summary",
	"item:legend", "item:li", "item:lj:poster", "item:lj:posterid",
	"item:lj:reply-count", "item:lj:security", "item:media:content",
	"item:media:credit", "item:media:description", "item:media:text",
	"item:media:thumbnail", "item:media:title", "item:name", "item:p",
	"item:pheedo:origlink", "item:script", "item:slash:comments",
	"item:slash:department", "item:slash:hit_parade", "item:slash:section",
	"item:source", "item:span", "item:strike", "item:strong", "item:thr:total",
	"item:topix:comments", "item:ul", "item:updated", "item:uri", "item:url",
	"item:wfw:comment", "item:wfw:commentrss", "top:id", "top:updated"
]
# http://www.timeanddate.com/library/abbreviations/timezones/
TimeZoneOffsets= {
	'EST': -5,	'EDT': -4,
	'CST': -6,	'CDT': -5,
	'MST': -7,	'MDT': -6,
	'PST': -8,	'PDT': -7,
	'Z': 0,		'GMT': 0,
}
MonthNames= ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
DateFormatPatterns= [
	{
		'pattern': re.compile(r"^([A-Z][a-z][a-z]),\s+([0-9]+)\s+([A-Z][a-z][a-z])\s+([0-9][0-9][0-9][0-9])\s+([0-9][0-9]):([0-9][0-9]):([0-9][0-9])\s+([A-Z]+)$"),
		'order': ['dayname', 'day', 'monthname', 'year', 'hour', 'minute', 'second', 'zonename'],

	},
	{
		'pattern': re.compile(r"^([A-Z][a-z][a-z]),\s+([0-9]+)\s+([A-Z][a-z][a-z])\s+([0-9][0-9][0-9][0-9])\s+([0-9][0-9]):([0-9][0-9]):([0-9][0-9])\s+([+-][0-9][0-9])00$"),
		'order': ['dayname', 'day', 'monthname', 'year', 'hour', 'minute', 'second', 'zoneoffset'],
	},
	{ # 2010-12-17T12:23:57Z, 2011-02-23T13:05:00.003Z
		'pattern': re.compile(r"^([0-9][0-9][0-9][0-9])-([0-9][0-9])-([0-9][0-9])T([0-9][0-9]):([0-9][0-9]):([0-9][0-9.]+)([A-Z]+)$"),
		'order': ['year', 'month', 'day', 'hour', 'minute', 'second', 'zonename'],
	},
	{
		'pattern': re.compile(r"^([0-9][0-9][0-9][0-9])-([0-9][0-9])-([0-9][0-9])T([0-9][0-9]):([0-9][0-9]):([0-9][0-9])([-+][0-9][0-9]):00$"),
		'order': ['year', 'month', 'day', 'hour', 'minute', 'second', 'zoneoffset'],
	},
	{
		'pattern': re.compile(r"^([0-9][0-9][0-9][0-9])-([0-9][0-9])-([0-9][0-9])T([0-9][0-9]):([0-9][0-9]):([0-9][0-9])\.[0-9]+([-+][0-9][0-9]):00$"),
		'order': ['year', 'month', 'day', 'hour', 'minute', 'second', 'zoneoffset'],
	},
	{
		'pattern': re.compile(r"^([A-Z][a-z][a-z]),\s+([0-9]+)\s+([A-Z][a-z][a-z])\s+([0-9][0-9][0-9][0-9])\s+([0-9][0-9]):([0-9][0-9])\s+([A-Z]+)$"),
		'order': ['dayname', 'day', 'monthname', 'year', 'hour', 'minute', 'zonename'],
	},
	{
		'pattern': re.compile(r"^([0-9][0-9])\s+([A-Z][a-z][a-z])\s+([0-9][0-9][0-9][0-9])\s+([0-9][0-9]):([0-9][0-9]):([0-9][0-9])\s+([A-Z]+)$"),
		'order': ['day', 'monthname', 'year', 'hour', 'minute', 'second', 'zonename'],
	},
	{
		'pattern': re.compile(r"^([A-Z][a-z][a-z])\s*,\s+([0-9][0-9])\s+([A-Z][a-z][a-z])\s+([0-9][0-9][0-9][0-9])\s+([0-9][0-9]):([0-9][0-9]):([0-9][0-9])\s+GMT([+-][0-9][0-9]):00$"),
		'order': ['dayname', 'day', 'monthname', 'year', 'hour', 'minute', 'second', 'zoneoffset'],
	},
]
def parseDate(stamp):
	for dateFormat in DateFormatPatterns:
		match= dateFormat['pattern'].match(stamp)
		if match:
			#print "stamp",stamp,"pattern",dateFormat['pattern'].pattern
			fields= {}
			for index in range(0, len(dateFormat['order'])):
				fields[dateFormat['order'][index]]= match.group(index + 1)
			if fields.has_key('monthname') and not fields.has_key('month') and fields['monthname'] in MonthNames:
				fields['month']= MonthNames.index(fields['monthname']) + 1
			if fields.has_key('zonename') and not fields.has_key('zoneoffset') and TimeZoneOffsets.has_key(fields['zonename']):
				fields['zoneoffset']= TimeZoneOffsets[fields['zonename']]
			if not fields.has_key('second'):
				fields['second']= "00"
			if fields.has_key('month') and fields.has_key('zoneoffset'):
				secondsFloat= float(fields['second'])
				seconds= int(secondsFloat)
				microseconds= int((secondsFloat - seconds) * 1000000.0)
				datestamp= datetime.datetime(
								int(fields['year']),
								int(fields['month']),
								int(fields['day']),
								int(fields['hour']),
								int(fields['minute']),
								seconds,
								microseconds
							)
				if int(fields['zoneoffset']) != 0:
					datestamp-= datetime.timedelta(hours=int(fields['zoneoffset']))
				return datestamp
	return stamp

XMLEscapeWords= {
	'quot': '"',
	'apos': "'",
	'amp': "&",
	'lt': "<",
	'gt': ">",
	'nbsp': " ",
	'raquo': ">>",
	'copy': "(C)",
	'laquo': "<<",
	'rsquo': "'",
	'lsquo': "`",
	'mdash': "-",
	'ldquo': '"',
	'rdquo': '"',
	'pound': "#",
	'agrave': "q",
}
EscapePattern= re.compile(r"\&(#?)(x?)([^;]+);")
def unescapeXML(text):
	output= ""
	lastStart= 0
	for escape in EscapePattern.finditer(text):
		output+= text[lastStart:escape.start(0)]
		if escape.group(1):
			if escape.group(2):
				base= 16
			else:
				base= 10
			if int(escape.group(3), base) < 256:
				output+= chr(int(escape.group(3), base))
				lastStart= escape.end()
		elif XMLEscapeWords.has_key(escape.group(3)):
			output+= XMLEscapeWords[escape.group(3)]
			lastStart= escape.end()
		else:
			print "WHAT?: "+escape.group(0)
	return output + text[lastStart:]

propertyBegin= re.compile(r"\s+([^ \t=]+)\s*=\s*(\S)")
nonWhitespace= re.compile(r"(\S+)$")
def parseTagProperties(tag):
	#print "parseTagProperties(",tag,")"
	endTag= tag[-1] == '/'
	if endTag:
		tag= tag[:-1]
	if not endTag:
		endTag= tag[0] == '/'
		if endTag:
			tag= tag[1:]
	properties= {'_': tag.strip(), '_end_': endTag}
	if tag.strip().startswith("!--") and tag.strip().endswith("--"):
		return properties
	lastStart= 0
	while True:
		propertyStart= propertyBegin.search(tag, lastStart)
		if not propertyStart:
			break
		if propertyStart.start(0) != lastStart and lastStart == 0:
			properties['_']= tag[0:propertyStart.start(0)] # extract tag name
		name= propertyStart.group(1)
		if propertyStart.group(2) == '"' or propertyStart.group(2) == "'":
			end= tag.find(propertyStart.group(2), propertyStart.end(2))
			properties[name]= tag[propertyStart.end(2):end]
			lastStart= end + 1
		else:
			print "::"+tag
			print ":::"+str(propertyStart.start(2))
			value= nonWhitespace.match(tag, propertyStart.start(2))
			print ":::"+name
			print ":::"+str(value)
			properties[name]= value.group(1)
			lastStart= value.end(0)
	return properties

def findNextTag(contents, offset= 0):
	openTagPosition= 0
	cdataPosition= 0
	preceeding= ""
	while True:
		openTagPosition= contents.find('<', offset)
		cdataPosition= contents.find('<![CDATA[', offset)
		if openTagPosition < 0:
			openTagPosition= len(contents)
		if cdataPosition < 0:
			cdataPosition= len(contents)
		if openTagPosition < cdataPosition:
			closeTagPosition= contents.find('>', openTagPosition)
			if closeTagPosition < 0:
				raise SyntaxError("Unmatched open tag at position "+str(openTagPosition)+"\n"+contents)
			preceeding+= unescapeXML(contents[offset:openTagPosition])
			tag= contents[openTagPosition + 1:closeTagPosition].lower()
			return (preceeding.strip(), tag, closeTagPosition + 1)
		if cdataPosition != len(contents):
			cdataEndPosition= contents.find(']]>', cdataPosition)
			if cdataEndPosition < 0:
				raise SyntaxError("Unmatched cdata at position "+str(openTagPosition)+"\n"+contents)
			preceeding+= contents[cdataPosition + 9:cdataEndPosition]
			offset= cdataEndPosition + 3
		else:
			break
	return ((preceeding + contents[offset:]).strip(), None, -1)

channelTags= ['title', 'description', 'link', 'subtitle', 'modified', 'tagline']
itemTags= ['title', 'category', 'link', 'description', 'dc:date', 'pubdate', 'published', 'guid', 'id', 'content:encoded', 'content', 'feedburner:origlink', 'summary', 'modified']
def rssContentsToDict(contents):
	unhandledTags= []
	results= {}
	state= None
	offset= 0
	lastItem= None
	while offset >= 0:
		(preceeding, tag, nextOffset)= findNextTag(contents, offset)
		#print "tag",tag
		if tag:
			properties= parseTagProperties(tag)
			#print "properties",properties
		if None == tag:
			pass
		elif None == state:
			if properties['_'] == 'channel' and not properties['_end_']:
				state= 'channel'
			elif properties['_'] == 'title' and not properties['_end_']:
				state= 'channel'
				lastItem= {'title': preceeding}
			elif "top:"+properties['_'] not in unhandledTags and properties['_end_']:
				unhandledTags.append("top:"+properties['_'])
		elif 'channel' == state:
			if properties['_'] == 'link' and properties['_end_'] and properties.has_key('href'):
				if properties.has_key('rel'):
					name= properties['_']+":"+properties['rel']
				else:
					name= properties['_']
				results[name]= properties['href']
			elif properties['_'] == 'item' and not properties['_end_']:
				state= 'item'
			elif properties['_'] == 'entry' and not properties['_end_']:
				state= 'item'
			elif properties['_'] in channelTags and properties['_end_']:
				results[properties['_']]= preceeding
			elif "channel:"+properties['_'] not in unhandledTags and properties['_end_']:
				unhandledTags.append("channel:"+properties['_'])
		elif 'item' == state:
			if None == lastItem:
				lastItem= {}
				if not results.has_key('items'):
					results['items']= [lastItem]
				else:
					results['items'].append(lastItem)
			if properties['_'] == 'link' and properties['_end_'] and properties.has_key('href'):
				if properties.has_key('rel'):
					name= properties['_']+":"+properties['rel']
				else:
					name= properties['_']
				lastItem[name]= properties['href']
			elif properties['_'] == 'category' and properties['_end_'] and properties.has_key('term'):
				if lastItem.has_key('category'):
					lastItem['category']+=", "+properties['term']
				else:
					lastItem['category']=properties['term']
			elif (properties['_'] == 'item' or properties['_'] == 'entry') and properties['_end_']:
				lastItem= None
				state= 'channel'
			elif properties['_'] in itemTags and properties['_end_']:
				lastItem[properties['_']]= preceeding
			elif "item:"+properties['_'] not in unhandledTags and properties['_end_']:
				unhandledTags.append("item:"+properties['_'])
		offset= nextOffset
	return (results, unhandledTags)

def standardizeRss(rss):
	missingStandardTags= []
	standard= {'items': []}
	standard['title']= rss['title']
	if rss.has_key('description'):
		standard['description']= rss['description']
	elif rss.has_key('subtitle'):
		standard['description']= rss['subtitle']
	elif rss.has_key('tagline'):
		standard['description']= rss['tagline']
	elif 'feed:description' not in missingStandardTags:
		missingStandardTags.append('feed:description')
	if rss.has_key('link'):
		standard['link']= rss['link']
	elif rss.has_key('link:alternate'):
		standard['link']= rss['link:alternate']
	elif 'feed:link' not in missingStandardTags:
		missingStandardTags.append('feed:link')
	if not rss.has_key('items'):
		return (standard, missingStandardTags)
	for item in rss['items']:
		fixed= {'title': item['title']}
		if item.has_key('feedburner:origlink'):
			fixed['link']= item['feedburner:origlink']
		elif item.has_key('link:alternate'):
			fixed['link']= item['link:alternate']
		else:
			fixed['link']= item['link']
		if item.has_key('content:encoded'):
			fixed['description']= item['content:encoded']
		elif item.has_key('content'):
			fixed['description']= item['content']
		elif item.has_key('summary'):
			fixed['description']= item['summary']
		else:
			fixed['description']= item['description']
		if item.has_key('published'):
			fixed['published']= item['published']
		elif item.has_key('pubdate'):
			fixed['published']= item['pubdate']
		elif item.has_key('dc:date'):
			fixed['published']= item['dc:date']
		elif item.has_key('modified'):
			fixed['published']= item['modified']
		elif 'item:published' not in missingStandardTags:
			missingStandardTags.append('item:published')
		if fixed.has_key('published'):
			stamp= parseDate(fixed['published'])
			if stamp == fixed['published']:
				print "UNABLE TO PARSE TIME: "+fixed['published']
			fixed['published']= stamp
		if item.has_key('category'):
			fixed['category']= item['category']
		else:
			fixed['category']= ""
		standard['items'].append(fixed)
		if item.has_key('guid'):
			fixed['id']= item['guid']
		elif item.has_key('id'):
			fixed['id']= item['id']
		else:
			fixed['id']= fixed['link']
	return (standard, missingStandardTags)

def read(url):
	contents= urllib2.urlopen(url).read()
	rawRSS= rssContentsToDict(contents)
	return standardizeRss(rawRSS[0])

if __name__ == "__main__":
	feeds= []
	for url in sys.argv[1:]:
		try:
			#print url
			contents= urllib2.urlopen(url).read()
			#print contents
			rawRSS= rssContentsToDict(contents)
			unhandledUnknown= []
			for tag in rawRSS[1]:
				if tag not in kKnownNotHandledTags:
					unhandledUnknown.append(tag)
			if unhandledUnknown:
				print "Unhandled/Unknown tags: ",unhandledUnknown,url
			rss= standardizeRss(rawRSS[0])
			if rss[1]:
				print "Missing standard tags: ",rss[1],url
			#print rss[0]
			feeds.append(rss[0])
		except KeyboardInterrupt:
			break
		except:
			exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
			traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback, limit=5, file=sys.stdout)
			print url
	for feed in feeds:
		if feed.has_key('link'):
			siteName= "<a href='%s'>%s</a>"%(feed['link'], feed['title'])
		else:
			siteName= feed['title']
		if feed.has_key('description'):
			description= feed['description']
		else:
			description= ""
		print "<hr>\n<h2>%s</h2><br>\n<i>%s</i><br>\n<br><center><table width=80%%>\n"%(siteName, description)
		for item in feed['items']:
			if item.has_key('published'):
				if isinstance(item['published'], datetime.datetime):
					time= item['published'].ctime()
				else:
					time= item['published']
			else:
				time= "[No Time Specified]"
			print "<tr><td><hr>\n<h3><a href='%s'>%s</a></h3><br>\n<i>%s</i><br>\n<br>\n%s<br></td></tr>\n"%(item['link'], item['title'], time, item['description'])
		print "</table>\n"


