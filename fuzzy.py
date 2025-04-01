import pandas as pd
from thefuzz import process

df = pd.read_csv(r"C:\Users\theau\Desktop\HETIC\M2\ML\releve_final.csv")

prix_cible = 25.00

if "vendor" in df.columns and "price" in df.columns:
    df_filtre = df[df["price"] == prix_cible]

if "vendor" in df.columns:
    bank_vendors = df["vendor"].dropna().unique().tolist()
else:
    print("La colonne 'vendor' n'existe pas dans le fichier.")
    bank_vendors = []

ticket_vendor = "Sukhothai Sushi Restaurant"

if bank_vendors:
    match, score = process.extractOne(ticket_vendor, bank_vendors)
    
    if score > 80:
        print(f"Meilleure correspondance : {match} avec un score de {score}")
    else:
        print("Aucune correspondance fiable trouvée.")
else:
    print("Aucun vendeur à comparer.")
