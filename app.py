from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from wtforms import StringField, SelectField, IntegerField, SubmitField
import os
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
import stripe


app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'

# Stripe API keys
app.config['STRIPE_PUBLIC_KEY'] = os.getenv('STRIPE_PUBLIC_KEY')  
app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY')  
        

db = SQLAlchemy(app)

# Initialize Stripe with your secret key
stripe.api_key = app.config['STRIPE_SECRET_KEY']


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
    paid = db.Column(db.Boolean, default=False)  # New field to track payment status


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
    product = SelectField('Product', choices=[
        ('Paneer Butter Masala', 'Paneer Butter Masala'),
        ('Chicken Biryani', 'Chicken Biryani'),
        ('Chole Bhature', 'Chole Bhature'),
        ('Masala Dosa', 'Masala Dosa'),
        ('Butter Chicken', 'Butter Chicken'),
        ('Palak Paneer', 'Palak Paneer'),
        ('Tandoori Chicken', 'Tandoori Chicken'),
        ('Dal Makhani', 'Dal Makhani'),
        ('Aloo Gobi', 'Aloo Gobi'),
        ('Prawn Masala', 'Prawn Masala')
    ], validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired()])
    submit = SubmitField('Submit Order')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')

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
            order_items=form.product.data  # Use 'product' instead of 'order_items'
        ).first()

        if existing_order:
            existing_order.quantity += form.quantity.data
            existing_order.phone = form.phone.data  # Update the phone number
            db.session.commit()
            return redirect(url_for('checkout', order_id=existing_order.id))
        else:
            order = Order(
                name=user.username,
                email=user.email,
                phone=form.phone.data,  # Store the phone number from the form
                order_items=form.product.data,  # Use 'product' instead of 'order_items'
                quantity=form.quantity.data
            )
            db.session.add(order)
            db.session.commit()
            return redirect(url_for('checkout', order_id=order.id))
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
    db.session.delete(order)
    db.session.commit()
    flash('Order deleted successfully!', 'success')
    return redirect(url_for('orders'))


@app.route('/checkout/<int:order_id>', methods=['GET'])
def checkout(order_id):
    order = Order.query.get_or_404(order_id)
    if not order.paid:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': order.order_items,
                    },
                    'unit_amount': 1000 * order.quantity,  # Assuming each item is $10
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('payment_success', order_id=order_id, _external=True),
            cancel_url=url_for('payment_cancel', _external=True),
        )
        return redirect(session.url, code=303)
    else:
        flash('Order already paid.', 'info')
        return redirect(url_for('orders'))


@app.route('/success/<int:order_id>')
def payment_success(order_id):
    order = Order.query.get_or_404(order_id)
    order.paid = True
    db.session.commit()
    flash('Payment successful! Thank you for your order.', 'success')
    return redirect(url_for('orders'))


@app.route('/cancel')
def payment_cancel():
    flash('Payment canceled. You can try again.', 'warning')
    return redirect(url_for('orders'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the database and tables if they don't exist
    app.run(debug=True)
