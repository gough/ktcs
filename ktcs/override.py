from functools import wraps
from flask import g, flash, url_for, request, redirect

def login_required(func):
	@wraps(func)
	def decorated_view(*args, **kwargs):
		if request.method == 'POST':
			return func(*args, **kwargs)
		
		try:
			if not g.identity.user.is_authenticated:
				flash('Please login to access this page.', 'info')
				return redirect(url_for('login', next=request.endpoint))
			return func(*args, **kwargs)
		except AttributeError:
			flash('Please login to access this page.', 'info')
			return redirect(url_for('login', next=request.endpoint))
	return decorated_view

def logout_required(func):
	@wraps(func)
	def decorated_view(*args, **kwargs):
		if request.method == 'POST':
			return func(*args, **kwargs)

		try:
			if g.identity.user.is_authenticated:
				flash('Please logout to access this page.', 'info')
				return redirect(url_for('home'))
			return func(*args, **kwargs)
		except AttributeError:
			return func(*args, **kwargs)
	return decorated_view