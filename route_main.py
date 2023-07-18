import uuid
import aiofiles
import uvicorn
from fastapi import FastAPI, UploadFile, BackgroundTasks, Request
import whisper
import logging as log
import os
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Configure logging
log.basicConfig()

# Create FastAPI app
app = FastAPI()

# CORS configuration
origins = [
    "https://cdhealthscanner-staging.azurewebsites.net",
    "https://healthscanner.marvsai.net",
]

app.add_middleware(SessionMiddleware, secret_key="x12j3j", max_age=5600)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Set the appropriate origins here
    allow_methods=["*"],  # Set the allowed HTTP methods
    allow_headers=["*"],  # Set the allowed headers
    allow_credentials=True,
)

# Load the Whisper model
model = whisper.load_model("medium.en", device="cuda", download_root="./")


# Function to generate a unique UUID for each session
def generate_uuid():
    return str(uuid.uuid1())


@app.post("/voice/")
async def upload_file(request: Request, background_tasks: BackgroundTasks, sound: UploadFile = None):
    c = 0
    if "uuid" not in request.session:
        request.session["uuid"] = generate_uuid()
        print(request.session["uuid"])

    if "count" in request.session:
        c = int(request.session["count"])

    c += 1
    request.session["count"] = c

    if sound is None:
        return {"error": "No file provided"}

    file_path = f"voice_data/{request.session['uuid']}{sound.filename}"
    await save_file(sound, file_path)

    # Schedule background task to process the file asynchronously
    if c % 1 == 0:
        background_tasks.add_task(process_file, file_path)

    return {"message": "File uploaded and processing started", "confirm_text": file_path}


@app.get("/get_text")
async def get_text(filename: str):
    txtfile = filename + ".txt"
    try:
        with open(txtfile, "r") as f:
            data = f.read()

        os.remove(txtfile)
        log.info("txt file removed")
    except Exception as e:
        log.error(str(e))
        data = "Error: File not found"

    return {"text": data}


async def process_file(file_path: str):
    output_file = f"{file_path}.txt"
    print("Processing the file now")
    # Replace this subprocess call with your text-to-speech engine command
    # Example: subprocess.run(["your_text_to_speech_command", file_path, output_file])
    text = convert_text(file_path)

    async with aiofiles.open(output_file, "a") as f:
        await f.write(text["text"])


async def save_file(file: UploadFile, file_path: str):
    async with aiofiles.open(file_path, "ab") as f:
        while chunk := await file.read(10000):
            await f.write(chunk)


@app.get("/")
async def read_index():
    return {"message": "Welcome to the Voice-to-Text API"}


def convert_text(audiopath: str):
    text = model.transcribe(audiopath)

    try:
        os.remove(audiopath)
        print("File removed")
    except Exception as e:
        log.error(str(e))

    return text


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
