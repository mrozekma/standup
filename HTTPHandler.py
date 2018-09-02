from bleach import clean
from os.path import isfile
import sys

from Jira import Jira, APIError
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
		user = self.session['user']
		if user:
			self.jira = Jira.fromHandler(self)
			try:
				user['jiraProfile'] = self.jira.get('api/myself', cacheRead = False)
			except APIError as e:
				if e.code == 401:
					# OAuth token is expired
					user = None
					del self.session['user']

		if 'name' in handler and handler['name'] == 'static':
			self.wrappers = False
			# self.log = False

		if user:
			if self.session['jiraCache']:
				# Clear Jira cache on hard refresh
				if 'view' in handler and self.headers.get('Cache-Control', None) == 'no-cache':
					self.session['jiraCache'].clear()
			else:
				from Jira import Cache
				self.session['jiraCache'] = Cache()
		elif 'allowGuest' not in handler or not handler['allowGuest']:
			print("<su-login></su-login>")
			return

		ParentHandler.invokeHandler(self, handler, query)

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
				includes['less'].append(f"/views/{handler['view']}.less")

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
