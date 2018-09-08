from bleach import clean
import re
from rorn.utils import done, redirect

import requests, requests_oauthlib, oauthlib

from Config import config
from Jira import oauth, Jira

@get('login', allowGuest = True)
def login(handler):
	authURL = oauth.authorize()
	redirect(authURL)

@get('login-finish', allowGuest = True)
def loginFinish(handler, oauth_token, oauth_verifier):
	if oauth_verifier == 'denied':
		print(f"<su-login denied='true'></su-login>")
		done()

	token = oauth.exchange(oauth_token, oauth_verifier)

	jira = Jira(config.consumerKey, config.sharedSecret, token['oauth_token'], token['oauth_token_secret'])
	myself = jira.get('api/myself')

	handler.session['user'] = {
		'username': myself['name'],
		'avatar': jira.getLargestAvatar(myself['avatarUrls']),
		'oauth': token,
	}
	handler.session.remember('user')

	redirect('/')

#TODO Improve
@get('logout')
def logout(handler):
	del handler.session['user']
	redirect('/')
