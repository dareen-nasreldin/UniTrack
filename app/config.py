import os


class Config:
    SECRET_KEY    = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    DATABASE_URL  = os.environ.get('DATABASE_URL')
    DEBUG         = False


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG        = False
    SECRET_KEY   = os.environ.get('SECRET_KEY')
    DATABASE_URL = os.environ.get('DATABASE_URL')


config_map = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
