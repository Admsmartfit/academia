PRD: Correção da Integração MegaAPI (Hotfix)
Versão: 3.4 (API Connectivity)
Arquivos Afetados: app/routes/admin/megaapi_config.py e app/templates/admin/megaapi/settings.html

1. Correção no Backend (megaapi_config.py)
Precisamos ajustar o endpoint para seguir o padrão /rest exigido pelo servidor apistart01 e garantir que o retorno seja sempre JSON, mesmo em caso de erro crítico.

Ação: Localize a função get_instance_status no ficheiro app/routes/admin/megaapi_config.py e atualize a chamada de URL:

Python
# app/routes/admin/megaapi_config.py

def get_instance_status(host=None, token=None, instance_key=None) -> dict:
    # Garante que o host termina sem barra e usa o prefixo correto
    base_url = (host or megaapi.base_url or '').rstrip('/')
    current_token = token or megaapi.token
    
    if not base_url or not current_token:
        return {'connected': False, 'error': 'Credenciais não configuradas'}
        
    headers = {
        'Authorization': f'Bearer {current_token}',
        'Content-Type': 'application/json'
    }

    try:
        # CORREÇÃO: O endpoint oficial segundo a documentação start01 é /instance/status
        # Se a base_url já tiver /rest, não duplicamos.
        status_path = "/instance/status" if "/rest" in base_url else "/rest/instance/status"
        
        response = requests.get(
            f"{base_url}{status_path}",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return {
                'connected': True,
                'status': 'Online',
                'data': response.json()
            }
        else:
            return {
                'connected': False,
                'error': f'Servidor MegaAPI retornou erro {response.status_code}'
            }
    except Exception as e:
        return {'connected': False, 'error': f"Falha na comunicação: {str(e)}"}
2. Correção no Frontend (settings.html)
Para evitar o erro de "JSON inválido", precisamos garantir que o fetch envie as credenciais de admin e trate erros de rede.

Ação: Substitua a função validateConnection() no ficheiro app/templates/admin/megaapi/settings.html:

JavaScript
// app/templates/admin/megaapi/settings.html

function validateConnection() {
    const btn = document.getElementById('validateBtn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Validando...';

    const data = {
        host: document.getElementById('host').value,
        instance_key: document.getElementById('instance_key').value,
        token: document.getElementById('token').value
    };

    fetch('{{ url_for("admin_megaapi.check_status_ajax") }}', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(async response => {
        // CORREÇÃO: Verifica se a resposta é HTML antes de tentar converter para JSON
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return response.json();
        } else {
            // Se for HTML, provavelmente é um erro 404/500 do Flask
            throw new Error("O servidor retornou HTML em vez de JSON. Verifique se está logado como Admin.");
        }
    })
    .then(data => {
        if (data.connected) {
            alert('✅ Conectado com sucesso!');
            location.reload();
        } else {
            alert('❌ Erro: ' + (data.error || 'Falha na conexão'));
        }
    })
    .catch(err => {
        alert('⚠️ Erro de requisição: ' + err.message);
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = originalText;
    });
}