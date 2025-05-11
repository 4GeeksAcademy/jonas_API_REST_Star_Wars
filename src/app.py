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
from models import db, User, People, Planet, Favorite
from sqlalchemy.orm.exc import NoResultFound

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
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

# muestra el link favorites en el navegador (solo como EJEMPLO)
@app.route('/favorites')
def get_example_favorites():
    user_id = 2  # O el que quieras usar como ejemplo
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    return jsonify([fav.to_dict() for fav in favorites]), 200


@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200


# Función para validar que el `user_id` existe en la base de datos
def validate_user(user_id):
    try:
        # Intentamos obtener el usuario de la base de datos
        user = User.query.get(user_id)
        if user:
            return user
        return None
    except NoResultFound:
        return None


# Obtener todos los personajes
@app.route("/people", methods=["GET"])
def get_all_people():
    people_list = People.query.all()
    return jsonify([person.serialize() for person in people_list]), 200

# Obtener un personaje por su ID


@app.route('/people/<int:people_id>', methods=['GET'])
def get_person_by_id(people_id):
    person = People.query.get(people_id)
    if not person:
        return jsonify({"error": "Person not found"}), 404
    return jsonify(person.serialize()), 200

# Obtener todos los planetas


@app.route('/planet', methods=['GET'])
def get_all_planets():
    planets = Planet.query.all()
    return jsonify([planet.serialize() for planet in planets]), 200

# Obtener un planeta por su ID


@app.route('/planet/<int:planet_id>', methods=['GET'])
def get_planet_by_id(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"error": "Planet not found"}), 404
    return jsonify(planet.serialize()), 200

# Obtener todos los usuarios
@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    return jsonify([user.serialize() for user in users]), 200

# Obtener todos los Favoritos del usuario actual
@app.route('/users/<int:user_id>/favorites', methods=['GET'])
def get_user_favorites(user_id):
    # Obtiene los favoritos del usuario
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    
    # Devuelve la lista de favoritos como JSON
    return jsonify([fav.to_dict() for fav in favorites]), 200



# Añade un nuevo planet favorito al usuario actual con el id = planet_id.
@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    body = request.get_json()
    user_id = body.get("user_id")

    if user_id is None:
        return jsonify({"error": "user_id is required"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"error": "Planet not found"}), 404

    # Verificar si ya existe ese favorito para no duplicar
    existing_fav = Favorite.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if existing_fav:
        return jsonify({"error": "Planet already in favorites"}), 409

    favorite = Favorite(user_id=user_id, planet_id=planet_id)
    db.session.add(favorite)
    db.session.commit()

    return jsonify({"message": "Planet added to favorites"}), 200



# Añade un nuevo people favorito al usuario actual con el id = people_id
@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_people(people_id):
    body = request.get_json()
    user_id = body.get("user_id")

    if user_id is None:
        return jsonify({"error": "user_id is required"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    person = People.query.get(people_id)
    if not person:
        return jsonify({"error": "Character not found"}), 404

    # Verificar si ya existe ese favorito para no duplicar
    existing_fav = Favorite.query.filter_by(user_id=user_id, people_id=people_id).first()
    if existing_fav:
        return jsonify({"error": "Character already in favorites"}), 409

    favorite = Favorite(user_id=user_id, people_id=people_id)
    db.session.add(favorite)
    db.session.commit()

    return jsonify({"message": "Character added to favorites"}), 200


# Elimina un planet favorito con el id = planet_id.
@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    user_id = 1  # temporal
    fav = Favorite.query.filter_by(
        user_id=user_id, planet_id=planet_id).first()
    if not fav:
        return jsonify({"error": "Favorite not found"}), 404

    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg": "Favorite planet deleted"}), 200

# Elimina un people favorito con el id = people_id


@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_people(people_id):
    user_id = 1  # temporal
    fav = Favorite.query.filter_by(
        user_id=user_id, people_id=people_id).first()
    if not fav:
        return jsonify({"error": "Favorite not found"}), 404

    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg": "Favorite character deleted"}), 200


# Crear un planeta
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


# Crear un personaje
@app.route('/people/create', methods=['POST'])
def create_person():
    data = request.get_json()

    required_fields = ['name']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"'{field}' is required"}), 400

    new_person = People(
        name=data["name"],
        height=data.get("height"),
        mass=data.get("mass"),
        hair_color=data.get("hair_color"),
        skin_color=data.get("skin_color"),
        eye_color=data.get("eye_color"),
        birth_year=data.get("birth_year"),
        gender=data.get("gender")
    )

    db.session.add(new_person)
    db.session.commit()
    return jsonify(new_person.serialize()), 201

# MODIFICA un planeta


@app.route('/planet/<int:planet_id>', methods=['PUT'])
def update_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"error": "Planet not found"}), 404

    data = request.get_json()

    planet.name = data.get("name", planet.name)
    planet.climate = data.get("climate", planet.climate)
    planet.terrain = data.get("terrain", planet.terrain)
    planet.population = data.get("population", planet.population)
    planet.orbital_period = data.get("orbital_period", planet.orbital_period)
    planet.rotation_period = data.get(
        "rotation_period", planet.rotation_period)
    planet.diameter = data.get("diameter", planet.diameter)

    db.session.commit()
    return jsonify(planet.serialize()), 200


# MODFICA un personaje
@app.route('/people/<int:people_id>', methods=['PUT'])
def update_person(people_id):
    person = People.query.get(people_id)
    if not person:
        return jsonify({"error": "Person not found"}), 404

    data = request.get_json()

    person.name = data.get("name", person.name)
    person.height = data.get("height", person.height)
    person.mass = data.get("mass", person.mass)
    person.hair_color = data.get("hair_color", person.hair_color)
    person.skin_color = data.get("skin_color", person.skin_color)
    person.eye_color = data.get("eye_color", person.eye_color)
    person.birth_year = data.get("birth_year", person.birth_year)
    person.gender = data.get("gender", person.gender)

    db.session.commit()
    return jsonify(person.serialize()), 200


# ELIMINAR un planeta
@app.route('/planet/<int:planet_id>', methods=['DELETE'])
def delete_planet(planet_id):
    planet = db.session.get(Planet, planet_id)
    if planet is None:
        return jsonify({"msg": "Planet not found"}), 404

    db.session.delete(planet)
    db.session.commit()
    return jsonify({"msg": f"Planet {planet_id} deleted successfully"}), 200

# ELIMINAR un personaje


@app.route('/people/<int:people_id>', methods=['DELETE'])
def delete_people(people_id):
    people = db.session.get(People, people_id)
    if people is None:
        return jsonify({"msg": "People not found"}), 404

    db.session.delete(people)
    db.session.commit()
    return jsonify({"msg": f"People {people_id} deleted successfully"}), 200

# Crear un usuario de prueba temporalmente
@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()

    # Verificamos si se proporcionaron todos los campos necesarios
    if not data.get('email') or not data.get('password') or data.get('is_active') is None:
        return jsonify({"error": "Email, password, and is_active are required"}), 400

    # Creación del usuario
    try:
        user = User(
            email=data['email'],
            password=data['password'],  # La contraseña será almacenada sin serializar
            is_active=data['is_active']
        )
        db.session.add(user)
        db.session.commit()

        # Devolvemos la respuesta sin la contraseña serializada
        return jsonify(user.serialize()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500




# TEST de prueba
@app.route('/test', methods=['GET'])
def test():
    return jsonify({"status": "working"}), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=True)
