# Официальный Playwright-образ: chromium + все системные либы уже внутри (vision-аудит)
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# браузеры уже в образе; на всякий случай гарантируем chromium
RUN python -m playwright install chromium

COPY . .
ENV PORT=8000
EXPOSE 8000
CMD ["sh","-c","uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
