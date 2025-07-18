import json
import os
import argparse
from sentence_transformers import SentenceTransformer, util
import torch

# --- Model Loading ---
# We specify the new, more powerful model here.
# The Dockerfile will ensure this is pre-downloaded.
MODEL_NAME = 'all-mpnet-base-v2'
INPUT_DIR = "input"
OUTPUT_DIR = "output"
INPUT_FILENAME = "structured_output.json" # The output file from service1a
OUTPUT_FILENAME = "ranked_intelligence_output.json"

def load_model():
    """Loads the Sentence Transformer model."""
    print(f"Loading the '{MODEL_NAME}' model...")
    # Using .to('cpu') ensures the model runs on the CPU, as required.
    model = SentenceTransformer(MODEL_NAME, device='cpu')
    print("Model loaded successfully.")
    return model

def rank_document_content(document_data, query, model):
    """
    Ranks the content of a document against a user query using sentence embeddings.

    Args:
        document_data (dict): The structured data for a single document from service1a.
        query (str): The user's query or persona description.
        model: The loaded SentenceTransformer model.

    Returns:
        dict: The document data, with each element enriched with a 'relevance_score'.
    """
    # 1. Encode the user query into a vector embedding
    query_embedding = model.encode(query, convert_to_tensor=True, show_progress_bar=False)

    # 2. Collect all text-based elements from the document for analysis
    text_elements_to_score = []
    
    for page in document_data.get("pages", []):
        for element in page.get("elements", []):
            content = None
            if element.get("type") in ["paragraph", "list_item", "title", "header"]:
                content = element.get("content", "")
            elif element.get("type") == "table":
                # For tables, create a single descriptive string.
                table_data = element.get("content", [])
                if table_data:
                    content = "\n".join([" | ".join(map(str, row)) for row in table_data])
            
            if content and isinstance(content, str) and content.strip():
                text_elements_to_score.append({"element": element, "text": content})

    if not text_elements_to_score:
        return document_data

    # 3. Encode all collected text contents into vector embeddings
    corpus_texts = [item['text'] for item in text_elements_to_score]
    corpus_embeddings = model.encode(corpus_texts, convert_to_tensor=True, show_progress_bar=False)

    # 4. Compute cosine similarity between the query and all text elements
    cosine_scores = util.cos_sim(query_embedding, corpus_embeddings)

    # 5. Add the relevance score back to each element in the original structure
    for i, item in enumerate(text_elements_to_score):
        element = item['element']
        element['relevance_score'] = cosine_scores[0][i].item()

    # Sort elements on each page by their relevance score for easy analysis
    for page in document_data.get("pages", []):
        if 'elements' in page:
            page['elements'].sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

    return document_data

def main():
    """
    Main function to run the intelligence service. It parses command-line arguments
    to get the user's query and then processes the documents.
    """
    # --- Step 1: Set up Argument Parser for User Input ---
    parser = argparse.ArgumentParser(description="Analyze document content based on a user-defined persona or query.")
    parser.add_argument("query", type=str, help="The persona or query to rank the document content against.")
    args = parser.parse_args()
    user_query = args.query

    # --- Step 2: Load Model and Data ---
    model = load_model()

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    input_filepath = os.path.join(INPUT_DIR, INPUT_FILENAME)
    try:
        with open(input_filepath, 'r') as f:
            all_documents_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_filepath}'")
        print("Please ensure the output from service1a ('structured_output.json') is in the 'input' directory.")
        return

    print(f"\nLoaded {len(all_documents_data)} documents.")
    print(f"Ranking content based on the user query: '{user_query}'")

    # --- Step 3: Process and Rank Each Document ---
    ranked_results = []
    for i, document_data in enumerate(all_documents_data):
        print(f"Processing document {i+1}/{len(all_documents_data)}: {document_data.get('pdf_path', 'Unknown PDF')}")
        ranked_doc = rank_document_content(document_data, user_query, model)
        ranked_results.append(ranked_doc)

    # --- Step 4: Save Final Output ---
    output_filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    with open(output_filepath, 'w') as f:
        json.dump(ranked_results, f, indent=4)

    print(f"\n✅ Processing complete. Ranked output saved to: {output_filepath}")

if __name__ == "__main__":
    main()