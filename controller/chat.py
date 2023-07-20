from app import app
from data.db import db
from security import token_required
from flask import jsonify, request, make_response
from data.chat import Chats, ChatEntrys
import json

@app.route("/chat/<chat_id>", methods=['GET'])
@token_required
def get_chat(current_user, chat_id):
    chat = db.get_or_404(Chats, chat_id)
    if chat.user_id == current_user.id:
        return jsonify(chat.serialize())
    else:
        return make_response('not allowed',  403)

@app.route("/chat/<chat_id>", methods=['PATCH'])
@token_required
def update_chat(current_user, chat_id):
    chat = db.get_or_404(Chats, chat_id)
    data = request.get_json()
    if chat.user_id == current_user.id:
        if 'model' in data:
            chat.model = data["model"]
        if 'properties' in data:
            oldProps = json.loads(chat.properties)
            chat.properties = json.dumps( dict( 
                temp = data["properties"]["temp"] if "temp" in data["properties"] else oldProps["temp"],
                top_k = data["properties"]["top_k"] if "top_k" in data["properties"] else oldProps["top_k"],
                top_p = data["properties"]["top_p"] if "top_p" in data["properties"] else oldProps["top_p"],
                repeat_penalty = data["properties"]["repeat_penalty"] if "repeat_penalty" in data["properties"] else oldProps["repeat_penalty"],
                repeat_last_n = data["properties"]["repeat_last_n"] if "repeat_last_n" in data["properties"] else oldProps["repeat_last_n"],
                n_predict = data["properties"]["n_predict"] if "n_predict" in data["properties"] else oldProps["n_predict"],
                n_batch = data["properties"]["n_batch"] if "n_batch" in data["properties"] else oldProps["n_batch"] ) )
        db.session.commit()
        return jsonify(chat.serialize())
    else:
        return make_response('not allowed',  403)
@app.route("/chat/<chat_id>", methods=['DELETE'])
@token_required
def delete_chat(current_user, chat_id):
    chat = db.get_or_404(Chats, chat_id)
    if chat.user_id == current_user.id:
        chatEntrys = ChatEntrys.query.filter(ChatEntrys.chat_id == chat_id).all()
        for chatEntry in chatEntrys:
            db.session.delete(chatEntry)
        db.session.delete(chat)
        db.session.commit()
        return make_response('deleted', 200)
    else:
        return make_response('not allowed',  403)

@app.route("/chat", methods=['POST'])
@token_required
def add_chat(current_user):
    data = request.get_json()
    chat = Chats(
        user_id = current_user.id,
        name = data['name'],
        model = data['model'],
        properties = json.dumps( dict(
                temp = data["properties"]["temp"] if "temp" in data["properties"] else 0.7,
                top_k = data["properties"]["top_k"] if "top_k" in data["properties"] else 1,
                top_p = data["properties"]["top_p"] if "top_p" in data["properties"] else 0.1,
                repeat_penalty = data["properties"]["repeat_penalty"] if "repeat_penalty" in data["properties"] else 1.18,
                repeat_last_n = data["properties"]["repeat_last_n"] if "repeat_last_n" in data["properties"] else 64,
                n_predict = data["properties"]["n_predict"] if "n_predict" in data["properties"] else 200,
                n_batch = data["properties"]["n_batch"] if "n_batch" in data["properties"] else 8) )
    )
    db.session.add(chat)
    db.session.commit()
    if chat.user_id == current_user.id:
        return jsonify(chat.serialize())
    else:
        return make_response('not allowed',  403)
    
@app.route("/chat/list", methods=["GET"])
@token_required
def list_chats(current_user):
    chats = Chats.query.filter(Chats.user_id == current_user.id).all()
    chatsJson = []
    for chat in chats:
        chatsJson.append(chat.serialize())
    return make_response(chatsJson)

@app.route("/chat/<chat_id>/entry/list", methods=["GET"])
@token_required
def list_chat_entrys(current_user, chat_id):
    chat = db.get_or_404(Chats, chat_id)
    if chat.user_id == current_user.id:
        chatEntrys = ChatEntrys.query.filter(ChatEntrys.chat_id == chat_id).all()
        chatsJson = []
        for chatEntry in chatEntrys:
            chatsJson.append(chatEntry.serialize())
        return make_response(chatsJson)
    else:
        return make_response('not allowed',  403)