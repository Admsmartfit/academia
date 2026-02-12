# Manual de Instalação e Execução - Sistema de Gestão de Academia

Este guia fornece o passo a passo para configurar e rodar o sistema no seu computador (Windows).

## Pré-requisitos

1.  **Python Instalado**: Certifique-se de ter o Python instalado (versão 3.8 ou superior).
    *   Para verificar, abra o terminal (PowerShell ou CMD) e digite: `python --version`

## Passo a Passo

### 1. Preparar o Ambpoweiente

Abra o terminal na pasta do projeto (`c:\Users\ralan\academia`) e execute os comandos abaixo na ordem:

**Criar o ambiente virtual (Recomendado):**
Isso cria uma pasta isolada para as bibliotecas do projeto, evitando conflitos com outros programas.
```powershell
python -m venv venv
```

**Ativar o ambiente virtual:**
```powershell
.\venv\Scripts\activate
```
*Você verá `(venv)` aparecer no início da linha do terminal.*

### 2. Instalar Dependências

Com o ambiente virtual ativado, instale as bibliotecas necessárias listadas no `requirements.txt`:
```powershell
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente

O sistema precisa de algumas configurações para rodar.
1.  Na pasta do projeto, encontre o arquivo chamado `.env.example`.
2.  Faça uma cópia dele e renomeie para `.env`.
3.  (Opcional) Edite o arquivo `.env` se quiser mudar alguma configuração, mas o padrão já funciona para testes locais.

**No Windows (comando rápido para copiar):**
```powershell
copy .env.example .env
```

### 4. Configurar o Banco de Dados

O sistema usa um banco de dados local (SQLite). Você precisa criar as tabelas iniciais:

```powershell
flask db upgrade
```
*Isso criará um arquivo `academia.db` na pasta `instance` ou na raiz, contendo a estrutura do banco.*

### 5. Executar o Sistema

Agora está tudo pronto para rodar!

```powershell
python run.py
```

Se tudo der certo, você verá uma mensagem parecida com:
`Running on http://0.0.0.0:5000` (ou `http://127.0.0.1:5000`)

### 6. Acessar

Abra seu navegador de internet e digite:
[http://localhost:5000](http://localhost:5000)

---

## Comandos Úteis

*   **Parar o servidor**: No terminal onde o programa está rodando, aperte `CTRL + C`.
*   **Criar um Usuário Admin (Via Terminal)**:
    Se você precisar criar um administrador manualmente, pode usar o shell do Flask:
    ```powershell
    flask shell
    ```
    E depois dentro do Python:
    ```python
    >>> u = User(name='Admin', email='admin@academia.com', role='admin')
    >>> u.set_password('senha123')
    >>> db.session.add(u)
    >>> db.session.commit()
    >>> exit()
    ```

## Solução de Problemas Comuns

*   **Erro "comando não encontrado"**: Verifique se instalou o Python e marcou a opção "Add Python to PATH".
*   **Erro de Permissão no PowerShell**: Se ao ativar o venv der erro, execute: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` e tente ativar novamente.
*   **Erro ao instalar `dlib` ou `face_recognition`**: Este erro ocorre porque o `dlib` exige um compilador C++ (Visual Studio Build Tools) instalado no Windows. 
    *   **Opção 1 (Recomendada)**: O sistema agora ignora essa parte por padrão no `requirements.txt` para você conseguir rodar o resto.
    *   **Opção 2 (Se precisar de reconhecimento facial)**: Baixe e instale o [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) e marque a opção "Desenvolvimento para desktop com C++".
    *   **Opção 3 (Rápida)**: Tente instalar via uma "wheel" pré-compilada para Python 3.13: 
        `pip install https://github.com/shaurya0028/dlib-for-python-3.13/releases/download/v19.24.99/dlib-19.24.99-cp313-cp313-win_amd64.whl`
