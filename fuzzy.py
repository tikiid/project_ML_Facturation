import pandas as pd
from thefuzz import process

# Charger le fichier CSV contenant les noms des vendeurs
df1 = pd.read_csv(r"C:\Users\theau\Desktop\HETIC\M2\ML\releve_01.csv")  # Remplace par ton fichier réel
df2 = pd.read_csv(r"C:\Users\theau\Desktop\HETIC\M2\ML\releve_02.csv" )
df3 = pd.read_csv(r"C:\Users\theau\Desktop\HETIC\M2\ML\releve_03.csv")
df4 = pd.read_csv(r"C:\Users\theau\Desktop\HETIC\M2\ML\releve_04.csv")
df5 = pd.read_csv(r"C:\Users\theau\Desktop\HETIC\M2\ML\releve_05.csv")
df6 = pd.read_csv(r"C:\Users\theau\Desktop\HETIC\M2\ML\releve_06.csv")

df = pd.concat([df1, df2, df3, df4, df5, df6], ignore_index=True)

prix_cible = 25.00  # Remplace par la valeur souhaitée

# Vérifier si les colonnes "vendor" et "price" existent
if "vendor" in df.columns and "price" in df.columns:
    # Filtrer les lignes où le prix correspond à la valeur donnée
    df_filtre = df[df["price"] == prix_cible]
# Vérifier si la colonne "vendor" existe
if "vendor" in df.columns:
    bank_vendors = df["vendor"].dropna().unique().tolist()  # Supprime les valeurs NaN et garde les uniques
else:
    print("La colonne 'vendor' n'existe pas dans le fichier.")
    bank_vendors = []

# Nom extrait d'un ticket de caisse
ticket_vendor = "Sukhothai Sushi Restaurant"

# Vérifier qu'il y a des vendeurs à comparer
if bank_vendors:
    # Trouver la meilleure correspondance
    match, score = process.extractOne(ticket_vendor, bank_vendors)

    print(f"Meilleure correspondance : {match} avec un score de {score}")
else:
    print("Aucun vendeur à comparer.")
