from fastapi import FastAPI, UploadFile, File, Body
from fastapi.responses import JSONResponse
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from typing import Optional
from pydantic import BaseModel
from io import BytesIO
from scripts.bloom_gen import BloomQuestionGenerator
from scripts.chunk import TextChunker, PDFChunker
from scripts.learner import LearningTracker
from scripts.neo4j_rag import KnowledgeGraphRAG
from utils.helpers import connection
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

BLOOM_MAP = {"remember": 1, "understand": 2, "apply": 3, "analyze": 4, "evaluate": 5, "create": 6}
BLOOM_MAP_REVERSE = {v: k for k, v in BLOOM_MAP.items()}

class AnswerRequest(BaseModel):
    answer: str
    elapsed_time: Optional[int] = None

class FeedbackRequest(BaseModel):
    session_id: str
    value: int
    location: str

app = FastAPI()

CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5173")

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGIN],  
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS = {}  

NEO4J_CREDENTIALS = {}

question_generator = BloomQuestionGenerator()

@app.post("/upload")
async def upload_and_process(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    contents = await file.read()
    filename = file.filename

    tracker = LearningTracker(
        session_id,
        strategy="default",
        min_success_question=1,
        max_fail_question=1,
        supabase=supabase,
    )

    session_data = {
        "tracker": tracker,
        "file_bytes": contents,
        "filename": filename,
        "chunks": None,
        "chunks_img": None,
        "questions": [],
        "answers": [],
        "bloom_levels": [],
        "question_types": [],
        "current_step": 0,
        "failed_attempts": {},  # Track failed attempts for each chunk
    }

    if filename.endswith(".pdf"):
        file_obj = BytesIO(contents)
        chunker = PDFChunker(file_obj=file_obj)
        session_data["chunks"] = chunker.formated_chunks
        session_data["chunks_img"] = chunker.chunks_img_b64
    elif filename.endswith(".txt"):
        text = contents.decode("utf-8")
        chunker = TextChunker(text)
        # session_data["chunks"] = chunker.recursive_chunk(chunk_size=1000)
        session_data["chunks"] = chunker.statistical_chunk()
        session_data["chunks_img"] = None
    else:
        raise ValueError("Unsupported file type")

    SESSIONS[session_id] = session_data

    return {"session_id": session_id, "status": "processed"}

@app.get("/chunk/{session_id}")
def get_chunk(session_id: str):
    session = SESSIONS.get(session_id)
    step = session["current_step"]
    total_chunks = len(session["chunks"])
    chunk = session["chunks"][step]

    tracker = session["tracker"]
    question_type = tracker.get_question_type()
    bloom_level = tracker.get_next_bloom_level()

    is_retry = session["failed_attempts"].get(step, 0) > 0

    if is_retry:
        last_question = session["questions"][-1]
    else:
        last_question = None
    
    response = question_generator.generate_question(chunk, 
                                                    question_type, 
                                                    level=bloom_level, 
                                                    prompt_type="desc", 
                                                    different_from=last_question,
                                                    refine=True)

    if question_type == "SAQ":
        question = response["question"]
    elif question_type == "MCQ":
        question = response

    session["bloom_levels"].append(bloom_level)
    session["questions"].append(question)
    session["question_types"].append(question_type)  

    if session["chunks_img"] is not None:
        chunk = session["chunks_img"][step]
        is_img = True
    else:
        chunk = chunk[0].page_content
        is_img = False

    return {"chunk": chunk if not is_retry else None,
            "question": question, 
            "question_type": question_type,
            "bloom_level": BLOOM_MAP_REVERSE[bloom_level],
            "is_img": is_img,
            "progress": {
                "current": step ,
                "total": total_chunks,
                "percent": int(((step) / total_chunks) * 100)
            },
            "is_retry": is_retry
        }

@app.post("/answer/{session_id}")
def submit_answer(session_id: str, body: AnswerRequest = Body(...)):
    answer = body.answer
    elapsed_time = body.elapsed_time
    session = SESSIONS.get(session_id)
    step = session["current_step"]
    total_chunks = len(session["chunks"])

    question = session["questions"][-1]
    chunk = session["chunks"][step]
    question_type = session["question_types"][-1]

    # Check answer
    if question_type == "MCQ":
        is_correct = question_generator.check_answer_mcq(question, answer)
        feedback = "" if is_correct else f"Correct answer is: {question['answer']}"
    else:
        is_correct, feedback = question_generator.check_answer_saq(chunk, question, answer)

    # Feedback message
    text_emoji = "Correct ✅." if is_correct else "Incorrect ❌."
    feedback = f"{text_emoji} {feedback}"

    # Track attempts
    session["answers"].append(answer)
    tracker = session["tracker"]
    bloom_level = session["bloom_levels"][-1]
    tracker.update_logs(question_type, is_correct, bloom_level, elapsed_time, question, answer)

    # Initialize failed attempts if not yet done
    if step not in session["failed_attempts"]:
        session["failed_attempts"][step] = 0

    # Handle progression logic
    if is_correct:
        session["current_step"] += 1
        session["failed_attempts"].pop(step, None)  # Reset failed attempts
    else:
        session["failed_attempts"][step] += 1
        if session["failed_attempts"][step] >= 2:
            session["current_step"] += 1
            session["failed_attempts"].pop(step, None)  # Reset for next chunk

    # Progress response
    step = session["current_step"]
    if step >= total_chunks:
        tracker.post_logs()
        return {
            "feedback": feedback,
            "is_last": True,
            "progress": {"current": step, "total": total_chunks, "percent": 100},
        }

    return {
        "feedback": feedback,
        "progress": {
            "current": step,
            "total": total_chunks,
            "percent": int((step / total_chunks) * 100),
        },
    }


    
@app.post("/feedback/{session_id}")
def submit_feedback(data: dict = Body(...)):
    try:
        session_id = data.get("session_id")
        rating = data.get("rating")
        session = SESSIONS.get(session_id)
        tracker = session["tracker"]
        tracker.update_rating(rating)

        if not session_id or rating is None:
            return {"status": "error", "message": "Missing session_id or rating"}

        response = tracker.post_logs()

        return {"status": "success"}
    except Exception as e:
        print("Error:", e)
        return {"status": "error", "message": str(e)}
    

@app.post("/neo4j/connect")
def connect_to_neo4j(data: dict = Body(...)):
    url = data.get("url")
    username = data.get("username")
    password = data.get("password")

    if not url or not username or not password:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "Missing Neo4j credentials"}
        )

    driver = connection(url, username, password)
    if driver is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"status": "error", "message": "Failed to connect to Neo4j. Please check your credentials."}
        )

    try:
        with driver.session() as session:
            session.run("RETURN 1")  # Test query

        driver.close()
        NEO4J_CREDENTIALS["url"] = url
        NEO4J_CREDENTIALS["username"] = username
        NEO4J_CREDENTIALS["password"] = password
        return {"status": "success", "message": "Connected to Neo4j successfully"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": f"An error occurred: {str(e)}"}
        )
    
@app.post("/neo4j/query")
def query_knowledge_graph(data: dict = Body(...)):
    query = data.get("query")
    if not query:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "Query is required"}
        )

    kg_rag = KnowledgeGraphRAG(
        url=NEO4J_CREDENTIALS["url"],
        username=NEO4J_CREDENTIALS["username"],
        password=NEO4J_CREDENTIALS["password"],
    )

    content = kg_rag.search_query(query)
    if not content:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"status": "error", "message": "No content found for this query"}
        )

    # Simulate uploaded text file flow
    session_id = str(uuid.uuid4())
    tracker = LearningTracker(
        session_id,
        strategy="default",
        min_success_question=1,
        max_fail_question=1,
        supabase=supabase,
    )

    chunker = TextChunker(content)
    chunks = chunker.statistical_chunk()

    session_data = {
        "tracker": tracker,
        "file_bytes": None,
        "filename": "neo4j_content.txt",
        "chunks": chunks,
        "chunks_img": None,
        "questions": [],
        "answers": [],
        "bloom_levels": [],
        "question_types": [],
        "current_step": 0,
    }

    SESSIONS[session_id] = session_data

    return {"session_id": session_id, "status": "processed"}


@app.post("/user_study")
def user_study(body: dict = Body(...)):
    prolific_id = body.get("prolific_id")
    if not prolific_id:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "Missing prolific_id"}
        )
    session_id = str(uuid.uuid4())

    PRE_CHUNK_PATH = "../user_study/chunks.json"
    chunker = PDFChunker(load_path=PRE_CHUNK_PATH)

    tracker = LearningTracker(
        session_id,
        prolific_id=prolific_id,
        strategy="default",
        min_success_question=1,
        max_fail_question=1,
        supabase=supabase,
    )

    session_data = {
        "tracker": tracker,
        "file_bytes": None,
        "filename": "user_study.pdf",
        "chunks": chunker.formated_chunks,
        "chunks_img": chunker.chunks_img_b64,
        "questions": [],
        "answers": [],
        "bloom_levels": [],
        "question_types": [],
        "current_step": 0,
        "failed_attempts": {},
    }

    SESSIONS[session_id] = session_data

    return {"session_id": session_id, "status": "processed"}
