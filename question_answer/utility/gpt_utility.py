import re
# from langchain.vectorstores import Chroma
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
import chromadb
from decouple import config

from question_answer.customEmbeddingsClass import CustomOpenAIEmbeddings
from .db_operations_utility import (
    get_processed_chat_history, 
    update_create_chat_history,
    update_create_ca_chat_history
)
from .reranking_utility import rerank
from .enum_utility import Prompt

chroma_ip = config('CHROMA_IP')

api_key = config('OPEN_AI_API_KEY')
BASE_TRANSCRIPT_PATH = config('BASE_TRANSCRIPT_PATH')
ca_collection_name = config("CA_EMBEDDINGS_COLLECTION")


def get_top_k_docs(query, class_id, ca_query=False):
    top_k = 6
    client = chromadb.HttpClient(host=chroma_ip, port=8000)

    # Get the stored vector db
    embedding = CustomOpenAIEmbeddings(openai_api_key=api_key)
    
    if ca_query:
        filter_data = {"article_id":class_id}
        collection_name = ca_collection_name
    else:
        # filter_data = {"source": f"{BASE_TRANSCRIPT_PATH}{class_id}_transcript.txt"}
        filter_data = {"source": f"{BASE_TRANSCRIPT_PATH}{class_id}/{class_id}_gemini_transcript_improved.txt"}
        collection_name = "live_query"
   
    vectordb = Chroma(
        client=client,
        embedding_function=embedding,
        collection_name=collection_name
    )

    relevant_docs = vectordb.max_marginal_relevance_search(
        query,
        k=8,
        filter=filter_data
    )

    return rerank(query=query, relevant_docs=relevant_docs, top_k=top_k)


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


def question_answer(class_id, member_id, package_id, query, old_conversation, ca_query=False):
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
    chat_history = get_processed_chat_history(class_id=class_id, member_id=member_id, ca_query=ca_query)
    context_query = get_contextualized_question(chat_history, query)
    print("Here is the context query..............")
    print(context_query)
    context = get_top_k_docs(query=context_query, class_id=class_id, ca_query=ca_query)
    print("here is the context................")
    print(context)
    res = rag_chain.invoke(
        {
            "question": query,
            "chat_history": chat_history,
            "context": context
        }
    )

    formatted_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', res)
    formatted_text = formatted_text.replace('\n', '<br>')
    
    if ca_query:
        id, time_stamp = update_create_ca_chat_history(
        query=query,
        old_conversation=old_conversation,
        article_id=class_id,
        member_id=member_id,
        res=formatted_text
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

    return formatted_text, get_chat_unique_id(id=id, time_stamp=time_stamp)
