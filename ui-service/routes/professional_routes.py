from flask import Blueprint, render_template, request, redirect, url_for, flash
import requests
from config import PROFESSIONAL_SERVICE_URL
from utils.security import is_logged_in

professional_routes = Blueprint('professional_routes', __name__)

@professional_routes.route('/professionals', methods=['GET'])
def list_professionals():
    if not is_logged_in():
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('user_routes.login'))

    response = requests.get(f"{PROFESSIONAL_SERVICE_URL}/professionals")
    professionals = response.json() if response.status_code == 200 else []

    return render_template('list_professionals.html', professionals=professionals)
