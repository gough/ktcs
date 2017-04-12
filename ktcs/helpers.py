from urllib.parse import urlparse, urljoin
from flask import request, url_for
from datetime import datetime, timedelta
import random
import string

def round_time(dt, delta=30):
	return dt + (datetime.min - dt) % timedelta(minutes=delta)

def date(delta=0):
	today = datetime.today() + timedelta(days=delta)
	return today

def time_pickup():
	return '00:00:00'

def time_dropoff():
	return '00:00:00'

def times():
	times = []
	for i in range(24):
		for j in [0, 30]:
			time = datetime.strptime(str(i) + ':' + str(j), '%H:%M')
			times.append((time.strftime('%H:%M:00'), time.strftime('%I:%M %p')))
	return times

def format_users(results, blank=False):
	if blank: users = [('0', '')]
	else: users = []
	
	for result in results:
		users.append((result.id, '{} {} ({})'.format(result.first_name, result.last_name, result.email)))
	return users

def format_cars(results, blank=False):
	if blank: cars = [('0', '')]
	else: cars = []

	for result in results:
		cars.append((result.id, '{} {} {}'.format(result.year, result.make, result.model)))
	return cars

def format_locations(results, blank=False):
	if blank: locations = [('0', '')]
	else: locations = []

	for result in results:
		locations.append((result.id, '{}, {}, {}'.format(result.address, result.city, result.province)))
	return locations

def format_rentals(results, blank=False):
	if blank: rentals = [('0', '')]
	else: rentals = []

	for result in results:
		rentals.append((result.id, '{} {} {}, {} to {}'.format(result.car.year, result.car.make, result.car.model, result.pickup, result.dropoff)))
	return rentals

def provinces(abbr=None):
	provinces = [('', ''),
				('AB', 'Alberta'),
				('BC', 'British Columbia'),
				('MB', 'Manitoba'),
				('NB', 'New Brunswick'),
				('NL', 'Newfoundland and Labrador'),
				('NS', 'Nova Scotia'),
				('NT', 'Northwest Territories'),
				('NU', 'Nunavut'),
				('ON', 'Ontario'),
				('PE', 'Prince Edward Island'),
				('QC', 'Quebec'),
				('SK', 'Saskatchewan'),
				('YT', 'Yukon')]
	if abbr:
		provinces = dict(provinces)
		return provinces[abbr]
	else:
		return provinces

def countries(abbr=None):
	countries = [('CA', 'Canada')]
	if abbr:
		countries = dict(countries)
		return countries[abbr]
	else:
		return countries

def is_safe_url(target):
	ref_url = urlparse(request.host_url)
	test_url = urlparse(urljoin(request.host_url, target))
	return test_url.scheme in ('http', 'https') and \
		   ref_url.netloc == test_url.netloc

def queries():
	queries =	[('5000', '5000 kilometres or more since last maintenance'),
				('highest', 'highest number of rentals'),
				('lowest', 'lowest number of rentals'),
				('damaged', 'damaged or not running status')]

	return queries

def statuses():
	statuses =	[('', ''),
				('normal', 'Running'),
				('damaged', 'Damaged'),
				('not-running', 'Not running')]

	return statuses

def ratings():
	ratings = [('0', ''),
			('1', '1'),
			('2', '2'),
			('3', '3'),
			('4', '4')]

	return ratings

def maintenances():
	maintenances = [('', ''),
					('scheduled', 'Scheduled'),
					('repair', 'Repair'),
					('body-work', 'Body work')]

	return maintenances

def can_pick_up(rental):
	if datetime.now() >= rental.pickup:
		if rental.pickup_actual == None:
			return True

	return False

def can_drop_off(rental):
	if datetime.now() >= rental.pickup:
		if rental.pickup_actual != None and rental.dropoff_actual == None:
			return True

	return False

def dropped_off(rental):
	if rental.pickup_actual != None and rental.dropoff_actual != None:
		return True

	return False

def access_code(length):
	return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

