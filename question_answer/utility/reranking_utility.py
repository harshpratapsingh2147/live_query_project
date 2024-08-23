from transformers import AutoTokenizer, AutoModel
import json
import torch


def format_docs(docs):
    if len(docs) > 0:
        return "\n\n".join(doc.page_content for doc in docs)
    else:
        return ""


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


def rerank(query, relevant_docs, top_k=6, ca_query=False):
    scores = []
    # Load the tokenizer and the model
    tokenizer = AutoTokenizer.from_pretrained("colbert-ir/colbertv2.0")
    model = AutoModel.from_pretrained("colbert-ir/colbertv2.0")

    # Encode the query
    query_encoding = tokenizer(query, return_tensors='pt')
    query_embedding = model(**query_encoding).last_hidden_state.mean(dim=1)

    # Get score for each document
    for document in relevant_docs:
        # print(document)
        document_encoding = tokenizer(document, return_tensors='pt', truncation=True, max_length=512)
        document_embedding = model(**document_encoding).last_hidden_state

        # Calculate MaxSim score
        score = maxsim(query_embedding.unsqueeze(0), document_embedding)
        scores.append({
            "score": score.item(),
            "document": document.page_content,
            "metadata":document.metadata
        })

    # Sort the scores by highest to lowest and print
    sorted_data = sorted(scores, key=lambda x: x['score'], reverse=True)[:top_k]
    metadata_list = [data["metadata"] for data in sorted_data]
    unique_metadata_list = list({json.dumps(d, sort_keys=True): d for d in metadata_list}.values())

    result = (
        format_docs([data["document"] for data in sorted_data])
        if not ca_query
        else {
            "context":format_docs([data["document"] for data in sorted_data]),
            "metadata":[{"article_id":data["article_id"],"url":data["url"]} for data in list(unique_metadata_list)]
        }
    )
    return result
