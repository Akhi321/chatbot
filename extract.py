import pdfplumber
import pandas as pd

pdf = pdfplumber.open('data.pdf')
tables = []
for page in pdf.pages:
    table = page.extract_table()
    if table:
        df = pd.DataFrame(table[1:], columns=table[0])
        tables.append(df)

if tables:
    final_df = pd.concat(tables, ignore_index=True)
    print(final_df.head())
    print(final_df.columns)
    final_df.to_csv('extracted_data.csv', index=False)
