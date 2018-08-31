import requests, oauthlib, requests_oauthlib

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
	def __init__(self, code, message = None):
		self.code = code
		self.message = message

	def __str__(self):
		return self.message or f"API request failed, code {self.code}"

class Jira:
	def __init__(self, key, secret, userToken, userSecret):
		self.auth = requests_oauthlib.OAuth1(resource_owner_key = userToken, resource_owner_secret = userSecret, **oauth.commonArgs)

	def get(self, route):
		req = requests.get(
			f"{config['jiraUrl']}/rest/api/2/{route}",
			auth = self.auth,
			headers = {
				'Accept': 'application/json',
			},
		)
		if req.status_code != 200:
			try:
				message = req.json()['message']
			except:
				message = None
			raise APIError(req.status_code, message)
		return req.json()

	@staticmethod
	def fromHandler(handler):
		user = handler.session['user']
		if not user:
			raise RuntimeError("Not logged in")
		return Jira(config['consumerKey'], config['sharedSecret'], user['oauth']['oauth_token'], user['oauth']['oauth_token_secret'])
