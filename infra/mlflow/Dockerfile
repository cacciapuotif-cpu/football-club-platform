FROM ghcr.io/mlflow/mlflow:v2.10.2

# Install PostgreSQL driver
RUN pip install --no-cache-dir psycopg2-binary

# Keep the same entrypoint as base image
ENTRYPOINT ["mlflow"]
CMD ["server", "--host", "0.0.0.0", "--port", "5000"]
