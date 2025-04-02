import pandas as pd
from thefuzz import process

def join(df, target):
    
    df_filtre = df[df["amount"] == target["amount"]]
    
    bank_vendors = df_filtre["vendor"].dropna().unique().tolist()
    
    match_str, score = process.extractOne(target["vendor"], bank_vendors)
    match_df = df_filtre[df_filtre["vendor"] == match_str]

    match_df["file_name"] = target["file_name"]
    
    return match_df
