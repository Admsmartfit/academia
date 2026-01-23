# Product Requirements Document (PRD)
## Sistema de Gestão de Academia - Auditoria e Melhorias

**Versão:** 1.0  
**Data:** 21/01/2026  
**Autor:** Análise Técnica  

---

## 1. AUDITORIA DO SISTEMA ATUAL

### 1.1 Veredito Geral
✅ **O código ATENDE aos requisitos fundamentais do PRD** para uma academia única rodando em servidor local.

### 1.2 Pontos Fortes (Conforme PRD)

#### Arquitetura
- ✅ Estrutura correta para uso local (Flask + SQLite)
- ✅ Pastas organizadas e modulares
- ✅ Separação clara de responsabilidades (routes, models, services)

#### Sistema de Créditos
- ✅ Modelo `credits_cost` na `Modality` implementado
- ✅ Campo `cost_at_booking` no `Booking` para histórico
- ✅ Lógica de débito/estorno funcionando
- ✅ Permite configuração flexível (Yoga = 1 crédito, Crossfit = 2)

#### Agendamento Recorrente
- ✅ Modelo `RecurringBooking` completo
- ✅ Lógica de verificação de saldo/validade robusta
- ✅ Processamento automático via scheduler

#### Gamificação
- ✅ Sistema de XP e Níveis implementado
- ✅ Conquistas (`AchievementChecker`) integradas
- ✅ Premiação por check-in, streaks, etc.

#### Loja e Pagamentos
- ✅ Fluxo de checkout funcional
- ✅ Upload de comprovante PIX
- ✅ Aprovação manual pelo admin
- ✅ Controle de inadimplência (15 dias = bloqueio, 90 dias = cancelamento)

---

## 2. PONTOS DE ATENÇÃO E OPORTUNIDADES

### 2.1 Validação de Telefone
**Situação Atual:** O código assume que o usuário digitará o telefone corretamente.

**Problema:** MegaAPI exige formato `5511999999999` (código país + DDD + número).

**Solução Proposta:**
```python
# Em app/services/megaapi.py - método _format_phone já existe
# Adicionar validação no cadastro do usuário
def validate_phone(phone):
    # Remove caracteres não numéricos
    clean = re.sub(r'\D', '', phone)
    
    # Adiciona 55 se não tiver
    if not clean.startswith('55'):
        clean = '55' + clean
    
    # Valida tamanho (13 dígitos: 55 + 11 + 9 dígitos)
    if len(clean) != 13:
        raise ValueError('Telefone inválido. Use: (11) 99999-9999')
    
    return clean
```

### 2.2 Backup Automático
**Situação Atual:** Banco local (`academia.db`) sem backup automatizado.

**Risco:** Perda total de dados em caso de falha do computador.

**Solução Proposta:**
```python
# Criar app/utils/backup.py
import shutil
from datetime import datetime

def backup_database():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    src = 'instance/academia.db'
    dst = f'backups/academia_backup_{timestamp}.db'
    shutil.copy2(src, dst)
    
    # Manter apenas últimos 7 backups
    cleanup_old_backups(keep=7)

# Adicionar ao scheduler (diário às 3h da manhã)
@scheduler.scheduled_job(CronTrigger(hour=3, minute=0))
def daily_backup():
    with app.app_context():
        backup_database()
```

---

## 3. COMPARATIVO COM LÍDERES DE MERCADO

Análise dos líderes: **Tecnofit**, **Evo**, **Next Fit**

| Funcionalidade | Sistema Atual | Líderes de Mercado | Prioridade | Ação Sugerida |
|---|---|---|---|---|
| **Prescrição de Treino** | ❌ Não tem | ✅ App com ficha (séries, reps) | **Alta** | Criar módulo onde instrutor vincula PDF/texto ao aluno |
| **Controle de Acesso** | ⚠️ Manual (Check-in) | ✅ Catracas + Reconhecimento Facial | **Média** | Implementar QR Code dinâmico que instrutor scaneia |
| **CRM de Vendas** | ❌ Básico | ✅ Funil para visitantes | **Média** | Criar status "Visitante" + rotina WhatsApp |
| **WhatsApp Interativo** | ⚠️ Só Texto/Template | ✅ Botões interativos | **Alta** | Implementar mensagens com botões (veja seção 5) |
| **Dashboard Analytics** | ✅ Básico | ✅ Avançado (gráficos, trends) | **Baixa** | Sistema atual atende |
| **App Mobile** | ❌ Não tem | ✅ iOS/Android nativos | **Baixa** | Web responsivo atende pequenas academias |

---

## 4. NOVO MÓDULO: CONFIGURADOR E TESTADOR MEGAAPI

### 4.1 Objetivo
Permitir que o administrador configure e teste a integração com MegaAPI sem precisar editar código.

### 4.2 Funcionalidades
1. **Visualizar Status da Conexão**: Mostra se a instância está conectada
2. **Configurar Credenciais**: Token, Host, Instance Key
3. **Teste de Envio**: Enviar mensagem teste para o próprio admin
4. **Sincronizar Status**: Verificar status dos templates

### 4.3 Implementação
O código completo está disponível no documento de auditoria fornecido, incluindo:
- **Backend**: `app/routes/admin/megaapi_config.py`
- **Frontend**: `app/templates/admin/megaapi/settings.html`
- **Registro**: Adicionar blueprint em `app/__init__.py`

### 4.4 Fluxo de Uso
1. Admin acessa `/admin/megaapi`
2. Visualiza status da conexão atual
3. Edita credenciais (salvas em memória para teste)
4. Envia mensagem teste para seu WhatsApp
5. Valida funcionamento antes de usar em produção

---

## 5. MELHORIAS DA FUNÇÃO WHATSAPP

### 5.1 Implementar Mensagens com Botões Interativos

**Problema Atual:** Mensagens são apenas texto. Usuário precisa responder digitando ou clicar em link externo.

**Solução:** Usar **List Messages** (Menu de Opções) da MegaAPI.

#### Implementação
```python
# Adicionar em app/services/megaapi.py

def send_list_message(self, phone: str, text: str, button_text: str, sections: List[dict]) -> Dict:
    """
    Envia mensagem de lista (Menu) conforme documentação MegaAPI.
    
    Args:
        phone: Número destino (5511999999999)
        text: Texto principal da mensagem
        button_text: Texto do botão (ex: "Opções")
        sections: Lista de seções com opções
        
    Example:
        sections = [
            {
                "title": "Gerenciar Aula",
                "rows": [
                    {
                        "title": "Confirmar Presença",
                        "rowId": "confirm_123",
                        "description": "Garante sua vaga"
                    },
                    {
                        "title": "Cancelar Aula",
                        "rowId": "cancel_123",
                        "description": "Libera vaga para outro"
                    }
                ]
            }
        ]
    """
    phone = self._format_phone(phone)
    
    payload = {
        "messageData": {
            "to": phone,
            "text": text,
            "buttonText": button_text,
            "title": "Ação Necessária",
            "description": "Selecione uma opção abaixo",
            "sections": sections,
            "listType": 0
        }
    }

    try:
        response = requests.post(
            f"{self.base_url}/sendMessage/{self.instance_key}/listMessage",
            headers=self.headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar lista: {e}")
        return None
```

### 5.2 Atualizar Scheduler para Usar Botões

**Substituir:**
```python
# Em app/utils/scheduler.py - lembrete 2h antes
cancel_url = f"https://academia.com/cancel/{booking.id}"
```

**Por:**
```python
# Usar List Message
sections = [
    {
        "title": "Gerenciar Aula",
        "rows": [
            {
                "title": "✅ Confirmar Presença",
                "rowId": f"confirm_{booking.id}",
                "description": "Garante sua vaga"
            },
            {
                "title": "❌ Cancelar Aula",
                "rowId": f"cancel_{booking.id}",
                "description": "Libera vaga p/ outro"
            }
        ]
    }
]

megaapi.send_list_message(
    phone=booking.user.phone,
    text=f"Lembrete: Sua aula de {booking.schedule.modality.name} é às {booking.schedule.start_time.strftime('%H:%M')}!",
    button_text="Opções",
    sections=sections
)
```

### 5.3 Implementar Webhook para Respostas

**Criar:** `app/routes/webhooks.py` (já existe, atualizar)

```python
@webhooks_bp.route('/megaapi/incoming', methods=['POST'])
def megaapi_incoming():
    """Processa respostas dos usuários (botões clicados)"""
    data = request.get_json()
    
    # Extrair resposta de lista
    if 'listResponseMessage' in data.get('message', {}):
        response = data['message']['listResponseMessage']
        row_id = response.get('rowId')  # Ex: "confirm_123" ou "cancel_123"
        
        # Parsear ação
        action, booking_id = row_id.split('_')
        booking = Booking.query.get(int(booking_id))
        
        if action == 'confirm':
            # Apenas registrar confirmação (opcional)
            pass
        elif action == 'cancel':
            # Cancelar aula
            if booking.can_cancel:
                booking.cancel(reason="Cancelado via WhatsApp")
                # Enviar confirmação
                megaapi.send_custom_message(
                    booking.user.phone,
                    f"Sua aula foi cancelada com sucesso. Crédito estornado."
                )
    
    return jsonify({'status': 'ok'}), 200
```

### 5.4 Benefícios
1. **Experiência Melhor**: Usuário não sai do WhatsApp
2. **Menos Erros**: Não depende de digitação correta
3. **Mais Conversões**: Facilita confirmação/cancelamento
4. **Profissional**: Interface moderna e intuitiva

---

## 6. PLANO DE IMPLEMENTAÇÃO

### Fase 1: Configurador MegaAPI (1-2 dias)
- [ ] Criar rota `app/routes/admin/megaapi_config.py`
- [ ] Criar template `app/templates/admin/megaapi/settings.html`
- [ ] Registrar blueprint
- [ ] Testar envio de mensagem

### Fase 2: Botões Interativos (2-3 dias)
- [ ] Implementar `send_list_message` em `megaapi.py`
- [ ] Atualizar scheduler para usar listas
- [ ] Implementar webhook para processar respostas
- [ ] Testar fluxo completo

### Fase 3: Validação e Backup (1 dia)
- [ ] Adicionar validação de telefone no cadastro
- [ ] Implementar backup automático
- [ ] Criar rotina de limpeza de backups antigos
- [ ] Documentar processo de restauração

### Fase 4: Prescrição de Treino (3-4 dias) - OPCIONAL
- [ ] Criar modelo `TrainingPlan`
- [ ] Interface admin para criar fichas
- [ ] Vincular fichas a alunos
- [ ] Visualização para aluno

### Fase 5: QR Code de Acesso (2-3 dias) - OPCIONAL
- [ ] Gerar QR Code único por aluno
- [ ] Interface instrutor para escanear
- [ ] Registrar entrada automática
- [ ] Log de acessos

---

## 7. REQUISITOS TÉCNICOS

### 7.1 Dependências Atuais (OK)
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-Migrate==4.0.5
requests==2.31.0
APScheduler==3.10.4
```

### 7.2 Novas Dependências (Sugeridas)
```
# Para QR Code
qrcode==7.4.2
Pillow==10.1.0

# Para Backup em nuvem (opcional)
boto3==1.34.0  # AWS S3
google-cloud-storage==2.14.0  # Google Cloud
```

---

## 8. MÉTRICAS DE SUCESSO

### 8.1 KPIs Técnicos
- **Uptime**: > 99.5% (monitorar com healthcheck)
- **Tempo de Resposta**: < 500ms para páginas
- **Taxa de Erro WhatsApp**: < 2%
- **Backup Success Rate**: 100%

### 8.2 KPIs de Negócio
- **Taxa de Check-in**: > 85% (alunos que fazem check-in vs. agendados)
- **Taxa de Cancelamento**: < 15%
- **Inadimplência**: < 10%
- **Satisfação do Aluno**: NPS > 70

### 8.3 Monitoramento
```python
# Adicionar em app/routes/webhooks.py
@webhooks_bp.route('/health', methods=['GET'])
def health_check():
    """Health check para monitoramento"""
    checks = {
        'database': check_database(),
        'megaapi': check_megaapi(),
        'scheduler': scheduler.running
    }
    
    status = 'healthy' if all(checks.values()) else 'degraded'
    
    return jsonify({
        'status': status,
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat()
    }), 200 if status == 'healthy' else 503
```

---

## 9. SEGURANÇA E COMPLIANCE

### 9.1 LGPD (Lei Geral de Proteção de Dados)
**Ações Necessárias:**
- [ ] Adicionar termo de consentimento no cadastro
- [ ] Implementar opção de exclusão de dados
- [ ] Criar log de acesso a dados pessoais
- [ ] Anonimizar dados em backups antigos (>1 ano)

### 9.2 Segurança
- [ ] Implementar rate limiting em rotas públicas
- [ ] Adicionar HTTPS em produção (Nginx + Let's Encrypt)
- [ ] Criptografar dados sensíveis (telefone, CPF)
- [ ] Auditoria de acesso a dados financeiros

---

## 10. DOCUMENTAÇÃO

### 10.1 Para Administrador
- Manual de configuração inicial
- Guia de uso do painel admin
- Procedimento de backup/restore
- Solução de problemas comuns

### 10.2 Para Aluno
- Como usar o sistema de agendamento
- Como fazer pagamentos via PIX
- FAQ sobre créditos e cancelamentos
- Tutorial de gamificação

### 10.3 Técnica
- Arquitetura do sistema
- Fluxo de dados
- APIs e integrações
- Guia de desenvolvimento

---

## 11. CONCLUSÃO

O sistema atual está **sólido e funcional** para uma academia local. As melhorias sugeridas são:

### Prioridade ALTA (implementar primeiro)
1. ✅ Configurador MegaAPI (facilita operação)
2. ✅ Botões interativos WhatsApp (melhora UX)
3. ✅ Backup automático (crítico para segurança)

### Prioridade MÉDIA (implementar depois)
4. Prescrição de treino
5. QR Code de acesso
6. CRM de visitantes

### Prioridade BAIXA (nice to have)
7. Dashboard avançado com gráficos
8. App mobile nativo
9. Integração com wearables

**Recomendação Final:** Focar nas melhorias de Prioridade ALTA, que agregam mais valor com menor esforço de desenvolvimento. O sistema já atende muito bem as necessidades de uma academia local.

---

## 12. ANEXOS

### Anexo A: Checklist de Implantação
```markdown
## Pré-Produção
- [ ] Testar todos os fluxos manualmente
- [ ] Criar usuários de teste (admin, instrutor, aluno)
- [ ] Configurar MegaAPI em ambiente de homologação
- [ ] Validar templates WhatsApp
- [ ] Fazer backup do banco vazio

## Produção - Dia 1
- [ ] Instalar dependências (requirements.txt)
- [ ] Configurar .env com dados reais
- [ ] Inicializar banco de dados (flask db upgrade)
- [ ] Criar usuário admin
- [ ] Cadastrar modalidades
- [ ] Cadastrar pacotes
- [ ] Cadastrar horários
- [ ] Testar agendamento end-to-end

## Pós-Produção
- [ ] Monitorar logs por 1 semana
- [ ] Coletar feedback dos primeiros usuários
- [ ] Ajustar templates WhatsApp se necessário
- [ ] Documentar casos de uso reais
```

### Anexo B: Troubleshooting Comum

**Problema:** MegaAPI não envia mensagens
- Verificar se token está correto
- Verificar se instância está ativa no painel
- Testar endpoint de status manualmente
- Verificar formato do telefone

**Problema:** Scheduler não roda
- Verificar se `WERKZEUG_RUN_MAIN` está definido
- Checar logs do APScheduler
- Reiniciar servidor Flask

**Problema:** Banco de dados corrompido
- Parar servidor
- Restaurar último backup
- Validar integridade com `sqlite3 academia.db "PRAGMA integrity_check;"`

---

**Fim do PRD**

*Este documento deve ser revisado e atualizado a cada nova versão do sistema.*
