# Online Food Ordering and Payment System

## Overview

This project is a web-based food ordering system built with Flask. Users can sign up, log in, place orders for various dishes, and pay for their orders using Stripe. The application manages user authentication, order management, and payment processing through a simple and intuitive interface.

## Features

- **User Authentication**: Sign up, log in, and manage user sessions.
- **Order Management**: Place, view, and delete food orders.
- **Payment Processing**: Secure payment processing using Stripe.
- **Database Management**: Stores user, order, and payment information using SQLAlchemy.

## Requirements

To run this application, you need the following:

- Python 3.7 or higher
- Flask
- SQLAlchemy
- Flask-WTF
- Stripe
- python-dotenv

## Flow of Functions

1. **Application Initialization**:
   - **`load_dotenv()`**: Loads environment variables from a `.env` file, including Stripe API keys.
   - **`app = Flask(__name__)`**: Initializes the Flask application.
   - **`db = SQLAlchemy(app)`**: Initializes the SQLAlchemy ORM with the app.
   - **`stripe.api_key`**: Sets the Stripe secret API key.

2. **Database Models**:
   - **`User`**: Represents users with fields for `username`, `email`, and `password`.
   - **`Order`**: Represents food orders with fields for `name`, `email`, `phone`, `order_items`, and `quantity`.
   - **`Payment`**: Represents payment records with fields for `session_id`, `amount`, `currency`, and `status`.

3. **Forms**:
   - **`SignUpForm`**: Handles user registration with fields for `username`, `email`, `password`, and `confirm_password`.
   - **`LoginForm`**: Handles user login with fields for `email` and `password`.
   - **`OrderForm`**: Handles food order submission with fields for `product`, `quantity`, and `phone`.

4. **Routes**:
   - **`/signup`**:
     - Displays the sign-up form.
     - On form submission, validates the input, hashes the password, and creates a new user record.
     - Handles `IntegrityError` in case of duplicate email or username.
   - **`/login`**:
     - Displays the login form.
     - On form submission, validates the input and checks the password.
     - Initiates a session on successful login.
   - **`/logout`**:
     - Logs out the user by clearing the session.
   - **`/` (Home/Index)**:
     - Displays the order form.
     - On form submission, validates the input, calculates the order price, and stores the order in the database.
   - **`/orders`**:
     - Displays a list of all orders for the logged-in user.
   - **`/checkout`**:
     - Displays the checkout page with the total price of the order.
   - **`/delete/<int:id>`**:
     - Deletes or decreases the quantity of an order.
   - **`/create-checkout-session`**:
     - Creates a Stripe checkout session for payment processing.
     - Returns a JSON response with the session ID.
   - **`/success`**:
     - Displays a success message after a successful payment.


### check out the function at 
https://youtu.be/t_nY72Zl_Kw

https://youtu.be/S3uNNJJs-P4
