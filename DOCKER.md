# 🐳 YouTube Buddy - Deployment com Docker

Guia completo para executar o YouTube Buddy em containers Docker, ideal para VPS e plataformas como Coolify.

## 📋 Pré-requisitos

- Docker instalado
- Docker Compose (opcional, mas recomendado)
- 4GB de RAM disponível
- Chaves de API configuradas

## 🚀 Deployment Rápido

### 1. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp env.example .env

# Editar com suas chaves de API
nano .env
```

**Conteúdo do `.env`:**
```env
GROQ_API_KEY=sua-chave-groq-aqui
GOOGLE_API_KEY=sua-chave-google-ai-aqui
```

### 2. Executar com Docker Compose (Recomendado)

```bash
# Build e execução em um comando
docker-compose up -d --build

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f
```

### 3. Executar com Scripts Automatizados

```bash
# Build da imagem
./scripts/build.sh

# Executar container
./scripts/run.sh
```

### 4. Executar Manualmente

```bash
# Build da imagem
docker build -t youtube-buddy:latest .

# Executar container
docker run -d \
  --name youtube-buddy-app \
  -p 8501:8501 \
  --env-file .env \
  -v $(pwd)/data/database:/app/database \
  -v $(pwd)/data/temp:/app/temp \
  --restart unless-stopped \
  youtube-buddy:latest
```

## 🌐 Acesso à Aplicação

Após iniciar o container, acesse:
- **Local**: http://localhost:8501
- **VPS**: http://seu-ip:8501
- **Coolify**: Configurado automaticamente

## 📁 Estrutura de Dados

```
data/
├── database/           # Banco SQLite (persistente)
│   └── youtube_buddy.db
└── temp/              # Arquivos temporários (limpos automaticamente)
```

## 🔧 Configuração para Coolify

### 1. Dockerfile Otimizado

O Dockerfile já está otimizado para Coolify com:
- ✅ Healthcheck configurado
- ✅ Variáveis de ambiente
- ✅ Volumes para persistência
- ✅ Restart automático

### 2. Variáveis de Ambiente no Coolify

Configure no painel do Coolify:
```
GROQ_API_KEY=sua-chave-groq
GOOGLE_API_KEY=sua-chave-google-ai
```

### 3. Volumes Persistentes

Configure volumes no Coolify:
- `/app/database` → Para persistir banco de dados
- `/app/temp` → Para arquivos temporários (opcional)

## 🛠️ Comandos Úteis

### Gerenciamento do Container

```bash
# Ver logs em tempo real
docker logs -f youtube-buddy-app

# Parar container
docker stop youtube-buddy-app

# Reiniciar container
docker restart youtube-buddy-app

# Remover container
docker rm youtube-buddy-app

# Ver status
docker ps | grep youtube-buddy
```

### Limpeza e Manutenção

```bash
# Executar limpeza manual
docker exec youtube-buddy-app python scripts/cleanup.py

# Ver estatísticas do banco
docker exec youtube-buddy-app python scripts/cleanup.py --stats-only

# Limpeza mais agressiva (3 dias)
docker exec youtube-buddy-app python scripts/cleanup.py --days 3
```

### Backup do Banco de Dados

```bash
# Backup
docker cp youtube-buddy-app:/app/database/youtube_buddy.db ./backup_$(date +%Y%m%d).db

# Restaurar
docker cp ./backup_20241201.db youtube-buddy-app:/app/database/youtube_buddy.db
docker restart youtube-buddy-app
```

## 🔍 Troubleshooting

### Container não inicia

```bash
# Verificar logs
docker logs youtube-buddy-app

# Verificar variáveis de ambiente
docker exec youtube-buddy-app env | grep -E "(GROQ|GOOGLE)"

# Testar conectividade
docker exec youtube-buddy-app curl -f http://localhost:8501/_stcore/health
```

### Problemas de Performance

```bash
# Verificar uso de recursos
docker stats youtube-buddy-app

# Limpar dados antigos
docker exec youtube-buddy-app python scripts/cleanup.py --days 3

# Reiniciar container
docker restart youtube-buddy-app
```

### Problemas de Rede

```bash
# Verificar portas
docker port youtube-buddy-app

# Testar conectividade interna
docker exec youtube-buddy-app curl localhost:8501

# Verificar firewall (VPS)
sudo ufw status
sudo ufw allow 8501
```

## 📊 Monitoramento

### Healthcheck

O container inclui healthcheck automático:
- **Intervalo**: 30 segundos
- **Timeout**: 10 segundos
- **Retries**: 3 tentativas

### Logs Estruturados

```bash
# Logs da aplicação
docker logs youtube-buddy-app 2>&1 | grep "INFO"

# Logs de erro
docker logs youtube-buddy-app 2>&1 | grep "ERROR"

# Logs de sessões
docker logs youtube-buddy-app 2>&1 | grep "session"
```

## 🔒 Segurança

### Variáveis de Ambiente

- ✅ Chaves de API via variáveis de ambiente
- ✅ Não expostas nos logs
- ✅ Isolamento por container

### Isolamento de Dados

- ✅ Sessões isoladas por usuário
- ✅ Limpeza automática de dados antigos
- ✅ Arquivos temporários em diretório isolado

### Rede

- ✅ Apenas porta 8501 exposta
- ✅ CORS configurado para segurança
- ✅ XSRF protection habilitado

## 🚀 Deploy para Produção

### Coolify

1. **Criar novo projeto** no Coolify
2. **Conectar repositório** Git
3. **Configurar variáveis** de ambiente
4. **Definir volumes** persistentes
5. **Deploy automático**

### VPS Manual

```bash
# Clone do repositório
git clone https://github.com/seu-usuario/youtube-buddy.git
cd youtube-buddy

# Configurar ambiente
cp env.example .env
nano .env

# Build e execução
./scripts/build.sh
./scripts/run.sh

# Configurar proxy reverso (opcional)
# nginx, caddy, traefik, etc.
```

## 📈 Otimizações

### Performance

- **Multi-stage build** para menor tamanho da imagem
- **Cache de dependências** Python
- **Limpeza automática** de dados antigos
- **Healthcheck** para monitoramento

### Recursos

- **Memória**: ~512MB em uso normal
- **CPU**: Baixo uso, picos durante transcrição
- **Disco**: Banco SQLite + arquivos temporários
- **Rede**: Apenas APIs externas

## 🆘 Suporte

Para problemas específicos do Docker:

1. **Verificar logs** detalhados
2. **Testar conectividade** das APIs
3. **Validar variáveis** de ambiente
4. **Verificar recursos** disponíveis
5. **Consultar documentação** do Coolify

---

**🎯 Resultado**: Aplicação totalmente containerizada, pronta para deployment em qualquer ambiente Docker, com isolamento de usuários e limpeza automática de dados! 