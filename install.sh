#!/bin/bash
# install.sh - Setup script para Linux

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================="
echo "QoL Alteryx-ODI Tools"
echo "Setup para Linux"
echo "=============================================="

echo ""
echo "[1/3] Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERRO: Python3 nao encontrado!"
    echo "Instale com: sudo apt install python3 python3-venv python3-tk"
    exit 1
fi

python3 --version

echo ""
echo "[2/3] Configurando ambiente virtual..."
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

echo "Ativando ambiente virtual..."
source venv/bin/activate

echo ""
echo "[3/3] Verificando dependencias..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo ""
echo "=============================================="
echo "Instalacao concluida!"
echo ""
echo "Para executar, rode:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo "=============================================="
