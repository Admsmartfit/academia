O erro **404** retornado pelo servidor `apistart01.megaapi.com.br` confirma que estamos a conseguir falar com o seu servidor dedicado, mas o "caminho" (URL) que o código está a tentar seguir não existe nessa versão específica da API.

Para instâncias da linha **Start/Dedicada**, a MegaAPI exige obrigatoriamente o prefixo `/rest` antes de qualquer comando, e o endpoint de status deve conter a sua chave no final.

Abaixo, o **PRD de Ajuste Final de Roteamento** para resolver o erro 404.

---

# PRD: Ajuste de Roteamento MegaAPI (Fix 404 Start Server)

**Versão:** 3.6 (Dedicated Routing)
**Arquivos Afetados:** `app/routes/admin/megaapi_config.py` e `app/services/megaapi.py`

## 1. Ajuste no Backend Administrativo (`megaapi_config.py`)

Precisamos forçar o uso do prefixo `/rest` e garantir que o Token seja enviado corretamente para o seu servidor `apistart01`.

**Ação:** Substitua a função `get_instance_status` no ficheiro `app/routes/admin/megaapi_config.py` por esta versão:

```python
# app/routes/admin/megaapi_config.py

def get_instance_status(host=None, token=None, instance_key=None) -> dict:
    """
    Busca status da instância adaptado especificamente para o servidor Start (apistart01).
    """
    # 1. Recupera as credenciais
    base_url = (host or megaapi.base_url or '').rstrip('/')
    current_token = token or megaapi.token
    current_instance_key = instance_key or getattr(megaapi, 'instance_key', None)
    
    if not base_url or not current_token or not current_instance_key:
        return {'connected': False, 'error': 'Credenciais incompletas'}
        
    headers = {
        'Authorization': f'Bearer {current_token}',
        'Content-Type': 'application/json'
    }

    try:
        # CORREÇÃO DEFINITIVA PARA apistart01: 
        # É obrigatório o prefixo /rest e o ID da instância na URL
        if "/rest" not in base_url:
            endpoint_url = f"{base_url}/rest/instance/status/{current_instance_key}"
        else:
            endpoint_url = f"{base_url}/instance/status/{current_instance_key}"
        
        response = requests.get(endpoint_url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            # No Start, o status vem dentro de um objeto 'instance' ou diretamente
            instance_data = data.get('instance', {})
            status_api = data.get('status') or instance_data.get('state')
            
            return {
                'connected': status_api in ('online', 'open', 'CONNECTED'),
                'status': 'Online' if status_api in ('online', 'open', 'CONNECTED') else 'Desconectado',
                'data': data
            }
        elif response.status_code == 404:
            return {'connected': False, 'error': f'A instância {current_instance_key} não foi encontrada no servidor.'}
        else:
            return {'connected': False, 'error': f'Erro HTTP {response.status_code}'}
            
    except Exception as e:
        return {'connected': False, 'error': f"Erro de conexão: {str(e)}"}
```

## 2. Ajuste no Serviço de Mensagens (`megaapi.py`)

Para que as notificações automáticas do Biohacking Studio funcionem, o serviço principal também deve conhecer o prefixo `/rest`.

**Ação:** No ficheiro `app/services/megaapi.py`, localize o método `__init__` e adicione o `/rest` à URL:

```python
# app/services/megaapi.py (Ajuste no construtor)

class MegapiService:
    def __init__(self):
        # Busca a URL do ambiente ou usa a padrão
        raw_url = os.getenv('MEGAAPI_BASE_URL', 'https://apistart01.megaapi.com.br')
        
        # Garante o prefixo /rest para servidores Start
        if "megaapi.com.br" in raw_url and "/rest" not in raw_url:
            self.base_url = f"{raw_url.rstrip('/')}/rest"
        else:
            self.base_url = raw_url.rstrip('/')
            
        self.token = os.getenv('MEGAAPI_TOKEN')
        self.instance_key = os.getenv('MEGAAPI_INSTANCE_KEY', '')
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
```

---

### Como configurar no painel após o código:

Aceda a `http://192.168.0.65:5000/admin/megaapi/` e preencha:

1.  **Host (URL da API):** `https://apistart01.megaapi.com.br` 
    * *(Não coloque nada depois do .br, o código agora trata o /rest automaticamente)*.
2.  **Instance Key:** `megastart-MR7EdIG0JY0`.
3.  **Token (Bearer):** `MR7EdIG0JY0`.

**Por que vai funcionar agora?**
A imagem que enviou mostra claramente que a sua instância está **Online** no servidor `apistart01`. O erro 404 acontecia porque o sistema antigo "batia à porta errada". Ao adicionar o `/rest` e o ID da instância na URL, o servidor agora saberá exatamente quem está a perguntar o status.