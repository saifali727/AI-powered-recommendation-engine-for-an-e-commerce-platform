import os

class Config:
    """Base configuration."""
    SECRET_KEY = 'bK2Rq9VazTnp3j8S1wWO59mnrIV72g2jv7GIxLeMjGE'
    MONGODB_URI = 'mongodb+srv://saif:bG8aqfirVhMApT#@atlascluster.uph9tug.mongodb.net/?retryWrites=true&w=majority&appName=AtlasCluster'
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your_jwt_secret_key')
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    MONGO_URI = os.getenv('DEV_MONGO_URI', 'mongodb://localhost:27017/your_dev_database')

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    MONGO_URI = os.getenv('TEST_MONGO_URI', 'mongodb://localhost:27017/your_test_database')

class ProductionConfig(Config):
    """Production configuration."""
    MONGO_URI = os.getenv('PROD_MONGO_URI', 'mongodb://localhost:27017/your_prod_database')

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

def get_config(config_name):
    return config_by_name.get(config_name, Config)
