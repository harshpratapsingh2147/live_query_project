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
from embedding.utility.s3_utility import CloudFrontDownloadUtility
from embedding.utility.pdf_text_processor import OCRDataExtract

chroma_ip = config('CHROMA_IP')
api_key = config('OPEN_AI_API_KEY')
ca_collection_name = config("CA_EMBEDDINGS_COLLECTION")
BASE_EMBEDDING_PATH = config('BASE_EMBEDDING_PATH')


AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY_ID = config('AWS_SECRET_KEY_ID')
S3_BUCKET = config('S3_BUCKET')
S3_EMBEDDING_FOLDER = config('S3_EMBEDDING_FOLDER')



def create_document(text, title, article_id, url="", source_type=""):
    pages = [Document(
        page_content=text, 
        metadata={"article_id":article_id, "title":title, "url":url, "type":source_type}
        )
    ]
    chunk_size = 800
    chunk_overlap = 200

    r_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    docs = r_splitter.split_documents(pages)
    # print(docs)
    return docs


def create_embeddings(doc):
    try:
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
 

def process(content, title, pdf_id, url="", source_type=""):
    
    doc = create_document(content, title, pdf_id, url, source_type)
    status = create_embeddings(doc)
    return status


def create_dirs(folder_path):
    os.makedirs(folder_path,exist_ok=True)


def download_pdf_file_to_local(cloudfront_link):
    value = cloudfront_link.split("/")
    local_file_name = f"{value[-2]}_{value[-1]}"
    local_pdf_folder = f"{BASE_EMBEDDING_PATH}/pdfs/"
    create_dirs(local_pdf_folder)
    local_file_path = f"{local_pdf_folder}{local_file_name}"
    _status = CloudFrontDownloadUtility().download_files(cloudfront_link=cloudfront_link, local_filepath=local_file_path)
    return local_file_path if _status else ""



def process_file(item):
    
    local_pdf_filepath = download_pdf_file_to_local(item.get("content"))
    if not local_pdf_filepath:
        return False
    
    # local_text_filepath = local_pdf_filepath.replace(".pdf",".txt")
    print("local file path: ", local_pdf_filepath)
    output_text_file = OCRDataExtract().process(
        input_file_path=local_pdf_filepath
    )
    with open(output_text_file, 'r') as file:
            text_data = file.read()
    
    if not process(text_data, item["title"], item["id"], item["url"], item.get("type", "")):
        return False
    return True
        
        

def process_pdf_embeddings(pdf_data):

    try:
        
        _status = process_file(pdf_data)
        return _status
        
    except Exception as err:
        return False, str(err)
        