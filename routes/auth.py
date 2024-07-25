from flask import Blueprint, request, jsonify
from models import User

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    print(data)
    User.create_user(data)
    return jsonify({"message": "User created successfully"}), 201


@auth.route('/create-users', methods=['POST'])
def create_users():
    data = request.json['users']
    # return data
    User.insert_many(data)
    return jsonify({"message": "User created successfully"}), 201


@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if 'email' not in data or 'password' not in data:
        return jsonify({"message": "Missing email or password in request"}), 400

    email = data['email']
    password = data['password']
    user = User.authenticate(email, password)

    if user:
        auth_token = User.encode_auth_token(user['_id'])
        print(user['_id'])

        if isinstance(auth_token, bytes):
            auth_token = auth_token.decode('utf-8')  # Convert bytes to string if necessary
        print(auth_token)
        return jsonify({"token": auth_token, "user_id": str(user['_id'])}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

