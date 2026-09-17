FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY content_model/ content_model/
COPY pptx_builder/ pptx_builder/
COPY scraper/ scraper/
COPY static_data/ static_data/
COPY TEMPLATE.pptx .

# Uso: docker run -v $(pwd)/data:/data slides-automation /data/mass_2026-08-30.json -o /data/missa_2026-08-30.pptx
ENTRYPOINT ["python", "-m", "pptx_builder"]
