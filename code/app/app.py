import streamlit as st
import os
import pandas as pd
import base64

# Variables

launch_function = False

# CSS


# Code 

st.set_page_config(page_title="Page de facturation", layout="wide")

st.title("Conto")

st.header("📂 Drag & Droper le fichier des photos")

facture_photos = st.file_uploader(label="", key="photos")

st.header("🧾 Drag & Drop de fichiers")

facture_file = st.file_uploader(label="", key="facture")

# 📌 Dossier temporaire pour stocker les fichiers

# unpacking the tuple
file_name, file_extension = os.path.splitext(facture_file)

print(file_name)
print(file_extension)
st.write(f"{file_extension}")

if facture_photos and facture_file:  # Les deux variables ne doivent pas être vides
    if st.button("Lancer la fonction"):
        st.success("Les conditions sont remplies, fonction exécutée !")
        launch_function = True

        df = facture_file 


else:
    st.warning("Veuillez remplir les deux champs pour activer le bouton.")



if launch_function:
    pass


# def read_data(filename):
#     df = pd.read_csv(filename, encoding='gbk')
#     return df

# st.subheader("1")
# df1 = pd.read_csv(file, encoding="gbk")
# st.write(df1)
# st.subheader("2")
# file.seek(0)  # Back to the beginning of the file.
# df = read_data(file)  # st.write(pd.read_csv(file, encoding="gbk"))
# st.write(df)

# Bouton pour effacer toutes les données
if st.button("Effacer toutes les données"):
    st.experimental_rerun()