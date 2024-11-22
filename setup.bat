@echo off
chcp 65001 >nul
REM ============================================================
REM setup.bat - Configuracao e execucao do QoL Alteryx-ODI Tools
REM Para Windows 10/11
REM ============================================================

echo.
echo ============================================================
echo   QoL Alteryx-ODI Tools
echo   Setup e Execucao Automatica
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/3] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo       ERRO: Python nao encontrado!
    echo       Por favor, instale o Python 3.10+ e adicione ao PATH.
    pause
    exit /b 1
) else (
    python --version
)

echo.
echo [2/3] Configurando ambiente virtual...
if not exist "venv" (
    echo       Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo       ERRO: Falha ao criar ambiente virtual!
        pause
        exit /b 1
    )
    echo       + Ambiente virtual criado com sucesso
) else (
    echo       - Ambiente virtual ja existe
)

echo       Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo.
echo [3/3] Verificando dependencias...
python -c "import pip; exit(0)" >nul 2>&1
if errorlevel 1 (
    echo       Instalando pip...
    python -m ensurepip --upgrade >nul 2>&1
)
REM Usa apenas bibliotecas built-in do Python (xml.etree, re, pathlib, tkinter)
echo       + Dependencias verificadas (apenas bibliotecas built-in)
echo       + Nenhuma instalacao necessaria

echo.
echo ============================================================
echo   Ambiente configurado com sucesso!
echo ============================================================
echo.
echo Iniciando QoL Alteryx-ODI Tools...
echo.

python main.py

echo.
echo ============================================================
echo   Processo finalizado!
echo ============================================================
echo.

pause
