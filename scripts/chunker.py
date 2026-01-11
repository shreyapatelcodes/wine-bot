"""
WSET Wine Knowledge Extraction and Chunking Script
Place your WSET Word document in the 'data' folder and run this script
"""

from docx import Document
import json
import os
from pathlib import Path

def extract_text_from_docx(file_path):
    """Extract text from Word document, preserving structure"""
    print(f"📖 Reading document: {file_path}")
    doc = Document(file_path)
    
    chunks = []
    current_chunk = {
        'text': '',
        'heading': 'Introduction',
        'metadata': {}
    }
    
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        
        if not text:  # Skip empty paragraphs
            continue
            
        # Check if this is a heading
        if paragraph.style.name.startswith('Heading'):
            # Save previous chunk if it has content
            if current_chunk['text']:
                chunks.append(current_chunk.copy())
            
            # Start new chunk with this heading
            current_chunk = {
                'text': '',
                'heading': text,
                'metadata': {
                    'heading_level': paragraph.style.name,
                    'type': 'section'
                }
            }
        else:
            # Add paragraph to current chunk
            current_chunk['text'] += text + '\n\n'
    
    # Don't forget the last chunk
    if current_chunk['text']:
        chunks.append(current_chunk)
    
    print(f"✓ Extracted {len(chunks)} initial sections")
    return chunks

def chunk_by_size(text, chunk_size=1000, overlap=200):
    """Split text into chunks with overlap for context continuity"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at a sentence boundary
        if end < len(text):
            last_period = text.rfind('.', end - 200, end)
            last_newline = text.rfind('\n', end - 200, end)
            
            break_point = max(last_period, last_newline)
            if break_point > start:
                end = break_point + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks

def smart_chunk_document(file_path, chunk_size=1000, overlap=200):
    """Main chunking function combining heading-based and size-based chunking"""
    
    # Extract by headings first
    heading_chunks = extract_text_from_docx(file_path)
    
    # Split large chunks further
    final_chunks = []
    
    print(f"📏 Splitting large sections (target size: {chunk_size} chars)...")
    
    for chunk_data in heading_chunks:
        heading = chunk_data['heading']
        text = chunk_data['text']
        
        # If chunk is reasonable size, keep as is
        if len(text) <= chunk_size * 1.5:
            final_chunks.append({
                'chunk_id': len(final_chunks),
                'text': text,
                'heading': heading,
                'metadata': chunk_data['metadata']
            })
        else:
            # Split large sections
            sub_chunks = chunk_by_size(text, chunk_size, overlap)
            for j, sub_chunk in enumerate(sub_chunks):
                final_chunks.append({
                    'chunk_id': len(final_chunks),
                    'text': sub_chunk,
                    'heading': heading,
                    'metadata': {
                        **chunk_data['metadata'],
                        'sub_chunk': j + 1,
                        'total_sub_chunks': len(sub_chunks)
                    }
                })
    
    print(f"✓ Created {len(final_chunks)} final chunks")
    return final_chunks

def save_chunks(chunks, output_file):
    """Save chunks to JSON file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved to: {output_file}")
    
    # Statistics
    total_chars = sum(len(chunk['text']) for chunk in chunks)
    avg_size = total_chars / len(chunks) if chunks else 0
    
    print(f"\n📊 Statistics:")
    print(f"   Total chunks: {len(chunks)}")
    print(f"   Total characters: {total_chars:,}")
    print(f"   Average chunk size: {avg_size:.0f} characters")
    print(f"   Estimated tokens: ~{total_chars // 4:,}")
    
    # Show some headings
    print(f"\n📑 Sample sections:")
    unique_headings = list(dict.fromkeys([c['heading'] for c in chunks]))
    for i, heading in enumerate(unique_headings[:5], 1):
        count = sum(1 for c in chunks if c['heading'] == heading)
        print(f"   {i}. {heading} ({count} chunks)")
    
    if len(unique_headings) > 5:
        print(f"   ... and {len(unique_headings) - 5} more sections")

def find_docx_files(data_dir):
    """Find all .docx files in the data directory"""
    docx_files = list(Path(data_dir).glob('*.docx'))
    # Filter out temp files (start with ~$)
    docx_files = [f for f in docx_files if not f.name.startswith('~$')]
    return docx_files

if __name__ == "__main__":
    print("🍷 WSET Wine Knowledge Chunking Tool\n")
    
    # Setup directories
    data_dir = Path('data')
    output_dir = Path('chunks')
    
    # Create directories if they don't exist
    data_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # Find Word documents
    docx_files = find_docx_files(data_dir)
    
    if not docx_files:
        print("❌ No Word documents found in 'data' folder!")
        print("\nPlease:")
        print("1. Place your WSET Word document in the 'data' folder")
        print("2. Run this script again")
        exit(1)
    
    # If multiple files, let user choose
    if len(docx_files) == 1:
        input_file = docx_files[0]
    else:
        print("Found multiple Word documents:")
        for i, f in enumerate(docx_files, 1):
            print(f"  {i}. {f.name}")
        choice = int(input("\nWhich file to process? (enter number): ")) - 1
        input_file = docx_files[choice]
    
    print(f"\nProcessing: {input_file.name}\n")
    
    # Chunk the document
    chunks = smart_chunk_document(
        input_file, 
        chunk_size=1000,  # Adjust if needed
        overlap=200
    )
    
    # Save output
    output_file = output_dir / 'wine_chunks.json'
    save_chunks(chunks, output_file)
    
    # Preview
    print("\n" + "="*60)
    print("PREVIEW - First chunk:")
    print("="*60)
    print(f"Heading: {chunks[0]['heading']}")
    print(f"\n{chunks[0]['text'][:400]}...")
    print("\n" + "="*60)
    print(f"\n✓ Next step: Create embeddings from these {len(chunks)} chunks")