import pandas as pd
from thefuzz import process

def join(df, target):
    
    df_filtre = df[df["amount"].round(1) == round(target["amount"], 1)]
    
    bank_vendors = df_filtre["vendor"].dropna().unique().tolist()
    if len(bank_vendors) > 0:
    
        match_str, score = process.extractOne(target["vendor"], bank_vendors)
        
        if len(match_str) > 0:
            match_df = df_filtre[df_filtre["vendor"] == match_str]

            match_df.loc[:,"file_name"] = target["file_name"]
            match_df.loc[:, "score"] = score
            """match_df.loc[:, "pic_amount"] = target["amount"]
            match_df.loc[:, "score"] = score
            match_df.loc[:, "vendor_pic"] = target["vendor"]"""

    else:
        match_df = None
    
    return match_df
