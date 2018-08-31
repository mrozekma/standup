from bleach import clean
import re
from rorn.utils import redirect

import requests, requests_oauthlib, oauthlib

from Jira import config, oauth, Jira

@get('login', allowGuest = True)
def login(handler):
	authURL = oauth.authorize()
	redirect(authURL)

@get('login-finish', allowGuest = True)
def loginFinish(handler, oauth_token, oauth_verifier):
	if oauth_verifier == 'denied':
		handler.die("Login failed", "Jira access denied")

	token = oauth.exchange(oauth_token, oauth_verifier)

	jira = Jira(config['consumerKey'], config['sharedSecret'], token['oauth_token'], token['oauth_token_secret'])
	myself = jira.get('myself')

	pat = re.compile('([0-9]+)x([0-9]+)')
	avatar, size = None, 0
	for dimensions, url in myself['avatarUrls'].items():
		m = pat.fullmatch(dimensions)
		if m:
			thisSize = int(m.group(1)) * int(m.group(2))
			if thisSize > size:
				avatar, size = url, thisSize

	handler.session['user'] = {
		'username': myself['name'],
		'avatar': avatar,
		'jiraProfile': myself,
		'oauth': token,
	}
	handler.session.remember('user')

	redirect('/')

#TODO Improve
@get('logout')
def logout(handler):
	del handler.session['user']
	redirect('/')
