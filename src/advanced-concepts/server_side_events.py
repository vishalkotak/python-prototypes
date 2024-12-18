import asyncio
import time

import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()


async def get_sse_data():
    for i in range(10):
        await asyncio.sleep(2)
        yield f"{time.time()}\n\n"


@app.get("/stream")
async def stream():
    return StreamingResponse(get_sse_data(), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run("server_side_events:app", host="127.0.0.1", port=8000, reload=True)
