FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv - gerenciador de pacotes Python ultrarrápido
RUN pip3 install uv
ENV PATH="/root/.cargo/bin:$PATH"

# Diretório de trabalho
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python com uv (muito mais rápido que pip!)
RUN uv pip install --system --no-cache -r requirements.txt

# Copiar o código da aplicação
COPY . .

# Criar diretório para dados do Qdrant
RUN mkdir -p /app/qdrant_data

# Expor porta do Streamlit
EXPOSE 8501

# Comando para iniciar o Streamlit
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]

