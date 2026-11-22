
import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True      # auto reload and tracebacks on own machine  


class TestingConfig(Config):
    TESTING = True                   # db.py use testdbname


class ProductionConfig(Config):
    pass                             # no debug and traceback


CONFIGS = {"development": DevelopmentConfig,
           "testing": TestingConfig,
           "production": ProductionConfig}
