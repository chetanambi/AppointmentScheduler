from flask import Flask, render_template
from routes.user_routes import user_routes
from routes.professional_routes import professional_routes
from routes.appointment_routes import appointment_routes

app = Flask(__name__)
app.secret_key = 'secret_key'

# Register blueprints
app.register_blueprint(user_routes)
app.register_blueprint(professional_routes)
app.register_blueprint(appointment_routes)

if __name__ == '__main__':
    app.run(debug=True, port=5004)
