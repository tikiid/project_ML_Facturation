import streamlit as st
import pandas as pd
import base64
# Variables
import asyncio
import os
import base64
from pathlib import Path
from mistralai import Mistral, ImageURLChunk, TextChunk
import nest_asyncio
from dotenv import load_dotenv
import os
import json
from pydantic import BaseModel
load_dotenv()
launch_function = False

# Streamlit
st.set_page_config(page_title="Page de facturation")

st.title("Conto")
st.header("📂 Drag & Droper le fichier des photos")

if "upload_key" not in st.session_state:
    st.session_state.upload_key = 0 

facture_photos = st.file_uploader(label=" ", key=f"photos_{st.session_state.upload_key}", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
st.header("🧾 Drag & Droper le fichier de facturation")
facture_file = st.file_uploader(label=" ", key=f"facture_{st.session_state.upload_key}", type=["csv"])

# if facture_file:
#     st.write("-----")
#     st.write(f"{facture_file.name}")
list_base64url = []
if facture_photos:

    for photo in facture_photos:
        st.image(photo, caption="Fichier reçu", use_column_width=True)

    # Lire les données binaires
        file_bytes = photo.read()

                    # Encodage base64 si tu veux utiliser dans un appel API
        encoded = base64.b64encode(file_bytes).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{encoded}"
        list_base64url.append(data_url)
        print(photo.name)
    

    class StructuredOCR(BaseModel):
        #file_name: str
        #topics: list[str]
        #languages: str
        #ocr_contents: dict
        currency: str
        vendor: str
        date: str
        amout: float
        address: str


    

    # Async function to process each image (no await on .process)
    async def fetch(client, base64_data_url):
        response = client.ocr.process(
            document=ImageURLChunk(image_url=base64_data_url),
            model="mistral-ocr-latest"
        )
        return response.pages[0].markdown
    async def chat_response(client , base64_data_url, marckdown_ocr):
        def read_txt_file(file_path):
            """Reads a text file and returns its content as a string."""
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    return file.read()
            except FileNotFoundError:
                return f"Error: The file '{file_path}' was not found."
            except Exception as e:
                return f"Error: {e}"
        
        response = client.chat.parse(
            model="pixtral-12b-latest",
            messages=[
                {"role": "system", "content": read_txt_file("context.txt")},
                {
                    "role": "user",
                    "content": [
                        ImageURLChunk(image_url=base64_data_url),
                        TextChunk(text=(
                            f"This is the image's OCR in markdown:\n{marckdown_ocr}\n.\n"
                            "Convert this into a structured JSON response "
                            "with the OCR contents in a sensible dictionary."
                        ))
                    ]
                }
            ],
            response_format=StructuredOCR,

        )
        
        return json.loads(response.choices[0].message.parsed.model_dump_json())

    # Main async runner
    async def main():
        api_key = os.getenv("CLEMENT_KEY")
        async with Mistral(api_key=api_key) as client:             
                semaphore = asyncio.Semaphore(5)

                async def safe_fetch(url):
                    async with semaphore:
                        return await fetch(client, url)

                async def safe_chat(url, markdown):
                    async with semaphore:
                        return await chat_response(client, url, markdown)

                # OCR
                ocr_tasks = [safe_fetch(url) for url in list_base64url]
                results = await asyncio.gather(*ocr_tasks)

                # Chat
                chat_tasks = [safe_chat(url, markdown) for url, markdown in zip(list_base64url, results)]
                chat_results = await asyncio.gather(*chat_tasks)

                return chat_results
                
        

    # If needed (e.g. in Jupyter)
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(main())
    print(results)
    # Affiche les résultats
    for i, res in enumerate(results):
        st.subheader(f"📄 Résultat pour facture {i+1}")
        st.json(res)
    
    



else:
    st.warning("Veuillez remplir les deux champs pour activer le bouton.")


if st.button("Réinitialiser les fichiers"):
    st.session_state.upload_key += 1
    st.rerun()  


#sentence_transformer / kmeans / hdbscan
#regarder les benchmark 
