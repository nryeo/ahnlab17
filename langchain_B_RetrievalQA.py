#!/usr/bin/env python
# coding: utf-8

# # Question Answering


import os
import time
import json
import sys
from typing import Iterable, List
from langchain.docstore.document import Document

import openai

from dotenv import load_dotenv

load_dotenv()


openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("ORGANIZATION")
sys.path.append(os.getenv("PYTHONPATH"))
llm_model = "gpt-3.5-turbo"
PDF_FILE = "./data/프리랜서 가이드라인 (출판본).pdf"
CSV_FILE = "data/OutdoorClothingCatalog_1000.csv"

from langchain.vectorstores import FAISS
from langchain.vectorstores import Chroma
from langchain.schema.vectorstore import VectorStore
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from utils import (
  load_pdf_vectordb,
  load_vectordb_from_file,
  get_vectordb_path_by_file_path
  )

llm = ChatOpenAI(model_name=llm_model, temperature=0)

def test_simple(vectordb, question)-> None:
  # question = "프리랜서들이 피해야 할 회사는 어떤 회사인가?"
  docs = vectordb.similarity_search(question,k=3)
  print(f"len(docs)=>{len(docs)}")

  qa_chain = RetrievalQA.from_chain_type(
    llm,
    retriever=vectordb.as_retriever()
  )

  result = qa_chain({"query": question})
  print(f"result['result']=>{result['result']}")



from langchain.prompts import PromptTemplate

def test_prompt(vectordb, question)-> None:
  # Build prompt
  # 마지막에 다음 문맥을 사용하여 질문에 답하세요. 답을 모르는 경우, 답을 지어내려고 하지 말고 모른다고만 말하세요. 최대 세 문장을 사용하세요. 가능한 한 간결하게 답변하세요. 답변 마지막에는 항상 "질문해 주셔서 감사합니다!"라고 말하세요.
  template = """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer. Use three sentences maximum. Keep the answer as concise as possible. Always say "thanks for asking!" at the end of the answer.
    {context}
    Question: {question}
    Helpful Answer:"""
  QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

  # Run chain
  qa_chain = RetrievalQA.from_chain_type(
    llm,
    retriever=vectordb.as_retriever(),
    return_source_documents=True,
    chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
  )

  result = qa_chain({"query": question})
  print(f"result['result']=>{result['result']}")
  print(f"result['source_documents'][0] = > {result['source_documents'][0]}")



def test_map_reduce(vectordb, question)-> None:

  qa_chain_mr = RetrievalQA.from_chain_type(
    llm,
    retriever=vectordb.as_retriever(),
    chain_type="map_reduce"
  )
  result = qa_chain_mr({"query": question})
  print(f"result['result']=>{result['result']}")

'''
Stuff 접근 방식은 다음과 같습니다:

    모든 문서를 하나의 문자열로 결합합니다.

    결합된 문자열을 LLM에 입력으로 전달하여 요약을 생성합니다.

    이는 매우 간단하지만 문서가 많고 길 경우 LLM의 context window를 초과할 수 있습니다.

Map-reduce 접근 방식은 다음 과정을 거칩니다:

    Map: 각 문서를 개별적으로 LLM에 전달하여 요약을 생성합니다.

    Reduce: 생성된 각 문서 요약을 결합하여 최종 요약을 생성합니다.

    필요 시 문서 요약들을 반복적으로 결합하여 최종 요약을 만듭니다.

    Map-reduce는 더 복잡하지만 문맥을 초과하는 문제를 피할 수 있습니다.

요약하면, Stuff는 간단하고 Map-reduce는 복잡하지만 더 큰 문서 집합을 처리할 수 있습니다. 문서 크기와 LLM의 능력에 따라 적절한 접근 방식을 선택하는 것이 좋습니다.
'''


def test_pdf():
  print("="*30)
  vectordb : FAISS = load_vectordb_from_file(PDF_FILE)
  print("Number of vectors in the index:", vectordb.index.ntotal)
  q = "프리랜서들이 피해야 할 회사는 어떤 회사인가?"

  test_simple(vectordb, q)
  test_prompt(vectordb, q)
  test_map_reduce(vectordb, q)


def test_csv():
  print("="*30)
  vectordb : FAISS = load_vectordb_from_file(CSV_FILE)
  print("Number of vectors in the index:", vectordb.index.ntotal)
  q = "잘 구김가지 않고 통기성이 좋은 셔츠를 추천해줘"

  test_simple(vectordb, q)
  test_prompt(vectordb, q)
  test_map_reduce(vectordb, q)



if __name__ == '__main__':
  # test_pdf()
  test_csv()





'''
# If you wish to experiment on the `LangChain plus platform`:
#
#  * Go to [langchain plus platform](https://www.langchain.plus/) and sign up
#  * Create an API key from your account's settings
#  * Use this API key in the code below
#  * uncomment the code
#  Note, the endpoint in the video differs from the one below. Use the one below.

# In[20]:


#import os
#os.environ["LANGCHAIN_TRACING_V2"] = "true"
#os.environ["LANGCHAIN_ENDPOINT"] = "https://api.langchain.plus"
#os.environ["LANGCHAIN_API_KEY"] = "..." # replace dots with your api key


# In[21]:


qa_chain_mr = RetrievalQA.from_chain_type(
  llm,
  retriever=vectordb.as_retriever(),
  chain_type="map_reduce"
)
result = qa_chain_mr({"query": question})
result["result"]


# In[22]:


qa_chain_mr = RetrievalQA.from_chain_type(
  llm,
  retriever=vectordb.as_retriever(),
  chain_type="refine"
)
result = qa_chain_mr({"query": question})
result["result"]


# ### RetrievalQA limitations
#
# QA fails to preserve conversational history.

# In[23]:


qa_chain = RetrievalQA.from_chain_type(
  llm,
  retriever=vectordb.as_retriever()
)


# In[24]:


question = "Is probability a class topic?"
result = qa_chain({"query": question})
result["result"]


# In[25]:


question = "why are those prerequesites needed?"
result = qa_chain({"query": question})
result["result"]


# Note, The LLM response varies. Some responses **do** include a reference to probability which might be gleaned from referenced documents. The point is simply that the model does not have access to past questions or answers, this will be covered in the next section.

# In[26]:


question = "확률도 수업 주제인가요?"
result = qa_chain({"query": question})
result["result"]


# In[ ]:




'''