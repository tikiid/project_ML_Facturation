from thefuzz import process

# Liste des noms du relevé bancaire
bank_vendors = ["Yogurtland", "Casa Rubia Cafe", "SUKHOTHAI SUSHI", "EL POLLO LOCO"]

# Nom extrait d'un ticket de caisse
ticket_vendor = "Sukhothai Sushi Restaurant"

# Trouver la meilleure correspondance
match, score = process.extractOne(ticket_vendor, bank_vendors)
