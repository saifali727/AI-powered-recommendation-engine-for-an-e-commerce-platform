import jwt
from bson import ObjectId
from flask import Blueprint, jsonify, request
from models import Product, User
from flask import current_app
import csv
import io
import chardet
products_blueprint = Blueprint('products', __name__)

@products_blueprint.route('/products', methods=['GET'])
def get_products():
    try:
        page = int(request.args.get('page', 1))  # Get page number from query parameter, default to 1
        per_page = int(request.args.get('per_page', 10))
        main_category = request.args.get('main_category', 'sports & fitness')
        sub_category = request.args.get('sub_category', 'All Exercise & Fitness')

        products = Product.get_paginated(page, per_page, main_category, sub_category)
        return products
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_blueprint.route('/create-categories', methods=['GET'])
def create_categories():
    try:
        products = Product.create_categories()
        return products
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_blueprint.route('/categories', methods=['GET'])
def get_categories():
    try:
        cats = Product.get_categories()
        return cats
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_blueprint.route('/update-quantities', methods=['GET'])
def update_quantities():
    try:
        products = Product.update_quantities()
        return products
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_blueprint.route('/update-product', methods=['GET'])
def update_product():
    try:
        products = Product.update_product()
        return products
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_blueprint.route('/product/<productid>', methods=['GET'])
def get_product(productid):
    try:
        product = Product.get_product(productid)
        if product:
            return jsonify(product)
        else:
            return jsonify({"error": "Product not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @products_blueprint.route('/products', methods=['POST'])
# def create_products():
#     try:
#         data = request.json  # Parse JSON data from the request body
#         products = data.get('products')
#         # return products
#         if not products:
#             return jsonify({"error": "No products provided"}), 400
#         if not isinstance(products, list):
#             return jsonify({"error": "Data should be an array of products"}), 400
#
#         # Validate products
#         valid_products = []
#         for product in products:
#             if all(product.get(key) is not None for key in
#                    ["ratings", "no_of_ratings", "discount_price", "actual_price"]):
#                 valid_products.append(product)
#
#         if not valid_products:
#             return jsonify({"error": "No valid products to insert"}), 400
#
#         # Insert valid products into the database
#         Product.insert_many(valid_products)
#         return jsonify({"message": "Products created successfully"}), 201
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

def decode_file(file):
    # Detect file encoding
    file_content = file.stream.read()
    encoding = chardet.detect(file_content)['encoding']
    file.stream.seek(0)  # Reset file stream position for further use
    try:
        return io.StringIO(file_content.decode(encoding), newline=None)
    except UnicodeDecodeError:
        raise UnicodeDecodeError("Unable to decode file with detected encoding.")

def clean_data(data):
    # Clean up unwanted characters in data
    return data.replace('â‚¹', '₹').replace('\u200c', '')

@products_blueprint.route('/products', methods=['POST'])
def create_products():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if not file.filename.endswith('.csv'):
            return jsonify({"error": "Invalid file format"}), 400

        # Decode the file
        try:
            stream = decode_file(file)
        except UnicodeDecodeError as e:
            return jsonify({"error": str(e)}), 400

        reader = csv.DictReader(stream)
        products = []
        for row in reader:
            # Clean data for each product
            cleaned_row = {key: clean_data(value) for key, value in row.items()}
            products.append(cleaned_row)

        # Validate products
        # Filter out invalid products
        valid_products = [
            product for product in products if all(
                product.get(key) not in [None, "", " ", "()", []] for key in
                ["rating", "rating_count", "discounted_price", "actual_price"]
            )
        ]

        if not valid_products:
            return jsonify({"error": "No valid products to insert"}), 400

        # Insert valid products into the database
        Product.insert_many(valid_products)
        return jsonify({"message": "Products created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@products_blueprint.route('/user-product-history', methods=['GET'])
def insert_fake_history():
    result = Product.insert_fake_history()
    try:
        return {'message': f'Successfully inserted {len(result)} records into user_product_history'}, 200
    except Exception as e:
        return {'error': str(e)}, 500

@products_blueprint.route('/create-user-product-history', methods=['POST'])
def insert_user_history():
    data = request.json  # Access the posted data
    product_id = data['product_id']
    user_id = data['user_id']
    result = Product.insert_user_history(product_id, user_id)
    try:
        return {'message': f'Successfully inserted {len(result)} records into user_product_history'}, 200
    except Exception as e:
        return {'error': str(e)}, 500

@products_blueprint.route('/filter', methods=['GET'])
def filter():
    from knn import recommend_products

    # Get the JWT token from the Authorization header

    user_id = request.args.get('user_id')
    product_id = request.args.get('product_id')
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.replace('Bearer ', '')  # Remove 'Bearer ' from the token
    else:
        return jsonify({'message': 'Token is missing!'}), 401


    # Get product_ids from query parameters
    product_ids = User.get_user_history(user_id)
    # Ensure user_id is in the correct format (ObjectId if necessary)
    # print("product_ids product.py",product_ids)

    # Fetch recommended products
    recommended_product_ids = recommend_products(user_id, product_ids)
    # print("recommended_product_ids",recommended_product_ids)

    # Get detailed product information
    recommended_products = Product.get_products(recommended_product_ids)
    # print(recommended_products)

    # Return recommended products as JSON
    return jsonify({'products': recommended_products})

