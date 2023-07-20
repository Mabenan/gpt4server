from app import app
from data.db import db
from security import token_required
from flask import jsonify, request, make_response, stream_with_context
from data.chat import Chats, ChatEntrys
from datetime import datetime
from gpt4all import GPT4All
import os
import json

@app.route("/gpt/model/list", methods=['GET'])
@token_required
def get_model_list(current_user):
    return jsonify(GPT4All.list_models())

@app.route("/gpt/chat/<chat_id>", methods=['GET'])
@token_required
def chat(current_user, chat_id):
    data = request.get_json()
    chat: Chats = db.session.get(Chats, chat_id)
    properties = json.loads(chat.properties)
    if chat.user_id != current_user.id:
        return make_response('not allowed',  403)
    app_data_loc = os.environ.get('APP_DATA_LOC')
    model = GPT4All(chat.model, model_path=app_data_loc)
    def chat_stream():
        with model.chat_session():
            limit = data["limit"] if 'limit' in data else 0
            if limit == 0:
                chatEntrys = ChatEntrys.query.filter(ChatEntrys.chat_id == chat.id).order_by(ChatEntrys.datetime.desc()).all()
            else:
                chatEntrys = ChatEntrys.query.filter(ChatEntrys.chat_id == chat.id).order_by(ChatEntrys.datetime.desc()).limit(limit).all()
            
            for chatEntry in reversed(chatEntrys):
                model.current_chat_session.append({"role": chatEntry.role, "content": chatEntry.content})
            generate_kwargs = dict(
                prompt=data["prompt"],
                temp = properties["temp"],
                top_k = properties["top_k"],
                top_p = properties["top_p"],
                repeat_penalty = properties["repeat_penalty"],
                repeat_last_n = properties["repeat_last_n"],
                n_predict = properties["n_predict"],
                n_batch = properties["n_batch"]
            )
            model.current_chat_session.append({"role": "user", "content": data["prompt"]})
            generate_kwargs['prompt'] = model._format_chat_prompt_template(messages=model.current_chat_session)
            db.session.add(ChatEntrys(chat_id = chat.id, role = "user", content = data["prompt"], datetime = datetime.now()))
            generate_kwargs['reset_context'] = len(model.current_chat_session) == 1
            resp = model.model.prompt_model_streaming(**generate_kwargs)
            compResp = ''
            for respEntry in resp:
                compResp = compResp + respEntry
                yield respEntry
            db.session.add(ChatEntrys(chat_id = chat.id, role = "assistant", content = compResp, datetime = datetime.now()))
            db.session.commit()
    return app.response_class(stream_with_context(chat_stream()), mimetype='text/plain')

