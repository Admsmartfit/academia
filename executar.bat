@echo off
echo ==========================================
echo Iniciando Sistema de Gestao de Academia
echo ==========================================

if not exist venv (
    echo Ambiente virtual nao encontrado. Por favor, execute instalar.bat primeiro.
    pause
    exit /b
)

echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo Iniciando servidor...
echo Acesse no navegador: http://localhost:5000
echo Pressione CTRL+C para parar o servidor.
echo.
python run.py

pause
