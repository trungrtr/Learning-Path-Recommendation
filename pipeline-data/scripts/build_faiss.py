import pandas as pd
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss

def build_faiss():
    print('Loading data...')
    df = pd.read_csv(Path(__file__).resolve().parent.parent / 'data/esco_data/skills.csv', keep_default_na=False)
    
    metadata = []
    texts = []
    
    for _, row in df.iterrows():
        meta = {
            'skill_uri': row['conceptUri'],
            'skill_label': row['preferredLabel'],
            'skill_description': str(row['description']) if row['description'] else '',
            'skill_type': row['skillType']
        }
        metadata.append(meta)
        
        # Combine label and description for semantic embedding
        desc = meta['skill_description']
        text = f"{meta['skill_label']}. {desc}".strip()
        texts.append(text)
        
    print('Loading embedding model...')
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
    
    print(f'Embedding {len(texts)} texts...')
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    
    print('Building FAISS index...')
    faiss.normalize_L2(embeddings)
    
    d = embeddings.shape[1]
    index = faiss.IndexFlatIP(d)
    index.add(embeddings)
    
    out_dir = Path(__file__).resolve().parent.parent / 'src/esco-skill-mapping/data/esco_filtered/v1/faiss'
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print('Saving index and metadata...')
    faiss.write_index(index, str(out_dir / 'esco_full.index'))
    
    with open(out_dir / 'esco_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
        
    print('Done!')

if __name__ == '__main__':
    build_faiss()
