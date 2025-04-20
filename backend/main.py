from fastapi import FastAPI, UploadFile, File, Body
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

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS = {}  

question_generator = BloomQuestionGenerator()

@app.post("/prepare")
async def prepare_upload(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    contents = await file.read()
    tracker = LearningTracker(session_id, strategy="default", min_question_per_level=1, until_success=False)

    SESSIONS[session_id] = {
        "tracker": tracker,
        "file_bytes": contents,
        "filename": file.filename,
        "chunks": None,
        "chunks_img": None,
        "questions": [],
        "answers": [],
        "bloom_levels": [],
        "question_types": [],
        "current_step": 0
    }

    return {"session_id": session_id}

@app.post("/process/{session_id}")
def process_file(session_id: str):
    session = SESSIONS.get(session_id)
    contents = session["file_bytes"] 
    filename = session["filename"]

    if filename.endswith(".pdf"):
        file_obj = BytesIO(contents)
        chunker = PDFChunker(file_obj=file_obj)
        session["chunks"] = chunker.formated_chunks
        session["chunks_img"] = chunker.chunks_img_b64
    elif filename.endswith(".txt"):
        text = contents.decode("utf-8")
        chunker = TextChunker(text)
        session["chunks"] = chunker.recursive_chunk(chunk_size=1000)
        session["chunks_img"] = None
    else:
        raise ValueError("Unsupported file type")

    return {"status": "done"}

@app.get("/chunk/{session_id}")
def get_chunk(session_id: str):
    session = SESSIONS.get(session_id)
    step = session["current_step"]
    total_chunks = len(session["chunks"])
    chunk = session["chunks"][step]

    tracker = session["tracker"]
    question_type = tracker.get_question_type()
    bloom_level = tracker.get_next_bloom_level()
    
    response = question_generator.generate_question(chunk, question_type, level=bloom_level, prompt_type="desc")

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

    return {"chunk": chunk, 
            "question": question, 
            "question_type": question_type,
            "bloom_level": BLOOM_MAP_REVERSE[bloom_level],
            "is_img": is_img,
            "progress": {
                "current": step ,
                "total": total_chunks,
                "percent": int(((step) / total_chunks) * 100)
            }
        }

@app.post("/answer/{session_id}")
def submit_answer(session_id: str, body: AnswerRequest = Body(...)):
    answer = body.answer
    elapsed_time = body.elapsed_time

    session = SESSIONS.get(session_id)

    total_chunks = len(session["chunks"])
    question = session["questions"][session["current_step"]]
    chunk = session["chunks"][session["current_step"]]
    session["answers"].append(answer)
    question_type = session["question_types"][session["current_step"]]

    if question_type == "MCQ":
        is_correct = question_generator.check_answer_mcq(question, answer)
        feedback = "" if is_correct else "Correct answer is: " + question["answer"]
    elif question_type == "SAQ":
        is_correct, feedback = question_generator.check_answer_saq(chunk, question, answer)

    text_emoji = "Correct ✅." if is_correct else "Incorrect ❌."

    feedback = f"{text_emoji} {feedback}"

    # Update logs of the tracker
    tracker = session["tracker"]
    bloom_level = session["bloom_levels"][session["current_step"]]
    tracker.update_logs(question_type, is_correct, bloom_level, elapsed_time, question, answer)

    session["current_step"] += 1
    step = session["current_step"]

    if step >= len(session["chunks"]):
        return {"feedback": feedback, 
                "is_last": True,
                "progress": {
                    "current": step,
                    "total": total_chunks,
                    "percent": 100
                } 
            }
    else:
        return {"feedback": feedback,
                "progress": {
                    "current": step,
                    "total": total_chunks,
                    "percent": int(((step) / total_chunks) * 100)
                }
            }
    
@app.post("/feedback/{session_id}")
def submit_feedback(data: dict = Body(...)):
    try:
        session_id = data.get("session_id")
        rating = data.get("rating")

        if not session_id or rating is None:
            return {"status": "error", "message": "Missing session_id or rating"}

        supabase.table("feedback").insert({
            "session_id": session_id,
            "rating": rating
        }).execute()

        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}