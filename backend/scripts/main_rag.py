import os
import sys
import argparse

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from scripts.neo4j_rag import KnowledgeGraphRAG
from scripts.rag import EuclideanRetriever, CosineRetriever, FaissRetriever
from scripts.bloom_gen import BloomQuestionGenerator

from utils.helpers import *


def main(args, query):
    kgrag = KnowledgeGraphRAG(args.url, args.username, args.password)
    results = kgrag.search_query(query)
    print("results: ", results)
    # for key, value in results.items():
    #     print(f"{key}: {value['name'], value['content']}")

    # retriever = EuclideanRetriever(args.url, args.username, args.password, node_id=1769)
    # idx, top_doc = retriever.retrieve_top_k(query, k=1)
    # retriever = CosineRetriever(args.url, args.username, args.password, node_id=1769)
    # idx, top_doc = retriever.retrieve_top_k(query, k=1)
    # retriever = FaissRetriever(args.url, args.username, args.password, node_id=1769)
    # idx, top_doc = retriever.retrieve_top_k(query, k=1)
    # print(f"Top k: {top_doc}")
    # bloom_gen = BloomQuestionGenerator()
    # question = bloom_gen.generate_question(top_doc[0], question_type="MCQ", level=1)
    # print(question)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Neo4j knowledge graph credentials')

    parser.add_argument('--url', type=str, default='bolt://localhost:7687', help='URL of the Neo4j database')
    parser.add_argument('--username', type=str, default='neo4j', help='Username of the Neo4j database')
    parser.add_argument('--password', type=str, default='password123', help='Password of the Neo4j database')
    parser.add_argument('--query', type=str, default='I want to learn about Machine Learning', help='Query to ask the knowledge graph')

    args = parser.parse_args()
  
    main(args, args.query)
