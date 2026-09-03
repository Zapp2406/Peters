FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 5001

# Port 5001 statt 5000: auf macOS belegt Apples AirPlay-Receiver Port 5000
# und antwortet dort mit 403 Forbidden, was mit einem lokal laufenden
# Flask-Dienst kollidiert.
#
# Ein einzelner Worker genügt für dieses interne Tool und ist hier auch
# notwendig, da das zuletzt hochgeladene Mieterlisten-Ergebnis (für den
# Excel-Export) im Prozessspeicher gehalten wird (siehe app.py).
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "1", "--timeout", "120", "app:app"]
