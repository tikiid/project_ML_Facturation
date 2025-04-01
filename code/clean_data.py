import pandas as pd

df = pd.read_csv("releve_concat_clean.csv", index_col = 0)

df_int = df.drop('Unnamed: 0', axis = 1)
df_int['date'] = df_int['date'].str.replace('/', '-', regex=False)
df_int["vendor"] = df_int["vendor"].str.replace('"', '', regex=False)

print(df_int.head())

df_int.to_csv("releve_final.csv")
