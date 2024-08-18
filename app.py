from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo
import os
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
db = SQLAlchemy(app)


# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


# Define the Order model
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    order_items = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


# Define the SignUpForm class
class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


# Define the LoginForm class
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Define the OrderForm class
class OrderForm(FlaskForm):
    order_items = StringField('Order Items', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired()])
    submit = SubmitField('Submit Order')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        try:
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Email or username already exists. Please choose another.', 'danger')
    return render_template('signup.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_email'] = user.email
            session['user_phone'] = user.email  # Dummy value, update as necessary
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your email and/or password.', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    form = OrderForm()
    if form.validate_on_submit():
        user = User.query.get(session['user_id'])
        existing_order = Order.query.filter_by(
            name=user.username,
            email=user.email,
            order_items=form.order_items.data
        ).first()

        if existing_order:
            existing_order.quantity += form.quantity.data
            existing_order.phone = form.phone.data  # Update the phone number
            db.session.commit()
        else:
            order = Order(
                name=user.username,
                email=user.email,
                phone=form.phone.data,  # Store the phone number from the form
                order_items=form.order_items.data,
                quantity=form.quantity.data
            )
            db.session.add(order)
            db.session.commit()

        return redirect(url_for('orders'))
    return render_template('index.html', form=form)

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    orders = Order.query.filter_by(email=session.get('user_email')).all()
    return render_template('orders.html', orders=orders)

@app.route('/delete/<int:id>')
def delete_order(id):
    if 'user_id' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    order = Order.query.get_or_404(id)
    if order.quantity > 1:
        # Decrease the quantity by one
        order.quantity -= 1
        db.session.commit()
        flash('Order quantity decreased by one.', 'success')
    else:
        # Remove the order if quantity is zero
        db.session.delete(order)
        db.session.commit()
        flash('Order deleted successfully!', 'success')

    return redirect(url_for('orders'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the database and tables if they don't exist
    app.run(debug=True)