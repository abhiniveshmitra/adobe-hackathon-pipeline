FROM --platform=linux/amd64 python:3.10

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install our Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy our actual processing script and rename it to match the spec
COPY main.py process_pdfs.py

# Set the command to run the script when the container starts
CMD ["python", "process_pdfs.py"]