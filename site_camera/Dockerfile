# 1. Usa uma imagem oficial do Python estável e leve
FROM python:3.12-slim

# 2. Define variáveis de ambiente para o Python não gerar arquivos .pyc e não reter buffers de saída
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# 4. Instala as dependências do sistema operacional necessárias para OpenCV e DeepFace
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 5. Copia o arquivo de requerimentos para dentro do contêiner
COPY requirements.txt /app/

# 6. Atualiza o pip e instala as bibliotecas do projeto (Django, paho-mqtt, deepface, opencv, etc)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 7. Copia o restante do código do projeto para o contêiner
COPY . /app/