import pandas as pd

df = pd.read_csv('data/processed/analyzed_reviews.csv')
pos_12 = df[(df['sample_group'] == 'all_1_2_star') & (df['primary_theme'] == 'POSITIVE')]
sample_pos = pos_12.sample(n=min(10, len(pos_12)), random_state=42)
for i, (_, row) in enumerate(sample_pos.iterrows(), 1):
    c = str(row['content']).strip()
    print(f"[{i}] Score: {row['score']} Star | TagMethod: {row['tag_method']} | Text: {repr(c)}")
