from langchain.vectorstores import Chroma
from .customEmbeddingsClass import CustomOpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from decouple import config
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
import chromadb
from .get_chat_history import get_processed_chat_history, update_create_chat_history
from .reranking_utility import rerank

chroma_ip = config('CHROMA_IP')

api_key = config('OPEN_AI_API_KEY')
BASE_TRANSCRIPT_PATH = config('BASE_TRANSCRIPT_PATH')


def get_top_k_docs(query, class_id):
    top_k = 5
    client = chromadb.HttpClient(host=chroma_ip, port=8000)

    # Get the stored vector db
    embedding = CustomOpenAIEmbeddings(openai_api_key=api_key)
    vectordb = Chroma(
        client=client,
        embedding_function=embedding
    )

    relevant_docs = vectordb.max_marginal_relevance_search(query,
                                                           k=8,
                                                           filter={"source": f"{BASE_TRANSCRIPT_PATH}{class_id}_transcript.txt"})
    return rerank(query=query, relevant_docs=relevant_docs, top_k=top_k)


def get_contextualized_qa_chain():
    llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=0, openai_api_key=api_key)

    contextualize_q_system_prompt = """
    You are provided with a chat-history between AI and human.

    You will be given a new question or statement from human.
    The question may or may not reference the chat-history.
    
    <instruction>
    Follow these steps:
    1. Formulate a standalone question which can be understood without the chat history only if latest user question or statements has pronouns or articles referring to someone or something in the chat-history, otherwise return it as is.
    2. You MUST NOT answer the question or statement. Just reformulated if needed or return as it is.
    3. DO not add "Dear student" OR "thank you".
    </instruction>
    
    <example>
    human: "When did they last discuss this issue?"
    Reformulated question: "When was the last discussion about this issue?"
    </example>
    
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


def get_contextualized_question(chat_history, query):
    if chat_history:
        contextualized_qa_chain = get_contextualized_qa_chain()
        contextualized_question = contextualized_qa_chain.invoke({
            "chat_history": chat_history,
            "question": query
        })
        print("here is the context question..........")
        print(contextualized_question)
        return contextualized_question
    else:
        return query


def get_chat_unique_id(id, time_stamp):
    return str(id) + "_" + str(time_stamp)


def question_answer(class_id, member_id, package_id, query, old_conversation):
    llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=0.3, openai_api_key=api_key)

    qa_system_prompt = """

    Use the following documents to answer the question.
    {context}
    
    <instruction>
    1. Understand the question asked by the user.
    2. Look for most appropriate response in maximum 100 words. Make answer as crisp and to the point.
    3 .If the answer to query can not be answered using the content provided by me, Reply
    "Dear Student,
    
    The Query asked by you is beyond the scope of this lecture. Please ask me another question from the content taught in the class.
    
    Thank you."
    4. Do not use your own knowledge or general knowledge to answer the question asked by the user. Only confine yourself to the content provided by me to provide the best possible answer.
    5. Structure the answer in the format below:
        Dear Student,
        
        A plain text answer.
       
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

    chat_history = get_processed_chat_history(class_id=class_id, member_id=member_id)
    print("here is the chat_history")
    print(chat_history)
    context_query = get_contextualized_question(chat_history, query)
    context = get_top_k_docs(query=context_query, class_id=class_id)
    print("here is the context............")
    print(context)

    res = rag_chain.invoke(
        {
            "question": query,
            "chat_history": chat_history,
            "context": context
        }
    )

    id, time_stamp = update_create_chat_history(
        query=query,
        old_conversation=old_conversation,
        class_id=class_id,
        member_id=member_id,
        package_id=package_id,
        res=res
    )

    return res, get_chat_unique_id(id=id, time_stamp=time_stamp)




