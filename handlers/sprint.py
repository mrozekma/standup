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
	}

def getParentIssues(jira, issues, existingIds = None):
	if existingIds is None:
		existingIds = {issue['id'] for issue in issues}
	for issue in issues:
		if issue['parent'] is not None and issue['parent'] not in existingIds:
			parent = processIssue(jira, jira.get(f"agile/issue/{issue['parent']}"))
			yield parent
			existingIds.add(parent['id'])
			yield from getParentIssues(jira, [parent], existingIds)

@get('sprint/(?P<id>[0-9]+)', view = 'sprint')
def sprint(handler, id):
	data = list(handler.jira.get(f"agile/sprint/{id}/issue"))
	issues = list(processIssue(handler.jira, issue) for issue in data)
	# Get parents that aren't in the sprint
	parents = list(getParentIssues(handler.jira, issues))

	# Every issue has the sprint info as one of the fields
	if data:
		sprint = data[0]['fields']['sprint']
	else:
		sprint = handler.jira.get(f"agile/sprint/{id}")

	handler.title(sprint['name'])
	return {'issues': issues, 'parents': parents}
