from textwrap import dedent

from rorn import code

@get('', view = 'home')
def home(handler):
	return {'projects': handler.jira.getProjects()}

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
	data = handler.jira.get(route, **kw)

	import json, types
	if isinstance(data, types.GeneratorType):
		print("<i>Paginated result</i>")
		data = list(data)
	print(f"<pre>{json.dumps(data, indent = 4)}</pre>")
