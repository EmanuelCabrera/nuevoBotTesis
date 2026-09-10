# Usar imagen base de Python limpia
FROM python:3.10-slim

# (B) Telemetría off (opcional)
ENV RASA_TELEMETRY_ENABLED=false

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear requirements.txt temporal con versiones específicas compatibles
# (A) Fijamos spaCy y agregamos el modelo por URL (compatible con spaCy 3.4.x)
RUN echo "rasa==3.6.20" > requirements.txt && \
    echo "rasa-sdk==3.6.2" >> requirements.txt && \
    echo "websockets==10.4" >> requirements.txt && \
    echo "sanic==21.12.2" >> requirements.txt && \
    echo "spacy==3.4.4" >> requirements.txt && \
    echo "es-core-news-sm @ https://github.com/explosion/spacy-models/releases/download/es_core_news_sm-3.4.0/es_core_news_sm-3.4.0-py3-none-any.whl" >> requirements.txt && \
    echo "python-dotenv==1.0.0" >> requirements.txt && \
    echo "supabase==1.0.3" >> requirements.txt && \
    echo "httpx==0.23.3" >> requirements.txt

# Instalar todas las dependencias de una vez
RUN pip install --no-cache-dir -r requirements.txt

# (A) Ya no hace falta descargar el modelo con spacy:
# RUN python -m spacy download es_core_news_sm   <-- ELIMINADO

# Eliminar requirements.txt temporal
RUN rm requirements.txt

# Copiar archivos de configuración
COPY config.yml domain.yml credentials.yml endpoints.yml ./
COPY data/ ./data/
COPY actions/ ./actions/

# Copiar modelo existente
COPY models/ ./models/

# Cambiar a root para permisos de archivos
USER root
COPY start.sh .
RUN chmod +x start.sh
RUN chown 1001:1001 start.sh

# Volver al usuario no root (como tenías)
USER 1001

# Exponer puertos para Rasa y acciones
EXPOSE 5005 5055

# Comando por defecto - ejecutar script de inicio
CMD ["./start.sh"]