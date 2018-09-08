from configparser import ConfigParser
import os
from pathlib import Path
import secrets
import socket
import subprocess

from Config import Config

def ask(question, default = None, convFn = None):
	if default is not None:
		question += f" [{default}]"
		if convFn is None and isinstance(default, int):
			convFn = int
	question += ': '
	while True:
		answer = input(question)
		if answer:
			if convFn:
				try:
					return convFn(answer)
				except:
					if convFn is int:
						print("Invalid answer -- must be an integer")
					else:
						print("Invalid answer")
			else:
				return answer
		elif default is not None:
			try:
				# default is a function that returns the value
				return default()
			except TypeError:
				# default is the value itself
				return default
		else:
			print("Answer required -- no default available")
		print()

class RandDefault:
	def __str__(self):
		return 'random'

	def __call__(self):
		return secrets.token_urlsafe(12) # Results in 16 characters
rand = RandDefault()

os.chdir(os.path.dirname(os.path.abspath(__file__)))
config = Config()

try:
	config.load()
	if ask("Overwrite existing configuration", 'n') not in ('y', 'Y', 'yes'):
		exit(0)
except SystemExit:
	raise
except:
	pass

config.localBindPort = ask("HTTP port", 80)

dfltUrl = f"http://{socket.getfqdn()}"
if config.localBindPort != 80:
	dfltUrl += f":{config.localBindPort}"

config.localUrl = ask("Local URL", dfltUrl)
config.jiraUrl = ask("Jira URL")
config.consumerKey = ask("OAuth consumer key", rand)
config.sharedSecret = ask("OAuth shared secret", rand)

dir = Path(ask("OAuth directory", 'oauth'))
if dir.is_dir():
	if not all((dir / filename).exists() for filename in ('priv.pem', 'pub.pem')):
		raise FileExistsError(f"'{dir}' exists but does not have OpenSSL artifacts")
else:
	dir.mkdir(parents = True, exist_ok = False)
	cmds = [
		'openssl genrsa -out priv.pem 1024',
		'openssl req -newkey rsa:1024 -x509 -key priv.pem -out pub.cer -days 365',
		'openssl pkcs8 -topk8 -nocrypt -in priv.pem -out priv.pkcs8',
		'openssl x509 -pubkey -noout -in pub.cer -out pub.pem',
	]
	for cmd in cmds:
		subprocess.call(cmd, shell = True, cwd = dir)

config.privateKey = dir / 'priv.pem'

config.save()
pubKey = dir / 'pub.pem'
print(f"""
Configuration complete. Follow these instructions to create an Application Link so Standup can connect to Jira:

* Go to {config.jiraUrl}/plugins/servlet/applinks/listApplicationLinks
* Enter URL {config.localUrl} and click "Create new link"
* Leave the URL unchanged in the warning dialog and click "Continue"
* Set the fields as follows and click "Continue":

        Application Name: Standup
        Application Type: Generic Application
   Service Provider Name: standup
            Consumer key: {config.consumerKey}
           Shared secret: {config.sharedSecret}
       Request Token URL: {config.localUrl}
        Access token URL: {config.localUrl}
           Authorize URL: {config.localUrl}
    Create incoming link: Yes
    
* Set the fields as follows and click "Continue":

            Consumer Key: {config.consumerKey}
           Consumer Name: Standup
              Public Key: (contents of {pubKey}, follows)
  
    {pubKey.read_text().replace(chr(10), chr(10) + ' ' * 4)}
""") # chr(10) is used because '\n' can't appear in an f-string
