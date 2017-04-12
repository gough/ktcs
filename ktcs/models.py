from flask_security import UserMixin, RoleMixin

from ktcs import db

roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.user_id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.role_id')))

class Role(db.Model, RoleMixin):
	id = db.Column('role_id', db.Integer(), primary_key=True)
	name = db.Column(db.String(80), unique=True)
	description = db.Column(db.String(255))

class User(db.Model, UserMixin):
	id = db.Column('user_id', db.Integer(), primary_key=True)
	email = db.Column(db.String(255), unique=True)
	password = db.Column(db.String(255))
	active = db.Column(db.Boolean())
	roles = db.relationship('Role', secondary=roles_users,
							backref=db.backref('users', lazy='dynamic'))

	# details
	first_name = db.Column(db.String(255))
	last_name = db.Column(db.String(255))
	date_of_birth = db.Column(db.Date())
	license = db.Column(db.String(255))
	license_province = db.Column(db.String(2))
	address = db.Column(db.String(255))
	address2 = db.Column(db.String(255))
	city = db.Column(db.String(255))
	province = db.Column(db.String(2))
	postal_code = db.Column(db.String(6))
	country = db.Column(db.String(2))
	primary_phone = db.Column(db.String(255))
	other_phone = db.Column(db.String(255))

class Car(db.Model):
	id = db.Column('car_id', db.Integer(), primary_key=True)
	make = db.Column(db.String(255))
	model = db.Column(db.String(255))
	year = db.Column(db.String(4))
	vin = db.Column(db.String(255), unique=True)
	location_id = db.Column(db.Integer(), db.ForeignKey('location.location_id'))
	location = db.relationship('Location')
	rate = db.Column(db.Integer())

	def __init__(self, make, model, year, vin, location_id, rate):
		self.make = make
		self.model = model
		self.year = year
		self.vin = vin
		self.location_id = location_id
		self.rate = rate
	
	def __repr__(self):
		return '<Car {}>'.format(str(id))

class Location(db.Model):
	id = db.Column('location_id', db.Integer(), primary_key=True)
	address = db.Column(db.String(255))
	city = db.Column(db.String(255))
	province = db.Column(db.String(255))
	postal_code = db.Column(db.String(6))
	country = db.Column(db.String(255))
	spaces = db.Column(db.Integer())

	def __init__(self, address, city, province, postal_code, country, spaces):
		self.address = address
		self.city = city
		self.province = province
		self.postal_code = postal_code
		self.country = country
		self.spaces = spaces

	def __repr__(self):
		return '<Location {}>'.format(str(id))

class Rental(db.Model):
	id = db.Column('rental_id', db.Integer(), primary_key=True)
	user_id = db.Column(db.Integer(), db.ForeignKey('user.user_id'))
	user = db.relationship('User')
	car_id = db.Column(db.Integer(), db.ForeignKey('car.car_id'))
	car = db.relationship('Car')
	location_id = db.Column(db.Integer(), db.ForeignKey('location.location_id'))
	location = db.relationship('Location')
	pickup = db.Column(db.String(255))
	dropoff = db.Column(db.String(255))
	pickup_actual = db.Column(db.String(255))
	dropoff_actual = db.Column(db.String(255))
	pickup_odometer = db.Column(db.Integer())
	dropoff_odometer = db.Column(db.Integer())
	pickup_status = db.Column(db.String(255))
	dropoff_status = db.Column(db.String(255))
	code = db.Column(db.String(255))

	def __init__(self, user_id, car_id, location_id, pickup, dropoff, code):
		self.user_id = user_id
		self.car_id = car_id
		self.location_id = location_id
		self.pickup = pickup
		self.dropoff = dropoff
		self.code = code
	
	def __repr__(self):
		return '<Rental {}>'.format(str(id))

class Comment(db.Model):
	id = db.Column('comment_id', db.Integer(), primary_key=True)
	parent_id = db.Column(db.Integer(), db.ForeignKey('comment.comment_id'))
	parent = db.relationship('Comment')
	user_id = db.Column(db.Integer(), db.ForeignKey('user.user_id'))
	user = db.relationship('User')
	rental_id = db.Column(db.Integer(), db.ForeignKey('rental.rental_id'))
	rental = db.relationship('Rental')
	title = db.Column(db.String(255))
	text = db.Column(db.Text())
	rating = db.Column(db.Integer())

	def __init__(self, parent_id, user_id, rental_id, title, text, rating):
		self.parent_id = parent_id
		self.user_id = user_id
		self.rental_id = rental_id
		self.title = title
		self.text = text
		self.rating = rating
	
	def __repr__(self):
		return '<Comment {}>'.format(str(id))

class Maintenance(db.Model):
	id = db.Column('maintenance_id', db.Integer(), primary_key=True)
	car_id = db.Column(db.Integer(), db.ForeignKey('car.car_id'))
	car = db.relationship('Car')
	date = db.Column(db.String(255))
	odometer = db.Column(db.Integer())
	mtype = db.Column('type', db.Integer())
	description = db.Column(db.String(255))

	def __init__(self, car_id, date, odometer, mtype, description):
		self.car_id = car_id
		self.date = date
		self.odometer = odometer
		self.mtype = mtype
		self.description = description

	def __repr__(self):
		return '<Maintenance {}>'.format(str(id))
