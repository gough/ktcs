from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Email, Length, Optional, NoneOf, NumberRange
from wtforms.fields.html5 import DateField, EmailField, IntegerField, DateTimeField

from .helpers import *
from .models import Location

class LoginForm(FlaskForm):
	email = EmailField('Email', validators=[
		DataRequired(message="Please enter your email."),
		Email(message="Your email is not valid.")])
	password = PasswordField('Password', validators=[DataRequired(message="Please enter your password.")])
	remember_me = BooleanField('Remember me', default=True, validators=[Optional()])

class SignupForm(FlaskForm):
	# login information
	email = EmailField('Email',
		validators=[
			DataRequired(message="Please enter your email."),
			Email(message="Your email is not valid.")])
	password = PasswordField('Password',
		description="Your password must be at least 8 characters long.",
		validators=[
			DataRequired(message="Please enter your password."),
			Length(min=8, message="Your password must be at least 8 characters long."),
			EqualTo('password_repeat', message="Your passwords do not match.")])
	password_repeat = PasswordField('Repeat',
		validators=[DataRequired()])

	# personal details
	first_name = StringField('First Name',
		description="Alphanumeric characters only please.",
		validators=[DataRequired(message="Please enter your first and last name.")])
	last_name = StringField('Last Name',
		validators=[DataRequired()])
	date_of_birth = DateField('Date of Birth',
		validators=[DataRequired(message="Please enter your date of birth.")])
	
	# drivers license
	license = StringField('License Number',
		description="Your full drivers license number. Please include all characters.",
		validators=[DataRequired(message="Please enter your drivers license number.")])
	license_province = SelectField('Issuing Province',
		description="The province where your drivers license was issued. Usually the province you currently reside in.",
		choices=provinces(),
		validators=[DataRequired(message="Please choose an issuing province.")])

	# contact information
	address = StringField('Address',
		validators=[DataRequired(message="Please enter your address.")])
	address2 = StringField('Address 2',
		validators=[Optional()])
	city = StringField('City',
		validators=[DataRequired(message="Please enter your city.")])
	province = SelectField('Province',
		choices=provinces(),
		validators=[DataRequired(message="Please choose a province.")])
	postal_code = StringField('Postal Code',
		validators=[
			DataRequired(message="Please enter your postal code."),
			Length(min=6, max=7, message="Please enter a valid postal code.")])
	country = SelectField('Country',
		description="We're only in Canada at the moment.",
		choices=countries(),
		validators=[DataRequired(message="Please enter your country.")])
	primary_phone = StringField('Primary Phone',
		validators=[DataRequired(message="Please enter your primary phone.")])
	other_phone = StringField('Other Phone',
		validators=[Optional()])

class CarForm(FlaskForm):
	make = StringField('Make',
		validators=[DataRequired(message="Please enter the make.")])
	model = StringField('Model',
		validators=[DataRequired(message="Please enter the model.")])
	year = IntegerField('Year',
		validators=[
			DataRequired(message="Please enter the year."),
			NumberRange(min=1900, max=2100, message="Please enter a valid year.")])
	vin = StringField('VIN',
		validators=[DataRequired(message="Please enter the VIN.")])
	location_id = SelectField('Location',
		validators=[DataRequired()],
		coerce=int)
	rate = IntegerField('Daily Rate',
		validators=[
			DataRequired(message="Please enter a daily rate."),
			NumberRange(min=0, message="Daily rate must be between greater than 0.")])

class CarDeleteForm(FlaskForm):
	confirm = BooleanField('Confirm',
		description="I really want to delete this car.",
		validators=[DataRequired(message="Please confirm deletion of car.")])

class AvailabilityForm(FlaskForm):
	location_id = SelectField('Location',
		validators=[DataRequired()],
		coerce=int)

class QueriesForm(FlaskForm):
	queries = SelectField('Queries',
		validators=[DataRequired()],
		choices=queries())

class LocationForm(FlaskForm):
	address = StringField('Address',
		validators=[DataRequired(message="Please enter an address.")])
	city = StringField('City',
		validators=[DataRequired(message="Please enter a city.")])
	province = SelectField('Province',
		choices=provinces(),
		validators=[DataRequired(message="Please choose a province.")])
	postal_code = StringField('Postal Code',
		validators=[
			DataRequired(message="Please enter a postal code."),
			Length(min=6, max=7, message="Please enter a valid postal code.")])
	country = SelectField('Country',
		choices=countries(),
		validators=[DataRequired(message="Please enter a country.")])
	spaces = IntegerField('Spaces',
		validators=[
			DataRequired(message="Please enter the amount of spaces."),
			NumberRange(min=1, message="Amount of spaces must be greater then 0.")])

class LocationsDeleteForm(FlaskForm):
	confirm = BooleanField('Confirm',
		description="I really want to delete this location.",
		validators=[DataRequired(message="Please confirm deletion of location.")])

class ReservationsForm(FlaskForm):
	car_id = SelectField('Car',
		validators=[DataRequired(message="Please choose a car.")],
		coerce=int)
	location_id = SelectField('Location',
		validators=[DataRequired(message="Please choose a location.")],
		coerce=int)
	pickup_date = DateField('Pick-up',
		description="Currently only day rentals are permitted. Drop-off required by end of day.",
		validators=[DataRequired(message="Please enter a pick-up date and time.")])
	pickup_time = SelectField('Pick-up',
		#validators=[DataRequired()],
		choices=times(),
		default=time_pickup(),
		render_kw={'disabled':''})
	dropoff_date = DateField('Drop-off',
		#validators=[DataRequired(message="Please enter a drop-off date and time.")],
		render_kw={'disabled':''})
	dropoff_time = SelectField('Drop-off',
		#validators=[DataRequired()],
		choices=times(),
		default=time_dropoff(),
		render_kw={'disabled':''})

class PickupForm(FlaskForm):
	odometer = IntegerField('Odometer',
		validators=[
			DataRequired(message="Please enter the odometer reading."),
			NumberRange(min=1, message="Odometer reading must be greater then 0.")])
	status = SelectField('Status',
		validators=[DataRequired(message="Please select a status.")],
		choices=statuses())
	confirm = BooleanField('Confirm',
		description="I confirm that my answers above are accurate and correct.",
		validators=[DataRequired(message="Please confirm pick-up.")])

class DropoffForm(FlaskForm):
	odometer = IntegerField('Odometer',
		validators=[
			DataRequired(message="Please enter the odometer reading."),
			NumberRange(min=1, message="Odometer reading must be greater then 0.")])
	status = SelectField('Status',
		validators=[DataRequired(message="Please select a status.")],
		choices=statuses())
	confirm = BooleanField('Confirm',
		description="I confirm that my answers above are accurate and correct.",
		validators=[DataRequired(message="Please confirm drop-off.")])

class CommentsForm(FlaskForm):
	rental_id = SelectField('Rental',
		validators=[
			DataRequired(message="Please select a rental."),
			NoneOf(['0'], message="Please select a rental.")],
		coerce=int)
	title = StringField('Title',
		validators=[DataRequired(message="Please enter a review title.")])
	text = TextAreaField('Text',
		validators=[DataRequired(message="Please enter the review text.")])
	rating = SelectField('Rating',
		validators=[
			DataRequired(message="Please select a rating."),
			NoneOf(['0'], message="Please select a rating.")],
		choices=ratings())

class CommentsDeleteForm(FlaskForm):
	confirm = BooleanField('Confirm',
		description="I really want to delete this comment.",
		validators=[DataRequired(message="Please confirm deletion of comment.")])

class CommentsReplyForm(FlaskForm):
	text = TextAreaField('Text',
		validators=[DataRequired(message="Please enter the reply text.")])

class MaintenanceForm(FlaskForm):
	car_id = SelectField('Car',
		validators=[
			DataRequired(message="Please select a car."),
			NoneOf(['0'], message="Please select a car.")],
		coerce=int)
	date = DateField('Date',
		validators=[DataRequired(message="Please enter a date.")])
	odometer = IntegerField('Odometer',
		validators=[
			DataRequired(message="Please enter the odometer reading."),
			NumberRange(min=1, message="Odometer reading must be greater then 0.")])
	mtype = SelectField('Type',
		validators=[
			DataRequired(message="Please select a maintenance type."),
			NoneOf(['0'], message="Please select a maintenance type.")],
		choices=maintenances())
	description = StringField('Description',
		validators=[DataRequired(message="Please enter a description.")])

class MaintenanceDeleteForm(FlaskForm):
	confirm = BooleanField('Confirm',
		description="I really want to delete this maintenance.",
		validators=[DataRequired(message="Please confirm deletion of maintenance.")])

class AdminReservationsForm(ReservationsForm):
	user_id = SelectField('User',
		validators=[DataRequired(message="Please choose a user.")],
		coerce=int)

class ReservationsDeleteForm(FlaskForm):
	confirm = BooleanField('Confirm',
		description="I really want to delete this reservation.",
		validators=[DataRequired(message="Please confirm deletion of reservation.")])

class AvailabilityForm(FlaskForm):
	location_id = SelectField('Location',
		validators=[DataRequired()],
		coerce=int)

class GenerateInvoiceForm(FlaskForm):
	user_id = SelectField('User',
		validators=[DataRequired()],
		coerce=int)

class QuickReserveForm(FlaskForm):
	pickup_date = DateField('pickup_date',
		validators=[DataRequired()],
		default=date())
	pickup_time = SelectField('pickup_time',
		validators=[DataRequired()],
		choices=times(),
		default=time_pickup())
	dropoff_date = DateField('dropoff_date',
		validators=[DataRequired()],
		default=date(1))
	dropoff_time = SelectField('dropoff_time',
		validators=[DataRequired()],
		choices=times(),
		default=time_dropoff())
	location = SelectField('location',
		validators=[DataRequired()])
