"""Database models and initialization for City Services API."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ServiceModel(db.Model):
    """Database model for city services."""
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    type = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type
        }


def init_db(app):
    """Initialize database with Flask app."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
