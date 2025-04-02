from pathlib import Path
from mistralai import Mistral, ImageURLChunk, TextChunk
from pydantic import BaseModel
import os
import asyncio
import json
import streamlit as st
import base64
from dotenv import load_dotenv
import time
load_dotenv()
class StructuredOCR(BaseModel):
    #file_name: str
    #topics: list[str]
    #languages: str
    #ocr_contents: dict
    currency: str
    vendor: str
    date: str
    amount: float
    address: str


def extract_photos(facture_photos):
    list_base64_url = [] 
    image_names = []
    for photo in facture_photos:
        st.image(photo, caption="Fichier reçu", use_column_width=True)

    # Lire les données binaires
        file_bytes = photo.read()

                    # Encodage base64 si tu veux utiliser dans un appel API
        encoded = base64.b64encode(file_bytes).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{encoded}"
        list_base64_url.append(data_url)
        image_names.append(photo.name)
    return image_names, list_base64_url 
          
def read_txt_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return f"Error: The file '{file_path}' was not found."
    except Exception as e:
        return f"Error: {e}"
# ou from mistralai.models import ...

def chunkify(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


async def fetch(client, base64_data_url):
    print(f"[{time.time():.2f}] Start OCR")
    loop = asyncio.get_event_loop() #permet de pouvoir run en paralelle

    def task():
        response = client.ocr.process(
            document=ImageURLChunk(image_url=base64_data_url),
            model="mistral-ocr-latest"
        )
        return response.pages[0].markdown

    result = await loop.run_in_executor(None, task)
    print(f"[{time.time():.2f}] End OCR")
    return result


async def chat_response(client, base64_data_url, markdown_ocr):
    print(f"[{time.time():.2f}] Start Chat")
    loop = asyncio.get_event_loop() #permet de pouvoir run en paralelle

    def task():
        response = client.chat.parse(
            model="pixtral-12b-latest",
            messages=[
                {"role": "system", "content": read_txt_file("context.txt")},
                {
                    "role": "user",
                    "content": [
                        ImageURLChunk(image_url=base64_data_url),
                        TextChunk(text=(
                            f"This is the image's OCR in markdown:\n{markdown_ocr}\n.\n"
                            "Convert this into a structured JSON response "
                            "with the OCR contents in a sensible dictionary."
                        ))
                    ]
                }
            ],
            response_format=StructuredOCR,
        )
        return json.loads(response.choices[0].message.parsed.model_dump_json())

    result = await loop.run_in_executor(None, task)
    print(f"[{time.time():.2f}] End Chat")
    return result


async def main(list_base64_url, list_image_names):
    start_time = time.time()
    api_key = os.environ["MISTRAL_KEY"]

    async with Mistral(api_key=api_key) as client:
        all_markdowns = []
        all_chat_results = []
        n_batch = 5
        
        for batch in chunkify(list_base64_url, n_batch):
            print(f"\n🚀 OCR batch of {len(batch)}")
            ocr_tasks = [fetch(client, url) for url in batch]
            batch_results = await asyncio.gather(*ocr_tasks)
            all_markdowns.extend(batch_results)

        
        for urls_batch, markdowns_batch in zip(
            chunkify(list_base64_url, n_batch), chunkify(all_markdowns, n_batch)):
            print(f"\n💬 Chat batch of {len(urls_batch)}")
            chat_tasks = [
                chat_response(client, url, markdown)
                for url, markdown in zip(urls_batch, markdowns_batch)
            ]
            batch_chat_results = await asyncio.gather(*chat_tasks)
            all_chat_results.extend(batch_chat_results)

    total_time = time.time() - start_time
    print(f"Total time: {total_time:.2f} seconds\n")

    return all_chat_results
