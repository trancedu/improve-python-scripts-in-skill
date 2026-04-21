"""my-skill server — started automatically by client.py via uv."""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


class RunRequest(BaseModel):
    input: str


@app.post("/run")
def run(req: RunRequest):
    return {"result": f"processed {req.input!r}"}
