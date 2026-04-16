PRD: Redesign da Loja (High-Ticket Pricing Page)
Versão: 3.0 (Marketing & CRO)
Ficheiro Afetado: app/templates/shop/packages.html

1. Estratégia de Design & Marketing Aplicada
Nomeação Premium: Em vez de "Comprar Pacotes", mudamos o texto para "Protocolos de Performance". Aumenta instantaneamente o valor percebido.

Decoy Effect (Efeito Isco): Destacamos visualmente um pacote (geralmente o plano do meio ou o que tem a flag is_featured), colocando-lhe uma faixa de "RECOMENDADO" e preenchendo o botão com o Neon Ciano, enquanto os outros pacotes recebem botões transparentes (btn-outline).

Imersão Visual: A grelha de pacotes vai flutuar sobre a textura de Biohacking (fundo azul profundo com brilhos radiais) e a logomarca de água do estúdio, eliminando o branco de "hospital" do Bootstrap padrão.

Tipografia de Preço: O símbolo "R$" fica pequeno, os números principais ficam gigantes (fonte Outfit com peso 900), e os cêntimos ficam em cinzento. É uma técnica psicológica para o preço parecer menor.

Passo Único: Substituição do Template da Loja
Ação: Substitua completamente o conteúdo do seu ficheiro app/templates/shop/packages.html pelo código abaixo:

HTML
{% extends "base.html" %}

{% block title %}Protocolos de Performance | Biohacking Studio{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/landing.css') }}">
<style>
    /* Ajustes específicos de E-commerce Biohacking */
    body {
        background-color: var(--bg-deep, #05070a);
        color: var(--text-main, #f8fafc);
    }
    
    .protocol-card {
        background: var(--bg-card, #0f172a);
        border: 1px solid rgba(0, 242, 255, 0.1);
        border-radius: 16px;
        padding: 40px 30px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    .protocol-card:hover {
        transform: translateY(-10px);
        border-color: var(--cyan-electric, #00f2ff);
        box-shadow: 0 10px 40px rgba(0, 242, 255, 0.15);
    }
    
    /* Destaque para o plano mais rentável (CRO) */
    .protocol-card.featured {
        border-color: rgba(0, 242, 255, 0.5);
        background: linear-gradient(180deg, #0f172a 0%, #0a101f 100%);
        transform: scale(1.05); /* Ligeiramente maior que os outros */
        z-index: 2;
    }
    
    .protocol-card.featured:hover {
        transform: scale(1.05) translateY(-10px);
    }

    .protocol-badge {
        position: absolute;
        top: 25px;
        right: -35px;
        background: var(--cyan-electric, #00f2ff);
        color: #000;
        padding: 5px 40px;
        font-weight: 800;
        font-size: 0.75rem;
        transform: rotate(45deg);
        letter-spacing: 2px;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.5);
    }
    
    /* Tipografia Psicológica de Preço */
    .price-tag {
        font-family: 'Outfit', sans-serif;
        font-size: 3.5rem;
        font-weight: 900;
        line-height: 1;
        margin: 20px 0;
        color: white;
    }
    
    .price-currency {
        font-size: 1.5rem;
        vertical-align: top;
        color: var(--cyan-electric, #00f2ff);
        margin-right: 5px;
    }
    
    .feature-list {
        list-style: none;
        padding: 0;
        margin: 30px 0;
        flex-grow: 1;
    }
    
    .feature-list li {
        margin-bottom: 15px;
        color: var(--text-dim, #94a3b8);
        display: flex;
        align-items: center;
        font-size: 0.95rem;
    }
    
    .feature-list li i {
        color: var(--cyan-electric, #00f2ff);
        margin-right: 12px;
        font-size: 1.1rem;
    }

    /* Ajuste para mobile */
    @media (max-width: 992px) {
        .protocol-card.featured {
            transform: scale(1);
        }
        .protocol-card.featured:hover {
            transform: translateY(-5px);
        }
    }
</style>
{% endblock %}

{% block content %}
<div class="bg-brand-texture" style="min-height: 100vh; padding: 60px 0; position: relative;">
    <div class="logo-watermark" style="top: 10%; right: -10%;"></div>

    <div class="container" style="max-width: 1100px; position: relative; z-index: 2;">
        
        <div class="text-center mb-5 pb-3">
            <div style="display: inline-block; padding: 6px 16px; background: rgba(0, 242, 255, 0.1); border: 1px solid var(--cyan-glow, rgba(0,242,255,0.4)); border-radius: 50px; color: var(--cyan-electric, #00f2ff); font-size: 0.75rem; letter-spacing: 3px; margin-bottom: 20px; font-weight: 600;">
                <i class="fas fa-shopping-cart me-2"></i> CHECKOUT SEGURO
            </div>
            <h1 style="font-size: clamp(2.5rem, 5vw, 4rem); font-weight: 900; margin-bottom: 15px; font-family: 'Outfit', sans-serif;">
                PROTOCOLOS DE <span style="color: var(--cyan-electric, #00f2ff); text-shadow: 0 0 30px rgba(0,242,255,0.4);">PERFORMANCE</span>
            </h1>
            <p style="color: var(--text-dim, #94a3b8); font-size: 1.15rem; max-width: 600px; margin: 0 auto;">
                Escolha o plano ideal para recodificar a sua biologia. Sessões monitorizadas de 20 minutos com tecnologia FES.
            </p>
        </div>

        <div class="row g-4 justify-content-center align-items-center">
            {% for package in packages %}
            {% set is_highlighted = package.is_featured or (loop.index == 2 and packages|length == 3) %}
            
            <div class="col-lg-4 col-md-6">
                <div class="protocol-card {% if is_highlighted %}featured{% endif %}">
                    
                    {% if is_highlighted %}
                    <div class="protocol-badge">RECOMENDADO</div>
                    {% endif %}
                    
                    <h3 style="font-family: 'Outfit', sans-serif; font-weight: 800; font-size: 1.5rem; margin-bottom: 5px;">{{ package.name }}</h3>
                    <p style="color: var(--cyan-electric, #00f2ff); font-weight: 600; font-size: 0.9rem; letter-spacing: 1px;">
                        <i class="fas fa-bolt text-warning me-1"></i> {{ package.credits }} SESSÕES
                    </p>
                    
                    <div class="price-tag">
                        <span class="price-currency">R$</span>{{ "%.0f"|format(package.price) }}<span style="font-size: 1.2rem; color: #64748b; font-weight: 600;">,{{ "%.2f"|format(package.price)|string|slice(-2) }}</span>
                    </div>
                    
                    {% if package.description %}
                    <p style="color: var(--text-dim, #94a3b8); font-size: 0.9rem; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 20px; min-height: 60px;">
                        {{ package.description }}
                    </p>
                    {% else %}
                    <div style="border-bottom: 1px solid rgba(255,255,255,0.05); margin-bottom: 20px;"></div>
                    {% endif %}
                    
                    <ul class="feature-list">
                        <li><i class="fas fa-check-circle"></i> Válido por {{ package.validity_days }} dias</li>
                        <li><i class="fas fa-check-circle"></i> Acesso total a FES (Ezbody)</li>
                        <li><i class="fas fa-check-circle"></i> Agendamento na App Biohacking</li>
                        <li><i class="fas fa-check-circle"></i> Suporte Personalizado</li>
                    </ul>
                    
                    <a href="{{ url_for('shop.package_detail', id=package.id) }}" class="btn-neon {% if not is_highlighted %}btn-outline{% endif %} w-100 justify-content-center mt-auto" style="padding: 15px;">
                        INICIAR PROTOCOLO
                    </a>
                </div>
            </div>
            {% else %}
            <div class="col-12 text-center py-5">
                <i class="fas fa-box-open fa-4x mb-3 opacity-25" style="color: var(--text-dim, #94a3b8);"></i>
                <h4 style="color: var(--text-dim, #94a3b8);">A carregar novos protocolos...</h4>
                <p class="text-muted">Nenhum plano disponível de momento.</p>
            </div>
            {% endfor %}
        </div>
        
    </div>
</div>
{% endblock %}