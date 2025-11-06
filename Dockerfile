FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

# Copy application code
COPY . .

RUN mkdir -p instance

ENV FLASK_APP=foodie
ENV PYTHONUNBUFFERED=1

RUN uv run flask --app foodie seed-db

EXPOSE 5001

CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "--threads", "2", "--timeout", "120", "wsgi:app"]

