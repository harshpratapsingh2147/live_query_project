import torch
from transformers import AutoTokenizer, AutoModel
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
chroma_ip = config('CHROMA_IP')

api_key = config('OPEN_AI_API_KEY')
BASE_TRANSCRIPT_PATH = config('BASE_TRANSCRIPT_PATH')


# Function to compute MaxSim
def maxsim(query_embedding, document_embedding):
    # Expand dimensions for broadcasting
    # Query: [batch_size, query_length, embedding_size] -> [batch_size, query_length, 1, embedding_size]
    # Document: [batch_size, doc_length, embedding_size] -> [batch_size, 1, doc_length, embedding_size]
    expanded_query = query_embedding.unsqueeze(2)
    expanded_doc = document_embedding.unsqueeze(1)

    # Compute cosine similarity across the embedding dimension
    sim_matrix = torch.nn.functional.cosine_similarity(expanded_query, expanded_doc, dim=-1)

    # Take the maximum similarity for each query token (across all document tokens)
    # sim_matrix shape: [batch_size, query_length, doc_length]
    max_sim_scores, _ = torch.max(sim_matrix, dim=2)

    # Average these maximum scores across all query tokens
    avg_max_sim = torch.mean(max_sim_scores, dim=1)
    return avg_max_sim


def get_top_k_docs(query, class_id):
    top_k = 6
    scores = []
    client = chromadb.HttpClient(host=chroma_ip, port=8000)

    # Get the stored vector db
    embedding = CustomOpenAIEmbeddings(openai_api_key=api_key)
    vectordb = Chroma(
        client=client,
        embedding_function=embedding
    )

    print(BASE_TRANSCRIPT_PATH)
    relevant_docs = vectordb.max_marginal_relevance_search(query,
                                                           k=8,
                                                           filter={"source": f"{BASE_TRANSCRIPT_PATH}{class_id}_transcript.txt"})

    print("relevant docs are here...............................................")
    print(relevant_docs)
    # Load the tokenizer and the model
    tokenizer = AutoTokenizer.from_pretrained("colbert-ir/colbertv2.0")
    model = AutoModel.from_pretrained("colbert-ir/colbertv2.0")

    # Encode the query
    query_encoding = tokenizer(query, return_tensors='pt')
    query_embedding = model(**query_encoding).last_hidden_state.mean(dim=1)

    # Get score for each document
    for document in relevant_docs:
        # print(document)
        document_encoding = tokenizer(document.page_content, return_tensors='pt', truncation=True, max_length=512)
        document_embedding = model(**document_encoding).last_hidden_state

        # Calculate MaxSim score
        score = maxsim(query_embedding.unsqueeze(0), document_embedding)
        scores.append({
            "score": score.item(),
            "document": document.page_content,
        })

    # Sort the scores by highest to lowest and print
    sorted_data = sorted(scores, key=lambda x: x['score'], reverse=True)[:top_k]
    return format_docs([data['document'] for data in sorted_data])


def format_docs(docs):
    return "\n\n".join(doc for doc in docs)


def get_chat_history(class_id, member_id):
    chat_history_list = get_latest_chat_history(class_id=class_id, member_id=member_id)
    chat_list = []
    for chat_history in chat_history_list:
        chat_list.append(HumanMessage(content=chat_history['question']))
        chat_list.append(AIMessage(content=chat_history['response']))
    print(chat_list)
    return chat_list


def get_contextualized_qa_chain():
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, openai_api_key=api_key)

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
        contextualized_question = contextualized_qa_chain.invoke({
            "chat_history": input['chat_history'],
            "question": input['question']
        })
        return contextualized_question
    else:
        return input["question"]


def get_context(class_id, query, chat_history):
    contextualized_question = get_contextualized_question({"chat_history": chat_history, "question": query})
    print("here is the context question.......................")
    print(contextualized_question)
    return get_top_k_docs(query=contextualized_question, class_id=class_id)


def question_answer(class_id, member_id, query):
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.3, openai_api_key=api_key)
    print("inside the GPT api ...............................................")
    # qa_system_prompt = """Use only the following pieces of context to answer the question.
    # If the question cannot be answered using the context or the chat_history, just say that you don't know the answer.
    # Do not try to make up an answer from some other source.
    # Always say "thanks for asking!" at the end of the answer.
    #
    # {context} """

    qa_system_prompt = """

    Use the following documents to answer the question.
    {context}
    
    
    Follow these steps:
        1. Identify the most relevant points to answer the question.
        2. Generate brief and to the point answer in less than 80 tokens from these relevant points.
        3. If the question cannot be answered using the context, just say that you don't know the answer. 
        4. Do not try to make up an answer from any external source.
        5. You must not use phrases like "Based on the information provided in the documents" in the answer
        6. Structure the answer in the format below:
        
        Dear Student,
        a plain text answer. 
        Thank you.
        
    
    
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

    return rag_chain.invoke(
        {
            "question": query,
            "chat_history": chat_history,
            "context": get_context(class_id, query, chat_history)
        }
    )