from textwrap import dedent

from rorn import code

@get('', view = 'home')
def home(handler):
	from Jira import Jira
	jira = Jira.fromHandler(handler)
	data = jira.get('myself')
	return {
		'apiTest': data,
	}

	return {}

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
