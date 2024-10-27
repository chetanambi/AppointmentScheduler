from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import requests
from config import USER_SERVICE_URL
from utils.security import is_logged_in

user_routes = Blueprint('user_routes', __name__)

@user_routes.route('/')
def home():
    return render_template('home.html')

@user_routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'email': request.form['email'],
            'phone': request.form['phone'],
            'location': request.form['location'],
            'password': request.form['password']
        }
        response = requests.post(f"{USER_SERVICE_URL}/register", json=data)
        if response.status_code == 201:
            flash('Registration successful!', 'success')
            return redirect(url_for('user_routes.login'))
        flash('Registration failed. Please try again.', 'error')
    return render_template('register.html')

@user_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = {
            'email': request.form['email'],
            'password': request.form['password']
        }
        response = requests.post(f"{USER_SERVICE_URL}/login", json=data)
        if response.status_code == 200:
            user_data = response.json()
            session['user_id'] = user_data['user_id']
            flash('Login successful!', 'success')
            return render_template('base.html', user=user_data)
    return render_template('login.html')

@user_routes.route('/user/<int:user_id>')
def profile(user_id):
    response = requests.get(f"{USER_SERVICE_URL}/user/{user_id}")
    if response.status_code == 200:
        user_data = response.json()
        return render_template('profile.html', user=user_data)
    flash('User not found!', 'error')
    return redirect(url_for('user_routes.login'))

@user_routes.route('/user/<int:user_id>/update', methods=['GET', 'POST'])
def update_profile(user_id):
    if request.method == 'POST':
        data = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'email': request.form['email'],
            'phone': request.form['phone'],
            'location': request.form['location'],
        }
        response = requests.put(f"{USER_SERVICE_URL}/user/{user_id}", json=data)
        if response.status_code == 200:
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('user_routes.profile', user_id=user_id))
        flash('Update failed. Please try again.', 'error')

    response = requests.get(f"{USER_SERVICE_URL}/user/{user_id}")
    if response.status_code == 200:
        user_data = response.json()
        return render_template('update_profile.html', user=user_data)
    flash('User not found!', 'error')
    return redirect(url_for('user_routes.login'))

@user_routes.route('/user/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    response = requests.delete(f"{USER_SERVICE_URL}/user/{user_id}")
    if response.status_code == 200:
        flash('User account deleted successfully!', 'success')
        return redirect(url_for('user_routes.login'))
    flash('Failed to delete user account. User not found!', 'error')
    return redirect(url_for('user_routes.profile', user_id=user_id))

@user_routes.route('/user/delete/confirm/<int:user_id>')
def delete_confirmation(user_id):
    return render_template('delete_confirmation.html', user_id=user_id)
