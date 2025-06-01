#!/bin/bash

# Script para build da imagem Docker do YouTube Buddy

set -e

echo "🐳 Construindo imagem Docker do YouTube Buddy..."

# Definir nome da imagem
IMAGE_NAME="youtube-buddy"
TAG=${1:-latest}
FULL_IMAGE_NAME="$IMAGE_NAME:$TAG"

echo "📦 Nome da imagem: $FULL_IMAGE_NAME"

# Verificar se o Dockerfile existe
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile não encontrado!"
    exit 1
fi

# Construir a imagem
echo "🔨 Iniciando build..."
docker build -t "$FULL_IMAGE_NAME" .

if [ $? -eq 0 ]; then
    echo "✅ Build concluído com sucesso!"
    echo "📋 Imagem criada: $FULL_IMAGE_NAME"
    echo ""
    echo "🚀 Para executar o container:"
    echo "   docker run -p 8501:8501 --env-file .env $FULL_IMAGE_NAME"
    echo ""
    echo "🐙 Para fazer push para Docker Hub:"
    echo "   docker tag $FULL_IMAGE_NAME seu-usuario/$IMAGE_NAME:$TAG"
    echo "   docker push seu-usuario/$IMAGE_NAME:$TAG"
else
    echo "❌ Erro durante o build!"
    exit 1
fi 