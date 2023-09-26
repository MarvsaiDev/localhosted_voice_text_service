import whisper
import fastapi
import redis.asyncio as redis
import pickle
import pandas as pd

model = whisper.load_model("medium.en", device="cuda")

async def get_redis():
    r = await redis.from_url("redis://localhost")
    yield r


async def store_data(raw_list, df:pd.DataFrame):

    raw = b''
    rawDf = b''
    async for r in get_redis():
        raw = pickle.dumps(raw_list)
        if not df.empty:
            rawDf = pickle.dumps(df)
            async with r.pipeline(transaction=True) as pipe:
                ok1, ok2 = await (pipe.append("raw_list", raw).set("recognized_df", rawDf).execute())
                load_raw_list = await (pipe.get('raw_list').execute())
                load_raw_list = pickle.loads(load_raw_list[0])
                loadDF = await (pipe.get('recognized_df').execute())
                loadDF = pickle.loads(loadDF[0])
                return load_raw_list, loadDF
        else:
            pass

        return None, None


# transcription = model.transcribe("hello_world.mp3", task=”transcribe”, language="en")
# print(transcription["text"])
' Hello world.'

def convert_text(audio:bytearray=None):

    if audio:
        with open('.wav', 'ab') as f:
            f.write(audio)
    text = model.transcribe('videoaudio.wav')
    print(text)

convert_text()
