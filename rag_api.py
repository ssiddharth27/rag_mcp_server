from fastapi import FastAPI
from pydantic import BaseModel
from rag_pipeline import load_qa_chain, ask_rag_question

app = FastAPI()

class Query(BaseModel):
    question: str
    
@app.post("/rag")
def run_rag(query: Query):
    return {"answer": ask_rag_question(query.question)}

# def run_rag(query: Query):
#     return {"answer": ask_rag_question(query)}

# print(run_rag("what is xApp ?"))