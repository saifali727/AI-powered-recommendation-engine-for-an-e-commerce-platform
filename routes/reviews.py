from flask import Blueprint, request, jsonify
from models import Review

reviews = Blueprint('reviews', __name__)

@reviews.route('/products/<product_id>/reviews', methods=['GET'])
def get_reviews(product_id):
    product_reviews = Review.get_reviews_for_product(product_id)
    return jsonify(product_reviews)

@reviews.route('/products/<product_id>/reviews', methods=['POST'])
def add_review(product_id):
    data = request.get_json()
    data['product_id'] = product_id
    Review.create_review(data)
    return jsonify({"message": "Review added successfully"}), 201
