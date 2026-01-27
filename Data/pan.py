import pandas as pd

df = pd.read_csv("recording.csv")
#print(df)

data = {'Name': ['Alice', 'Bob', 'Charlie'],
        'Age': [25, 30, 35],
        'City': ['New York', 'Los Angeles', 'Chicago']}
df1 = pd.DataFrame(data)
df2 = df.query('ch2 > 0 and sample_index > 15')
print(df['ch2'].mean())
