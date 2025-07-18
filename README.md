📄 Document Intelligence Pipeline
This project is a two-stage pipeline built for the Adobe India Hackathon. It automates the process of extracting structured information from a batch of PDF documents and then uses a powerful AI model to find and rank content based on a user's specific query.

Service 1a (Extraction): Scans PDF files and intelligently extracts structural elements like titles, paragraphs, lists, and tables.

Service 1b (Intelligence): Takes the structured data and a user-defined query (or "persona"), and ranks every piece of content by its relevance using a state-of-the-art sentence-transformer model.

🚀 Prerequisites
Before you begin, ensure you have Docker Desktop installed and running on your system.

📂 Project Setup
1. Place Your PDFs
Add all the PDF files you want to process into the following directory:

document_intelligence/input_pdfs/
2. Make the Script Executable
This is a one-time setup step. Open a terminal in the project's root directory and run the following command to grant execute permissions to the main script:

Bash

chmod +x run_pipeline.sh
⚡ How to Run the Pipeline
The entire process is managed by the run_pipeline.sh script.

Navigate to the project's root directory in your terminal.

Run the script. You have two options:

To run with the default query ("What are the key event dates, submission deadlines, and topics?"):

Bash

./run_pipeline.sh
To run with a custom query, simply pass it as an argument in quotes:

Bash

./run_pipeline.sh "Your custom query about the documents goes here"
Example:

Bash

./run_pipeline.sh "Find all information about prizes and awards"
The script will first build the necessary Docker images (this may take a few minutes on the first run as it downloads the AI model), and then execute the two services in sequence.

📊 Output
The final, ranked output is saved as a JSON file at the following location:

document_intelligence/service1b/output/ranked_intelligence_output.json
This file contains the full structured content from all processed PDFs, with each text element enriched with a relevance_score based on your query.
