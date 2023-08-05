from typing import Any, AsyncIterator, List, Optional

from app import app, hugmodels
from data.db import db
from security import token_required
from flask import jsonify, request, make_response, stream_with_context, Response
from data.chat import Chats, ChatEntrys
from datetime import datetime
from langchain import PromptTemplate, ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
from pathlib import Path
from langchain.llms import GPT4All
from functools import partial
from typing import Any, List
from langchain.callbacks.manager import AsyncCallbackManagerForLLMRun
from langchain.llms.utils import enforce_stop_tokens
import asyncio
import requests 
import os
import json
from langchain import HuggingFaceHub
from huggingface_hub import list_models

class AGPT4All(GPT4All):
    async def _acall(self, prompt: str, stop: List[str] | None = None, run_manager: AsyncCallbackManagerForLLMRun | None = None, **kwargs: Any) -> str:
        text_callback = None
        if run_manager:
            text_callback = partial(run_manager.on_llm_new_token, verbose=self.verbose)
        text = ""
        params = {**self._default_params(), **kwargs}
        n_predict = params["n_predict"] if 'n_predict' in params else None
        max_tokens = params["max_tokens"] if 'max_tokens' in params else 200
        if n_predict in params:
            params.pop("n_predict")
        if max_tokens in params:
            kwargs.pop("max_tokens")
        generate_kwargs = dict(
            prompt=prompt,
            **kwargs,
            n_predict=n_predict if n_predict is not None else max_tokens,
            reset_context = False,
        )
        for token in self.client.model.prompt_model_streaming(**generate_kwargs):
            if text_callback:
                await text_callback(token)
            text += token
        if stop is not None:
            text = enforce_stop_tokens(text, stop)
        return text

@app.route("/gpt/model/list", methods=['GET'])
@token_required
def get_model_list(current_user):
    llm = os.environ.get('LLM')
    if llm is None:
        llm = "GPT4All"
    if llm == "GPT4All":
        response = get_models_from_gpt()
        return app.make_response(response)
    else:
        return get_models_from_hug()

def get_models_from_gpt():
    return requests.get("https://gpt4all.io/models/models.json").json()

def get_models_from_hug():
    if len(hugmodels) == 0:
        models = list_models(cardData=True)
        modelJson = []
        for model in models:
            if hasattr(model, 'cardData') and ( "inference" not in model.cardData or model.cardData["inference"] == True ) and model.pipeline_tag == "text2text-generation":
                modelJsonEntry = dict(
                    filename=model.modelId,
                    order="",
                    md5sum="",
                    name=model.modelId,
                    filesize="",
                    ramrequired="",
                    parameters="",
                    quant="",
                    type="",
                    systemPrompt="",
                    description="",
                )
                modelJson.append(modelJsonEntry)
                hugmodels.append(modelJsonEntry)
        return jsonify(modelJson)
    else:
        return jsonify(hugmodels)
    

def iter_over_async(ait, loop):
    ait = ait.__aiter__()
    async def get_next():
        try: obj = await ait.__anext__(); return False, obj
        except StopAsyncIteration: return True, None
    while True:
        done, obj = loop.run_until_complete(get_next())
        if done: break
        yield obj
@app.route("/gpt/chat/<chat_id>", methods=['GET'])
@token_required
def chat(current_user, chat_id):
    data = request.get_json()
    chat: Chats = db.session.get(Chats, chat_id)
    properties = json.loads(chat.properties)
    if chat.user_id != current_user.id:
        return make_response('not allowed',  403)
    llm = os.environ.get('LLM')
    if llm is None:
        llm = "GPT4All"
    threadString = os.environ.get('GPT4ALL_THREADS')
    threads = None
    if threadString is not None:
        threads = int(threadString)
    app_data_loc = os.environ.get('APP_DATA_LOC')
    if app_data_loc is None:
        app_data_loc = Path.home().joinpath(".cache/gpt4all").as_posix()
    async def chat_stream() -> AsyncIterator[str]:
        limit = data["limit"] if 'limit' in data else 0
        history = ConversationBufferMemory(ai_prefix="### HUMAN:", human_prefix="### RESPONSE:")
        if limit == 0:
            chatEntrys = ChatEntrys.query.filter(ChatEntrys.chat_id == chat.id).order_by(ChatEntrys.datetime.desc()).all()
        else:
            chatEntrys = ChatEntrys.query.filter(ChatEntrys.chat_id == chat.id).order_by(ChatEntrys.datetime.desc()).limit(limit).all()
        
        for chatEntry in reversed(chatEntrys):
            if chatEntry.role == "user":
                history.chat_memory.add_user_message(chatEntry.content)
            elif chatEntry.role == "assistant":
                history.chat_memory.add_ai_message(chatEntry.content)
        template = """{history}
        ### HUMAN:
        {prompt}
        ### RESPONSE:"""
        prompt = PromptTemplate(template=template, input_variables=["history","input"])
        modelpath = Path(app_data_loc).joinpath(chat.model).as_posix()
        print(modelpath)
        llmObj = None
        streaminCallback = None
        if llm == 'GPT4All':
            streaminCallback = AsyncIteratorCallbackHandler()
            llmObj = AGPT4All(model = modelpath, verbose=False, allow_download=True,
                temp = properties["temp"],
                top_k = properties["top_k"],
                top_p = properties["top_p"],
                repeat_penalty = properties["repeat_penalty"],
                repeat_last_n = properties["repeat_last_n"],
                n_predict = properties["n_predict"],
                n_batch = properties["n_batch"],
                callbacks=[streaminCallback],
                n_threads= threads,
                streaming = True)
        elif llm == "Hugging":
            llmObj = HuggingFaceHub(
                repo_id=chat.model,
                model_kwargs={
                    "temperature": properties["temp"],
                    "max_length": properties["n_predict"],
                }
            )

        history.load_memory_variables({})
        chain = ConversationChain(prompt=prompt, llm=llmObj, memory=history)
        compResp = ''
        if streaminCallback is not None:
            asyncio.create_task(chain.apredict(input=data["prompt"]))
            start = datetime.now()
            tokenCount = 0
            async for respEntry in streaminCallback.aiter():
                now = datetime.now()
                diff = now - start
                tokenCount += 1
                print("Tokens per Second: " + str(tokenCount / diff.total_seconds()))
                compResp = compResp + respEntry
                yield respEntry
        else:
            compResp += chain.predict(input=data["prompt"])
            yield compResp
    
        db.session.add(ChatEntrys(chat_id = chat.id, role = "user", content = data["prompt"], datetime = datetime.now()))
        db.session.add(ChatEntrys(chat_id = chat.id, role = "assistant", content = compResp, datetime = datetime.now()))
        db.session.commit()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return app.response_class(stream_with_context(iter_over_async(chat_stream(), loop)), mimetype='text/plain')

