# Dockerfile for Streamlit app + optional FastAPI
FROM python:3.11-slim

WORKDIR /app

# System deps for psycopg2 and build tools
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default to Streamlit app
ENV STREAMLIT_SERVER_PORT=8501
EXPOSE 8501 8000

# Choose service by CMD override: streamlit or api
CMD ["sh", "-c", "streamlit run app.py --server.port=$STREAMLIT_SERVER_PORT --server.address=0.0.0.0"]
