from fastapi import FastAPI, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from pydantic import BaseModel
from scripts.bloom_gen import BloomQuestionGenerator
from scripts.chunk import TextChunker, PDFChunker
from utils.helpers import load_pdf, load_txt


class AnswerRequest(BaseModel):
    answer: str

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS = {}  

chunker = TextChunker()
question_generator = BloomQuestionGenerator()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    save_path = f"./backend/uploads/{file.filename}"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(await file.read())
    
    # check file type:
    if save_path.endswith(".pdf"):
        text = load_pdf(save_path)
        # chunker = PDFChunker(pdf_path=save_path)
    elif save_path.endswith(".txt"):
        text = load_txt(save_path)
        chunker = TextChunker()
    else:
        print("File type not supported")

    
    chunks = chunker.recursive_chunk(text, chunk_size=1000)

    SESSIONS[session_id] = {
        "chunks": chunks,
        "questions": [],
        "answers": [],
        "current_step": 0
    }
    return {"session_id": session_id}

@app.get("/chunk/{session_id}")
def get_chunk(session_id: str):
    session = SESSIONS.get(session_id)
    step = session["current_step"]
    chunk = session["chunks"][step]
    question_dict = question_generator.generate_question(chunk, "SAQ", level=1, prompt_type="desc")
    question = question_dict["question"]
    session["questions"].append(question)

    return {"chunk": chunk, "question": question}

@app.post("/answer/{session_id}")
def submit_answer(session_id: str, body: AnswerRequest = Body(...)):
    answer = body.answer
    session = SESSIONS.get(session_id)
    question = session["questions"][session["current_step"]]
    chunk = session["chunks"][session["current_step"]]
    session["answers"].append(answer)

    is_correct, feedback = question_generator.check_answer_saq(chunk, question, answer)

    text_emoji = "Correct ✅." if is_correct else "Incorrect ❌."

    feedback = f"{text_emoji} {feedback}"

    session["current_step"] += 1
    step = session["current_step"]

    if step >= len(session["chunks"]):
        return {"feedback": feedback, "is_last": True}

    chunk = session["chunks"][step]
    question_dict = question_generator.generate_question(chunk, "SAQ", level=1, prompt_type="desc")
    question = question_dict["question"]
    return {"next_chunk": chunk, "next_question": question, "feedback": feedback}