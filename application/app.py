import streamlit as st
import pandas as pd
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from fuzzy_join import join
from async_scripting import main, extract_photos
import io
import openpyxl
from openpyxl.drawing.image import Image
import os

temp_image_folder = "temp_images"
os.makedirs(temp_image_folder, exist_ok=True)


load_dotenv()
launch_function = False

# Streamlit
st.set_page_config(page_title="Conto")


if "upload_key" not in st.session_state:
    st.session_state.upload_key = 0 


st.title("Conto")
st.header("🧾 Déposer / Glisser le fichier de facturation")
facture_file = st.file_uploader(label=" ", key=f"facture_{st.session_state.upload_key}", type=["csv"])

st.header("📂 Déposer / Glisser le fichier des photos")
facture_photos = st.file_uploader(label=" ", key=f"photos_{st.session_state.upload_key}", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

mistral_response_df= None

if facture_photos and mistral_response_df is None and "excel_file" not in st.session_state:

    
    list_image_names, list_facture_photos = extract_photos(facture_photos)

    nest_asyncio.apply()

    response = asyncio.run(main(list_facture_photos, list_image_names))
    
    if response:
        final_results = []
        dataframe = None
        for i, res in enumerate(response):
            final_results.append({"file_name": list_image_names[i], **res})
        
        try:
            df = pd.read_csv(facture_file, index_col=0)
            list_columns = df.columns.to_list()
            list_columns.append("file_name")
            dataframe = pd.DataFrame(columns=list_columns)
            for target in final_results:
                
                match_df = join(df, target)
                dataframe = pd.concat([dataframe, match_df])

            mistral_response_df=dataframe
            print(dataframe)
            st.dataframe(mistral_response_df)
        except Exception as e:
            st.error(f"Erreur de lecture : {e}")
            
        


else:
    st.warning("Veuillez remplir les deux champs pour activer le bouton.")


if st.button("Réinitialiser les fichiers"):
    if "excel_file" in st.session_state:
        del st.session_state["excel_file"]
    st.session_state.upload_key += 1
    st.rerun()  



#sentence_transformer / kmeans / hdbscan
#regarder les benchmark 

if mistral_response_df is not None and not mistral_response_df.empty and "excel_file" not in st.session_state:

    # If the user has uploaded files, handle them
    if facture_photos:
        # Save the uploaded images to the temporary folder
        image_paths = []
        for idx, uploaded_file in enumerate(facture_photos):
            file_path = os.path.join(temp_image_folder, f"image_{idx}.jpg")
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            image_paths.append(file_path)
        
        # Now let's create the Excel file and embed the images
        excel_path = "transactions_with_images.xlsx"

        # Create Excel file
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            # Write DataFrame excluding 'file_name' column
            mistral_response_df.drop(columns=["file_name"]).to_excel(writer, sheet_name="Transactions", index=False)
            
            # Get the workbook and sheet
            workbook = writer.book
            sheet = writer.sheets["Transactions"]
            
            # Insert a new header for the image column
            sheet.cell(row=1, column=5, value="Receipt Image")
            sheet.column_dimensions['E'].width = 20  # Adjust column width for the image column

            # Dynamically calculate the width of column D (Vendor) based on the longest text in column D
            max_length = max(mistral_response_df["vendor"].apply(lambda x: len(str(x))))  # Find the max length of text in column D
            sheet.column_dimensions['D'].width = max_length + 5  # Add some padding to fit the text

            # Loop through the images and add them to the Excel sheet
            for idx, image_path in enumerate(image_paths, start=2):  # Start from row 2
                if os.path.exists(image_path):
                    img = Image(image_path)
                    
                    # Resize the image to fit within a smaller space (adjust as needed)
                    img.width, img.height = 100, 100  
                    
                    # Adjust the row height dynamically based on the length of the text in previous columns
                    max_text_length = max(len(str(val)) for val in mistral_response_df.iloc[idx-2, :])  # Get the max text length in this row
                    estimated_row_height = 20 + (max_text_length // 30) * 10  # Adjust the height based on text length
                    
                    # Set the row height for the current row
                    sheet.row_dimensions[idx].height = max(estimated_row_height, 80)  # Ensure row height is at least 80
                    
                    # Place image in the correct position (in column E)
                    sheet.add_image(img, f"E{idx}")  # Place image in column E
                    
                else:
                    print(f"Warning: Image not found - {image_path}")

            # Save the modified Excel file
            workbook.save(excel_path)

        # Save the generated Excel file path to session state so it doesn't get recreated
        with open(excel_path, "rb") as f:
            st.session_state.excel_file = f.read()

    else:
        st.write("Please upload receipt images to generate the Excel file.")

# Check if the Excel file is available in session state
if "excel_file" in st.session_state:
    # Streamlit download button, which will not cause a rerun of the app
    st.download_button(
        label="Download Excel",
        data=st.session_state.excel_file,
        file_name="transactions_with_images.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
