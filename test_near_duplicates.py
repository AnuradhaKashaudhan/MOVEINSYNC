import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

df = pd.read_csv('data/processed/analyzed_reviews.csv')
df_12 = df[(df['sample_group'] == 'all_1_2_star') & (~df['is_legacy'])].copy().reset_index(drop=True)

# At least 15 words
df_15w = df_12[df_12['content'].astype(str).apply(lambda x: len(x.split())) >= 15].copy().reset_index(drop=True)
print(f"Reviews with >= 15 words: {len(df_15w)}")

tfidf = TfidfVectorizer(stop_words='english', min_df=2)
tfidf_mat = tfidf.fit_transform(df_15w['content'].astype(str))
sim = cosine_similarity(tfidf_mat)
np.fill_diagonal(sim, 0)

dup_pairs = []
seen = set()
for i in range(len(df_15w)):
    matches = np.where(sim[i] > 0.85)[0]
    for j in matches:
        if j > i and (i, j) not in seen:
            seen.add((i, j))
            dup_pairs.append({
                'id1': df_15w.loc[i, 'reviewId'],
                'text1': df_15w.loc[i, 'content'],
                'id2': df_15w.loc[j, 'reviewId'],
                'text2': df_15w.loc[j, 'content'],
                'similarity': float(sim[i, j])
            })

print(f"Total near-duplicate pairs (>= 15 words, sim > 0.85): {len(dup_pairs)}")
for idx, p in enumerate(dup_pairs[:5], 1):
    print(f"[{idx}] Similarity: {p['similarity']:.3f}")
    print(f"     A: {repr(p['text1'][:90])}")
    print(f"     B: {repr(p['text2'][:90])}")
