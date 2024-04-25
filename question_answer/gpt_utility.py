from langchain.vectorstores import Chroma
from .customEmbeddingsClass import CustomOpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from decouple import config
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
import chromadb
from .get_chat_history import get_latest_chat_history
import datetime
from .reranking_utility import rerank

chroma_ip = config('CHROMA_IP')

api_key = config('OPEN_AI_API_KEY')
BASE_TRANSCRIPT_PATH = config('BASE_TRANSCRIPT_PATH')


def get_top_k_docs(query, class_id):
    top_k = 6
    scores = []
    client = chromadb.HttpClient(host='46.4.66.230', port=8000)

    # Get the stored vector db
    embedding = CustomOpenAIEmbeddings(openai_api_key=api_key)
    vectordb = Chroma(
        client=client,
        embedding_function=embedding
    )
    print("fetching docs from chroma db............")
    print("start_time: ", datetime.datetime.now())
    # print(BASE_TRANSCRIPT_PATH)
    relevant_docs = vectordb.max_marginal_relevance_search(query,
                                                           k=8,
                                                           filter={"source": f"{BASE_TRANSCRIPT_PATH}{class_id}_transcript.txt"})
    print("end_time: ", datetime.datetime.now())
    # print("relevant docs are here...............................................")
    # print(relevant_docs)
    print("reranking the docs.............")
    print("start_time: ", datetime.datetime.now())
    top_k_docs = rerank(query=query, relevant_docs=relevant_docs, top_k=6)
    print("end_time: ", datetime.datetime.now())
    # return rerank(query=query, relevant_docs=relevant_docs, top_k=6)
    return top_k_docs


def format_docs(docs):
    return "\n\n".join(doc for doc in docs)


def get_chat_history(class_id, member_id):
    chat_history_list = get_latest_chat_history(class_id=class_id, member_id=member_id)

    chat_list = []
    for chat_history in chat_history_list:
        chat_list.append(HumanMessage(content=chat_history['question']))
        chat_list.append(AIMessage(content=chat_history['response']))

    return chat_list


def get_contextualized_qa_chain():
    llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=0, openai_api_key=api_key)

    contextualize_q_system_prompt = """
    You are provided with a chat-history between AI and human.
        
    You will be given a new question from human.
    The question may or may not reference the chat-history.
    
    <instructions>
        1. Formulate a standalone question which can be understood without the chat history only if latest user question has pronouns or articles referring to someone or something in the chat-history, otherwise return it as is.
        2. You MUST NOT answer the question
        3. Do not add any extra line like 'Here is the standalone question based on the latest user query:'
    </instructions>
    """

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
        ]
    )
    contextualize_q_chain = contextualize_q_prompt | llm | StrOutputParser()
    return contextualize_q_chain


def get_contextualized_question(input: dict):
    if input.get("chat_history"):
        contextualized_qa_chain = get_contextualized_qa_chain()
        print("getting context question................")
        print("start_time: ", datetime.datetime.now())
        contextualized_question = contextualized_qa_chain.invoke({
            "chat_history": input['chat_history'],
            "question": input['question']
        })
        print("end_time: ", datetime.datetime.now())
        return contextualized_question
    else:
        return input["question"]


def get_context(class_id, query, chat_history):
    # contextualized_question = get_contextualized_question({"chat_history": chat_history, "question": query})
    return get_top_k_docs(query=query, class_id=class_id)


def question_answer(class_id, member_id, query):
    llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=0.3, openai_api_key=api_key)
    print("inside the GPT api ...............................................")

    qa_system_prompt = """

    Use the following documents to answer the question.
    {context}
    
    <instruction>
    Follow these steps:
        1. Identify the most relevant points to answer the question.
        2. Generate brief and to the point answer in less than 25 tokens from these relevant points.
        3. If the question cannot be answered using the context, just say that you don't know the answer. 
        4. Do not try to make up an answer from any external source.
        5. You must not use phrases like "Based on the information provided in the documents" in the answer
        6. Structure the answer in the format below:
        
        Dear Student,
        a plain text answer. 
        Thank you.
        
    </instruction>
    
    """

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

    chat_history = get_chat_history(class_id=class_id, member_id=member_id)
    # context_query = get_contextualized_question(query)
    context = get_context(class_id, query, chat_history)

    print("creating final answer..........")
    print("start_time: ", datetime.datetime.now())
    final_ans = rag_chain.invoke(
        {
            "question": query,
            "chat_history": chat_history,
            "context": context
        }
    )

    print("end_time: ", datetime.datetime.now())

    return final_ans