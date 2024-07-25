from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app,  jsonify
import jwt
import datetime
import random
from bson.objectid import ObjectId

# Singleton MongoDB client instance
client = None

def get_db():
    global client
    if client is None:
        uri = "mongodb+srv://saif:bG8aqfirVhMApT%23@atlascluster.uph9tug.mongodb.net/?retryWrites=true&w=majority&appName=AtlasCluster"
        client = MongoClient(uri)
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    return client['recommendation_engine']

class User:
    @staticmethod
    def create_user(data):
        try:
            data['password'] = generate_password_hash(data['password'])
            db = get_db()
            db['users'].insert_one(data)
        except Exception as e:
            current_app.logger.error(f"Error creating user: {str(e)}")

    @staticmethod
    def get_user_history(user_id):
        try:
            db = get_db()
            pipeline = [
                {'$match': {'user_id': user_id}},
                {'$group': {
                    '_id': '$product_id',  # Use '_id' for grouping
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}},
                {'$limit': 2}
            ]
            user_history = db['user_product_history'].aggregate(pipeline)
            product_ids = [record['_id'] for record in user_history]  # Use '_id' to get the product_id
            return product_ids
        except Exception as e:
            current_app.logger.error(f"Error fetching user history: {str(e)}")
            return []

    @staticmethod
    def get_users_history(user_ids):
        try:
            db = get_db()
            user_ids = [ObjectId(uid) for uid in user_ids]
            print("user_ids",user_ids)
            query = {'user_id': {'$in': user_ids}}
            user_histories = list(db['user_product_history'].find(query, {'product_id': 1, '_id': 0}))
            product_ids = [record['product_id'] for record in user_histories]
            print("product_ids",product_ids)
            return product_ids
        except Exception as e:
            current_app.logger.error(f"Error fetching users history: {str(e)}")
            return []

    @staticmethod
    def get_all():
        try:
            db = get_db()
            return list(db['users'].find())
        except Exception as e:
            current_app.logger.error(f"Error fetching all users: {str(e)}")
            return []

    @staticmethod
    def insert_many(users):
        try:
            db = get_db()
            db['users'].insert_many(users)
        except Exception as e:
            current_app.logger.error(f"Error inserting multiple users: {str(e)}")

    @staticmethod
    def authenticate(email, password):
        try:
            db = get_db()
            user = db['users'].find_one({"email": email})
            if user and check_password_hash(user['password'], password):
                return user
            return None
        except Exception as e:
            current_app.logger.error(f"Error authenticating user: {str(e)}")
            return None

    @staticmethod
    def encode_auth_token(user_id):
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
                'iat': datetime.datetime.utcnow(),
                'sub': str(user_id)
            }
            return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
        except Exception as e:
            current_app.logger.error(f"Error encoding auth token: {str(e)}")
            return str(e)

    @staticmethod
    def decode_auth_token(auth_token):
        try:
            payload = jwt.decode(auth_token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'

class Product:
    @staticmethod
    def insert_many(products):
        try:
            db = get_db()
            db['products'].insert_many(products)
        except Exception as e:
            current_app.logger.error(f"Error inserting multiple products: {str(e)}")

    @staticmethod
    def get_paginated(page, per_page, main_category=None, sub_category=None):
        try:
            db = get_db()

            # Build the filter query
            filter_query = {}
            if main_category:
                filter_query['main_category'] = main_category
            if sub_category:
                filter_query['sub_category'] = sub_category

            # Count the total number of filtered products
            total_products = db['products'].count_documents(filter_query)

            # Calculate total pages
            total_pages = (total_products + per_page - 1) // per_page

            # Skip and limit for pagination
            skip = (page - 1) * per_page

            # Fetch the paginated and filtered products
            products = list(db['products'].find(filter_query).skip(skip).limit(per_page))

            # Convert ObjectId to string
            for product in products:
                product['_id'] = str(product['_id'])

            return {
                'page': page,
                'per_page': per_page,
                'total_products': total_products,
                'total_pages': total_pages,
                'products': products
            }
        except Exception as e:
            current_app.logger.error(f"Error fetching paginated products: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def get_all():
        try:
            db = get_db()
            products = list(db['products'].find())
            # for product in products:
            #     product['_id'] = str(product['_id'])
            return products
        except Exception as e:
            current_app.logger.error(f"Error fetching all products: {str(e)}")
            return []

    @staticmethod
    def create_categories():
        try:
            products = Product.get_all()
            categories = {}

            for product in products:
                main_category = product.get('main_category')
                sub_category = product.get('sub_category')

                if main_category not in categories:
                    categories[main_category] = set()

                if sub_category:
                    categories[main_category].add(sub_category)

            # Convert sets to lists for JSON serialization
            categories = {k: list(v) for k, v in categories.items()}

            # Insert categories into the database
            db = get_db()
            db['categories'].insert_one({'categories': categories})

            return jsonify({'message': 'Categories created successfully', 'categories': categories}), 201
        except Exception as e:
            current_app.logger.error(f"Error creating categories: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @staticmethod
    def get_categories():
        try:
            db = get_db()
            categories_data = db['categories'].find_one()
            if categories_data:
                return jsonify(categories_data['categories'])
            else:
                return jsonify({'categories': {}}), 404
        except Exception as e:
            current_app.logger.error(f"Error fetching categories: {str(e)}")
            return jsonify({'error': str(e)}), 500
    @staticmethod
    def update_quantities():
        try:
            db = get_db()
            products = list(db['products'].find())
            bulk_operations = []

            for product in products:
                quantity = random.randint(1, 10)
                bulk_operations.append(
                    UpdateOne(
                        {"_id": ObjectId(product['_id'])},
                        {"$set": {"quantity": quantity}}
                    )
                )

            result = db['products'].bulk_write(bulk_operations)

            return {
                'success': True,
                'message': f'Updated {result.modified_count} products with random quantities.'
            }
        except BulkWriteError as bwe:
            current_app.logger.error(f"Bulk write error: {bwe.details}")
            return {'success': False, 'message': f'Bulk write error: {bwe.details}'}
        except Exception as e:
            current_app.logger.error(f"Error updating quantities: {str(e)}")
            return {'success': False, 'message': f'Error updating quantities: {str(e)}'}

    @staticmethod
    def update_product():
        try:
            db = get_db()
            products = list(db['products'].find())
            bulk_operations = []

            for product in products:
                # Add the product_id attribute
                product_id = str(product['_id'])

                # Add bulk operation with quantity update and product_id addition
                bulk_operations.append(
                    UpdateOne(
                        {"_id": ObjectId(product['_id'])},
                        {
                            "$set": {
                                "quantity": random.randint(1, 100),
                                "product_id": product_id
                            }
                        }
                    )
                )

            result = db['products'].bulk_write(bulk_operations)

            return {
                'success': True,
                'message': f'Updated {result.modified_count} products with random quantities and added product_id.'
            }
        except BulkWriteError as bwe:
            current_app.logger.error(f"Bulk write error: {bwe.details}")
            return {'success': False, 'message': f'Bulk write error: {bwe.details}'}
        except Exception as e:
            current_app.logger.error(f"Error updating quantities: {str(e)}")
            return {'success': False, 'message': f'Error updating quantities: {str(e)}'}
    @staticmethod
    def get_product(productid):
        try:
            db = get_db()
            product = db['products'].find_one({"product_id": productid})
            if product:
                product['_id'] = str(product['_id'])  # Convert ObjectId to string
            return product
        except Exception as e:
            current_app.logger.error(f"Error fetching product {productid}: {str(e)}")
            return None

    @staticmethod
    def get_products(product_ids):
        try:
            db = get_db()
            query = {
                'product_id': {'$in': product_ids},
                'quantity': {'$gt': 0}  # Corrected to use '$gt' for greater than
            }
            products_cursor = db['products'].find(query, {'_id': 0})
            products_list = list(products_cursor)
            return products_list
        except Exception as e:
            current_app.logger.error(f"Error fetching products by IDs: {str(e)}")
            return []

    @staticmethod
    def insert_fake_history():
        try:
            db = get_db()
            users = list(db['users'].find())
            products = list(db['products'].find())
            user_product_history = []

            for user in users:
                for _ in range(random.randint(1, 5)):
                    product = random.choice(products)
                    history_entry = {
                        'user_id': user['_id'],
                        'product_id': product['product_id'],
                        'event_date': datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(1, 365)),
                        'type': 'view'
                    }
                    user_product_history.append(history_entry)

            result = db['user_product_history'].insert_many(user_product_history)
            return {'success': True, 'message': f'Inserted {len(result.inserted_ids)} records into user_product_history'}
        except Exception as e:
            current_app.logger.error(f"Error inserting fake history: {str(e)}")
            return {'success': False, 'message': f'Error inserting fake history: {str(e)}'}

    @staticmethod
    def insert_user_history(product_id, user_id):
        try:
            db = get_db()

            history_entry = {
                'user_id': user_id,
                'product_id': product_id,
                'event_date': datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(1, 365)),
                'type': 'view',
            }

            result = db['user_product_history'].insert_one(history_entry)
            return {'success': True, 'message': 'Inserted 1 record into user_product_history'}
        except Exception as e:
            current_app.logger.error(f"Error inserting history: {str(e)}")
            return {'success': False, 'message': f'Error inserting history: {str(e)}'}
class Review:
    @staticmethod
    def create_review(data):
        try:
            db = get_db()
            db['reviews'].insert_one(data)
        except Exception as e:
            current_app.logger.error(f"Error creating review: {str(e)}")

    @staticmethod
    def get_reviews_for_product(product_id):
        try:
            db = get_db()
            return list(db['reviews'].find({"product_id": product_id}))
        except Exception as e:
            current_app.logger.error(f"Error fetching reviews for product {product_id}: {str(e)}")
            return []
