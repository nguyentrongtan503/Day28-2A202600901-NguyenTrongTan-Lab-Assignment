import json
import time
import os
import glob
import pandas as pd
import requests
import redis
from datetime import datetime
from kafka import KafkaConsumer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Redis
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Qdrant
qdrant = QdrantClient(host="localhost", port=6333)

# Embed URL (mock Kaggle service)
EMBED_URL = os.environ.get("EMBED_NGROK_URL", "http://localhost:8001")

def process_record(record):
    print(f"Processing record: {record}")
    record_id = record.get("id")
    text = record.get("text", "")
    timestamp = record.get("timestamp", time.time())
    
    # 1. Write to Delta Lake (mock parquet)
    df = pd.DataFrame([record])
    path = "delta-lake/raw"
    os.makedirs(path, exist_ok=True)
    df.to_parquet(f"{path}/batch_{record_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet")
    print(f"  Saved to Delta Lake")
    
    # 2. Push to Feast (Redis)
    feature_key = f"feature:{record_id}"
    r.set(feature_key, json.dumps({
        "text": text,
        "timestamp": timestamp,
        "processed": True
    }))
    print(f"  Pushed to Feast (Redis)")
    
    # 3. Embed and store to Qdrant
    try:
        response = requests.post(f"{EMBED_URL}/embed", json={"texts": [text]}, timeout=10)
        embeddings = response.json()["embeddings"]
        emb = embeddings[0]
        
        # Ensure collection exists
        try:
            qdrant.get_collection(collection_name="documents")
        except Exception:
            qdrant.recreate_collection(
                collection_name="documents",
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            
        # Determine a numeric ID for Qdrant (must be int or UUID)
        import hashlib
        h = hashlib.md5(record_id.encode()).hexdigest()
        qdrant_id = int(h[:16], 16)
        
        qdrant.upsert(
            collection_name="documents",
            points=[PointStruct(id=qdrant_id, vector=emb, payload=record)]
        )
        print(f"  Stored vector in Qdrant with ID {qdrant_id}")
    except Exception as e:
        print(f"  Error embedding/storing to Qdrant: {e}")

def main():
    print("Pipeline worker starting...")
    
    # Ensure Qdrant collection exists
    try:
        qdrant.get_collection(collection_name="documents")
    except Exception:
        qdrant.recreate_collection(
            collection_name="documents",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print("Created Qdrant collection 'documents'")

    # Consume from Kafka
    while True:
        try:
            consumer = KafkaConsumer(
                "data.raw",
                bootstrap_servers="localhost:9092",
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode()),
                consumer_timeout_ms=1000
            )
            print("Connected to Kafka. Listening for messages...")
            for msg in consumer:
                try:
                    process_record(msg.value)
                except Exception as e:
                    print(f"Error processing message: {e}")
            consumer.close()
            time.sleep(1)
        except Exception as e:
            print(f"Kafka connection error: {e}. Retrying in 2 seconds...")
            time.sleep(2)

if __name__ == "__main__":
    main()
