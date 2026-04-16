PRD: Correção do Calendário e Rebranding (Biohacking Studio)
Versão: 1.2 (Bugfix e Identidade Visual)
Módulos Afetados: Área do Aluno (/student), Templates Base e Configurações Globais.

1. Visão Geral
Este documento descreve as etapas para corrigir o bug de renderização do calendário na nova interface de agendamento (Two-Pane Layout) e aplicar a mudança global de nomenclatura de "Academia" (ou termos genéricos) para "Biohacking Studio", integrando a logomarca da empresa no sistema.

Etapa 1: Correção do Bug do Calendário (Flatpickr)
1.1. Causa Raiz
O Flatpickr constrói o calendário injetando HTML ao lado do input original. Se o input tem a classe .d-none (Bootstrap), ele pode herdar comportamentos que quebram a visibilidade. Além disso, se o base.html não possuir uma tag {% block scripts %}, o JavaScript não será renderizado na página final.

1.2. Solução no arquivo app/templates/student/schedule_v2.html
Modificaremos a injeção do CSS e JS garantindo que eles carreguem corretamente dentro da página, e ajustaremos a tag do input.

Ação: Substitua completamente a estrutura do container do calendário e mova os scripts para o final do {% block content %}.

HTML
<div class="card">
    <div class="card-body p-3 d-flex justify-content-center">
        <div id="inline-calendar"></div>
    </div>
    <div class="card-footer bg-white text-muted small text-center">
        <span class="badge bg-success opacity-75">&nbsp;</span> Disponível 
        <span class="badge bg-warning opacity-75 text-dark ms-2">&nbsp;</span> Poucas vagas
    </div>
</div>
Ação: No final do arquivo schedule_v2.html (logo antes de fechar o {% block content %}), insira as dependências diretamente para garantir a execução:

HTML
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
    <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
    <script src="https://npmcdn.com/flatpickr/dist/l10n/pt.js"></script>

    <script>
    document.addEventListener("DOMContentLoaded", function() {
        let heatmapData = {};
        let selectedDateStr = new Date().toISOString().split('T')[0];
        
        // Renderizar numa div em vez de input evita bugs de ocultação
        const fp = flatpickr("#inline-calendar", {
            inline: true,
            locale: "pt",
            defaultDate: "today",
            minDate: "today",
            onChange: function(selectedDates, dateStr, instance) {
                selectedDateStr = dateStr;
                if(typeof fetchSlots === "function") fetchSlots(dateStr, dateStr);
            },
            onMonthChange: function(selectedDates, dateStr, instance) {
                if(typeof fetchHeatmap === "function") fetchHeatmap(instance.currentYear, instance.currentMonth);
            },
            onReady: function(selectedDates, dateStr, instance) {
                if(typeof fetchHeatmap === "function") fetchHeatmap(instance.currentYear, instance.currentMonth);
                if(typeof fetchSlots === "function") fetchSlots(dateStr, dateStr);
            },
            onDayCreate: function(dObj, dStr, fp, dayElem) {
                const dateString = dayElem.dateObj.toISOString().split('T')[0];
                if (heatmapData[dateString]) {
                    dayElem.classList.add(`status-${heatmapData[dateString].status}`);
                }
            }
        });

        // (Mantenha aqui as funções fetchHeatmap, fetchSlots e renderSlots do PRD anterior)
    });
    </script>
{% endblock %}
Etapa 2: Atualização de Branding (Biohacking Studio)
O sistema deve refletir a identidade corporativa. Removeremos jargões genéricos e implementaremos a logo do Studio.

2.1. Variáveis e Títulos (Backend & Jinja)
Onde houver variáveis de sistema ou configurações de nome, elas devem ser padronizadas.

Arquivo alvo: config.py ou chamadas no __init__.py.

Ação: Garantir que o nome da aplicação (SITE_NAME ou equivalente) retorne Biohacking Studio.

Ação: Em app/templates/base.html, atualizar a tag de título principal:

HTML
<title>{% block title %}{% endblock %} | Biohacking Studio</title>
2.2. Atualização da Barra de Navegação (navbar.html)
Substituir o texto padrão no cabeçalho pelo uso de uma logomarca oficial, com fallback elegante (caso a imagem demore a carregar).

Arquivo alvo: app/templates/includes/navbar.html (ou o arquivo que contém o menu superior no seu projeto).

Ação:

HTML
<a class="navbar-brand d-flex align-items-center" href="{{ url_for('student.dashboard') }}">
    <img src="{{ url_for('static', filename='img/logo.png') }}" alt="Biohacking Studio" height="40" class="d-inline-block align-text-top me-2" onerror="this.style.display='none';">
    <span class="fw-bold text-primary">Biohacking Studio</span>
</a>
2.3. Renomear Termos de UI (User Interface)
Uma varredura e substituição devem ser feitas nas páginas principais (Login, Dashboard, Headers) para trocar nomenclaturas.

Regras de Substituição Textual:

"Academia" ou "Academia System" ➔ "Biohacking Studio"

"Bem-vindo à Academia" ➔ "Bem-vindo ao Biohacking Studio"

"Minha Academia" ➔ "Meu Studio"

"biohack" (minúsculo/incompleto) ➔ "Biohacking Studio"

Arquivos Principais para Varredura:

app/templates/auth/login.html e register.html (Títulos de formulário).

app/templates/student/dashboard.html (Mensagens de boas-vindas).

app/templates/admin/dashboard.html (Visão geral do administrador).

2.4. Atualização de E-mails e Notificações (WhatsApp/CRM)
Se o sistema possui disparos automáticos, o texto das templates precisa refletir a marca.

Arquivo alvo (exemplo): Modelos de whatsapp_template.py ou funções no notification_service.py.

Ação: O texto base dos gatilhos de WhatsApp deve dizer:

"Olá {nome}, seu agendamento no Biohacking Studio está confirmado para..." ao invés de "na academia".

3. Plano de Ação para Execução (Resumo)
Copiar a imagem logo.png fornecida pelo designer para a pasta app/static/img/.

Aplicar as mudanças de id e injeção de script no schedule_v2.html para resolver a ausência do calendário na tela.

Rodar um Find and Replace global no diretório de templates (app/templates/) substituindo as palavras-chave conforme as regras definidas na Seção 2.3.

Substituir o cabeçalho no arquivo principal da navbar.

Recarregar a aplicação e limpar o cache do navegador (Ctrl+F5) para testar o carregamento do CSS/JS do calendário e a nova logo.