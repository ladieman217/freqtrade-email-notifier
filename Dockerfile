FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create a non-root user for security
RUN useradd -m appuser
USER appuser

# Expose the port
EXPOSE 5001

# Use environment variables from docker run/compose
ENV AWS_ACCESS_KEY_ID=
ENV AWS_SECRET_ACCESS_KEY=
ENV AWS_REGION=us-east-1
ENV EMAIL_SENDER=
ENV EMAIL_RECIPIENT=
ENV API_KEY=
ENV PORT=5001

# Run the application
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT}
