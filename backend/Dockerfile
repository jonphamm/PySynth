FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install deps first for layer caching
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# App code + static assets the prompts/progress modules read at runtime
COPY backend /app/backend
COPY shared /app/shared
COPY Workflows /app/Workflows
COPY Resources /app/Resources

RUN chmod +x /app/backend/start.sh
EXPOSE 8000
CMD ["/app/backend/start.sh"]
