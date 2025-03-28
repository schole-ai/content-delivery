import os

from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker

from chunking_evaluation.chunking import ClusterSemanticChunker, LLMSemanticChunker

from semantic_chunkers import StatisticalChunker
from semantic_router.encoders import OpenAIEncoder

from dotenv import load_dotenv


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SEPARATORS = ["\n\n", "\n", ".", "?", "!", " ", ""]

class TextChunker:
    """A class which implements many methods for create bite-sized blocks of text."""
    def __init__(self):
        self.embedding_model = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
        self.encoder_model = OpenAIEncoder(name="text-embedding-3-small")
    
    def recursive_chunk(self, text, chunk_size=500, chunk_overlap=0, by_tokens=False):
        """Chunk text recursively."""
        if by_tokens:
            splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(model_name="gpt-4", 
                                                                            chunk_size=chunk_size,
                                                                            chunk_overlap=chunk_overlap,
                                                                            separators=SEPARATORS)
        else:
            splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, 
                                                      chunk_overlap=chunk_overlap,
                                                      separators=SEPARATORS)
        return splitter.split_text(text)

    def semantic_chunk(self, text):
        """Chunk text based on semantic similarity."""
        splitter = SemanticChunker(self.embedding_model)
        return splitter.split_text(text)
    
    def cluster_chunk(self, text, max_chunk_size=500):
        """Chunk text based on clustering."""
        splitter = ClusterSemanticChunker(
            embedding_function=self.embedding_model.embed_documents,
            max_chunk_size=max_chunk_size
        )
        return splitter.split_text(text)
    
    def statistical_chunk(self, text):
        """Chunk text based on statistical methods."""
        splitter = StatisticalChunker(encoder=self.encoder_model)
        chunks = splitter(docs=[text])
        return chunks
    
    def llm_chunk(self, text):
        """Chunk text based on LLMs."""
        splitter = LLMSemanticChunker(
            organisation="openai",
            model_name="gpt-4o",
            api_key=OPENAI_API_KEY
        )
        return splitter.split_text(text)

