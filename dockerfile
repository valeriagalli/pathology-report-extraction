FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install -e .

# Declares the port the container listens on (documentation only, doesn't
# actually publish the port, that happens via --port in the CMD and via
# docker run's -p flag or Cloud Run's own port configuration).
EXPOSE 8080 

CMD ["uvicorn", "pathology_extraction.api:app", "--host", "0.0.0.0", "--port", "8080"]