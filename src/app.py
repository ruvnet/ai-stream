from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from video_processor import process_frame
import uvicorn

app = FastAPI()

@app.post("/process_frame")
async def process_frame_endpoint(file: UploadFile = File(...)):
    try:
        frame = await file.read()
        response = await process_frame(frame)
        return JSONResponse(content={'response': response})
    except Exception as e:
        return JSONResponse(content={'error': str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
