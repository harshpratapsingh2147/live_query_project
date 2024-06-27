from datetime import datetime
from bs4 import BeautifulSoup
from decouple import config

from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores import Chroma

# from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# from decouple import config
import chromadb
import json
import boto3
import os


from question_answer.customEmbeddingsClass import CustomOpenAIEmbeddings

chroma_ip = config('CHROMA_IP')
api_key = config('OPEN_AI_API_KEY')
ca_collection_name = config("CA_EMBEDDINGS_COLLECTION")
BASE_EMBEDDING_PATH = config('BASE_EMBEDDING_PATH')


AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY_ID = config('AWS_SECRET_KEY_ID')
S3_BUCKET = config('S3_BUCKET')
S3_EMBEDDING_FOLDER = config('S3_EMBEDDING_FOLDER')


DATE = datetime.now().strftime("%Y_%m_%d__%H_%M")
FILE_NAME = "article_embed_start_{DATE}.json"
LOCAL_FILE_PATH = f"{BASE_EMBEDDING_PATH}/{FILE_NAME}"



def parse_html(html_str):
    soup = BeautifulSoup(html_str, 'html.parser')
    text = soup.get_text( strip=True)
    return text


def create_document(text, title, article_id):
    pages = [Document(page_content=text, metadata={"article_id":article_id, "title":title})]
    chunk_size = 500
    chunk_overlap = 4

    r_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    docs = r_splitter.split_documents(pages)
    # print(docs)
    return docs


def create_embeddings(doc):
    try:
        print(chroma_ip)
        client = chromadb.HttpClient(host=chroma_ip, port=8000)
        collection_name = ca_collection_name
        collection = client.get_or_create_collection(collection_name)
        embedding = CustomOpenAIEmbeddings(openai_api_key=api_key)
        vectordb = Chroma(
            collection_name=collection_name, client=client, embedding_function=embedding
        ).add_documents(
            documents=doc,
            
        )
        return True
    except Exception as err:
        print("Here is the issue: ", err)
        return False
 

def process(content, title, article_id):
    text = parse_html(content)
    doc = create_document(text, title, article_id)
    status = create_embeddings(doc)
    return status

def process_data(data):
    for item in data:
        if item.get("status") == 1:
            continue
        
        html_content = item["content"]
        if not process(html_content, item["title"], item["id"]):
            item["status"] = 0
            continue
        item["status"] = 1
    return data
        
        

def save_data(data):
    os.makedirs(BASE_EMBEDDING_PATH, exist_ok=True)
    with open(LOCAL_FILE_PATH, 'w') as file:
        json.dump(data, file, indent=4)


def collect_data():
    with open(LOCAL_FILE_PATH, 'r') as file:
        return json.load(file)



def upload_embedding_file_to_s3():
    s3_client = boto3.client('s3',
                             aws_access_key_id=AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=AWS_SECRET_KEY_ID
                             )
    try:
        s3_client.upload_file(LOCAL_FILE_PATH, S3_BUCKET, f"{S3_EMBEDDING_FOLDER}/{FILE_NAME}")
    except Exception as err:
        print(err)


def process_embeddings(article_data):

    try:
        
        save_data(article_data)
        data = collect_data()
        data = process_data(data)
        save_data(data)
        upload_embedding_file_to_s3()
        return True, "Embeddings are created."
        
    except Exception as err:
        return False, str(err)
        