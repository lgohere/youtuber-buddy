# 📱 Guia de Configuração: Uploads de até 2GB no Coolify

## 🚨 **PROBLEMA IDENTIFICADO**
O erro **413 Content Too Large** está vindo do **proxy reverso do Coolify**, não da nossa aplicação. O Coolify usa um nginx proxy na frente que tem limite padrão de 1MB.

## ✅ **SOLUÇÕES IMPLEMENTADAS PARA 2GB**

### 1. **Labels Docker no docker-compose.yml**
```yaml
labels:
  - "coolify.proxy.nginx.client_max_body_size=0"
  - "coolify.proxy.nginx.proxy_read_timeout=7200s"      # 2 horas
  - "coolify.proxy.nginx.proxy_connect_timeout=7200s"   # 2 horas
  - "coolify.proxy.nginx.proxy_send_timeout=7200s"      # 2 horas
  - "coolify.proxy.nginx.client_body_timeout=7200s"     # 2 horas
  - "coolify.proxy.nginx.client_header_timeout=7200s"   # 2 horas
  - "coolify.proxy.nginx.proxy_request_buffering=off"
  - "coolify.proxy.nginx.proxy_buffering=off"
  - "coolify.proxy.nginx.proxy_max_temp_file_size=0"
  - "coolify.proxy.nginx.client_body_buffer_size=256k"
```

### 2. **Variáveis de Ambiente no Coolify**
Adicione estas variáveis no painel do Coolify:

```bash
NGINX_CLIENT_MAX_BODY_SIZE=0
NGINX_PROXY_READ_TIMEOUT=7200
NGINX_PROXY_CONNECT_TIMEOUT=7200
NGINX_PROXY_SEND_TIMEOUT=7200
NGINX_CLIENT_BODY_TIMEOUT=7200
NGINX_CLIENT_HEADER_TIMEOUT=7200
NGINX_PROXY_MAX_TEMP_FILE_SIZE=0
NGINX_CLIENT_BODY_BUFFER_SIZE=256k
```

### 3. **Configuração Manual do Nginx (Se necessário)**
Se as labels não funcionarem, use o arquivo `coolify-nginx.conf`:

```nginx
# Configurações para uploads de até 2GB
client_max_body_size 0;
client_body_timeout 7200s;       # 2 horas
client_header_timeout 7200s;     # 2 horas
proxy_read_timeout 7200s;        # 2 horas
proxy_connect_timeout 7200s;     # 2 horas
proxy_send_timeout 7200s;        # 2 horas
proxy_request_buffering off;
proxy_buffering off;
proxy_max_temp_file_size 0;
client_body_buffer_size 256k;
```

## 🔧 **PASSOS PARA IMPLEMENTAR**

### **Passo 1: Atualizar o Projeto**
```bash
git add -A
git commit -m "fix: Configure Coolify proxy for 2GB video uploads"
git push origin master
```

### **Passo 2: No Painel do Coolify**
1. Vá para **Environment Variables**
2. Adicione as variáveis listadas acima
3. **Redeploy** a aplicação

### **Passo 3: Verificar Configuração**
1. Acesse: `https://api.texts.com.br/api/health/`
2. Teste upload de arquivo pequeno primeiro (5MB)
3. Teste upload de arquivo médio (100MB)
4. Teste upload de arquivo grande (500MB)
5. Teste upload de vídeo 2GB

### **Passo 4: Se Ainda Não Funcionar**
1. Acesse **Settings** > **Advanced** no Coolify
2. Procure por **Custom Nginx Configuration**
3. Cole o conteúdo do arquivo `coolify-nginx.conf`

## 📊 **MONITORAMENTO PARA 2GB**

### **Logs para Verificar**
```bash
# No Coolify, verifique os logs:
# 1. Application Logs
# 2. Proxy Logs
# 3. System Logs
# 4. Disk Usage (2GB por upload)
```

### **Testes de Validação Progressivos**
```bash
# Teste 1: Health Check
curl -I https://api.texts.com.br/api/health/

# Teste 2: CORS
curl -X OPTIONS https://api.texts.com.br/api/transcriptions/create/ \
  -H "Origin: https://yt.texts.com.br" -v

# Teste 3: Upload pequeno (5MB) - deve funcionar
# Teste 4: Upload médio (100MB) - deve funcionar
# Teste 5: Upload grande (500MB) - deve funcionar
# Teste 6: Upload 2GB - deve funcionar após fix
```

## 🎯 **RESULTADOS ESPERADOS PARA 2GB**

✅ **Antes do Fix:**
- ❌ Uploads >1MB: `413 Content Too Large`
- ❌ Mobile uploads: Falham
- ❌ Vídeos grandes: Impossível

✅ **Depois do Fix:**
- ✅ Uploads até 2GB funcionando
- ✅ Mobile uploads de vídeos grandes
- ✅ CORS configurado corretamente
- ✅ Timeouts de 2 horas para conexões lentas
- ✅ Streaming de upload (sem buffering)

## 🚀 **CONFIGURAÇÕES ESPECÍFICAS PARA 2GB**

### **Espaço em Disco Necessário**
```bash
# Sua VPS tem 80GB, então pode armazenar:
# - Aproximadamente 40 vídeos de 2GB
# - Ou 160 vídeos de 500MB
# - Ou 800 vídeos de 100MB
```

### **Para Arquivos Ainda Maiores (>2GB)**
```bash
# Se precisar de mais que 2GB no futuro:
NGINX_PROXY_READ_TIMEOUT=10800  # 3 horas
NGINX_CLIENT_BODY_TIMEOUT=10800  # 3 horas
```

### **Otimizações de Performance**
```bash
# Para melhor performance com arquivos grandes:
NGINX_CLIENT_BODY_BUFFER_SIZE=512k
NGINX_WORKER_PROCESSES=auto
NGINX_WORKER_CONNECTIONS=1024
```

## 📱 **TESTE ESPECÍFICO PARA VÍDEOS 2GB**

### **Dispositivos para Testar:**
- iPhone (Safari, Chrome) - Vídeos 4K
- Android (Chrome, Firefox) - Vídeos 4K
- iPad/Tablet - Vídeos longos
- Conexões: WiFi (essencial para 2GB), 5G

### **Arquivos para Testar Progressivamente:**
1. **Áudio:** 5MB, 50MB, 150MB
2. **Vídeo Pequeno:** 10MB, 100MB
3. **Vídeo Médio:** 500MB, 1GB
4. **Vídeo Grande:** 1.5GB, 2GB
5. **Formatos:** MP4, MOV, AVI, MKV

### **Cenários de Teste:**
- ✅ Upload WiFi rápido (2GB em ~10-15 min)
- ✅ Upload WiFi lento (2GB em ~30-60 min)
- ✅ Upload 5G (2GB em ~15-30 min)
- ⚠️ Upload 4G (2GB pode levar 1-2 horas)

## 🔍 **TROUBLESHOOTING PARA 2GB**

### **Se ainda der 413:**
1. Verificar se o redeploy foi feito
2. Verificar se as variáveis de ambiente foram aplicadas
3. Verificar logs do proxy nginx
4. Testar com arquivo menor primeiro (100MB)

### **Se der timeout:**
1. Verificar conexão de internet (WiFi recomendado para 2GB)
2. Aumentar timeouts para 3 horas se necessário
3. Testar com arquivo menor (500MB)

### **Se der erro de espaço:**
1. Verificar espaço disponível na VPS (80GB total)
2. Limpar arquivos antigos se necessário
3. Monitorar uso de disco

### **Se der erro de memória:**
1. Verificar RAM disponível (4GB total)
2. Otimizar configurações de buffer
3. Reiniciar serviços se necessário

## 💾 **GESTÃO DE ESPAÇO PARA 2GB**

### **Monitoramento de Disco:**
```bash
# Comandos para monitorar no Coolify:
df -h                    # Espaço total
du -sh /app/media       # Espaço usado pelos uploads
ls -lah /app/media      # Listar arquivos por tamanho
```

### **Limpeza Automática (Recomendado):**
```bash
# Configurar limpeza de arquivos antigos:
# - Deletar arquivos processados após 30 dias
# - Manter apenas os últimos 20 uploads
# - Comprimir arquivos antigos
```

---

**🎉 Com essas configurações, sua aplicação suporta uploads de até 2GB!**

**⚠️ IMPORTANTE:** Para uploads de 2GB, recomende aos usuários:
- Usar conexão WiFi estável
- Não fechar o navegador durante o upload
- Aguardar até 2 horas para uploads completos 