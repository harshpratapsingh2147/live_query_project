import torch
from transformers import AutoTokenizer, AutoModel
from langchain.vectorstores import Chroma
from .customEmbeddingsClass import CustomOpenAIEmbeddings
from decouple import config
import chromadb
import anthropic
from .get_chat_history import get_latest_chat_history

chroma_ip = config('CHROMA_IP')

api_key = config('OPEN_AI_API_KEY')
BASE_TRANSCRIPT_PATH = config('BASE_TRANSCRIPT_PATH')


def valid_integer(value):
    """
    Validates if the provided value is a valid integer.

    Args:
    - `value` (str): The value to be validated.

    Returns:
    - bool: True if the value is a valid integer, False otherwise.
    """
    # valid_integer changes
    if not value.isdigit():
        return False
    return True


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
    print("here is the query...................")
    print(query)
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
    return "\n\n".join(f"<document>{doc}</document>" for doc in docs)


def get_chat_history(class_id, member_id):
    chat_history_list = get_latest_chat_history(class_id=class_id, member_id=member_id)
    chat_list = []
    for chat_history in chat_history_list:
        chat_list.append(f"human: {chat_history['question']}")
        chat_list.append(f"AI: {chat_history['response']}")

    return "\n".join(chat for chat in chat_list)


def get_contextualized_question(input: dict):
    client = anthropic.Anthropic(
        # defaults to os.environ.get("ANTHROPIC_API_KEY")
        api_key=config('ANTHRO_API_KEY'),
    )
    if input.get("chat_history"):
        contextualize_q_system_prompt = f"""
        You will be provided with a chat history between AI and human.
        You will also be provided with a latest question from human which might context in the chat history.
        <chat-history>
        {input['chat_history']}
        </chat-history>
        <instructions>
        1. formulate a standalone question 
            which can be understood without the chat history.
        2. You MUST NOT answer the question
        3. just reformulate the latest user question if needed, otherwise return it as is.
        4. Do not add any extra line like 'Here is the standalone question based on the latest user query:'
        </instructions>
        """

        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            system=contextualize_q_system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": input['question']
                }
            ]
        )
        return message.content[0].text
    else:
        return input["question"]


def get_context(class_id, query):
    return get_top_k_docs(query=query, class_id=class_id)


def question_answer(class_id, member_id, query):
    chat_history = get_chat_history(class_id=class_id, member_id=member_id)
    contextualized_question = get_contextualized_question({"chat_history": chat_history, "question": query})

    context = get_context(class_id, contextualized_question)

    qa_system_prompt = f"""
    Use only the following documents to answer the question.
    {context}
    
    <instructions>
    Follow these steps:
    1. Identify five key points from the provided context.
    2. Generate detailed explanation from these key points.
    3. If the question cannot be answered using the documents, just say that you don't know the answer. 
    4. Do not try to make up an answer from some external source.
    </instructions>
    
    <example>
    Explanation: <Explanation of the provided context in detail> 
    Bullet points: <Five Bullet points from explanation>
    </example>
    """

    client = anthropic.Anthropic(
        # defaults to os.environ.get("ANTHROPIC_API_KEY")
        api_key= config('ANTHRO_API_KEY'),
    )

    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0.0,
        system=qa_system_prompt,
        messages=[
            {"role": "user", "content": contextualized_question}
        ]
    )

    return message.content[0].text



