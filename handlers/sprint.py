import json

from Jira import APIError

def formatTransitions(transitions):
	return [{
		'id': transition['id'],
		'name': transition['name'],
		'status': {
			'name': transition['to']['name'],
			'category': transition['to']['statusCategory']['key'],
		}
	} for transition in transitions]

def processIssue(jira, issue):
	parent = None
	for link in issue['fields']['issuelinks']:
		if link['type']['name'] == 'Structure' and 'inwardIssue' in link:
			parent = link['inwardIssue']['id']
			break
	else:
		if 'epic' in issue['fields']:
			# For some reason this is an int instead of a string
			parent = str(issue['fields']['epic']['id'])

	return {
		'id': issue['id'],
		'key': issue['key'],
		'type': {
			'name': issue['fields']['issuetype']['name'],
			'icon': issue['fields']['issuetype']['iconUrl'],
		},
		'summary': issue['fields']['summary'],
		'status': {
			'name': issue['fields']['status']['name'],
			'category': issue['fields']['status']['statusCategory']['key'],
		},
		'assignee': {
			'username': issue['fields']['assignee']['name'],
			'avatar': jira.getLargestAvatar(issue['fields']['assignee']['avatarUrls']),
		} if issue['fields']['assignee'] else None,
		'estimate': issue['fields']['timetracking'].get('originalEstimateSeconds', None),
		'remaining': issue['fields']['timetracking'].get('remainingEstimateSeconds', None),
		'parent': parent,
		'transitions': formatTransitions(issue['transitions']),
	}

def getParentIssues(jira, issues, existingIds = None):
	if existingIds is None:
		existingIds = {issue['id'] for issue in issues}
	for issue in issues:
		if issue['parent'] is not None and issue['parent'] not in existingIds:
			parent = processIssue(jira, jira.get(f"agile/issue/{issue['parent']}", expand = 'transitions'))
			yield parent
			existingIds.add(parent['id'])
			yield from getParentIssues(jira, [parent], existingIds)

@get('sprint/(?P<id>[0-9]+)', view = 'sprint', statics = 'third-party/animate')
def sprint(handler, id):
	handler.title(False)
	return {} # Loaded via AJAX

@get('sprint/(?P<id>[0-9]+)/data')
def sprintData(handler, id):
	handler.wrappers = False

	try:
		data = list(handler.jira.get(f"agile/sprint/{id}/issue", expand = 'transitions'))
		issues = list(processIssue(handler.jira, issue) for issue in data)
		# Get parents that aren't in the sprint
		parents = list(getParentIssues(handler.jira, issues))

		# Every issue has the sprint info as one of the fields
		if data:
			sprint = data[0]['fields']['sprint']
		else:
			sprint = handler.jira.get(f"agile/sprint/{id}")

		members = {issue['assignee']['username']: issue['assignee'] for issue in issues + parents if issue['assignee']}.values()
		members = sorted(members, key = lambda user: user['username'])

		rtn = {'sprint_name': sprint['name'], 'members': members, 'issues': issues, 'parents': parents}
		print(json.dumps(rtn))
		handler.contentType = 'application/json'
	except APIError as e:
		print(str(e))
		handler.responseCode = 400

@post('sprint/(?P<id>[0-9]+)/update')
def sprintUpdate(handler, id, p_issue, p_transition = None, p_assignee = None, p_remaining = None, p_estimate = None, p_returnUserInfo = False):
	handler.wrappers = False
	p_issue = int(p_issue)

	try:
		if p_transition is not None:
			handler.jira.post(f"api/issue/{p_issue}/transitions", data = {'transition': {'id': str(p_transition)}})
			data = handler.jira.get(f"api/issue/{p_issue}/transitions")
			print(json.dumps(formatTransitions(data['transitions'])))
			handler.contentType = 'application/json'
		elif p_assignee is not None:
			handler.jira.put(f"api/issue/{p_issue}", data = {'fields': {'assignee': {'name': str(p_assignee)}}})
			if p_returnUserInfo:
				data = handler.jira.get("api/user", username = p_assignee)
				print(json.dumps({
					'username': data['name'],
					'avatar': handler.jira.getLargestAvatar(data['avatarUrls'])
				}))
				handler.contentType = 'application/json'
		elif p_remaining is not None or p_estimate is not None:
			tracking = {}
			if p_remaining is not None: tracking['remainingEstimate'] = p_remaining
			if p_estimate is not None: tracking['originalEstimate'] = p_estimate
			handler.jira.put(f"api/issue/{p_issue}", data = {'fields': {'timetracking': tracking}})
		else:
			handler.responseCode = 400
			print("No update")
	except BaseException as e:
		handler.responseCode = 400
		print(str(e))
