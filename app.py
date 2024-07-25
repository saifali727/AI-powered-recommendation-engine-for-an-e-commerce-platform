from flask import Flask, render_template, request
from config import Config
from routes.auth import auth
from routes.products import products_blueprint
from routes.reviews import reviews
from flask_caching import Cache
import webbrowser
app = Flask(__name__)
app.config.from_object(Config)
import requests as request
# Initialize caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

app.register_blueprint(auth, url_prefix='/api/auth')
app.register_blueprint(products_blueprint, url_prefix='/api')
app.register_blueprint(reviews, url_prefix='/api')

@app.route('/')
@cache.cached(timeout=300)  # Cache the home page for 5 minutes
def index():
    return render_template('signup.html')

@app.route('/login')
@cache.cached(timeout=300)  # Cache the login page for 5 minutes
def login():
    return render_template('login.html')

@app.route('/product_display')
@cache.cached(timeout=300)  # Cache product display for 5 minutes
def product_display():
    product_id = request.args.get('product_id')
    return render_template('product_display.html', product_id=product_id)

@app.route('/products')
@cache.cached(timeout=300)  # Cache products page for 5 minutes
def products():
    return render_template('products.html')

if __name__ == '__main__':
    webbrowser.open_new('http://127.0.0.1:5000/')
        # Start the Flask app after the API call is complete
    app.run(debug=True, host='0.0.0.0', port=5000)