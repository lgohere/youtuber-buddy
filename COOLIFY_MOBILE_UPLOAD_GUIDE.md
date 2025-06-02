# 📱 Guia de Configuração: Uploads Móveis Ilimitados no Coolify

## 🚨 **PROBLEMA IDENTIFICADO**
O erro **413 Content Too Large** está vindo do **proxy reverso do Coolify**, não da nossa aplicação. O Coolify usa um nginx proxy na frente que tem limite padrão de 1MB.

## ✅ **SOLUÇÕES IMPLEMENTADAS**

### 1. **Labels Docker no docker-compose.yml**
```yaml
labels:
  - "coolify.proxy.nginx.client_max_body_size=0"
  - "coolify.proxy.nginx.proxy_read_timeout=3600s"
  - "coolify.proxy.nginx.proxy_connect_timeout=3600s"
  - "coolify.proxy.nginx.proxy_send_timeout=3600s"
  - "coolify.proxy.nginx.client_body_timeout=3600s"
  - "coolify.proxy.nginx.client_header_timeout=3600s"
  - "coolify.proxy.nginx.proxy_request_buffering=off"
```

### 2. **Variáveis de Ambiente no Coolify**
Adicione estas variáveis no painel do Coolify:

```bash
NGINX_CLIENT_MAX_BODY_SIZE=0
NGINX_PROXY_READ_TIMEOUT=3600
NGINX_PROXY_CONNECT_TIMEOUT=3600
NGINX_PROXY_SEND_TIMEOUT=3600
NGINX_CLIENT_BODY_TIMEOUT=3600
NGINX_CLIENT_HEADER_TIMEOUT=3600
```

### 3. **Configuração Manual do Nginx (Se necessário)**
Se as labels não funcionarem, use o arquivo `coolify-nginx.conf`:

```nginx
# Adicionar ao nginx.conf do Coolify
client_max_body_size 0;
client_body_timeout 3600s;
client_header_timeout 3600s;
proxy_read_timeout 3600s;
proxy_connect_timeout 3600s;
proxy_send_timeout 3600s;
proxy_request_buffering off;
```

## 🔧 **PASSOS PARA IMPLEMENTAR**

### **Passo 1: Atualizar o Projeto**
```bash
git add -A
git commit -m "fix: Configure Coolify proxy for unlimited mobile uploads"
git push origin master
```

### **Passo 2: No Painel do Coolify**
1. Vá para **Environment Variables**
2. Adicione as variáveis listadas acima
3. **Redeploy** a aplicação

### **Passo 3: Verificar Configuração**
1. Acesse: `https://api.texts.com.br/api/health/`
2. Teste upload de arquivo pequeno primeiro
3. Teste upload de arquivo grande (>1MB)

### **Passo 4: Se Ainda Não Funcionar**
1. Acesse **Settings** > **Advanced** no Coolify
2. Procure por **Custom Nginx Configuration**
3. Cole o conteúdo do arquivo `coolify-nginx.conf`

## 📊 **MONITORAMENTO**

### **Logs para Verificar**
```bash
# No Coolify, verifique os logs:
# 1. Application Logs
# 2. Proxy Logs
# 3. System Logs
```

### **Testes de Validação**
```bash
# Teste 1: Health Check
curl -I https://api.texts.com.br/api/health/

# Teste 2: CORS
curl -X OPTIONS https://api.texts.com.br/api/transcriptions/create/ \
  -H "Origin: https://yt.texts.com.br" -v

# Teste 3: Upload pequeno (deve funcionar)
# Teste 4: Upload grande (>1MB) - deve funcionar após fix
```

## 🎯 **RESULTADOS ESPERADOS**

✅ **Antes do Fix:**
- ❌ Uploads >1MB: `413 Content Too Large`
- ❌ Mobile uploads: Falham
- ❌ CORS errors em alguns casos

✅ **Depois do Fix:**
- ✅ Uploads ilimitados (até o espaço em disco)
- ✅ Mobile uploads funcionando
- ✅ CORS configurado corretamente
- ✅ Timeouts adequados para conexões lentas

## 🚀 **CONFIGURAÇÕES ADICIONAIS**

### **Para Arquivos Muito Grandes (>1GB)**
```bash
# Adicionar no Coolify se necessário:
NGINX_PROXY_MAX_TEMP_FILE_SIZE=0
NGINX_CLIENT_BODY_BUFFER_SIZE=128k
```

### **Para Redes Muito Lentas**
```bash
# Aumentar timeouts ainda mais:
NGINX_PROXY_READ_TIMEOUT=7200  # 2 horas
NGINX_CLIENT_BODY_TIMEOUT=7200  # 2 horas
```

## 📱 **TESTE ESPECÍFICO MOBILE**

### **Dispositivos para Testar:**
- iPhone (Safari, Chrome)
- Android (Chrome, Firefox)
- iPad/Tablet
- Conexões: WiFi, 4G, 5G

### **Arquivos para Testar:**
- Áudio MP3: 5MB, 50MB, 150MB
- Vídeo MP4: 10MB, 100MB, 500MB
- Formatos diversos: WAV, FLAC, MOV, AVI

## 🔍 **TROUBLESHOOTING**

### **Se ainda der 413:**
1. Verificar se o redeploy foi feito
2. Verificar logs do proxy nginx
3. Testar com arquivo menor primeiro
4. Verificar se as variáveis foram aplicadas

### **Se der timeout:**
1. Aumentar os timeouts
2. Verificar conexão de internet
3. Testar com arquivo menor

### **Se der CORS error:**
1. Verificar se o frontend está acessando a URL correta
2. Verificar se as headers CORS estão sendo enviadas
3. Testar com curl primeiro

---

**🎉 Com essas configurações, sua aplicação deve aceitar uploads móveis ilimitados!** 