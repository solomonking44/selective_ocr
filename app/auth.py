from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)  
    
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            if check_password_hash(user.password, password):
                flash("Logged in successfully", category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash("Incorrect Password", category='error')
        else:
            flash("Email does not exist", category='error')
    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        print("GET request")
    elif request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        age = request.form['age']
        email = request.form['email']
        password = request.form['password']
        confirmpassword = request.form['confirmpassword']
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            flash("User already exists", category='error')
        else:
            if password != confirmpassword:
                flash('Passwords don\'t match', category='error')
            elif len(password) < 7:
                flash('Password cannot be shorter than 7 characters', category='error')
            elif len(firstname) < 2:
                flash('First name must be greater than 1 character', category='error')
            elif len(lastname) < 2:
                flash('Last name must be greater than 1 character', category='error')
            elif int(age) >= 150:
                flash('Age cannot be greater than 150 years', category='error')
            else:
                new_user = User(firstname=firstname, lastname=lastname, age=age, email=email, password=generate_password_hash(password, method='sha256'))
                db.session.add(new_user)
                db.session.commit()
                flash('Account created!', category='success')
                login_user(new_user, remember=True)
                return redirect(url_for('views.home'))
    else:
        print("Invalid Method")

    return render_template('signup.html', user=current_user)
