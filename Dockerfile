# Use Python 3.9 as the base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy your local marker repository with modifications
COPY . .

# Install the marker project using Poetry (from the local directory)
RUN poetry config virtualenvs.create false
RUN poetry lock
RUN poetry install

# Install the additional dependencies needed for the API server
RUN pip install -U uvicorn fastapi python-multipart streamlit

# Expose port 8001
EXPOSE 8501

# Run the marker server
CMD ["marker_gui", "--port", "8501", "--host", "0.0.0.0"]