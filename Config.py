from configparser import ConfigParser
import os
from pathlib import Path

FILENAME = 'config'

entries = set()

def entry(section, name, type = str):
	entries.add((section, name))
	def get(self):
		return type(self.parser[section][name])
	def set(self, v):
		if section not in self.parser:
			self.parser[section] = {}
		self.parser[section][name] = str(v)
	return property(get, set)

class Config:
	localBindPort = entry('local', 'port', int)
	localUrl = entry('local', 'url')
	jiraUrl = entry('jira', 'url')
	consumerKey = entry('jira', 'consumer_key')
	sharedSecret = entry('jira', 'shared_secret')
	privateKey = entry('jira', 'private_key', Path)

	def __init__(self):
		self.parser = ConfigParser()

	def load(self, filename = FILENAME):
		if not os.path.exists(filename):
			raise FileNotFoundError("Configuration file not found")
		if filename not in self.parser.read(filename):
			raise SyntaxError("Malformed configuration file (failed to parse)")
		try:
			for section, name in entries:
				self.parser[section][name]
		except KeyError:
			raise RuntimeError("Malformed configuration file (missing keys)")

	def save(self, filename = FILENAME):
		with open(filename, 'w') as f:
			self.parser.write(f)

# This is pretty hacky; setup.py needs access to Config but is the only module where the config not existing isn't an error
import __main__
if os.path.basename(__main__.__file__) != 'setup.py':
	config = Config()
	config.load()
