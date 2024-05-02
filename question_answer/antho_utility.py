from decouple import config
import chromadb
from langchain.vectorstores import Chroma

from .customEmbeddingsClass import CustomOpenAIEmbeddings
from .get_chat_history import get_processed_chat_history
from .anthro_api_utility import anthropic_api_call
from live_query_resolution.question_answer.utility.reranking_utility import rerank

chroma_ip = config('CHROMA_IP')
api_key = config('OPEN_AI_API_KEY')
BASE_TRANSCRIPT_PATH = config('BASE_TRANSCRIPT_PATH')


def get_top_k_docs(query, class_id):
    print("here is the query...................")
    print(query)
    fetch_k = 8
    scores = []
    client = chromadb.HttpClient(host=chroma_ip, port=8000)

    # Get the stored vector db
    embedding = CustomOpenAIEmbeddings(openai_api_key=api_key)
    vectordb = Chroma(
        client=client,
        embedding_function=embedding
    )

    relevant_docs = vectordb.max_marginal_relevance_search(query,
                                                           k=fetch_k,
                                                           filter={"source": f"{BASE_TRANSCRIPT_PATH}{class_id}_transcript.txt"})

    print("relevant docs are here...............................................")
    print(relevant_docs)

    return rerank(query=query, relevant_docs=relevant_docs, top_k=6)


def get_contextualized_question(chat_history, query):

    if chat_history:
        contextualize_q_system_prompt = f"""
        You are provided with a chat-history between AI and human.
        
        <chat-history>
            {chat_history}
        </chat-history>
        
        You will be given a new question from user.
        The question may or may not reference the chat-history.
        
        <instructions>
            1. Formulate a standalone question which can be understood without the chat history only if latest user question has pronouns or articles referring to someone or something in the chat-history, otherwise return it as is.
            2. You MUST NOT answer the question
            3. Do not add any extra line like 'Here is the standalone question based on the latest user query:'
        </instructions>
        """

        return anthropic_api_call(prompt=contextualize_q_system_prompt, query=query)
    else:
        return query


def question_answer(class_id, member_id, query):
    print("inside the anthropic api ...............................................")

    chat_history = get_processed_chat_history(class_id=class_id, member_id=member_id)
    print("here is the chat history.................")
    print(chat_history)
    contextualized_question = get_contextualized_question(chat_history=chat_history, query=query)

    context = get_top_k_docs(query=contextualized_question, class_id=class_id)

    qa_system_prompt = f"""
    
    Use the following documents to answer the question.
    {context}
    
    <instructions>
    Follow these steps:
        1. Identify the most relevant points to answer the question.
        2. Generate brief answer of not more than 100 words from these relevant points.
        3. If the question cannot be answered using the documents, just say that you don't know the answer. 
        4. Do not try to make up an answer from some external source.
        5. You must not use phrases like "Based on the information provided in the documents" in the answer
        6. Structure the answer in the format below:
        
        Dear Student,
        a plain text answer. 
        Thank you.
        
    </instructions>
    
    
    """
    return anthropic_api_call(prompt=qa_system_prompt, query=contextualized_question, temperature=0.3)



