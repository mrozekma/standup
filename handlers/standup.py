import json
from textwrap import dedent

from Config import config
from Jira import apiHandler

from rorn import code
from rorn.utils import redirect

@get('', view = 'home')
def home(handler):
	return {} # Loaded via AJAX

@get('data')
@apiHandler
def projectData(handler, recent = False):
	return handler.jira.getProjects(recent = recent) if handler.session['user'] else []

@get('code.css', allowGuest = True)
def codeCSS(handler):
	handler.wrappers = False
	handler.contentType = 'text/css'
	code.showCodeCSS()

	# Override a few things
	print(dedent("""
	.code_default { border-spacing: 0; }
	.code_default.light { color: #000; }
	.selected_line { background-color: #aa0000aa; }
	"""))

@get('jira.png', allowGuest = True)
def icon(handler):
	redirect(f"{config.jiraUrl}/images/64jira.png")
