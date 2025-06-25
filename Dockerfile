FROM python:3.11-slim

# Crea directory lavoro
WORKDIR /app

# Copia i file
COPY . .

# Installa le dipendenze
RUN pip install --no-cache-dir \
    langchain \
    langchain-google-genai \
    google-cloud-bigquery \
    google-auth \
    fastapi \
    uvicorn

# Espone la porta
EXPOSE 8080

# Avvia il server MCP
CMD ["python", "-m", "toolbox.server"]
