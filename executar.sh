#!/bin/bash

echo "=========================================="
echo "Iniciando Sistema de Gestao de Academia"
echo "=========================================="

if [ ! -d "venv" ]; then
    echo "Ambiente virtual nao encontrado."
    echo "Por favor, execute ./instalar.sh primeiro."
    exit 1
fi

echo "Ativando ambiente virtual..."
source venv/bin/activate

echo "Iniciando servidor..."
echo "Acesse no navegador: http://localhost:5000"
echo "Pressione CTRL+C para parar o servidor."
echo ""

python run.py
