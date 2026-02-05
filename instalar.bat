@echo off
echo ==========================================
echo Instalando Sistema de Gestao de Academia
echo ==========================================

echo 1. Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo Python nao encontrado. Por favor instale o Python.
    pause
    exit /b
)

echo.
echo 2. Criando ambiente virtual...
if not exist venv (
    python -m venv venv
    echo Ambiente virtual criado com sucesso.
) else (
    echo Ambiente virtual ja existe.
)

echo.
echo 3. Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo.
echo 4. Atualizando ferramentas de build...
python -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
    echo Erro ao atualizar pip/setuptools/wheel.
    pause
    exit /b
)

echo.
echo 5. Instalando dependencias...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Erro ao instalar dependencias.
    pause
    exit /b
)

echo.
echo 5. Configurando variaveis de ambiente...
if not exist .env (
    copy .env.example .env
    echo Arquivo .env criado.
) else (
    echo Arquivo .env ja existe.
)

echo.
echo 6. Configurando banco de dados...
flask db upgrade
if %errorlevel% neq 0 (
    echo Erro ao configurar banco de dados.
    pause
    exit /b
)

echo.
echo ==========================================
echo Instalacao concluida com sucesso!
echo ==========================================
echo Voce pode fechar esta janela e usar o arquivo executar.bat para abrir o sistema.
pause
