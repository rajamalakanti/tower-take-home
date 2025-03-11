import os
import json
import argparse
from typing import List
from bs4 import BeautifulSoup


# for pdf chunking
def parse_pdf(pdf_path: str) -> List[dict]:
    import pdfplumber
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append({"page": i, "text": text})
    return pages

# for epub chunking
def parse_epub(epub_path: str) -> List[dict]:
    import ebooklib
    from ebooklib import epub

    chapters = []
    book = epub.read_epub(epub_path)
    chapter_count = 0
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapter_count += 1
            content = item.get_content()
            soup = BeautifulSoup(content, features="html.parser")
            text = soup.get_text()
            chapters.append({"chapter": chapter_count, "text": text})
    return chapters

# for xml chunking
def parse_xml(xml_path: str) -> List[dict]:
    import xml.etree.ElementTree as ET
    tree = ET.parse(xml_path)
    root = tree.getroot()
    full_text = "".join(root.itertext())
    return [{"chapter": 1, "text": full_text}]

# aggregate chunking w/ overlap (best practice)
def chunk_blocks(blocks: List[dict], file_name: str, chunk_size: int = 500, overlap: int = 50) -> List[dict]:
    all_chunks = []
    chunk_id = 1

    for block in blocks:
        # find loc and val
        if "page" in block:
            loc_type = "page"
            loc_val = block["page"]
        elif "chapter" in block:
            loc_type = "chapter"
            loc_val = block["chapter"]
        else:
            loc_type = "unknown"
            loc_val = 1

        words = block["text"].split()
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk_text = " ".join(words[start:end])
            chunk_entry = {
                "file": file_name,
                "chunk_id": chunk_id,
                "location_type": loc_type,
                "location_val": loc_val,
                "text": chunk_text
            }
            all_chunks.append(chunk_entry)
            chunk_id += 1
            start += (chunk_size - overlap)

    return all_chunks

def main():
    parser = argparse.ArgumentParser(description="Ingest and chunk books based on file paths in found_files.json")
    parser.add_argument("--found_files", default="found_files.json", help="JSON file containing an array of file paths")
    parser.add_argument("--output", default="vector_chunks.json", help="Output JSON file for chunk data")
    parser.add_argument("--chunk_size", type=int, default=500, help="Approximate number of words per chunk")
    parser.add_argument("--overlap", type=int, default=50, help="Number of overlapping words between chunks")
    args = parser.parse_args()

    # load found_files.json (from utility function finder.py)
    with open(args.found_files, "r", encoding="utf-8") as f:
        file_paths = json.load(f)

    all_chunks = []
    for path in file_paths:
        print(f"Processing file: {path}")
        file_ext = os.path.splitext(path)[1].lower()
        if file_ext == ".pdf":
            blocks = parse_pdf(path)
        elif file_ext == ".epub":
            blocks = parse_epub(path)
        elif file_ext == ".xml":
            blocks = parse_xml(path)
        else:
            print(f"Unrecognized file extension '{file_ext}' for {path}. Skipping.")
            continue

        file_name = os.path.basename(path)
        chunks = chunk_blocks(blocks, file_name=file_name, chunk_size=args.chunk_size, overlap=args.overlap)
        all_chunks.extend(chunks)
        print(f"Extracted {len(chunks)} chunks from {file_name}")

    # save chunks to output JSON file
    with open(args.output, "w", encoding="utf-8") as out_f:
        json.dump(all_chunks, out_f, indent=2)
    print(f"Saved {len(all_chunks)} total chunks to {args.output}")

if __name__ == "__main__":
    main()