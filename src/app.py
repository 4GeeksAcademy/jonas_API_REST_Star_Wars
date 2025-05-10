"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200

@app.route("/people", methods=["GET", "POST"])
def people():
    if request.method == "GET":
        people_list = People.query.all()
        return jsonify([person.serialize() for person in people_list])
    
    if request.method == "POST":
        data = request.get_json()
        new_person = People(name=data["name"])
        db.session.add(new_person)
        db.session.commit()
        return jsonify(new_person.serialize()), 201

# Obtener todos los planetas
@app.route('/planet', methods=['GET'])
def get_all_planets():
    planets = Planet.query.all()
    return jsonify([planet.serialize() for planet in planets]), 200

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"status": "working"}), 200


# Obtener un planeta por su ID
@app.route('/planet/<int:planet_id>', methods=['GET'])
def get_planet_by_id(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"error": "Planet not found"}), 404
    return jsonify(planet.serialize()), 200

@app.route('/planet/create', methods=['POST'])
def create_planet():
    data = request.get_json()
    new_planet = new_planet = Planet(
    name=data.get("name", "Tatooine"),
    climate=data.get("climate", ""),
    terrain=data.get("terrain", ""),
    population=data.get("population", ""),
    orbital_period=data.get("orbital_period", ""),
    rotation_period=data.get("rotation_period", ""),
    diameter=data.get("diameter", "")
)

    db.session.add(new_planet)
    db.session.commit()
    return jsonify(new_planet.serialize()), 201


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=True)
