@get('help', view = 'help', allowGuest = True)
def help(handler):
	handler.title('Help')
	return {}
