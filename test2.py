from pathlib import Path
from src.connectors.databricks_uploader import get_uploader

p = sorted(Path('data/processed').glob('*.parquet'))[-1]
print(get_uploader().upload_and_register(p))