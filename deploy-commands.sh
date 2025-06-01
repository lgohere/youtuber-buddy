#!/bin/bash

# Deploy do YouTube Buddy no servidor
echo "🚀 Iniciando deploy do YouTube Buddy..."

# Parar containers existentes
docker-compose down 2>/dev/null || true

# Pull da imagem mais recente
docker pull lgohere/youtube-buddy:latest

# Criar diretórios necessários
mkdir -p ./data/database
mkdir -p ./data/temp

# Iniciar com docker-compose
docker-compose -f docker-compose.coolify.yml up -d

echo "✅ Deploy concluído!"
echo "🌐 Aplicação disponível em: https://your.texts.com.br"
echo "📊 Logs: docker-compose logs -f" 