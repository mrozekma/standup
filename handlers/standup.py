from textwrap import dedent

from rorn import code

from Jira import Jira

@get('', view = 'home')
def home(handler):
	jira = Jira.fromHandler(handler)
	return {'projects': jira.getProjects()}

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

# For testing
@get('api/(?P<route>.+)')
def api(handler, route, **kw):
	jira = Jira.fromHandler(handler)
	data = jira.get(route, **kw)

	import json, types
	if isinstance(data, types.GeneratorType):
		print("<i>Paginated result</i>")
		data = list(data)
	print(f"<pre>{json.dumps(data, indent = 4)}</pre>")
