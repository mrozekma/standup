from datetime import datetime, timedelta
import re
import requests, oauthlib, requests_oauthlib

from Log import console

'''
URL: http://localhost:8081/
Create new link
Continue

Application Name: Standup
Application Type: Generic Application
Service Provider Name: a
Consumer Key: b
Shared secret: c
Request Token URL: d
Access token URL: e
Authorize URL: f
Create incoming link: yes
Continue

Consumer Key: b
Consumer Name: g
Public Key: oauth/pub.pem
'''

#TODO Move to a config file
config = {
	'localUrl': 'http://localhost:8081',
	'jiraUrl': 'http://localhost:2990/jira',
	'consumerKey': 'b',
	'sharedSecret': 'c',
}

oauthUrl = f"{config['jiraUrl']}/plugins/servlet/oauth/%s"

class OAuth:
	def __init__(self):
		with open('oauth/priv.pem', 'r') as f:
			privateKey = f.read()
		self.commonArgs = {
			'client_key': config['consumerKey'],
			'client_secret': config['sharedSecret'],
			'rsa_key': privateKey,
			'signature_method': oauthlib.oauth1.SIGNATURE_RSA,
		}

	def authorize(self):
		s = requests_oauthlib.OAuth1Session(callback_uri = f"{config['localUrl']}/login-finish", **self.commonArgs)
		s.fetch_request_token(oauthUrl % 'request-token')
		return s.authorization_url(oauthUrl % 'authorize')

	def exchange(self, oauth_token, oauth_verifier):
		s = requests_oauthlib.OAuth1Session(resource_owner_key = oauth_token, verifier = oauth_verifier, **self.commonArgs)
		return s.fetch_access_token(oauthUrl % 'access-token')

oauth = OAuth()

class APIError(BaseException):
	def __init__(self, code, message = None, url = None):
		self.code = code
		self.message = message
		self.url = url

	def __str__(self):
		return (self.message or f"API request failed, code {self.code}") + (f" ({self.url})" if self.url else '')

apiVersions = {
	'api': '2',
	'auth': '1',
	'agile': '1.0',
}

class Jira:
	def __init__(self, key, secret, userToken, userSecret, cache = None):
		self.auth = requests_oauthlib.OAuth1(resource_owner_key = userToken, resource_owner_secret = userSecret, **oauth.commonArgs)
		self.cache = cache

	def get(self, route, *, cacheRead = True, cacheWrite = True, **params):
		if self.cache is None:
			cacheRead = cacheWrite = False

		if cacheRead:
			rtn = self.cache[(route, params)]
			if rtn:
				return rtn

		console('jira', f"API request: {route}")
		namespace, rest = route.split('/', 1)
		try:
			version = apiVersions[namespace]
		except KeyError:
			raise ValueError(f"Unknown API namespace: {namespace}")
		url = f"{config['jiraUrl']}/rest/{namespace}/{version}/{rest}"
		req = requests.get(
			url,
			params = params,
			auth = self.auth,
			headers = {
				'Accept': 'application/json',
			},
		)
		if req.status_code != 200:
			try:
				message = req.json()['message']
			except:
				try:
					message = req.json()['errorMessages'][0]
				except:
					message = None
			console('jira api', f"{req}: {req.text}")
			raise APIError(req.status_code, message, url)

		rtn = req.json()
		if 'startAt' in rtn:
			# Result is paginated
			if 'startAt' in params:
				# This is one page of a paginated request being called from paginate(), just return it
				return rtn
			else:
				# This is the beginning of a paginated request
				return self.paginate(route, params, rtn, cacheWrite)
		else:
			# Result is not paginated, just return the whole thing
			if cacheWrite:
				self.cache[(route, params)] = rtn
			return rtn

	def paginate(self, route, params, firstPage, cacheWrite):
		# First, determine the key the actual values are stored at.
		# It's supposed to be 'values'
		if 'values' in firstPage:
			key = 'values'
		else:
			# ...but sometimes it isn't
			candidates = set(firstPage.keys()) - {'expand', 'startAt', 'maxResults', 'total'}
			if len(candidates) == 1:
				key = next(iter(candidates))
			else:
				raise RuntimeError(f"Unable to determine pagination key (possibilities: {', '.join(candidates)})")

		wholeList = list(firstPage[key]) # Copy
		yield from firstPage[key]

		page = firstPage
		# Sometimes 'total' isn't in the result, even though Atlassian claims it will be. I think this happens when Jira finishes caching a result and it becomes no longer paginated even though it started that way
		while len(page[key]) > 0 and ('total' not in page or len(wholeList) < page['total']):
			page = self.get(route, startAt = page['startAt'] + len(page[key]), **params)
			wholeList += page[key]
			yield from page[key]

		# Cache the entire result
		if cacheWrite:
			self.cache[(route, params)] = wholeList

	def getProjects(self):
		convertDate = lambda ts: self.parseTimestamp(ts).strftime('%d %b').lstrip('0')

		return [{
			'key': project['key'],
			'name': project['name'],
			'avatar': self.getLargestAvatar(project['avatarUrls']),
			'boards': [{
				'id': board['id'],
				'name': board['name'],
				'sprints': [{
					'id': sprint['id'],
					'name': sprint['name'],
					'startDate': convertDate(sprint['startDate']),
					'endDate': convertDate(sprint['endDate']),
				} for sprint in self.get(f"agile/board/{board['id']}/sprint")],
			} for board in self.get('agile/board', projectKeyOrId = project['key'], type = 'scrum')],
		} for project in self.get('api/project', expand = 'lead')]

	def getLargestAvatar(self, avatars):
		pat = re.compile('([0-9]+)x([0-9]+)')
		avatar, size = None, 0
		for dimensions, url in avatars.items():
			m = pat.fullmatch(dimensions)
			if m:
				thisSize = int(m.group(1)) * int(m.group(2))
				if thisSize > size:
					avatar, size = url, thisSize
		return avatar

	def parseTimestamp(self, ts):
		# Python expects +HHMM but Jira emits +HH:MM
		ts = re.sub('([+-][0-9]{2}):([0-9]{2})$', '\g<1>\g<2>', ts)
		return datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S.%f%z')

	@staticmethod
	def fromHandler(handler):
		user = handler.session['user']
		if not user:
			raise RuntimeError("Not logged in")
		return Jira(config['consumerKey'], config['sharedSecret'], user['oauth']['oauth_token'], user['oauth']['oauth_token_secret'], handler.session['jiraCache'])

CACHE_LENGTH = timedelta(hours = 1)
class Cache:
	def __init__(self):
		self.entries = {}

	def formatKey(self, k):
		if isinstance(k, tuple):
			return tuple(self.formatKey(k2) for k2 in k)
		elif isinstance(k, dict):
			return frozenset(k.items())
		else:
			return k

	def __getitem__(self, k):
		k = self.formatKey(k)
		if k not in self.entries:
			return
		entry = self.entries[k]
		if datetime.now() > entry['expiration']:
			del self.entries[k]
			return
		return entry['value']

	def __setitem__(self, k, v):
		k = self.formatKey(k)
		self.entries[k] = {
			'expiration': datetime.now() + CACHE_LENGTH,
			'value': v,
		}

	def clear(self):
		self.entries.clear()
