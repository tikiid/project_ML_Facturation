import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

def text_embedding(df):
    return model.encode(df['vendor'].tolist(), convert_to_tensor=True)

def match_and_filter(df, target, embedded_vendors):
    target_text = target['vendor']
    
    target_embedded = model.encode(target_text, convert_to_tensor=True)
    
    similarities = torch.nn.functional.cosine_similarity(target_embedded.unsqueeze(0), embedded_vendors)
    max_idx = torch.argmax(similarities).item()
    sim_score = similarities[max_idx].item()

    # Get top match row
    match_vendor_row = df.iloc[max_idx]
    
    matched_rows = df[df['vendor'] == match_vendor_row["vendor"]].copy()

    # Common fields to assign
    matched_rows["file_name"] = target["file_name"]
   #matched_rows["sim"] = sim_score

    # If exactly one row matched by vendor
    if len(matched_rows) == 1:
        return matched_rows

    # If multiple rows match on vendor, filter on amount
    if len(matched_rows) > 1:
        matched_rows = matched_rows[matched_rows["amount"].round(1) == round(target["amount"], 1)]
        return matched_rows if not matched_rows.empty else None

    return None


