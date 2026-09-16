import pandas as pd
from rank_bm25 import BM25Okapi
import pickle
import json
from pathlib import Path

def build_bm25():
    print('Loading data...')
    df = pd.read_csv(Path(__file__).resolve().parent.parent / 'data/esco_data/skills.csv')
    
    metadata = []
    tokenized_corpus = []
    
    for _, row in df.iterrows():
        meta = {
            'skill_uri': row['conceptUri'],
            'skill_label': row['preferredLabel'],
            'skill_description': str(row['description']) if pd.notna(row['description']) else '',
            'skill_type': row['skillType']
        }
        metadata.append(meta)
        
        # Tokenize label + description for BM25
        text = f"{meta['skill_label']} {meta['skill_description']}"
        tokens = text.lower().split()
        tokenized_corpus.append(tokens)
        
    print(f'Building BM25 for {len(tokenized_corpus)} docs...')
    bm25 = BM25Okapi(tokenized_corpus)
    
    out_dir = Path(__file__).resolve().parent.parent / 'src/esco-skill-mapping/data/esco_filtered/v1/bm25'
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_dir / 'bm25_corpus.pkl', 'wb') as f:
        pickle.dump(bm25, f)
        
    # Create metadata file for bm25 as well (pipeline might expect it in bm25 folder? Wait, pipeline uses faiss_metadata.json for bm25 too? Let's check config.)
    with open(out_dir / 'bm25_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
        
    print('Done!')

if __name__ == '__main__':
    build_bm25()
