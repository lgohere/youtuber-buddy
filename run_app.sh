#!/bin/bash

# Verificar se python está instalado
if ! command -v python &> /dev/null
then
    echo "Python não está instalado. Por favor, instale Python para continuar."
    exit 1
fi

# Verificar se pip está instalado
if ! command -v pip &> /dev/null
then
    echo "pip não está instalado. Por favor, instale pip para continuar."
    exit 1
fi

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]
then
    echo "Criando ambiente virtual..."
    python -m venv venv
fi

# Ativar ambiente virtual
echo "Ativando ambiente virtual..."
source venv/bin/activate || source venv/Scripts/activate

# Instalar dependências
echo "Instalando dependências..."
pip install -r requirements.txt

# Iniciar o aplicativo
echo "Iniciando o aplicativo Streamlit..."
streamlit run app.py 