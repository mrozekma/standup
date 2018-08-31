from bleach import clean
from os.path import isfile
from pathlib import Path
import re
import sys

from Log import console
from wrappers import header, footer

from rorn.HTTPHandler import HTTPHandler as ParentHandler
from rorn.ResponseWriter import ResponseWriter
from rorn.utils import done

TITLE = 'Standup'

def ensureList(l):
	return l if isinstance(l, list) else [l]

class HTTPHandler(ParentHandler):
	def __init__(self, request, address, server):
		self.wrappers = True
		self.wrapperData = {'jsOnReady': [], 'view': None}
		self.localData = {}
		ParentHandler.__init__(self, request, address, server)

	def log_message(self, fmt, *args):
		console('rorn', "%s - %s", self.address_string(), fmt % args)

	def invokeHandler(self, handler, query):
		if 'name' in handler and handler['name'] == 'static':
			self.wrappers = False
			# self.log = False

		if (not self.session['user']) and ('allowGuest' not in handler or not handler['allowGuest']):
			print("<su-login></su-login>")
			return

		return ParentHandler.invokeHandler(self, handler, query)

	def preprocessViewData(self, data):
		data = data or {}
		data['user'] = self.session['user']
		return data

	def requestDone(self):
		if self.wrappers:
			types = ['less', 'css', 'js']
			includes = {type: [] for type in types}
			handler = getattr(self, 'handler', None)

			if handler and 'statics' in handler:
				for key in ensureList(handler['statics']):
					for type in types:
						if isfile(f"static/{key}.{type}"):
							includes[type].append(f"/static/{key}.{type}")

			if handler and 'view' in handler:
				includes['js'].append(f"/views/{handler['view']}.js")
				includes['css'].append(f"/views/{handler['view']}.css")

			with ResponseWriter(storageType = bytes) as writer:
				components = getattr(self, 'viewComponents', [])
				data = self.preprocessViewData(getattr(self, 'viewData', {}))

				header(self, includes, components)
				sys.stdout.write(self.response)
				footer(self, data)
				self.response = writer.done()

	def title(self, title, path = None):
		if title is None:
			self.pageTitle = TITLE
			self.pageSubtitle = ''
		else:
			self.pageSubtitle = title
			self.pageTitle = f"{self.pageSubtitle} - {TITLE}"

	def jsOnReady(self, js):
		self.wrapperData['jsOnReady'].append(js)

	def die(self, title, text = None):
		if text is None:
			title, text = '', title
		print(f"""<su-callout type="danger" title="{title}">{clean(text)}</su-callout>""")
		done()

from handlers import *
