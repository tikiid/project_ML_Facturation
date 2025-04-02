import streamlit as st
import pandas as pd
# Variables
import asyncio
import os

import nest_asyncio

import os
import json

from fuzzy_join import join
from async_scripting import main, extract_photos

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


list_base64url = []
image_names = []
if facture_photos:

    
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
                dataframe = match_df.copy() if dataframe.empty else pd.concat([dataframe, match_df])
            print(dataframe)
        except Exception as e:
            st.error(f"Erreur de lecture : {e}")
            
        

          



else:
    st.warning("Veuillez remplir les deux champs pour activer le bouton.")


if st.button("Réinitialiser les fichiers"):
    st.session_state.upload_key += 1
    st.rerun()  

