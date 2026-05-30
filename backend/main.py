from __future__ import annotations

import traceback

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from config import MAX_UPLOAD_SIZE
from services.pdf_parser import parse_pdf
from services.llm_service import stream_summarize, stream_translate

app = FastAPI(title="PDF 论文解析器")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TextRequest(BaseModel):
    text: str


class TranslateRequest(BaseModel):
    paragraphs: list[str]


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 20MB")

    try:
        result = parse_pdf(contents)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF 解析失败: {str(e)}")

    return {
        "filename": file.filename,
        "file_size": len(contents),
        "total_pages": result["total_pages"],
        "pages": result["pages"],
        "full_text": result["full_text"],
        "paragraphs": result["paragraphs"],
        "first_page_image": result["first_page_image"],
    }


@app.post("/api/summarize")
async def summarize(req: TextRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="文本内容不能为空")

    async def event_generator():
        try:
            async for token in stream_summarize(req.text):
                yield {"event": "message", "data": token}
            yield {"event": "done", "data": "[DONE]"}
        except Exception as e:
            traceback.print_exc()
            yield {"event": "error", "data": str(e)}

    return EventSourceResponse(event_generator())


@app.post("/api/translate")
async def translate(req: TranslateRequest):
    if not req.paragraphs:
        raise HTTPException(status_code=400, detail="段落列表不能为空")

    async def event_generator():
        try:
            async for data in stream_translate(req.paragraphs):
                yield {"event": "message", "data": data}
            yield {"event": "done", "data": "[DONE]"}
        except Exception as e:
            traceback.print_exc()
            yield {"event": "error", "data": str(e)}

    return EventSourceResponse(event_generator())


@app.get("/api/health")
async def health():
    return {"status": "ok"}
