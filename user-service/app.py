from flask import Flask
from db.models import db
from config import Config
from routes.user_routes import user_bp

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(user_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)