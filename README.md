# KNN-Based Product Recommendation System

This project is a working prototype of a recommendation model created using generative AI. It includes a UI design and Flask APIs to demonstrate the functionality of the model.

## Installation

To get started, clone the repository and install the required packages:
make sure to have latest version of python
```bash
git clone https://github.com/saifali727/AI-powered-recommendation-engine-for-an-e-commerce-platform.git
cd AI-powered-recommendation-engine-for-an-e-commerce-platform
run setup_and_run.bat ( for windows)
run setup_and_run.sh ( for mac and linux)
```

# Model Performance Overview
## Initial Setup:

When you first run the server, the model will need some time to set up. This is because it needs to create clusters and process data for the initial load. Think of it as the model’s “warm-up” phase where it prepares itself to handle requests efficiently.

## Post Initialization:

Once the clustering is done, the performance improves significantly. Future calls to the model will be much faster and more efficient, even with a large number of users. The model has already done the heavy lifting, so it can swiftly handle subsequent requests with minimal delay.

## In Summary:

First Run: Slightly slower as the model creates clusters.
Subsequent Runs: Much faster due to pre-computed clusters and optimizations.
This initial setup ensures that, despite the initial wait, the model delivers rapid and reliable performance for all future interactions.

the model takes time only the first time on running server  when it create clusters. after it every call will be much faster for large number of users to handle
## How to Test the Model

- **Signup and Login**: The application starts with a signup page. You need to first signup and then log in to access the application.
- **Default Credentials**: You can use the following default credentials to log in:
  - Email: saif@gmail.com
  - Password: 12345678
- **Product Listing**: Upon login, you will see a list of products and categories.
  - The product data is sourced from Kaggle: [Amazon Products Dataset](https://www.kaggle.com/datasets/lokeshparab/amazon-products-dataset)
- **Recommended Products**: At the end of the product listing page, you can see your recommended products.
- **Product Details**: Clicking on each product opens a new page where you can see more details about the product and additional recommendations.

1. **Signup and Login**:
   - Open the application and navigate to the signup page.
   - Create a new account or use the default credentials provided above to log in.
2. **View Products and Recommendations**:
   - After logging in, browse the list of products and categories.
   - Scroll to the bottom of the page to see the recommended products.
   - Click on a product to open its detail page, where you will also find more recommended products.

## Model Explanation

The core functionality of the recommendation engine is implemented in `knn.py`. This file contains the logic for the K-Nearest Neighbors (KNN) algorithm, which is used to generate product recommendations based on user behavior and product similarities.

This project implements a K-Nearest Neighbors (KNN) model for recommending products to users based on their browsing history and demographic information. It also employs KMeans clustering to group users with similar characteristics, enhancing the recommendation accuracy.

## Table of Contents

1. [Installation](#installation)
2. [Data Loading and Preprocessing](#data-loading-and-preprocessing)
3. [Model Training](#model-training)
4. [Product Recommendation](#product-recommendation)
5. [Running the Code](#running-the-code)
6. [Dependencies](#dependencies)


## Data Loading and Preprocessing

### Data Loading

The data is loaded from the `Product` and `User` models. These models are assumed to be ORM representations of  product and user collections in a database.

```python
def load_and_preprocess_data():
    try:
        product_data = Product.get_all()
        user_data = User.get_all()

        products = pd.DataFrame(product_data)
        users = pd.DataFrame(user_data)

        if products.empty or users.empty:
            raise ValueError("Data is empty or could not be loaded correctly.")

        products = preprocess_products(products)
        users = preprocess_users(users)

        return products, users

    except Exception as e:
        raise RuntimeError(f"Error loading or preprocessing data: {str(e)}")
```

### Data Preprocessing

#### Products

- Missing values in `discounted_price`, `actual_price`, `rating`, and `rating_count` are filled with random numbers within specified ranges.
- Categories (`main_category` and `sub_category`) are encoded using one-hot encoding.

```python
def preprocess_products(products):
    products['discounted_price'] = pd.to_numeric(products['discounted_price'].replace({'₹': '', ',': ''}, regex=True),
                                                 errors='coerce').fillna(random.randrange(100,200))
    products['actual_price'] = pd.to_numeric(products['actual_price'].replace({'₹': '', ',': ''}, regex=True),
                                             errors='coerce').fillna(random.randrange(200,250))
    products['rating'] = pd.to_numeric(products['rating'], errors='coerce').fillna(random.randrange(2,5))
    products['rating_count'] = pd.to_numeric(products['rating_count'].replace({',': ''}, regex=True), errors='coerce').fillna(random.randrange(1000,2000))
    products['product_id'] = products['product_id']
    products['main_category'] = products['main_category'].fillna('unknown')
    products['sub_category'] = products['sub_category'].fillna('unknown')

    if 'main_category' in products.columns and 'sub_category' in products.columns:
        main_categories = pd.get_dummies(products['main_category'], prefix='main_cat')
        sub_categories = pd.get_dummies(products['sub_category'], prefix='sub_cat')
        products = pd.concat([products, main_categories, sub_categories], axis=1)

    return products
```

#### Users

- Date of birth (`dob`) is converted to age.
- Gender is encoded using one-hot encoding.

```python
def preprocess_users(users):
    if 'dob' in users.columns:
        users['dob'] = pd.to_datetime(users['dob'], errors='coerce')
        today = pd.to_datetime('today')
        users['age'] = users['dob'].apply(
            lambda x: (today.year - x.year) - ((today.month, today.day) < (x.month, x.day)))
        users['age'] = users['age'].fillna(users['age'].mean())

    users = pd.get_dummies(users, columns=['gender'], drop_first=True)

    return users
```

## Model Training

### KNN Model for Products

The KNN model is trained using numerical features from the product data, specifically `discounted_price` and `rating`, along with the encoded category features.

```python
product_features = ['discounted_price', 'rating'] + [col for col in products.columns if
                                                     col.startswith('main_cat_') or col.startswith('sub_cat_')]

knn = NearestNeighbors(n_neighbors=10, algorithm='auto')
knn.fit(products[product_features])
```

### KMeans Clustering for Users

The KMeans model clusters users based on their age and gender.

```python
kmeans = KMeans(n_clusters=5, random_state=42)
kmeans.fit(users[['age'] + [col for col in users.columns if col.startswith('gender_')]])
users['cluster'] = kmeans.labels_
```

## Product Recommendation

The recommendation function finds similar products based on the KNN model. If a user's browsing history is not available, it recommends products based on the behavior of similar users.

```python
def recommend_products(user_id, product_ids=None, num_recommendations=6):
    global user_recommendation_attempted
    if product_ids is None:
        product_ids = []

    if isinstance(user_id, list):
        raise TypeError("user_id should not be a list")
    user_id = ObjectId(user_id) if not isinstance(user_id, ObjectId) else user_id

    recommendations = []
    product_ids_from_similar_users = []

    for product_id in product_ids:
        if product_id not in products['product_id'].values:
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
        return list(pd.DataFrame(recommendations, columns=['product_id'])['product_id'].astype(str))
    else:
        return []
```

## Running the Code

To run the preprocessing and recommendation functions, use the following:

```python
if __name__ == "__main__":
    try:
        products, users = load_and_preprocess_data()
    except Exception as e:
        print("Error during preprocessing:", str(e))
```

## Dependencies


- Ensure setup_and_run.bat or setup_and_run.sh  file runs smoothly if occur any error try as run with administrator.


This README provides a comprehensive overview of how the KNN model and KMeans clustering are utilized to recommend products to users based on their demographics and browsing history. Make sure to update the sections as per any changes in your actual implementation.
