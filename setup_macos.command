#!/bin/bash

# Define o diretório do script como diretório de trabalho
cd "$(dirname "$0")"

# Exibe cabeçalho
echo "================================="
echo "    Setup Salus Transcriptor     "
echo "================================="

# Remover ambiente virtual existente (se houver)
if [ -d "venv" ]; then
    echo "Removendo ambiente virtual antigo..."
    rm -rf venv
fi

# Verificar e instalar Homebrew se necessário
if ! command -v brew &> /dev/null; then
    echo "Instalando Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Adicionar Homebrew ao PATH para esta sessão
    if [[ -d "/opt/homebrew/bin/" ]]; then
        # Para Apple Silicon (M1/M2)
        export PATH="/opt/homebrew/bin:$PATH"
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -d "/usr/local/bin/" ]]; then
        # Para Intel Macs
        export PATH="/usr/local/bin:$PATH"
        echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/usr/local/bin/brew shellenv)"
    fi
else
    echo "Homebrew já está instalado."
fi

# Instalar FFmpeg se necessário
if ! command -v ffmpeg &> /dev/null; then
    echo "Instalando FFmpeg..."
    brew install ffmpeg
fi

# Verificar Python e instalar se necessário
if ! command -v python3 &> /dev/null; then
    echo "Instalando Python..."
    brew install python@3
fi

# Criar ambiente virtual
echo "Criando novo ambiente virtual..."
python3 -m venv venv

# Ativar ambiente virtual
echo "Ativando ambiente virtual..."
source venv/bin/activate

# Atualizar pip
echo "Atualizando pip..."
pip install --upgrade pip

# Instalar dependências
echo "Instalando dependências..."
pip install -r requirements.txt

# Criar diretórios necessários
mkdir -p texts
mkdir -p transcriptions

echo "================================="
echo "Setup concluído com sucesso!"
echo "Para iniciar o aplicativo, execute:"
echo "double-click em run_app.command"
echo "================================="

# Criar script de execução
echo "Criando script de execução..."
cat > run_app.command << 'EOL'
#!/bin/bash
cd "$(dirname "$0")"
echo "Iniciando Salus Transcriptor..."
source venv/bin/activate
streamlit run app.py
EOL

# Tornar executável
chmod +x run_app.command

echo "Pressione qualquer tecla para fechar..."
read -n 1 