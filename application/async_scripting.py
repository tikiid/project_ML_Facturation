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
        
        file_bytes = photo.read()

                    # Encodage base64 si tu veux utiliser dans un appel API
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

async def retry_async(func, *args, retries=3, delay=2, **kwargs):
    for attempt in range(retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt < retries - 1:
                print(f"[retry] Attempt {attempt + 1} failed: {e} — retrying in {delay}s")
                await asyncio.sleep(delay)
            else:
                print(f"[retry] Failed after {retries} attempts: {e}")
                raise

def chunkify(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


async def fetch(client, base64_data_url):

    loop = asyncio.get_event_loop() #permet de pouvoir run en paralelle

    def task():
        response = client.ocr.process(
            document=ImageURLChunk(image_url=base64_data_url),
            model="mistral-ocr-latest"
        )
        return response.pages[0].markdown

    result = await loop.run_in_executor(None, task)

    return result


async def chat_response(client, base64_data_url, markdown_ocr):

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

    return result

async def main(list_base64_url, list_image_names):
    api_key = os.environ["MISTRAL_KEY"]

    async with Mistral(api_key=api_key) as client:
        all_markdowns = []
        all_chat_results = []
        n_batch = 4

        for batch in chunkify(list_base64_url, n_batch):
            ocr_tasks = [retry_async(fetch, client, url, retries=10, delay=4) for url in batch]
            try:
                batch_results = await asyncio.gather(*ocr_tasks)
                all_markdowns.extend(batch_results)
            except Exception as e:
                all_markdowns.extend([""] * len(batch))


        for i, (urls_batch, markdowns_batch) in enumerate(zip(
            chunkify(list_base64_url, n_batch), chunkify(all_markdowns, n_batch)
        )):
            chat_tasks = [
                retry_async(chat_response, client, url, markdown, retries=3, delay=2)
                for url, markdown in zip(urls_batch, markdowns_batch)
            ]

            try:
                batch_chat_results = await asyncio.gather(*chat_tasks)
            except Exception as e:
                batch_chat_results = [{}] * len(urls_batch)

            # 👇 Add file_name to each result
            start_idx = i * n_batch
            for j, result in enumerate(batch_chat_results):
                file_name = list_image_names[start_idx + j]
                if isinstance(result, dict):
                    result["file_name"] = file_name
                else:
                    result = {"file_name": file_name}
                all_chat_results.append(result)

        return all_chat_results
