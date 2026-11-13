"""Download the public model and verify sample inference during installation."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ['HF_HOME'] = str(ROOT / 'data' / 'models')
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', device='cpu')
vectors = model.encode(['실내 식물 물 주기', '실내 식물에 물을 주는 방법'])
assert vectors.shape == (2, 384), vectors.shape
print('AI model ready: sample inference passed', flush=True)
