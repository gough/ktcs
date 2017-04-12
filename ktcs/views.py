from flask import render_template, request, flash, redirect, url_for, abort, session, g
from flask_security.decorators import roles_required
from flask_security.utils import encrypt_password, verify_password, login_user, logout_user
from datetime import datetime, timedelta

from ktcs import app, db, user_datastore

from .forms import *
from .helpers import *
from .models import *
from .override import login_required, logout_required

#@app.before_first_request
def create_user():
	db.create_all()

@app.route('/')
def home():
	form = QuickReserveForm(request.form)
	form.location.choices = format_locations(Location.query.all())
	return render_template('home.html', form=form)

@app.route('/cars/')
def cars():
	cars = Car.query.all()
	return render_template('cars.html', cars=cars)

@app.route('/locations/')
def locations():
	locations = Location.query.all()
	return render_template('locations.html', locations=locations)

@app.route('/login')
@app.route('/login/', methods=['GET', 'POST'])
@logout_required
def login():
	template = 'user/login.html'
	form = LoginForm(request.form)
	if request.method == 'POST':
		if form.validate():
			user = User.query.filter(User.email == form.email.data).first()
			if user:
				if verify_password(form.password.data, user.password):
					login_user(user, remember=form.remember_me.data)
					
					next = request.args.get('next')
					if not is_safe_url(next):
						return abort(400)

					flash('<strong>Success!</strong> You are now logged in.', 'success')
					return redirect(next or url_for('home'))
				else:
					flash('<strong>Error!</strong> Incorrect password. Please try again.', 'danger')
			else:
				flash('<strong>Error!</strong> An account with that email address does not exist.', 'danger')

	return render_template(template, form=form)

@app.route('/logout')
@app.route('/logout/')
@login_required
def logout():
	logout_user()
	flash('<strong>Success!</strong> You have been logged out.', 'success')
	return redirect(url_for('home'))

@app.route('/signup/', methods=['GET', 'POST'])
@logout_required
def signup():
	form = SignupForm(request.form)

	if request.method == 'POST':
		if form.validate():
			user_datastore.create_user(
				email=form.email.data,
				password=encrypt_password(form.password.data),
				first_name=form.first_name.data,
				last_name=form.last_name.data,
				date_of_birth=form.date_of_birth.data,
				license=form.license.data,
				license_province=form.license_province.data,
				address=form.address.data,
				address2=form.address2.data,
				city=form.city.data,
				province=form.province.data,
				postal_code=form.postal_code.data.replace(' ', ''),
				country=form.country.data,
				primary_phone=form.primary_phone.data,
				other_phone=form.other_phone.data)
			db.session.commit()
			flash('<strong>Success!</strong> You have successfully signed up. Please login using the account you created.', 'success')
			return redirect(url_for('login'))
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	return render_template('user/signup.html', form=form)

@app.route('/profile/')
@login_required
def profile():
	return render_template('user/profile.html')

@app.route('/rental_history/')
@login_required
def rental_history():
	past_rentals = Rental.query.filter(Rental.user_id == g.identity.user.id).filter(db.or_(Rental.pickup < (datetime.now() - timedelta(days=1)), Rental.dropoff_actual != None)).order_by(Rental.pickup.desc()).all()
	return render_template('user/rental_history.html', past_rentals=past_rentals)

@app.route('/reservations/')
@login_required
def reservations():
	rentals = Rental.query.filter(Rental.user_id == g.identity.user.id).filter(db.and_(Rental.pickup >= (datetime.now() - timedelta(days=1)), Rental.dropoff_actual == None)).order_by(Rental.pickup.asc()).order_by(Rental.id.asc()).all()
	past_rentals = Rental.query.filter(Rental.user_id == g.identity.user.id).filter(db.or_(Rental.pickup < (datetime.now() - timedelta(days=1)), Rental.dropoff_actual != None)).order_by(Rental.pickup.desc()).all()
	return render_template('user/reservations.html', rentals=rentals, past_rentals=past_rentals)

@app.route('/reservations/new/', methods=['GET', 'POST'])
@login_required
def reservations_new():
	form = ReservationsForm()
	form.car_id.choices = format_cars(Car.query.all(), True)
	form.location_id.choices = format_locations(Location.query.all(), True)
	if request.method == 'POST':
		if form.validate():
			pickup = datetime.strptime('{} {}'.format(form.pickup_date.data, form.pickup_time.data), '%Y-%m-%d %H:%M:%S')
			dropoff = datetime.strptime('{} {}'.format(form.pickup_date.data, '23:59:59'), '%Y-%m-%d %H:%M:%S')
			#dropoff = datetime.strptime('{} {}'.format(form.dropoff_date.data, form.dropoff_time.data), '%Y-%m-%d %H:%M:%S')
			if pickup >= round_time(datetime.now(), -1440):
				if pickup < dropoff:
					query1 = Rental.query.filter(Rental.car_id == form.car_id.data).filter(pickup <= Rental.pickup, db.and_(dropoff <= Rental.dropoff, dropoff >= Rental.pickup)).all()
					query2 = Rental.query.filter(Rental.car_id == form.car_id.data).filter(db.and_(pickup >= Rental.pickup, pickup <= Rental.dropoff), dropoff >= Rental.dropoff).all()
					query3 = Rental.query.filter(Rental.car_id == form.car_id.data).filter(pickup >= Rental.pickup, dropoff <= Rental.dropoff).all()
					query4 = Rental.query.filter(Rental.car_id == form.car_id.data).filter(pickup <= Rental.pickup, dropoff >= Rental.dropoff).all()
					if len(query1 + query2 + query3 + query4) != 0:
						flash('<strong>Error!</strong> The selected car is already reserved during that period.', 'danger')
					else:
						rental = Rental(g.identity.user.id, form.car_id.data, form.location_id.data, pickup, dropoff, access_code(6))
						db.session.add(rental)
						db.session.commit()
						flash('<strong>Success!</strong> Reservation created', 'success')
						return redirect(url_for('reservations'))
				else:
					flash('<strong>Error!</strong> Drop-off time cannot be before pick-up time.', 'danger')
			else:
				flash('<strong>Error!</strong> Pick-up time must not be in the past.', 'danger')
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	return render_template('user/reservations_new.html', form=form)

@app.route('/reservations/<int:id>/pickup/', methods=['GET', 'POST'])
@login_required
def reservations_pickup(id):
	rental = Rental.query.get_or_404(id)
	form = PickupForm()

	if g.identity.user.id != rental.user_id:
		flash('<strong>Error!</strong> You cannot pick-up another user\'s rental.', 'danger')
		return redirect(url_for('reservations'))
	elif datetime.now() > rental.dropoff:
		flash('<strong>Error!</strong> The period for this rental has already passed.', 'danger')
		return redirect(url_for('reservations'))
	elif datetime.now() < rental.pickup:
		flash('<strong>Error!</strong> This rental cannot be picked up until day of rental.', 'danger')
		return redirect(url_for('reservations'))
	elif rental.dropoff_actual != None:
		flash('<strong>Error!</strong> This rental has already been dropped off.', 'danger')
		return redirect(url_for('reservations'))
	elif rental.pickup_actual != None:
		flash('<strong>Error!</strong> This rental has already been picked up.', 'danger')
		return redirect(url_for('reservations'))

	if request.method == 'POST':
		if form.validate():
			last_odometer = Rental.query.filter(Rental.car_id == rental.car_id).filter(Rental.dropoff_actual != None).order_by(Rental.dropoff_actual.desc()).first()
			if last_odometer == None:
				rental.pickup_actual = datetime.now()
				rental.pickup_odometer = form.odometer.data
				rental.pickup_status = form.status.data
				db.session.commit()
				flash('<strong>Success!</strong> Picked up car.', 'success')
				return redirect(url_for('reservations'))
			elif form.odometer.data >= last_odometer.dropoff_odometer:
				rental.pickup_actual = datetime.now()
				rental.pickup_odometer = form.odometer.data
				rental.pickup_status = form.status.data
				db.session.commit()
				flash('<strong>Success!</strong> Picked up car.', 'success')
				return redirect(url_for('reservations'))
			else:
				flash('<strong>Error!</strong> Pick-up odometer reading must be greater than or equal to last drop-off odometer reading.', 'danger')
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	return render_template('user/reservations_pickup.html', rental=rental, form=form)

@app.route('/reservations/<int:id>/dropoff/', methods=['GET', 'POST'])
@login_required
def reservations_dropoff(id):
	rental = Rental.query.get_or_404(id)
	form = DropoffForm()

	if g.identity.user.id != rental.user_id:
		flash('<strong>Error!</strong> You cannot drop-off another user\'s rental.', 'danger')
		return redirect(url_for('reservations'))
	elif rental.pickup_actual == None:
		flash('<strong>Error!</strong> You cannot drop-off a rental until it has been picked up.', 'danger')
		return redirect(url_for('reservations'))
	elif rental.dropoff_actual != None:
		flash('<strong>Error!</strong> This rental has already been dropped off.', 'danger')
		return redirect(url_for('reservations'))

	if request.method == 'POST':
		if form.validate():
			if form.odometer.data >= rental.pickup_odometer:
				rental.dropoff_actual = datetime.now()
				rental.dropoff_odometer = form.odometer.data
				rental.dropoff_status = form.status.data
				db.session.commit()
				flash('<strong>Success!</strong> Dropped off car.', 'success')
				return redirect(url_for('reservations'))
			else:
				flash('<strong>Error!</strong> Drop-off odometer reading must be greater than or equal to pick-up odometer reading.', 'danger')
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	return render_template('user/reservations_dropoff.html', rental=rental, form=form)

@app.route('/reservations/availability')
@login_required
def availability():
	if request.method == 'POST':
		if form.validate():
			pass
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	return render_template('user/reservations_availability.html', form=form)

@app.route('/comments/')
@login_required
def comments():
	comments = Comment.query.filter(Comment.user_id == g.identity.user.id).order_by(Comment.id.desc()).all()
	responses = Comment.query.filter(Comment.user_id == g.identity.user.id, Comment.parent_id != None).order_by(Comment.id.desc()).all()
	return render_template('user/comments.html', comments=comments, responses=responses)

@app.route('/comments/new/', methods=['GET', 'POST'])
@login_required
def comments_new():
	form = CommentsForm()
	form.rental_id.choices = format_rentals(Rental.query.filter(Rental.user_id == g.identity.user.id).filter(Rental.dropoff_actual != None).order_by(Rental.pickup.desc()).all(), True)

	if request.method == 'POST':
		if form.validate():
			comment = Comment(None, g.identity.user.id, form.rental_id.data, form.title.data, form.text.data, form.rating.data)
			db.session.add(comment)
			db.session.commit()
			flash('<strong>Success!</strong> Added comment.', 'success')
			return redirect(url_for('comments'))
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	return render_template('user/comments_new.html', form=form)

@app.route('/comments/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def comments_delete(id):
	form = CommentsDeleteForm()
	comment = Comment.query.get_or_404(id)

	if g.identity.user.id != comment.user_id:
		flash('<strong>Error!</strong> You cannot delete another user\'s comment.', 'danger')
		return redirect(url_for('comments'))

	if request.method == 'POST':
		if form.validate():
			db.session.delete(comment)
			db.session.commit()
			flash('<strong>Success!</strong> Deleted comment.', 'success')
			return redirect(url_for('comments'))
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	return render_template('user/comments_delete.html', form=form)

@app.route('/admin/')
@roles_required('admin')
def admin():
	return render_template('admin/dashboard.html')

@app.route('/admin/cars/')
@roles_required('admin')
def admin_cars():
	cars = Car.query.order_by(Car.id.desc()).all()
	return render_template('admin/cars.html', cars=cars)

@app.route('/admin/cars/add/', methods=['GET', 'POST'])
@roles_required('admin')
def admin_car_add():
	form = CarForm()
	form.location_id.choices = format_locations(Location.query.all(), True)
	if request.method == 'POST':
		if form.validate():
			car = Car(form.make.data, form.model.data, form.year.data, form.vin.data, form.location_id.data, form.rate.data)
			db.session.add(car)
			db.session.commit()
			flash('<strong>Success!</strong> Added car.', 'success')
			return redirect(url_for('admin_cars'))
		else:
			print(form.errors)
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	return render_template('admin/cars_add.html', form=form)

@app.route('/admin/cars/edit/<int:id>', methods=['GET', 'POST'])
@roles_required('admin')
def admin_car_edit(id):
	car = Car.query.get_or_404(id)
	form = CarForm()
	form.location_id.choices = format_locations(Location.query.all())

	if request.method == 'POST':
		if form.validate():
			changed = False
			if form.make.data != car.make:
				car.make = form.make.data
				changed = True
			if form.model.data != car.model:
				car.model = form.model.data
				changed = True
			if str(form.year.data) != car.year:
				car.year = str(form.year.data)
				changed = True
			if form.vin.data != car.vin:
				car.vin = form.vin.data
				changed = True
			if form.location_id.data != car.location_id:
				car.location_id = form.location_id.data
				changed = True
			if form.rate.data != car.rate:
				car.rate = form.rate.data
				changed = True

			if changed:
				db.session.commit()
				flash('<strong>Success!</strong> Updated car.', 'success')
			else: 
				flash('No changes were detected.', 'info')
			return redirect(url_for('admin_cars'))
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	form.make.default = car.make
	form.model.default = car.model
	form.year.default = int(car.year)
	form.vin.default = car.vin
	form.location_id.default = car.location_id
	form.rate.default = car.rate
	form.process()

	return render_template('admin/cars_edit.html', form=form, car=car)

@app.route('/admin/cars/delete/<int:id>', methods=['GET', 'POST'])
@roles_required('admin')
def admin_car_delete(id):
	form = CarDeleteForm()
	car = Car.query.get_or_404(id)
	if request.method == 'POST':
		if form.validate():
			db.session.delete(car)
			db.session.commit()
			flash('<strong>Success!</strong> Deleted car.', 'success')
			return redirect(url_for('admin_cars'))
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	return render_template('admin/cars_delete.html', form=form)

@app.route('/admin/availability/', methods=['GET', 'POST'])
@roles_required('admin')
def admin_availability():
	form = AvailabilityForm()
	form.location_id.choices = format_locations(Location.query.all())
	
	if request.method == 'POST':
		if form.validate():
			cars = Car.query.filter(Car.location_id == form.location_id.data).all()
			upcoming = db.session.query(Rental.car_id, db.func.count().label('count')).group_by(Rental.car_id).all()
			for up in upcoming:
				print(up.car_id, up.count)
			# SELECT car_id, COUNT(*) FROM rental GROUP BY car_id
			return render_template('admin/availability.html', form=form, cars=cars, submitted=True, upcoming=dict(upcoming))
	
	return render_template('admin/availability.html', form=form)

@app.route('/admin/locations/')
@roles_required('admin')
def admin_locations():
	locations = Location.query.order_by(Location.id.desc()).all()
	return render_template('admin/locations.html', locations=locations)

@app.route('/admin/locations/add/', methods=['GET', 'POST'])
@roles_required('admin')
def admin_locations_add():
	form = LocationForm()
	if request.method == 'POST':
		if form.validate():
			location = Location(form.address.data, form.city.data, form.province.data, form.postal_code.data.replace(' ', ''), form.country.data, form.spaces.data)
			db.session.add(location)
			db.session.commit()
			flash('<strong>Success!</strong> Added location.', 'success')
			return redirect(url_for('admin_locations'))
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	return render_template('admin/locations_add.html', form=form)

@app.route('/admin/locations/edit/<int:id>', methods=['GET', 'POST'])
@roles_required('admin')
def admin_locations_edit(id):
	location = Location.query.get_or_404(id)
	form = LocationForm()

	if request.method == 'POST':
		if form.validate():
			changed = False
			if form.address.data != location.address:
				location.address = form.address.data
				changed = True
			if form.city.data != location.city:
				location.city = form.city.data
				changed = True
			if form.province.data != location.province:
				location.province = form.province.data
				changed = True
			if form.postal_code.data.replace(' ', '') != location.postal_code:
				location.postal_code = form.postal_code.data.replace(' ', '')
				changed = True
			if form.country.data != location.country:
				location.country = form.country.data
				changed = True
			if form.spaces.data != location.spaces:
				location.spaces = form.spaces.data
				changed = True

			if changed:
				db.session.commit()
				flash('<strong>Success!</strong> Updated location.', 'success')
			else: 
				flash('No changes were detected.', 'info')
			return redirect(url_for('admin_locations'))
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	form.address.default = location.address
	form.city.default = location.city
	form.province.default = location.province
	form.postal_code.default = location.postal_code[0:3] + ' ' + location.postal_code[3:]
	form.country.default = location.country
	form.spaces.default = location.spaces
	form.process()

	return render_template('admin/locations_edit.html', form=form, location=location)

@app.route('/admin/locations/delete/<int:id>', methods=['GET', 'POST'])
@roles_required('admin')
def admin_locations_delete(id):
	form = LocationsDeleteForm()
	location = Location.query.get_or_404(id)
	if request.method == 'POST':
		if form.validate():
			db.session.delete(location)
			db.session.commit()
			flash('<strong>Success!</strong> Deleted location.', 'success')
			return redirect(url_for('admin_locations'))
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	return render_template('admin/locations_delete.html', form=form)

@app.route('/admin/reservations/')
@roles_required('admin')
def admin_reservations():
	rentals = Rental.query.order_by(Rental.id.desc()).all()
	return render_template('admin/reservations.html', rentals=rentals)

@app.route('/admin/reservations/add/', methods=['GET', 'POST'])
@roles_required('admin')
def admin_reservations_new():
	form = AdminReservationsForm()
	form.user_id.choices = format_users(User.query.all(), True)
	form.car_id.choices = format_cars(Car.query.all(), True)
	form.location_id.choices = format_locations(Location.query.all(), True)
	if request.method == 'POST':
		if form.validate():
			pickup = datetime.strptime('{} {}'.format(form.pickup_date.data, form.pickup_time.data), '%Y-%m-%d %H:%M:%S')
			dropoff = datetime.strptime('{} {}'.format(form.pickup_date.data, '23:59:59'), '%Y-%m-%d %H:%M:%S')
			#dropoff = datetime.strptime('{} {}'.format(form.dropoff_date.data, form.dropoff_time.data), '%Y-%m-%d %H:%M:%S')
			if pickup < dropoff:
				query1 = Rental.query.filter(Rental.car_id == form.car_id.data).filter(pickup <= Rental.pickup, db.and_(dropoff <= Rental.dropoff, dropoff >= Rental.pickup)).all()
				query2 = Rental.query.filter(Rental.car_id == form.car_id.data).filter(db.and_(pickup >= Rental.pickup, pickup <= Rental.dropoff), dropoff >= Rental.dropoff).all()
				query3 = Rental.query.filter(Rental.car_id == form.car_id.data).filter(pickup >= Rental.pickup, dropoff <= Rental.dropoff).all()
				query4 = Rental.query.filter(Rental.car_id == form.car_id.data).filter(pickup <= Rental.pickup, dropoff >= Rental.dropoff).all()
				if len(query1 + query2 + query3 + query4) != 0:
					flash('<strong>Error!</strong> The selected car is already reserved during that period.', 'danger')
				else:
					rental = Rental(form.user_id.data, form.car_id.data, form.location_id.data, pickup, dropoff, access_code)
					db.session.add(rental)
					db.session.commit()
					car = Car.query.get(form.car_id.data)
					flash('<strong>Success!</strong> Reservation created.', 'success')
					return redirect(url_for('admin_reservations'))
			else:
				flash('<strong>Error!</strong> Drop-off time cannot be before pick-up time.', 'danger')
		else:
			print(form.errors)
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	return render_template('admin/reservations_new.html', form=form)

@app.route('/admin/reservations/edit/<int:id>', methods=['GET', 'POST'])
@roles_required('admin')
def admin_reservations_edit(id):
	rental = Rental.query.get_or_404(id)
	form = AdminReservationsForm()
	form.user_id.choices = format_users(User.query.all(), True)
	form.car_id.choices = format_cars(Car.query.all(), True)
	form.location_id.choices = format_locations(Location.query.all(), True)

	if request.method == 'POST':
		if form.validate():
			pickup = datetime.strptime('{} {}'.format(form.pickup_date.data, form.pickup_time.data), '%Y-%m-%d %H:%M:%S')
			dropoff = datetime.strptime('{} {}'.format(form.pickup_date.data, '23:59:59'), '%Y-%m-%d %H:%M:%S')
			#dropoff = datetime.strptime('{} {}'.format(form.dropoff_date.data, form.dropoff_time.data), '%Y-%m-%d %H:%M:%S')

			changed = False
			if form.user_id.data != rental.user_id:
				rental.user_id = form.user_id.data
				changed = True
			if form.car_id.data != rental.car_id:
				rental.car_id = form.car_id.data
				changed = True
			if form.location_id.data != rental.location_id:
				rental.location_id = form.location_id.data
				changed = True
			if pickup != rental.pickup:
				rental.pickup = pickup
				changed = True
			if dropoff != rental.dropoff:
				rental.dropoff = dropoff
				changed = True

			if changed:
				if pickup < dropoff:
					query1 = Rental.query.filter(Rental.car_id == form.car_id.data).filter(pickup <= Rental.pickup, db.and_(dropoff <= Rental.dropoff, dropoff >= Rental.pickup)).all()
					query2 = Rental.query.filter(Rental.car_id == form.car_id.data).filter(db.and_(pickup >= Rental.pickup, pickup <= Rental.dropoff), dropoff >= Rental.dropoff).all()
					query3 = Rental.query.filter(Rental.car_id == form.car_id.data).filter(pickup >= Rental.pickup, dropoff <= Rental.dropoff).all()
					query4 = Rental.query.filter(Rental.car_id == form.car_id.data).filter(pickup <= Rental.pickup, dropoff >= Rental.dropoff).all()
					query_length = len(query1 + query2 + query3 + query4)
					if query_length == 0 or query_length == 4:
						db.session.commit()
						flash('<strong>Success!</strong> Updated reservation.', 'success')
						return redirect(url_for('admin_reservations'))
					else:
						flash('<strong>Error!</strong> The selected car is already reserved during that period.', 'danger')
				else:
					flash('<strong>Error!</strong> Drop-off time cannot be before pick-up time.', 'danger')
			else: 
				flash('No changes were detected.', 'info')
				return redirect(url_for('admin_reservations'))
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	form.user_id.default = rental.user_id
	form.car_id.default = rental.car_id
	form.location_id.default = rental.location_id
	form.pickup_date.default = rental.pickup
	form.pickup_time.default = rental.pickup.strftime('%H:%M:%S')
	form.dropoff_date.default = rental.dropoff
	form.dropoff_time.default = rental.dropoff.strftime('%H:%M:%S')
	form.process()

	return render_template('admin/reservations_edit.html', form=form, rental=rental)

@app.route('/admin/reservations/delete/<int:id>', methods=['GET', 'POST'])
@roles_required('admin')
def admin_reservations_delete(id):
	form = ReservationsDeleteForm()
	rental = Rental.query.get_or_404(id)
	if request.method == 'POST':
		if form.validate():
			db.session.delete(rental)
			db.session.commit()
			flash('<strong>Success!</strong> Deleted reservation.', 'success')
			return redirect(url_for('admin_reservations'))
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	return render_template('admin/reservations_delete.html', form=form)

@app.route('/admin/reservations/bycar/<int:id>', methods=['GET', 'POST'])
@roles_required('admin')
def admin_reservations_bycar(id):
	car = Car.query.get_or_404(id)
	rentals = Rental.query.filter(Rental.car_id == id).filter(Rental.pickup >= round_time(datetime.now(), -1440)).order_by(Rental.pickup.asc()).all()
	past_rentals = Rental.query.filter(Rental.car_id == id).filter(Rental.pickup < round_time(datetime.now(), -1440)).order_by(Rental.pickup.asc()).all()
	return render_template('admin/reservations_bycar.html', car=car, rentals=rentals, past_rentals=past_rentals)

@app.route('/admin/reservations/bydate/<date>', methods=['GET', 'POST'])
@roles_required('admin')
def admin_reservations_bydate(date):
	rentals = Rental.query.filter(Rental.pickup == date).order_by(Rental.pickup.asc()).all()
	return render_template('admin/reservations_bydate.html', date=date, rentals=rentals)

@app.route('/admin/queries/', methods=['GET', 'POST'])
@roles_required('admin')
def admin_queries():
	form = QueriesForm()
	if request.method == 'POST':
		if form.validate():
			query = form.queries.data
			if query == '5000':
				cars = Rental.query.with_entities(Rental, db.func.max(Rental.dropoff_odometer).label('kilometres')).filter(Rental.dropoff_odometer >= 5000).group_by(Rental.car_id).all()
			elif query == 'highest':
				cars = Rental.query.with_entities(Rental, db.func.count(Rental.dropoff_odometer).label('rentals')).group_by(Rental.car_id).order_by(db.func.count(Rental.dropoff_odometer).desc()).all()
			elif query == 'lowest':
				cars = Rental.query.with_entities(Rental, db.func.count(Rental.dropoff_odometer).label('rentals')).group_by(Rental.car_id).order_by(db.func.count(Rental.dropoff_odometer).asc()).all()
			elif query == 'damaged':
				cars = Rental.query.with_entities(Rental, Rental.dropoff_status).filter(Rental.dropoff_actual != None).order_by(Rental.dropoff_actual.desc()).group_by(Rental.car_id).all()
			else:
				cars = Car.query.filter(Car.id == '-1').all()
			return render_template('admin/queries.html', form=form, query=query, cars=cars)
	return render_template('admin/queries.html', form=form)

@app.route('/admin/maintenance/')
@roles_required('admin')
def admin_maintenance():
	maintenances = Maintenance.query.order_by(Maintenance.id.desc()).all()
	return render_template('admin/maintenance.html', maintenances=maintenances)

@app.route('/admin/maintenance/add/', methods=['GET', 'POST'])
@roles_required('admin')
def admin_maintenance_add():
	form = MaintenanceForm()
	form.car_id.choices = format_cars(Car.query.all(), True)

	if request.method == 'POST':
		if form.validate():
			maintenance = Maintenance(form.car_id.data, form.date.data, form.odometer.data, form.mtype.data, form.description.data)
			db.session.add(maintenance)
			db.session.commit()
			flash('<strong>Success!</strong> Added maintenance.', 'success')
			return redirect(url_for('admin_maintenance'))
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	return render_template('admin/maintenance_add.html', form=form)

@app.route('/admin/maintenance/edit/<int:id>', methods=['GET', 'POST'])
@roles_required('admin')
def admin_maintenance_edit(id):
	form = MaintenanceForm()
	maintenance = Maintenance.query.get_or_404(id)
	form.car_id.choices = format_cars(Car.query.all(), True)

	if request.method == 'POST':
		if form.validate():
			changed = False
			if form.car_id.data != maintenance.car_id:
				maintenance.car_id = form.car_id.data
				changed = True
			if str(form.date.data) != str(maintenance.date).split(' ')[0]:
				maintenance.date = form.date.data
				changed = True
			if form.odometer.data != maintenance.odometer:
				maintenance.odometer = form.odometer.data
				changed = True
			if form.mtype.data != maintenance.mtype:
				maintenance.mtype = form.mtype.data
				changed = True
			if form.description.data != maintenance.description:
				maintenance.description = form.description.data
				changed = True

			if changed:
				db.session.commit()
				flash('<strong>Success!</strong> Maintenance updated.', 'success')
				return redirect(url_for('admin_maintenance'))
			else: 
				flash('No changes were detected.', 'info')
				return redirect(url_for('admin_maintenance'))
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	form.car_id.default = maintenance.car_id
	form.date.default = maintenance.date
	form.odometer.default = maintenance.odometer
	form.mtype.default = maintenance.mtype
	form.description.default = maintenance.description
	form.process()

	return render_template('admin/maintenance_edit.html', form=form, maintenance=maintenance)

@app.route('/admin/maintenance/delete/<int:id>', methods=['GET', 'POST'])
@roles_required('admin')
def admin_maintenance_delete(id):
	form = MaintenanceDeleteForm()

	maintenance = Maintenance.query.get_or_404(id)
	if request.method == 'POST':
		if form.validate():
			db.session.delete(maintenance)
			db.session.commit()
			flash('<strong>Success!</strong> Deleted reservation.', 'success')
			return redirect(url_for('admin_maintenance'))
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	return render_template('admin/maintenance_delete.html', form=form)

@app.route('/admin/comments/')
@roles_required('admin')
def admin_comments():
	comments = Comment.query.filter(Comment.parent_id == None).order_by(Comment.id.desc()).all()
	return render_template('admin/comments.html', comments=comments)

@app.route('/admin/comments/reply/<int:id>', methods=['GET', 'POST'])
@roles_required('admin')
def admin_comments_reply(id):
	form = CommentsReplyForm()
	comment = Comment.query.get_or_404(id)

	if request.method == 'POST':
		if form.validate():
			comment = Comment(comment.id, g.identity.user.id, comment.rental_id, comment.title, form.text.data, comment.rating)
			db.session.add(comment)
			db.session.commit()
			flash('<strong>Success!</strong> Added comment.', 'success')
			return redirect(url_for('admin_comments'))
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	return render_template('admin/comments_reply.html', form=form, comment=comment)

@app.route('/admin/comments/delete/<int:id>', methods=['GET', 'POST'])
@roles_required('admin')
def admin_comments_delete(id):
	form = CommentsDeleteForm()
	comment = Comment.query.get_or_404(id)

	if request.method == 'POST':
		if form.validate():
			db.session.delete(comment)
			db.session.commit()
			flash('<strong>Success!</strong> Deleted comment.', 'success')
			return redirect(url_for('admin_comments'))
		else:
			flash('<strong>Error!</strong> Check the highlighted fields below and try again.', 'danger')

	return render_template('admin/comments_delete.html', form=form)

@app.route('/admin/generate_invoice/', methods=['GET', 'POST'])
@roles_required('admin')
def admin_generate_invoice():
	form = GenerateInvoiceForm()
	form.user_id.choices = format_users(User.query.all())
	
	if request.method == 'POST':
		if form.validate():
			user = User.query.filter(User.id == form.user_id.data).first()
			rentals = Rental.query.filter(Rental.user_id == form.user_id.data, Rental.dropoff_actual != None).order_by(Rental.dropoff_actual.asc()).all()

			subtotal_km = 0
			for rental in rentals:
				subtotal_km += rental.dropoff_odometer - rental.pickup_odometer

			return render_template('admin/generate_invoice.html', form=form, user=user, rentals=rentals, subtotal_km=subtotal_km, now=datetime.now(), submitted=True)	
	
	return render_template('admin/generate_invoice.html', form=form)
