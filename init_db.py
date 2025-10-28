import os
from app import app
from database import db
from models import User

if not app or not db:
    raise Exception("App oder DB ist nicht korrekt importiert..")

with app.app_context():
    db.create_all()

    #wenn admin nicht vorhanden, admin erstellen:
    if not User.query.filter_by(username='admin').first():
        admin = User()
        admin.username = os.environ.get('ADMIN_USERNAME')
        admin.set_password(os.environ.get('ADMIN_PASSWORD'))
        db.session.add(admin)
        db.session.commit()
        print("Admin-Benutzer erstellt.")
