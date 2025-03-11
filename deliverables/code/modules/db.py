import os
import json
import time
import argparse
from typing import List, Dict, Any
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv


def main():

    # environment set up
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    client = OpenAI(api_key=openai_api_key)

    # make sure env is set up properly, reference instructions provided with submission
    if not openai_api_key or not pinecone_api_key:
        raise ValueError("OPENAI_API_KEY or PINECONE_API_KEY not found in env")

    # parse command line args
    parser = argparse.ArgumentParser(description="Upsert chunks to Pinecone")
    parser.add_argument("--chunks_file", default="vector_chunks.json", help="JSON file containing chunk data")
    parser.add_argument("--index_name", default="tower-demo-v0", help="Name of your Pinecone index")
    parser.add_argument("--namespace", default="ns1", help="Pinecone namespace")
    parser.add_argument("--batch_size", type=int, default=50, help="Batch size for upserts")
    args = parser.parse_args()


    # pinecone index set up
    serverless = ServerlessSpec(cloud="aws", region="us-east-1")
    pc = Pinecone(api_key=pinecone_api_key, default_spec=serverless)

    # create index if not there
    indexes = pc.list_indexes().names()
    if args.index_name not in indexes:
        print(f"Index '{args.index_name}' not found, creating a new one (dimension=1536, metric=cosine)...")
        pc.create_index(name=args.index_name, dimension=1536, metric="cosine", spec=serverless)
        print(f"Index '{args.index_name}' created.")
    else:
        print(f"Index '{args.index_name}' found.")

    index = pc.Index(args.index_name)
    print(f"Using Pinecone index: {args.index_name}")

    # loading chunk data from JSON
    with open(args.chunks_file, "r", encoding="utf-8") as f:
        chunks: List[Dict[str, Any]] = json.load(f)
    print(f"Loaded {len(chunks)} chunks from '{args.chunks_file}'")

    # batched chunk upsertion into vector embeddings
    vectors_to_upsert = []
    total_count = 0

    for chunk in chunks:
        text_data = chunk.get("text", "").strip()
        if not text_data:
            continue  # skip empty text


        chunk_id = str(chunk.get("chunk_id", total_count + 1))
        
        # metadata for quote citation
        metadata = {
            "file": chunk.get("file", "unknown"),
            "chunk_id": chunk.get("chunk_id", total_count + 1),
            "location_type": chunk.get("location_type", ""),
            "location_val": chunk.get("location_val", ""),
            "text": text_data  # storing the text for retrieval and direct quoting (no hallucinations this way)
        }

        # embed the chunk text
        embed_response = client.embeddings.create(model="text-embedding-ada-002", # can play around with diff embedding models
        input=text_data)
        vector = embed_response.data[0].embedding  # dimension 1536

        vectors_to_upsert.append((chunk_id, vector, metadata))
        total_count += 1

        if len(vectors_to_upsert) >= args.batch_size:
            index.upsert(vectors=vectors_to_upsert, namespace=args.namespace)
            print(f"Upserted {len(vectors_to_upsert)} vectors...")
            vectors_to_upsert.clear()
            time.sleep(0.5)  # small delay due to rate limiting

    # upsert any remaining vectors
    if vectors_to_upsert:
        index.upsert(vectors=vectors_to_upsert, namespace=args.namespace)
        print(f"Upserted final {len(vectors_to_upsert)} vectors.")

    print(f"Finished upsertion of {total_count} chunks to index '{args.index_name}' in namespace '{args.namespace}'.")

if __name__ == "__main__":
    main()
