import streamlit as st
import pandas as pd
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from fuzzy_join import *
from asyn_v2 import *
import io
import os
from openpyxl.drawing.image import Image as OpenPyXLImage
from PIL import Image as PILImage

# Load environment variables
load_dotenv()

# Temp folder for Excel files
TEMP_FOLDER = "temp_files"
os.makedirs(TEMP_FOLDER, exist_ok=True)

st.set_page_config(page_title="Page de Facturation")

st.title("Conto")
st.header("📂 Drag & Drop les photos des factures")

if "upload_key" not in st.session_state:
    st.session_state.upload_key = 0

facture_photos = st.file_uploader(label=" ", key=f"photos_{st.session_state.upload_key}", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
st.header("🧾 Drag & Drop le fichier CSV de facturation")
facture_file = st.file_uploader(label=" ", key=f"facture_{st.session_state.upload_key}", type=["csv"])

# Store processed results in session_state to prevent reruns
if "mistral_response_df" not in st.session_state:
    st.session_state.mistral_response_df = None
if "excel_files" not in st.session_state:
    st.session_state.excel_files = {}

# Process the uploaded files
if facture_photos and facture_file and st.session_state.mistral_response_df is None:
    list_image_names, list_facture_photos = extract_photos(facture_photos)

    nest_asyncio.apply()
    response = asyncio.run(main(list_facture_photos, list_image_names))
    
    # Precompute embeddings
    
    if response:
        final_results = []
        for i, res in enumerate(response):
            final_results.append({"file_name": list_image_names[i], **res})

        try:
            df = pd.read_csv(facture_file, index_col=0)
            csv_text_embedded = text_embedding(df)
            list_columns = df.columns.to_list() + ["file_name"]
            dataframe = pd.DataFrame(columns=list_columns)
            final_rows = []
            for target in final_results:
                        matched_data = match_and_filter(df, target, csv_text_embedded)
                        final_rows.append(matched_data)

        # Concatenate all matches into one dataframe
            dataframe = pd.concat(final_rows, ignore_index=True)
        
        
            st.session_state.mistral_response_df = dataframe
            st.dataframe(st.session_state.mistral_response_df)
            #print(dataframe)

        except Exception as e:
            st.error(f"Erreur de lecture : {e}")
else:
    st.warning("Veuillez remplir les deux champs pour activer le bouton.")

# Reset Button
if st.button("Réinitialiser les fichiers"):
    st.session_state.upload_key += 1
    st.session_state.mistral_response_df = None
    st.session_state.excel_files = {}
    st.rerun()

# Generate Excel file with multiple sheets
if st.session_state.mistral_response_df is not None:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Create a sheet for the main DataFrame
        st.session_state.mistral_response_df.to_excel(writer, index=False, sheet_name="Main")

            # Access the workbook and the "Main" sheet
        workbook = writer.book
        main_sheet = workbook['Main']
        main_sheet.column_dimensions['D'].width = 100
        main_sheet.column_dimensions['A'].width = 15
        main_sheet.column_dimensions['B'].width = 15
        main_sheet.column_dimensions['E'].width = 15

        # Iterate over each row of the DataFrame and create a new sheet for each receipt
        for index, row in st.session_state.mistral_response_df.iterrows():
            file_name = row['file_name']
            
            # Create a new sheet for each receipt
            sheet_name = file_name[:31]  # Excel sheet name is limited to 31 characters
            df_row = pd.DataFrame([row])

            # Write the row to the new sheet
            df_row.to_excel(writer, index=False, sheet_name=sheet_name)

            # Get the image corresponding to the file_name (if it exists)
            image_path = None
            for uploaded_file in facture_photos:
                if uploaded_file.name == file_name:
                    image_path = uploaded_file
                    break

            # If image is found, insert it into the new sheet
            if image_path:
                img = PILImage.open(image_path)  # Open image using PIL
                img.save(f"{TEMP_FOLDER}/{file_name}")  # Save it to temp folder
                img = OpenPyXLImage(f"{TEMP_FOLDER}/{file_name}")  # Load the image into openpyxl
                
                sheet = writer.sheets[sheet_name]
                # Add image to cell A1 in the sheet

                max_length = max(df_row["vendor"].apply(lambda x: len(str(x))))  # Find the max length of text in column D
                sheet.column_dimensions['D'].width = max_length + 5
                sheet.column_dimensions['A'].width = 15
                sheet.column_dimensions['B'].width = 15
                img.anchor = 'E1'

                img.width, img.height = 500,500 
                sheet.add_image(img)

                hyperlink_formula = f'=HYPERLINK("#\'Main\'!A1", "back to main")'
                sheet[f"A{5}"] = hyperlink_formula

        for i, file_name in enumerate(st.session_state.mistral_response_df['file_name'], start=2):  # Excel is 1-indexed
            hyperlink_formula = f'=HYPERLINK("#\'{file_name}\'!A1", "{file_name}")'
            main_sheet[f"E{i}"] = hyperlink_formula
            

    # Save the file into session state
    st.session_state["main_excel"] = output.getvalue()

# Streamlit UI for Downloads
if st.session_state.get("main_excel"):
    st.title("📊 Télécharger le fichier Excel")

    st.download_button(
        label="📥 Télécharger le fichier Excel principal",
        data=st.session_state.main_excel,
        file_name="Main.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
