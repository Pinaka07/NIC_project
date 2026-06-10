FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV SECRET_KEY=your-real-secret-key-here
ENV DEBUG=True
ENV ALLOWED_HOSTS=localhost,127.0.0.1
ENV DB_NAME=user_management_db
ENV DB_USER=postgres
ENV DB_PASSWORD=Prateek@13
ENV DB_HOST=localhost
ENV DB_PORT=1042

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]