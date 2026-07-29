import pandas as pd

df = pd.read_csv("outputs_endogenous.csv")

print(df.columns.tolist())
print(df[["year", "overflow_R", "overflow_O"]].head().to_string(index=False))
print(df[["overflow_R", "overflow_O"]].max())