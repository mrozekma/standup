import json
from textwrap import dedent

from Config import config
from Jira import APIError

from rorn import code

@get('', view = 'home')
def home(handler):
	return {'recent_projects': handler.jira.getProjects(recent = True)}

@get('data')
def projectData(handler):
	handler.wrappers = False

	try:
		print(json.dumps({'projects': handler.jira.getProjects()}))
		handler.contentType = 'application/json'
	except APIError as e:
		print(str(e))
		handler.responseCode = 400

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

@get('dyn.css', allowGuest = True)
def dynCSS(handler):
	handler.wrappers = False
	handler.contentType = 'text/css'
	print(dedent(f"""
	a.jira, button.jira {{
		padding-left: 20px;
		background: url({config.jiraUrl}/images/64jira.png) 2px 4px/16px no-repeat;
	}}
	"""))