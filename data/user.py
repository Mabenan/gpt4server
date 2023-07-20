from data.db import db

class Users(db.Model):
     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
     public_id = db.Column(db.Integer)
     name = db.Column(db.String(50))
     password = db.Column(db.String(50))
     admin = db.Column(db.Boolean)
     def serialize(self):
          return {
               'name': self.name,
               'admin': self.admin
          }