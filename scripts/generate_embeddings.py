"""
INSYTE — Vector Embedding Generation Engine
Generates 384-dimensional dense text embeddings for product descriptions using
sentence-transformers (all-MiniLM-L6-v2) and stores them directly inside
Oracle Database 23ai's native VECTOR(384, FLOAT32) column.
"""

import os
import sys
import array
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "1521"))
DB_SERVICE = os.getenv("DB_SERVICE", "FREEPDB1")
DB_USER = os.getenv("APP_ADMIN_USER", "INSYTE_ADMIN")
DB_PASSWORD = os.getenv("APP_ADMIN_PASSWORD", "AdminSecurePassword2026!")
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

def generate_and_store_embeddings():
    print("=" * 70)
    print("INSYTE — Oracle 23ai AI Vector Search Embedding Engine")
    print("=" * 70)

    try:
        from sentence_transformers import SentenceTransformer
        import oracledb
    except ImportError:
        print("[ERROR] Missing required libraries. Please install:")
        print("  pip install sentence-transformers torch oracledb")
        return

    print(f"Loading embedding model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    print("Model loaded successfully (Output dimension: 384).")

    # Connect to Oracle 23ai
    try:
        conn = oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            service_name=DB_SERVICE
        )
        cursor = conn.cursor()
    except Exception as e:
        print(f"[ERROR connecting to database]: {e}")
        return

    # Fetch products needing embeddings
    cursor.execute("""
        SELECT stock_code, normalized_description 
        FROM PRODUCTS 
        WHERE normalized_description IS NOT NULL AND embedding IS NULL
    """)
    rows = cursor.fetchall()
    print(f"Found {len(rows):,} products awaiting vector embeddings.")

    if not rows:
        print("All products already have embeddings.")
        cursor.close()
        conn.close()
        return

    batch_size = 200
    for i in range(0, len(rows), batch_size):
        chunk = rows[i:i + batch_size]
        stock_codes = [r[0] for r in chunk]
        descriptions = [r[1] for r in chunk]

        # Generate 384-dimensional dense vectors
        embeddings = model.encode(descriptions, normalize_embeddings=True)

        # Prepare for Oracle 23ai native VECTOR insertion
        # python-oracledb accepts array.array('f', vector_values) for VECTOR(FLOAT32)
        update_data = []
        for stock, emb in zip(stock_codes, embeddings):
            vec_array = array.array('f', emb.tolist())
            update_data.append((vec_array, stock))

        cursor.executemany("""
            UPDATE PRODUCTS
            SET embedding = :1
            WHERE stock_code = :2
        """, update_data)
        conn.commit()
        print(f"  Processed {min(i + batch_size, len(rows)):,}/{len(rows):,} product vectors.")

    cursor.close()
    conn.close()
    print("\n" + "=" * 70)
    print("[VECTOR GENERATION COMPLETE] All product embeddings stored in Oracle 23ai!")
    print("=" * 70)

if __name__ == "__main__":
    generate_and_store_embeddings()
