from langchain.llms import GPT4All
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

template = """
            {history}
            ### Human: {input}
            ### Assistant:"""
history = ConversationBufferMemory(ai_prefix="### Assistant", human_prefix="### Human")
prompt = PromptTemplate(template=template, input_variables=["history","input"])
llmObj = GPT4All(model = "/home/daniel/.cache/gpt4all/ggml-model-gpt4all-falcon-q4_0.bin", verbose=False, allow_download=True, n_threads=8)
history.load_memory_variables({})
chain = ConversationChain(prompt=prompt, llm=llmObj, memory=history)
predicted = chain.predict(input="Hi I'm Daniel")
print(predicted)
predicted2 = chain.predict(input="What is my Name?")
print(predicted2)