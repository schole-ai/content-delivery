import os
import argparse

from scripts.rag import KnowledgeGraphRAG

from utils.login import *


def main(args, query):
    kgrag = KnowledgeGraphRAG(args.url, args.username, args.password)
    # results = kgrag.search_query(query)
    results = kgrag.extract_topics(query)
    print(results)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Neo4j knowledge graoh credentials')

    parser.add_argument('--url', type=str, default='bolt://localhost:7687', help='URL of the Neo4j database')
    parser.add_argument('--username', type=str, default='neo4j', help='Username of the Neo4j database')
    parser.add_argument('--password', type=str, default='password123', help='Password of the Neo4j database')
    parser.add_argument('--query', type=str, default='I want to learn about Machine Learning', help='Query to ask the knowledge graph')

    args = parser.parse_args()
  
    main(args, args.query)
