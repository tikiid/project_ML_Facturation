import streamlit as st
import pandas as pd

# Variables
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

if facture_photos and facture_file:  
    st.success("Les conditions sont remplies, fonction exécutée !")
    if st.button("Lancer la fonction"):
        launch_function = True
        df = pd.read_csv(facture_file)
        st.write(df)
else:
    st.warning("Veuillez remplir les deux champs pour activer le bouton.")


if st.button("Réinitialiser les fichiers"):
    st.session_state.upload_key += 1
    st.rerun()  