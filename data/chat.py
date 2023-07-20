from data.db import db
from data.user import Users

class Chats(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    name = db.Column(db.String(50))
    model = db.Column(db.String(50))
    properties = db.Column(db.String(300))
    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'model': self.model,
            'properties': self.properties
        }
    
class ChatEntrys(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chat_id = db.Column(db.Integer, db.ForeignKey("chats.id"))
    role = db.Column(db.String(50))
    content = db.Column(db.Text(90000))
    datetime = db.Column(db.DateTime)
    def serialize(self):
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'role': self.role,
            'content': self.content,
            'datetime': self.datetime.isoformat()
        }