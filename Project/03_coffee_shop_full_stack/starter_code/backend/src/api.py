import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from database.models import db_drop_and_create_all, setup_db, Drink
from auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


# db_drop_and_create_all()

# ROUTES
@app.route('/drinks', methods=['GET'])
def retrieve_drinks():
    drinks = Drink.query.all()

    if not drinks:
        abort(404)

    formated_drinks = [drink.short() for drink in drinks]
    return jsonify({
        'success': True,
        'drinks': formated_drinks
    }), 200


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def retrieve_drinks_detail(payload):

    drinks = drinks = Drink.query.all()
    if not drinks:
        abort(404)

    formated_drinks = [drink.long() for drink in drinks]
    return jsonify({
        'success': True,
        'drinks': formated_drinks
    }), 200


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def drinks(payload):

    title = request.get_json().get('title', None)
    new_recipe = request.get_json().get('recipe', None)
    if not isinstance(new_recipe, list):
        new_recipe = [new_recipe]
    recipe = json.dumps(new_recipe)

    try:
        drink = Drink(title=title, recipe=recipe)
        drink.insert()

    except Exception as e:
        drink.rollback()
        abort(422)

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    }), 200


@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(payload, id):
    drink = Drink.query.filter_by(id=id).first()
    if not drink:
        abort(404)

    title = request.get_json().get('title', None)
    new_recipe = request.get_json().get('recipe', None)
    
    recipe = json.dumps(new_recipe)

    try:
        drink.title = title
        drink.recipe = recipe
        drink.update()

    except Exception as e:
        drink.rollback()
        abort(422)

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    }), 200


@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    drink = Drink.query.filter_by(id=id).first()
    if not drink:
        abort(404)

    try:
        drink.delete()
    except Exception as e:
        drink.rollback()
        abort(422)

    return jsonify({
        'success': True,
        'delete': id
    }), 200


# Error Handling
@app.errorhandler(422)
def unprocessable(error):
    '''422 Error handler
    '''
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def not_found(error):
    '''404 Error handler
    '''
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
        }), 404


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        'success': False,
        'error': error.error['code'],
        'message': error.error['description']
    }), error.status_code


# iamfinal.us.auth0.com/authorize?response_type=token&client_id=Jv4n1HwrzPMoUlJPJkr0CKLtQHvZGrcL&redirect_uri=https://127.0.0.1:8080/login-results&audience=iamfinal
if __name__ == '__main__':
    app.run(debug=True)