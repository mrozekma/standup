import bleach
import json
from pathlib import Path
import subprocess
from textwrap import dedent
from xml.sax.saxutils import quoteattr

from Config import config
from Jira import APIError

proc = subprocess.run(['git', 'describe', '--all', '--long', '--abbrev=40', '--dirty'], cwd = Path(__file__).resolve().parent, stdout = subprocess.PIPE)
curHash = proc.stdout.decode('utf8')

def header(handler, includes, view):
	print("<!DOCTYPE html>")
	print("<html>")
	print("<head>")
	print("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">")
	print(f"<title>{handler.pageTitle}</title>")
	print("<link rel=\"shortcut icon\" href=\"/static/images/favicon.ico\">")

	print("<link rel=\"stylesheet\" href=\"/static/third-party/font-awesome/css/font-awesome.min.css\">")
	print("<link rel=\"stylesheet\" type=\"text/css\" href=\"/code.css\">")

	# jQuery
	print("<script src=\"/static/third-party/jquery.min.js\"></script>")
	print("<link rel=\"stylesheet\" href=\"/static/third-party/jquery-ui.css\" />")
	print("<script src=\"/static/third-party/jquery-ui.min.js\"></script>")

	print("<link rel=\"stylesheet\" type=\"text/css\" href=\"/static/third-party/bootstrap.css\">")
	print("<script src=\"/static/third-party/bootstrap.min.js\"></script>")

	# Vue
	components = view['components'] if view else []
	print("<script src=\"/static/third-party/vue/vue.js\"></script>")
	print("<script src=\"/static/third-party/vue/basic.js\"></script>")
	print(f"<script src=\"/components.js?{'&'.join(components)}\"></script>")
	print(f"<link rel=\"stylesheet/less\" type=\"text/css\" href=\"/components.less?{'&'.join(components)}\">")

	for filename in includes['less']:
		print(f"<link rel=\"stylesheet/less\" type=\"text/css\" href=\"{filename}\" />")
	for filename in includes['css']:
		print(f"<link rel=\"stylesheet\" type=\"text/css\" href=\"{filename}\" />")
	for filename in includes['js']:
		print(f"<script src=\"{filename}\" type=\"text/javascript\"></script>")

	print("<script type=\"text/javascript\">")
	localUrl = config.localUrl
	try:
		localUrl = localUrl[localUrl.index('://') + 3:]
	except IndexError:
		pass
	print(f"if(window.location.host != {json.dumps(localUrl)}) {{window.location.host = {json.dumps(localUrl)};}}")
	if handler.wrapperData['jsOnReady']:
		print("$(function() {")
		for js in handler.wrapperData['jsOnReady']:
			print(f"    {js}")
		print("});")
	print("</script>")

	# Less
	print("<link rel=\"stylesheet/less\" type=\"text/css\" href=\"/static/style.less\">")
	print("<script type=\"text/javascript\">")
	print("less = %s;" % json.dumps({'env': 'production', 'async': False, 'dumpLineNumbers': 'comments'}))
	print("</script>")
	print("<script src=\"/static/third-party/less.js\" type=\"text/javascript\"></script>")

	print("</head>")
	print("<body>")
	print("<div id=\"vue-root\" v-cloak>")

	projects = None
	if handler.session['user']:
		try:
			projects = handler.jira.getProjects(recent = True)
		except APIError:
			pass
	print(f"<su-header :projects={quoteattr(json.dumps(projects))}></su-header>")

	print("<div class=\"content\">")
	if handler.pageSubtitle is not False:
		print(f"<h1>{handler.pageSubtitle or handler.pageTitle}</h1>")

def footer(handler, data, view):
	print("</div>")
	print(f"""<div class="footer-hash">{bleach.clean(curHash, [])}</div>""")
	print("</div>")

	globalData = {
		'jiraUrl': config.jiraUrl,
	}
	if handler.session['user']:
		user = handler.session['user']
		globalData['user'] = {
			'username': user['username'],
			'avatar': user['avatar'],
		}

	print(dedent(f"""
	<script type="text/javascript">
	Vue.config.productionTip = false;
	Vue.prototype.$global = {json.dumps(globalData)};
	(function() {{
		var viewInfo = {view.get('script-vue', '{}') if view else '{}'};
		viewInfo.el = '#vue-root';
		var backendData = {json.dumps(data or {})};
		if(!viewInfo.data) {{
			viewInfo.data = backendData;
		}} else {{
			Object.assign(viewInfo.data, backendData);
		}}
		new Vue(viewInfo);
	}})();
	</script>
	</body>
	</html>
	"""))
