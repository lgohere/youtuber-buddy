#!/bin/bash

# Script para executar o container do YouTube Buddy

set -e

echo "🚀 Executando YouTube Buddy em container..."

# Definir nome da imagem
IMAGE_NAME="youtube-buddy:latest"
CONTAINER_NAME="youtube-buddy-app"

# Verificar se o arquivo .env existe
if [ ! -f ".env" ]; then
    echo "⚠️ Arquivo .env não encontrado!"
    echo "📋 Copie o arquivo env.example para .env e configure suas chaves de API:"
    echo "   cp env.example .env"
    echo "   # Edite o arquivo .env com suas chaves"
    exit 1
fi

# Parar container existente se estiver rodando
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "🛑 Parando container existente..."
    docker stop $CONTAINER_NAME
fi

# Remover container existente se existir
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "🗑️ Removendo container existente..."
    docker rm $CONTAINER_NAME
fi

# Criar diretórios de dados se não existirem
mkdir -p data/database data/temp

echo "🐳 Iniciando container..."

# Executar o container
docker run -d \
    --name $CONTAINER_NAME \
    -p 8501:8501 \
    --env-file .env \
    -v "$(pwd)/data/database:/app/database" \
    -v "$(pwd)/data/temp:/app/temp" \
    --restart unless-stopped \
    $IMAGE_NAME

if [ $? -eq 0 ]; then
    echo "✅ Container iniciado com sucesso!"
    echo "🌐 Aplicação disponível em: http://localhost:8501"
    echo ""
    echo "📋 Comandos úteis:"
    echo "   Ver logs: docker logs -f $CONTAINER_NAME"
    echo "   Parar: docker stop $CONTAINER_NAME"
    echo "   Status: docker ps | grep $CONTAINER_NAME"
    echo ""
    echo "🗄️ Banco de dados persistido em: ./data/database/"
    echo "🧹 Arquivos temporários em: ./data/temp/ (limpos automaticamente)"
else
    echo "❌ Erro ao iniciar container!"
    exit 1
fi 