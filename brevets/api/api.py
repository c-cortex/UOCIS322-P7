# List Times
from flask import Flask, request
from flask_restful import Resource, Api

import os
from pymongo import MongoClient

import json

from bson.json_util import loads, dumps

from itsdangerous import (TimedJSONWebSignatureSerializer \
                                  as Serializer, BadSignature, \
                                  SignatureExpired)

from passlib.apps import custom_app_context as pwd_context


app = Flask(__name__)
api = Api(app)

client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
db = client.tododb

client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
usersdb = client.usersdb


SECRET_KEY = 'test1234@#$'


def generate_auth_token(expiration=600):
   s = Serializer(SECRET_KEY, expires_in=expiration)
   return s.dumps({'id': id})


def verify_auth_token(token):
    s = Serializer(SECRET_KEY)
    try:
        data = s.loads(token)
    except SignatureExpired:
        return None    # valid token, but expired
    except BadSignature:
        return None    # invalid token
    return "Success! Welcome."


def verify_password(password, hashVal):
    return pwd_context.verify(password, hashVal)


class listAll(Resource):
    def get(self, dtype=""):
        times = list(db.tododb.find({},{"_id":0, "open": 1, "close": 1 }))
        if dtype == 'json':
            return loads(dumps(times))
        if dtype == 'csv':
            # cant get into csv form
            return loads(dumps(times))


class listOpenOnly(Resource):
    def get(self, dtype=""):
        top = request.args.get('top', type=int)
        app.logger.debug(top)
        times = db.tododb.find({},{"_id":0, "open": 1 })
        # cant get k to work
        # times = db.tododb.find({},{"_id":0, "open": 1 }).limit(top)
        # times = times[:top]
        if dtype == 'json':
            return loads(dumps(times))
        if dtype == 'csv':
            # cant get into csv form
            return loads(dumps(times))


class listCloseOnly(Resource):
    def get(self, dtype=""):
        top = request.args.get('top', type=int)
        app.logger.debug(top)
        times = list(db.tododb.find({},{"_id":0, "close": 1 }))
        # cant get k to work
        # times = db.tododb.find({},{"_id":0, "close": 1 }).limit(top)
        # times = times[:top]
        if dtype == 'json':
            return loads(dumps(times))
        if dtype == 'csv':
            # cant get into csv form
            return loads(dumps(times))


class register(Resource):
    def post(self):
        app.logger.debug("Registration in progress")
        username = request.args.get('username', type=str)
        password = request.args.get('password', type=str)
        users = usersdb.usersdb.find_one({"username": username})
        if users:
            app.logger.debug("ERROR 400")
            return {'message': 'ERROR'}, 400
        else:
            app.logger.debug("Inserting ENTRY")
            id = usersdb.usersdb.find().count()
            usersdb.usersdb.insert_one({
                'id': id,
                'username': username,
                'password': pwd_context.encrypt(password)
            })
            app.logger.debug("SUCCESSFUL ENTRY")
            return 201


# class token(Resource):
#     def get(self):


# for testing only
class listUsers(Resource):
    def get(self):
        users = list(usersdb.usersdb.find({},{"_id":0, "username": 1, "password": 1}))
        return loads(dumps(users))



# Create routes
# Another way, without decorators
api.add_resource(listAll, '/listAll', '/listAll/<string:dtype>')
api.add_resource(listOpenOnly, '/listOpenOnly', '/listOpenOnly/<string:dtype>')
api.add_resource(listCloseOnly, '/listCloseOnly', '/listCloseOnly/<string:dtype>')
api.add_resource(register, '/register')
# api.add_resource(token, '/token')

# for testing only
api.add_resource(listUsers, '/listUsers')



# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
