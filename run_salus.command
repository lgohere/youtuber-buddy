#!/bin/bash

# Define o diretório do script como diretório de trabalho
cd "$(dirname "$0")"

# Exibe cabeçalho
echo "================================="
echo "    Iniciando Salus Transcriptor"
echo "================================="

# Verificar e instalar Homebrew se necessário
if ! command -v brew &> /dev/null; then
    echo "Homebrew não está instalado. Instalando Homebrew primeiro..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Adicionar Homebrew ao PATH para esta sessão
    if [[ -d "/opt/homebrew/bin/" ]]; then
        # Para Apple Silicon (M1/M2)
        export PATH="/opt/homebrew/bin:$PATH"
    elif [[ -d "/usr/local/bin/" ]]; then
        # Para Intel Macs
        export PATH="/usr/local/bin:$PATH"
    fi
    
    # Verificar novamente se brew está disponível agora
    if ! command -v brew &> /dev/null; then
        echo "Falha ao instalar ou configurar Homebrew. Por favor instale manualmente."
        echo "Visite: https://brew.sh"
        echo "Pressione qualquer tecla para sair..."
        read -n 1
        exit 1
    else
        echo "Homebrew instalado com sucesso!"
    fi
fi

# Verifica se ffmpeg está instalado
if ! command -v ffmpeg &> /dev/null; then
    echo "FFmpeg não encontrado. Instalando via Homebrew..."
    brew install ffmpeg
    
    if ! command -v ffmpeg &> /dev/null; then
        echo "Falha ao instalar FFmpeg automaticamente."
        echo "Tentando instalação alternativa..."
        
        # Tentar com sudo se a instalação normal falhar
        echo "Esta operação pode solicitar sua senha de administrador."
        sudo brew install ffmpeg || {
            echo "Não foi possível instalar FFmpeg. O aplicativo pode não funcionar corretamente."
            echo "Você deseja continuar mesmo assim? (s/n)"
            read -n 1 resposta
            if [[ "$resposta" != "s" && "$resposta" != "S" ]]; then
                echo "Instalação cancelada."
                exit 1
            fi
        }
    fi
else
    echo "FFmpeg já está instalado."
fi

# Verifica se python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "Python 3 não encontrado. Instalando via Homebrew..."
    brew install python@3 || { 
        echo "Falha ao instalar Python. Tentando com sudo..."
        sudo brew install python@3 || {
            echo "Falha ao instalar Python. Por favor instale manualmente."
            exit 1
        }
    }
fi

# Verifica versão do Python
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Versão do Python detectada: $PYTHON_VERSION"

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv || { 
        echo "Falha ao criar ambiente virtual. Tentando instalar venv..."
        pip3 install virtualenv
        python3 -m virtualenv venv || {
            echo "Instalando pip e virtualenv no usuário..."
            curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
            python3 get-pip.py --user
            pip3 install --user virtualenv
            python3 -m virtualenv venv || {
                echo "Não foi possível criar o ambiente virtual."
                exit 1
            }
            if [ -f "get-pip.py" ]; then
                rm get-pip.py
            fi
        }
    }
fi

# Ativar ambiente virtual
echo "Ativando ambiente virtual..."
VENV_ACTIVATE="venv/bin/activate"
if [ -f "$VENV_ACTIVATE" ]; then
    source "$VENV_ACTIVATE" || . "$VENV_ACTIVATE"
else
    echo "Arquivo de ativação não encontrado em: $VENV_ACTIVATE"
    echo "Verificando estrutura da venv..."
    find venv -type f -name "activate" | while read file; do
        echo "Tentando ativar com: $file"
        source "$file" && echo "Ativação bem-sucedida!" && break
    done
fi

# Verificar se o ambiente virtual foi ativado
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Aviso: Ambiente virtual pode não ter sido ativado corretamente."
else
    echo "Ambiente virtual ativado: $VIRTUAL_ENV"
fi

# Atualizar pip dentro do ambiente virtual
echo "Atualizando pip..."
python -m pip install --upgrade pip || python3 -m pip install --upgrade pip

# Instalar/atualizar dependências
echo "Instalando/atualizando dependências..."
python -m pip install -r requirements.txt || {
    echo "Falha ao instalar dependências com pip. Tentando pip3..."
    python3 -m pip install -r requirements.txt || {
        echo "Falha ao instalar todas as dependências de uma vez."
        echo "Tentando instalar uma por uma..."
        
        # Instalação linha por linha em caso de falha
        while IFS= read -r line; do
            if [[ ! -z "$line" && ! "$line" =~ ^# ]]; then
                echo "Instalando: $line"
                python -m pip install "$line" || python3 -m pip install "$line" || echo "Falha ao instalar $line"
            fi
        done < requirements.txt
    }
}

# Garantir que streamlit esteja instalado
echo "Verificando instalação do Streamlit..."
python -m pip install streamlit==1.26.0 || python3 -m pip install streamlit==1.26.0

# Criar diretórios necessários se não existirem
mkdir -p texts
mkdir -p transcriptions

# Encontrar o executável do streamlit
STREAMLIT_PATH=$(which streamlit 2>/dev/null)
if [ -z "$STREAMLIT_PATH" ]; then
    echo "Procurando streamlit no ambiente virtual..."
    if [ -f "venv/bin/streamlit" ]; then
        STREAMLIT_PATH="venv/bin/streamlit"
    elif [ -f "$VIRTUAL_ENV/bin/streamlit" ]; then
        STREAMLIT_PATH="$VIRTUAL_ENV/bin/streamlit"
    else
        echo "Não foi possível encontrar o executável do streamlit."
        echo "Tentando executar diretamente com python..."
        echo "Iniciando o aplicativo..."
        python -m streamlit run app.py
        exit_code=$?
        if [ $exit_code -ne 0 ]; then
            echo "Falha ao iniciar o aplicativo com 'python -m streamlit'."
            echo "Tentando método alternativo..."
            pip install streamlit==1.26.0
            python -c "import streamlit.cli as cli; cli.main(['run', 'app.py'])"
        fi
        echo "Aplicativo encerrado. Pressione qualquer tecla para fechar esta janela..."
        read -n 1
        exit 0
    fi
fi

# Iniciar o aplicativo
echo "Iniciando o aplicativo Streamlit..."
if [ ! -z "$STREAMLIT_PATH" ]; then
    echo "Usando streamlit em: $STREAMLIT_PATH"
    "$STREAMLIT_PATH" run app.py
elif command -v streamlit &> /dev/null; then
    echo "Usando streamlit do PATH"
    streamlit run app.py
else
    echo "Tentando método alternativo com python -m..."
    python -m streamlit run app.py || python3 -m streamlit run app.py
fi

# Manter o terminal aberto até o usuário pressionar uma tecla
echo "Aplicativo encerrado. Pressione qualquer tecla para fechar esta janela..."
read -n 1 