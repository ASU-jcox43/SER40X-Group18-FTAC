from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class IngestDocsPut(BaseModel):
    start_url: str
    layers: int
    get_pdfs: bool
    regex: str

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/ingest-docs")
async def update_item(layers:int, start_url:str, get_pdfs:bool, regex:str|None):
    """
    :param layers:
    :param start_url:
    :param get_pdfs:
    :param regex:
    :return:
    """
    # run DocumentScraper1
    # return all the links
    return {"output": f"i will extract {layers} layers from {start_url} and {"get pdfs" if get_pdfs else "get html text"} filtering with {regex}"}