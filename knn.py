import random

import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans
from bson import ObjectId  # Import ObjectId from bson
from models import Product, User  # Assuming User model is also available


def load_and_preprocess_data():
    try:
        # Load data
        product_data = Product.get_all()
        user_data = User.get_all()

        # Convert to DataFrames
        products = pd.DataFrame(product_data)
        users = pd.DataFrame(user_data)

        # Validate data formats
        if products.empty or users.empty:
            raise ValueError("Data is empty or could not be loaded correctly.")

        # Preprocess product data
        products = preprocess_products(products)

        # Preprocess user data
        users = preprocess_users(users)

        return products, users

    except Exception as e:
        raise RuntimeError(f"Error loading or preprocessing data: {str(e)}")


# def preprocess_products(products):
#     # Handle missing values and convert types
#     products['discounted_price'] = pd.to_numeric(products['discounted_price'].replace({'₹': '', ',': ''}, regex=True),
#                                                  errors='coerce')
#     products['actual_price'] = pd.to_numeric(products['actual_price'].replace({'₹': '', ',': ''}, regex=True),
#                                              errors='coerce')
#     products['rating'] = pd.to_numeric(products['rating'], errors='coerce')
#     products['rating_count'] = pd.to_numeric(products['rating_count'].replace({',': ''}, regex=True), errors='coerce')
#     products['product_id'] = products['_id'].astype(str)  # Ensure product_id is string representation of ObjectId
#
#     # Drop rows with NaN values in specific columns
#     products = products.dropna(subset=['discounted_price', 'actual_price', 'rating', 'rating_count'])
#
#     # Keep only products with a positive quantity
#     products = products[products['quantity'] > 0]
#
#     # Process main and subcategories
#     if 'main_category' in products.columns and 'sub_category' in products.columns:
#         main_categories = pd.get_dummies(products['main_category'], prefix='main_cat')
#         sub_categories = pd.get_dummies(products['sub_category'], prefix='sub_cat')
#         products = pd.concat([products, main_categories, sub_categories], axis=1)
#
#     return products

def preprocess_products(products):
    # Handle missing values and convert types
    products['discounted_price'] = pd.to_numeric(products['discounted_price'].replace({'₹': '', ',': ''}, regex=True),
                                                 errors='coerce').fillna(random.randrange(100,200))
    products['actual_price'] = pd.to_numeric(products['actual_price'].replace({'₹': '', ',': ''}, regex=True),
                                             errors='coerce').fillna(random.randrange(200,250))
    products['rating'] = pd.to_numeric(products['rating'], errors='coerce').fillna(random.randrange(2,5))
    products['rating_count'] = pd.to_numeric(products['rating_count'].replace({',': ''}, regex=True), errors='coerce').fillna(random.randrange(1000,2000))
    products['product_id'] = products['product_id']

    # Fill missing quantity with a default value, e.g., 0
    products['quantity'] = products['quantity']

    # Process main and subcategories, fill missing with a default category
    products['main_category'] = products['main_category'].fillna('unknown')
    products['sub_category'] = products['sub_category'].fillna('unknown')

    if 'main_category' in products.columns and 'sub_category' in products.columns:
        main_categories = pd.get_dummies(products['main_category'], prefix='main_cat')
        sub_categories = pd.get_dummies(products['sub_category'], prefix='sub_cat')
        products = pd.concat([products, main_categories, sub_categories], axis=1)

    return products
def preprocess_users(users):
    if 'dob' in users.columns:
        users['dob'] = pd.to_datetime(users['dob'], errors='coerce')
        today = pd.to_datetime('today')
        users['age'] = users['dob'].apply(
            lambda x: (today.year - x.year) - ((today.month, today.day) < (x.month, x.day)))
        users['age'] = users['age'].fillna(users['age'].mean())

    # Encode categorical features
    users = pd.get_dummies(users, columns=['gender'], drop_first=True)

    return users


# Load and preprocess data
products, users = load_and_preprocess_data()

# Select numeric features for the product model
product_features = ['discounted_price', 'rating'] + [col for col in products.columns if
                                                     col.startswith('main_cat_') or col.startswith('sub_cat_')]

# Fit the Nearest Neighbors model
knn = NearestNeighbors(n_neighbors=10, algorithm='auto')
knn.fit(products[product_features])

# Fit the KMeans model for user clustering
kmeans = KMeans(n_clusters=5, random_state=42)
kmeans.fit(users[['age'] + [col for col in users.columns if col.startswith('gender_')]])
users['cluster'] = kmeans.labels_

user_recommendation_attempted = False


def recommend_products(user_id, product_ids=None, num_recommendations=6):
    global user_recommendation_attempted
    if product_ids is None:
        product_ids = []

    if isinstance(user_id, list):
        raise TypeError("user_id should not be a list")
    user_id = ObjectId(user_id) if not isinstance(user_id, ObjectId) else user_id

    recommendations = []
    product_ids_from_similar_users = []  # Initialize here

    for product_id in product_ids:
        if product_id not in products['product_id'].values:
            # Product ID {product_id} not found in the dataset
            continue

        product_index = products[products['product_id'] == product_id].index[0]
        distances, indices = knn.kneighbors(products.iloc[product_index][product_features].values.reshape(1, -1),
                                            n_neighbors=num_recommendations + 1)
        recommended_indices = indices.flatten()[1:]
        recommended_products = products.iloc[recommended_indices]
        recommendations.extend(recommended_products['product_id'])

        if not recommendations and not user_recommendation_attempted:
            user_recommendation_attempted = True
            user_data = users[users['_id'] == user_id]
            user_cluster = user_data['cluster'].values[0]
            user_age = user_data['age'].values[0]
            user_gender_columns = [col for col in users.columns if
                                   col.startswith('gender_') and user_data[col].values[0] == 1]

            similar_users = users[
                (users['cluster'] == user_cluster) & (users['age'].between(user_age - 5, user_age + 5))]

            for col in user_gender_columns:
                similar_users = similar_users[similar_users[col] == 1]

            similar_user_ids = similar_users['_id'].tolist()
            product_ids_from_similar_users = User.get_users_history(similar_user_ids)
            product_ids_from_similar_users = list(set(product_ids_from_similar_users))

        if product_ids_from_similar_users:
            return recommend_products(user_id, product_ids_from_similar_users, num_recommendations)

    user_recommendation_attempted = False
    if recommendations:
        # Convert the list of product IDs to the desired format
        return list(pd.DataFrame(recommendations, columns=['product_id'])['product_id'].astype(str))
    else:
        return []


