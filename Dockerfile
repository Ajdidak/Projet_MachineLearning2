FROM python:3.11-slim

WORKDIR /app

# Empêche Python de mettre en mémoire tampon sa sortie (print) dans le
# conteneur — sans ça, certains messages n'apparaissent jamais dans
# `docker logs` avant l'arrêt du programme.
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir --upgrade pip "setuptools<81" wheel

# torch/torchvision en version CPU uniquement : évite de télécharger ~2 Go
# de bibliothèques CUDA/NVIDIA totalement inutiles (Docker Desktop n'a pas
# accès au GPU ici), ce qui causait des timeouts réseau au build.
RUN pip install --no-cache-dir torch==2.3.1 torchvision==0.18.1 \
    --index-url https://download.pytorch.org/whl/cpu

COPY Requirements.txt .
RUN pip install --no-cache-dir -r Requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "Frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
