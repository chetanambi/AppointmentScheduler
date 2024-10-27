from werkzeug.security import generate_password_hash as generate_hash, check_password_hash as check_hash

def generate_password_hash(password, method='sha256'):
    return generate_hash(password, method)

def check_password_hash(pw_hash, password):
    return check_hash(pw_hash, password)
