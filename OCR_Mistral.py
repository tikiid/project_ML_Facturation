# Initialize Mistral client with API key
from mistralai import Mistral

api_key = "API_KEY" # Replace with your API key
client = Mistral(api_key=api_key)

# Import required libraries
from pathlib import Path
from mistralai import DocumentURLChunk, ImageURLChunk, TextChunk
import json

# Verify PDF file exists
import base64

# Verify image exists
image_file = Path("/Users/eliot/Desktop/project_ML/dataset/receipts/1127-receipt.jpg")
assert image_file.is_file()

# Encode image as base64 for API
encoded = base64.b64encode(image_file.read_bytes()).decode()
base64_data_url = f"data:image/jpeg;base64,{encoded}"

image_response = client.ocr.process(
    document=ImageURLChunk(image_url=base64_data_url),
    model="mistral-ocr-latest"
)

# Convert response to JSON
response_dict = json.loads(image_response.model_dump_json())
json_string = json.dumps(response_dict, indent=4)

image_ocr_markdown = response_dict["pages"][0]["markdown"]
# Get structured response from model
chat_response = client.chat.complete(
    model="pixtral-12b-latest",
    messages=[
        {
            "role": "user",
            "content": [
                ImageURLChunk(image_url=base64_data_url),
                TextChunk(
                    text=(
                        f"This is image's OCR in markdown:\n\n{image_ocr_markdown}\n.\n"
                        "I wan't same structured json with only 'name' restaurant final 'total' and 'date'"
                        "The output should be strictly be json with no extra commentary"
                        
                    )
                ),
            ],
        }
    ],
    response_format={"type": "json_object"},
    temperature=0,
)

# Parse and return JSON response
response_dict = json.loads(chat_response.choices[0].message.content)

