import re
# from langchain.vectorstores import Chroma
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.list import NumberedListOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
import chromadb
from decouple import config
from langchain.llms import OpenAI
import openai
import json


from question_answer.customEmbeddingsClass import CustomOpenAIEmbeddings
from .db_operations_utility import (
    get_processed_chat_history, 
    update_create_chat_history,
    update_create_ca_chat_history,
    get_formatted_chat_history,
)
from .reranking_utility import rerank, format_docs
from .enum_utility import Prompt

chroma_ip = config('CHROMA_IP')

api_key = config('OPEN_AI_API_KEY')
BASE_TRANSCRIPT_PATH = config('BASE_TRANSCRIPT_PATH')
ca_collection_name = config("CA_EMBEDDINGS_COLLECTION")


def filter_docs(docs, class_id):
    other_lecture = []
    for doc in docs:
        if doc.metadata['lecture_id'] != class_id:
            other_lecture.append(doc)

    return other_lecture


def get_top_k_docs(query, class_id, section=None, ca_query=False):
    top_k = 6
    client = chromadb.HttpClient(host=chroma_ip, port=8000)

    # Get the stored vector db
    embedding = CustomOpenAIEmbeddings(openai_api_key=api_key)
    
    if ca_query:
        collection_name = ca_collection_name
        if class_id:
            filter_data = {"article_id":{"$in":class_id}} if isinstance(class_id, list) else {"article_id":class_id}
        else :
            filter_data = {}
    else:
        # filter_data = {"source": f"{BASE_TRANSCRIPT_PATH}{class_id}_transcript.txt"}
        filter_data = {"source": f"{BASE_TRANSCRIPT_PATH}{class_id}/{class_id}_gemini_transcript_improved.txt"}
        collection_name = "live_query"
   
    vectordb = Chroma(
        client=client,
        embedding_function=embedding,
        collection_name=collection_name
    )

    current_lecture = vectordb.similarity_search(
        query,
        k=6,
        filter=filter_data
    )
    
    if not ca_query:
        other_lecture = vectordb.similarity_search(
            query,
            k=4,
            filter={"section": section}
        )


        other_lecture = filter_docs(other_lecture, class_id)
        other_lecture = format_docs(other_lecture)

        current_lecture = format_docs(current_lecture)
        # other_lecture = format_docs(other_lecture)
        relevant_docs = "/n/n".join([current_lecture, other_lecture])
        
    else:
        metadata_list = [data.metadata for data in current_lecture]
        unique_metadata_list = list({json.dumps(d, sort_keys=True): d for d in metadata_list}.values())
        
        current_lecture = format_docs(current_lecture)
        result = "/n/n".join([current_lecture])

        relevant_docs = {
                "context": result,
                "metadata":[{"article_id":data["article_id"],"url":data["url"]} for data in list(unique_metadata_list)]
            }

    return relevant_docs
    # if ca_query:
        

    # return rerank(query=query, relevant_docs=relevant_docs, top_k=top_k, ca_query=ca_query)


def get_contextualized_qa_chain():
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0, openai_api_key=api_key)

    contextualize_q_system_prompt = Prompt.contextualize_q_system_prompt.value

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
        ]
    )
    contextualize_q_chain = contextualize_q_prompt | llm | StrOutputParser()
    return contextualize_q_chain


def get_contextualized_question(chat_history, query):
    if chat_history:
        contextualized_qa_chain = get_contextualized_qa_chain()
        contextualized_question = contextualized_qa_chain.invoke({
            "chat_history": chat_history,
            "question": query
        })
        return contextualized_question
    else:
        return query


def get_chat_unique_id(id, time_stamp):
    return str(id) + "_" + str(time_stamp)


def question_answer(class_id, member_id, package_id, query, old_conversation, section=None, ca_query=False, chat_session_id=None):
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0.2, openai_api_key=api_key)

    qa_system_prompt = Prompt.qa_system_prompt.value

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
        ]
    )

    rag_chain = (
            qa_prompt | llm | StrOutputParser()
    )
    chat_history = get_processed_chat_history(
        class_id=class_id, member_id=member_id, ca_query=ca_query, chat_session_id=chat_session_id
    )
    print(chat_history)
    context_query = get_contextualized_question(chat_history, query)
    context = get_top_k_docs(query=context_query, class_id=class_id, section=section, ca_query=ca_query)
    
    metadata = ""
    if ca_query:
        metadata = context["metadata"]
        context = context["context"]
    
    res = rag_chain.invoke(
        {
            "question": query,
            "chat_history": chat_history,
            "context": context
        }
    )
    print("\n here is the res.......................\n", res)
    formatted_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', res)
    formatted_text = formatted_text.replace('\n', '<br>')
    
    if ca_query:
        id, time_stamp = update_create_ca_chat_history(
        query=query,
        old_conversation=old_conversation,
        article_id=class_id,
        member_id=member_id,
        res=formatted_text,
        chat_session_id=chat_session_id
    )
    else:
        id, time_stamp = update_create_chat_history(
            query=query,
            old_conversation=old_conversation,
            class_id=class_id,
            member_id=member_id,
            package_id=package_id,
            res=formatted_text
        )

    return formatted_text, get_chat_unique_id(id=id, time_stamp=time_stamp), metadata


def get_last_query_from_chat_histroy(chat_history):
    last_query = ""
    if chat_history:
        last_query = chat_history[-2] or ""
        if last_query:
            last_query = last_query.content
    return last_query
    

def predict_questions(chat_id, article_id):
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0.2, openai_api_key=api_key)

    predict_question_prompt = Prompt.predict_next_question_prompt.value

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", predict_question_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
        ]
    )

    rag_chain = (
            qa_prompt | llm | NumberedListOutputParser()
    )
    chat_history = get_formatted_chat_history(chat_id=chat_id)
    print("chat history:-----------------",chat_history)
    
    last_query = get_last_query_from_chat_histroy(chat_history)
    context = get_top_k_docs(query=last_query, class_id=article_id, ca_query=True)
    context = context["context"]
    # print("the context is -----------------",context)
    
    res = rag_chain.invoke(
        {
            "question": last_query,
            "chat_history": chat_history,
            "context": context
        }
    )
    print("\n here is the res.......................\n", res)
    
    return res

    
