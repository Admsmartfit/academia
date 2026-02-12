#!/bin/bash

echo "=========================================="
echo "Instalando Sistema de Gestao de Academia"
echo "=========================================="

echo ""
echo "1. Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "Python3 nao encontrado. Por favor instale o Python 3."
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    echo "  Arch: sudo pacman -S python python-pip"
    exit 1
fi
python3 --version

echo ""
echo "2. Criando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Ambiente virtual criado com sucesso."
else
    echo "Ambiente virtual ja existe."
fi

echo ""
echo "3. Ativando ambiente virtual..."
source venv/bin/activate

echo ""
echo "4. Atualizando ferramentas de build..."
pip install --upgrade pip setuptools wheel
if [ $? -ne 0 ]; then
    echo "Erro ao atualizar pip/setuptools/wheel."
    exit 1
fi

echo ""
echo "5. Instalando dependencias..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Erro ao instalar dependencias."
    exit 1
fi

echo ""
echo "6. Configurando variaveis de ambiente..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Arquivo .env criado a partir do .env.example"
    else
        echo "Criando arquivo .env basico..."
        cat > .env << 'EOF'
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=sua-chave-secreta-aqui
DATABASE_URL=sqlite:///instance/academia.db
EOF
        echo "Arquivo .env criado."
    fi
else
    echo "Arquivo .env ja existe."
fi

echo ""
echo "7. Configurando banco de dados..."
flask db upgrade
if [ $? -ne 0 ]; then
    echo "Erro ao configurar banco de dados."
    exit 1
fi

echo ""
echo "=========================================="
echo "Instalacao concluida com sucesso!"
echo "=========================================="
echo "Execute ./executar.sh para iniciar o sistema."
