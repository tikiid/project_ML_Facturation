from pathlib import Path
from mistralai import Mistral, ImageURLChunk, TextChunk
from pydantic import BaseModel
import os
import asyncio
import json
import streamlit as st
import base64
from dotenv import load_dotenv

load_dotenv()


# --- MODEL DE SORTIE ---
class StructuredOCR(BaseModel):
    vendor: str
    address: str
    amount: float
    date: str


# --- EXTRACTION DES PHOTOS EN BASE64 ---
def extract_photos(facture_photos):
    list_base64_url = []
    image_names = []
    for photo in facture_photos:
        st.image(photo, caption="Fichier reçu", use_column_width=True)
        file_bytes = photo.read()
        encoded = base64.b64encode(file_bytes).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{encoded}"
        list_base64_url.append(data_url)
        image_names.append(photo.name)
    return image_names, list_base64_url


# --- LIRE LE CONTEXTE ---
def read_txt_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        return f"Error: {e}"


# --- RETRY ASYNC ---
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


# --- BATCH UTILS ---
def chunkify(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


# --- APPEL MISTRAL CHAT ---
async def chat_response(client, base64_data_url):
    loop = asyncio.get_event_loop()
    context = read_txt_file("context.txt")

    def task():
        response = client.chat.parse(
            model="pixtral-large-latest",
            messages=[
                {"role": "system", "content": context},
                {
                    "role": "user",
                    "content": [
                        ImageURLChunk(image_url=base64_data_url),
                        TextChunk(text=(
                            f"This is the image's task to do on the image:\n{context}\n.\n"
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


# --- PIPELINE PRINCIPALE ---
async def main(list_base64_url, list_image_names):
    api_key = os.environ["MISTRAL_KEY"]
    async with Mistral(api_key=api_key) as client:
        all_chat_results = []
        n_batch = 3

        for i, batch_urls in enumerate(chunkify(list_base64_url, n_batch)):
            print(f"🚀 Traitement du batch {i + 1}/{len(list_base64_url) // n_batch + 1}")

            chat_tasks = [
                retry_async(chat_response, client, url, retries=3, delay=2)
                for url in batch_urls
            ]

            try:
                batch_chat_results = await asyncio.gather(*chat_tasks)
            except Exception as e:
                print(f"⚠️ Erreur batch : {e}")
                batch_chat_results = [{}] * len(batch_urls)

            start_idx = i * n_batch
            for j, result in enumerate(batch_chat_results):
                file_name = list_image_names[start_idx + j]
                if isinstance(result, dict):
                    result["file_name"] = file_name
                else:
                    result = {"file_name": file_name}
                all_chat_results.append(result)

        return all_chat_results
