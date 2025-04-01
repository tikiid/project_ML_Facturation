import asyncio
import os
import base64
from pathlib import Path
from mistralai import Mistral, ImageURLChunk, TextChunk
import nest_asyncio
from dotenv import load_dotenv
import os
import json

load_dotenv()
# Prepare base64 image data
path = "/Users/eliot/Desktop/project_ML/project_ML_Facturation/receipt_dropzone"
urls_path = os.listdir(path)
list_base64url = []
from pydantic import BaseModel

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


for image_filename in urls_path:
    image_file = Path(os.path.join(path, image_filename))
    if image_file.is_file():
        encoded = base64.b64encode(image_file.read_bytes()).decode()
        list_base64url.append(f"data:image/jpeg;base64,{encoded}")

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
    async with Mistral(api_key=os.environ["CLEMENT_KEY"]) as client:
        tasks = [fetch(client, url) for url in list_base64url]
        results = await asyncio.gather(*tasks)

        chat_tasks = [
            chat_response(client, url, markdown)
            for url, markdown in zip(list_base64url, results)
        ]
        chat_results = await asyncio.gather(*chat_tasks)
        
       

# If needed (e.g. in Jupyter)
nest_asyncio.apply()

# Run it
asyncio.run(main())




