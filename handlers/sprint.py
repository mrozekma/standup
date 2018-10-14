import json
from datetime import datetime, timedelta

import lxml.html

from Config import config
from Jira import APIError, apiHandler

def formatTransitions(transitions):
	return [{
		'id': transition['id'],
		'name': transition['name'],
		'status': {
			'name': transition['to']['name'],
			'category': transition['to']['statusCategory']['key'],
		}
	} for transition in transitions]

def processJiraHtml(html):
	if not html:
		return html

	configBase = config.jiraUrl
	try:
		start = configBase.index('://') + 3
	except ValueError:
		start = 0
	try:
		configBase = configBase[:configBase.index('/', start)]
	except ValueError:
		pass

	# Rendered emoticons use relative URLs for some reason
	root = lxml.html.fromstring(html)
	for el in root.iter('img'):
		if 'src' in el.attrib:
			el.attrib['src'] = configBase + el.attrib['src']
	return lxml.html.tostring(root).decode('utf8')

def processIssue(jira, issue):
	parent = None
	for link in issue['fields']['issuelinks']:
		if link['type']['name'] == 'Structure' and 'inwardIssue' in link:
			parent = link['inwardIssue']['id']
			break
	else:
		for field in ('parent', 'epic'):
			if field in issue['fields']:
				# For some reason this is an int instead of a string
				parent = str(issue['fields'][field]['id'])

	return {
		'id': issue['id'],
		'key': issue['key'],
		'description': processJiraHtml(issue['renderedFields']['description']),
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
		'tracking': {
			'estimate': issue['fields']['timetracking'].get('originalEstimateSeconds', None),
			'remaining': issue['fields']['timetracking'].get('remainingEstimateSeconds', None),
			'logged': issue['fields']['timetracking'].get('timeSpentSeconds', None),
		} if 'timetracking' in issue['fields'] else None,
		'parent': parent,
		'transitions': formatTransitions(issue['transitions']),
		'comments': [{
			'id': comment['id'],
			'author': {
				'username': comment['author']['name'],
				'avatar': jira.getLargestAvatar(comment['author']['avatarUrls']),
			},
			'body': processJiraHtml(comment['body']),
		} for comment in (issue['renderedFields']['comment']['comments'] if 'comment' in issue['renderedFields'] else [])],
	}

def getParentIssues(jira, issues, existingIds = None):
	if existingIds is None:
		existingIds = {issue['id'] for issue in issues}
	parentIds = {issue['parent'] for issue in issues if issue['parent'] is not None and issue['parent'] not in existingIds}
	if not parentIds:
		return []
	data = jira.get('api/search', jql = ' or '.join(f"id={id}" for id in parentIds), expand = 'transitions,renderedFields')
	parents = list(processIssue(jira, issue) for issue in data)
	existingIds |= parentIds
	return parents + getParentIssues(jira, parents, existingIds)

def countDays(fromdate, todate):
	# https://stackoverflow.com/a/3615984/309308
	daygenerator = (fromdate + timedelta(x + 1) for x in range((todate - fromdate).days))
	return sum(1 for day in daygenerator if day.weekday() < 5)

@get('sprint/(?P<id>[0-9]+)', view = 'sprint', statics = 'third-party/animate')
def sprint(handler, id):
	handler.title(False)
	return {
		'sprintId': id,
		# Rest loaded via AJAX
	}

@get('sprint/(?P<id>[0-9]+)/data')
@apiHandler
def sprintData(handler, id):
	data = list(handler.jira.get(f"agile/sprint/{id}/issue", expand = 'transitions,renderedFields'))
	issues = list(processIssue(handler.jira, issue) for issue in data)
	# Get parents that aren't in the sprint
	parents = list(getParentIssues(handler.jira, issues))

	# Every issue has the sprint info as one of the fields (unless the sprint is inactive)
	try:
		sprint = data[0]['fields']['sprint']
	except:
		sprint = handler.jira.get(f"agile/sprint/{id}")

	start, end = handler.jira.parseTimestamp(sprint['startDate']), handler.jira.parseTimestamp(sprint['endDate'])
	today = datetime.now(start.tzinfo) + timedelta(days = 29 - 14)
	sprintLen = countDays(start, end) + 1
	curDay = 0 if today < start else countDays(start, today) + 1

	members = {issue['assignee']['username']: issue['assignee'] for issue in issues + parents if issue['assignee']}.values()
	members = sorted(members, key = lambda user: user['username'])

	return {
		'sprint_name': sprint['name'],
		'sprint_day': curDay,
		'sprint_len': sprintLen,
		'board_id': sprint['originBoardId'],
		'members': members,
		'issues': issues,
		'parents': parents
	}

@post('sprint/(?P<id>[0-9]+)/update')
def sprintUpdate(handler, id, p_issue, p_transition = None, p_assignee = None, p_remaining = None, p_estimate = None, p_logged = None, p_returnUserInfo = False):
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
		elif p_remaining is not None: # remaining, estimate, and logged are all sent together; unset values are empty strings
			tracking = {}
			if p_remaining:
				tracking['remainingEstimate'] = p_remaining
			if p_estimate:
				tracking['originalEstimate'] = p_estimate
			if tracking:
				handler.jira.put(f"api/issue/{p_issue}", data = {'fields': {'timetracking': tracking}})

			if p_logged:
				handler.jira.post(f"api/issue/{p_issue}/worklog", adjustEstimate = 'leave', data = {'timeSpent': p_logged})
		else:
			handler.responseCode = 400
			print("No update")
	except BaseException as e:
		handler.responseCode = 400
		print(str(e))
