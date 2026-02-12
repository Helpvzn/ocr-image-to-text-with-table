FROM python:3.10-slim-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    libgl1-mesa-glx \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY . .

# Install heavy dependencies first to avoid OOM
# Install heavy dependencies first to avoid OOM
RUN pip install --no-cache-dir paddlepaddle==2.6.1

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7860

HEALTHCHECK CMD curl --fail http://localhost:7860/_stcore/health

ENTRYPOINT ["streamlit", "run", "vizan_studio_v2/app.py", "--server.port=7860", "--server.address=0.0.0.0"]
