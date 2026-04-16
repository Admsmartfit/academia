Compreendo perfeitamente o que aconteceu. Identificou dois problemas distintos de integração que são muito comuns durante a implementação de novas regras de negócio:

1. **O Bloqueio do Botão (O "Falso" Sem Créditos):** No backend nós criámos a regra que liberta o passe gratuito (`is_eligible_for_trial`), mas a **tabela de horários** no HTML ainda tem a regra antiga ("chumbada") que desativa o botão de agendar se o aluno não tiver `active_subscriptions` (planos pagos). A tabela está a ignorar o passe livre.
2. **O Erro 404 (Página Não Encontrada):** O link `/shop/packages` está a tentar aceder ao ficheiro de rotas da Loja (`app/routes/shop.py`), mas a rota específica `/packages` ou o Blueprint inteiro da loja não está registado corretamente na aplicação.

Abaixo está o **PRD de Correção Definitiva** para desbloquear as vendas e os agendamentos.

---

# PRD: Desbloqueio do Agendamento Experimental e Fix 404

**Versão:** 2.7 (Bugfix Crítico)
**Arquivos Afetados:** `app/templates/student/schedule.html` e `app/routes/shop.py`

## Passo 1: Correção da Tabela de Agendamento (Frontend)

Vamos ensinar a tabela de horários a reconhecer a sessão experimental e a **ativar o botão de Agendar** para os novos clientes, enviando a palavra `experimental` em vez do ID de um plano pago.

**Ação:** Abra o ficheiro `app/templates/student/schedule.html` e localize a secção onde a tabela de horários é gerada (perto da linha onde diz `<td class="text-center">`). 

Substitua as antigas validações (`{% elif not active_subscriptions %}`) por este bloco corrigido:

```html
<td class="text-center">
    {% if schedule.user_booked %}
        <span class="badge bg-info">Já agendado</span>
    {% elif schedule.gender_restricted %}
        <button class="btn btn-sm btn-secondary" disabled title="{{ schedule.gender_message }}">
            <i class="fas fa-ban"></i> Restrito
        </button>
        <br><small class="text-danger">{{ schedule.gender_message }}</small>
    {% elif not parq_ok %}
        <a href="{{ url_for('health.fill_parq') }}" class="btn btn-sm btn-warning text-dark">
            Requer Avaliação
        </a>
    {% elif schedule.requires_ems and not schedule.ems_ok %}
        <a href="{{ url_for('health.fill_ems') }}" class="btn btn-sm btn-warning text-dark">
            Requer Anamnese
        </a>
    {% elif schedule.available_spots <= 0 %}
        <button class="btn btn-sm btn-secondary" disabled>Lotado</button>
        
    {% elif not active_subscriptions and not is_eligible_for_trial %}
        <button class="btn btn-sm btn-secondary" disabled>Sem créditos</button>
        
    {% else %}
        <form action="{{ url_for('student.book_class', schedule_id=schedule.id) }}" method="POST" class="d-inline booking-form">
            <input type="hidden" name="date" value="{{ selected_date.strftime('%Y-%m-%d') }}">
            
            <input type="hidden" name="subscription_id" class="subscription-input" 
                   value="{% if is_eligible_for_trial %}experimental{% elif active_subscriptions %}{{ active_subscriptions[0].id }}{% endif %}">
                   
            <button type="submit" class="btn btn-sm btn-primary fw-bold text-dark">
                <i class="fas fa-bolt me-1"></i> Agendar
            </button>
        </form>
    {% endif %}
</td>
```

---

## Passo 2: Ocultar o Alerta de Erro "Sem Créditos"

Ainda no mesmo ficheiro `schedule.html`, se o utilizador for novo, não lhe devemos mostrar o alerta amarelo a mandar comprar um plano, pois ele tem direito ao passe gratuito.

**Ação:** Vá ao topo do ficheiro `schedule.html` e garanta que o painel inteligente está escrito com esta validação:

```html
{% if active_subscriptions or is_eligible_for_trial %}
    <div class="card mb-4 border-0 shadow-sm" style="background: var(--bg-card, #0f172a);">
        <div class="card-body p-4">
            <h6 class="mb-3 fw-bold" style="color: var(--cyan-electric, #00f2ff);">
                <i class="fas fa-microchip me-2"></i> SEU ACESSO
            </h6>
            
            <div class="row g-3">
                {% if is_eligible_for_trial %}
                <div class="col-md-6">
                    <div class="form-check custom-radio-box p-3 rounded" style="border: 2px solid #00f2ff; background: rgba(0, 242, 255, 0.05);">
                        <input class="form-check-input subscription-radio" type="radio" name="subscription_select" id="sub_exp" value="experimental" checked>
                        <label class="form-check-label w-100 cursor-pointer text-white" for="sub_exp">
                            <strong style="color: #00f2ff;"><i class="fas fa-bolt text-warning me-1"></i> Primeira Sessão Gratuita</strong>
                        </label>
                    </div>
                </div>
                {% endif %}
                
                </div>
        </div>
    </div>
{% else %}
    <div class="alert alert-warning border-0" style="background: rgba(245, 158, 11, 0.1); color: #f59e0b;">
        <i class="fas fa-exclamation-triangle me-2"></i> Os seus créditos acabaram. 
        <a href="{{ url_for('shop.packages') }}" class="alert-link text-white fw-bold ms-1 text-decoration-none border-bottom">Ver Planos</a>.
    </div>
{% endif %}
```

---

## Passo 3: Correção do Erro 404 (`/shop/packages`)

Se a página dos pacotes diz "não encontrada", a rota está ausente do ficheiro da loja.

**Ação 1:** Abra o ficheiro `app/routes/shop.py` e adicione (ou substitua) a rota `/packages` desta forma exata:

```python
# app/routes/shop.py

from flask import Blueprint, render_template
from flask_login import login_required
from app.models.package import Package

shop_bp = Blueprint('shop', __name__, url_prefix='/shop')

@shop_bp.route('/packages')
@login_required
def packages():
    """Página de listagem de planos do Biohacking Studio"""
    # Procura todos os pacotes ativos na base de dados
    packages = Package.query.filter_by(is_active=True).order_by(Package.price.asc()).all()
    
    return render_template('shop/packages.html', packages=packages)

# Restante do seu código da loja (checkout, pagamento, etc...)
```

**Ação 2 (Garantia Máxima):** Abra o seu ficheiro `app/__init__.py` e confirme que a loja está a ser importada e registada. Deverá ter algo semelhante a isto nas configurações das rotas:

```python
# app/__init__.py
# Localize a secção onde os blueprints são registados:

from app.routes.shop import shop_bp
app.register_blueprint(shop_bp)
```

### O que acontece agora?
1. O seu novo Lead cadastra-se e vai para o calendário. O botão "+ Agendar" agora estará **AZUL e CLICÁVEL**, porque o sistema sabe que a variável `is_eligible_for_trial` existe.
2. Ao clicar, o sistema fará o agendamento a custo zero e moverá o cliente na aba do CRM.
3. Se os créditos dele acabarem mais tarde e ele clicar em "Ver Planos", o sistema encontrará perfeitamente o ficheiro `shop.py` e carregará a página dos pacotes sem o temido erro 404.