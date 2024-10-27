from flask import session, redirect, url_for, flash

def is_logged_in():
    return 'user_id' in session
