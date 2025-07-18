# Stage 1: Use a slim Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Set an environment variable for the model cache location
ENV SENTENCE_TRANSFORMERS_HOME=/app/models

# Copy the requirements file
COPY requirements.txt .

# Install dependencies from the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container
COPY . .

# --- CRITICAL STEP: Download and cache the larger model during the build ---
# This command runs a short Python script to download the 'all-mpnet-base-v2' model.
# This ensures the model is included in the final image for offline execution.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-mpnet-base-v2')"

# Specify the command to run when the container starts.
# We no longer hardcode the query here; it will be passed in when 'docker run' is called.
CMD ["python", "main.py"]