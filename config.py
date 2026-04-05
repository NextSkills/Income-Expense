import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fiscal-architect-secret-key-2024')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///fiscal_architect.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    SESSION_TYPE = 'sqlalchemy'
    SESSION_USE_SIGNER = True
