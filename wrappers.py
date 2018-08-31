import json
from pathlib import Path
import re
import sys

def header(handler, includes, components):
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

	# Vue
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

	if handler.wrapperData['jsOnReady']:
		print("<script type=\"text/javascript\">")
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
	print("<div id=\"vue-root\">")
	if handler.session['user']:
		user = handler.session['user']
		print(f"<su-header username=\"{user['username']}\" user-avatar=\"{user['avatar']}\"></su-header>")
	else:
		print("<su-header></su-header>")

	print("<div class=\"content\">")
	print(f"<h1>{handler.pageTitle}</h1>")

def footer(handler, data = None):
	print("</div>")
	print("</div>")
	print("<script type=\"text/javascript\">")
	print(f"new Vue({{ el: '#vue-root', data: function() {{ return {json.dumps(data or {})}; }}}});")
	print("</script>")
	print("</body>")
	print("</html>")
