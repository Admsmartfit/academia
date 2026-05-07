Prompt de Limpeza e Refatoração: Biohacking Studio
Contexto: Sou o proprietário do "Biohacking Studio", um sistema web em Python (Flask) e HTML (Jinja2/Bootstrap 5). O código atual possui redundâncias de testes, arquivos órfãos e estilos CSS repetidos.
Objetivo: Executar uma auditoria profunda e limpeza técnica para tornar o código 100% profissional, modular e escalável.

Etapa 1: Auditoria de Arquivos e Redundâncias
"Analise a estrutura de pastas do projeto. Identifique e liste:

Arquivos de template (HTML) que parecem ser versões antigas ou duplicadas (ex: schedule.html vs schedule_v2.html).

Scripts de teste ou 'seed' que não são mais necessários em produção (ex: seed_data.py, validate_phase_10.py).

Rotas no Flask que realizam a mesma função em Blueprints diferentes.
Ação: Sugira quais arquivos podem ser deletados com segurança e quais rotas devem ser unificadas."

Etapa 2: Unificação Estética (CSS & Variáveis)
"Audite todos os arquivos HTML e o landing.css.

Localize todas as ocorrências de cores hardcoded (especialmente o antigo laranja #FF6B35 ou variações).

Substitua-as pela variável centralizada --accent: #00f2ff (Ciano Elétrico) ou similares definidas no :root.

Extraia blocos de <style> internos de templates como dashboard.html e instructor/dashboard.html e mova-os para um novo arquivo CSS global chamado studio_internal.css.
Critério: O HTML deve ficar limpo, contendo apenas estrutura, enquanto todo o 'look & feel' deve vir de arquivos .css externos."

Etapa 3: Refatoração da Lógica de Negócio (Services)
"Mova a inteligência do sistema das Rotas (controllers) para a camada de Serviços:

Toda lógica de cálculo de créditos e validação de 'Passe Livre' deve sair de routes/student.py e ir para services/credit_service.py.

Toda automação de mudança de status no CRM (Kanban) ao agendar aulas deve ir para services/crm_service.py.
Objetivo: As rotas devem apenas receber a requisição e chamar uma função do Service, diminuindo o tamanho dos arquivos de rotas e facilitando a manutenção."

Etapa 4: Otimização de Performance e Templates
"Analise os loops {% for %} nos templates de agenda e dashboard:

Verifique se o datalist de alunos ou modalidades está sendo carregado dentro de loops (gerando HTML gigante). Mova-os para fora do loop e use IDs únicos.

Identifique consultas ao banco de dados (SQLAlchemy) que estão sendo feitas dentro do template (N+1 problem) e mova a busca dos dados para o view_function no Python usando .options(joinedload(...)).
Meta: Reduzir o tamanho do DOM e o número de queries ao banco de dados por carregamento de página."

Etapa 5: Limpeza de Ambiente e Dependências
"Finalize a limpeza:

Verifique o arquivo requirements.txt e identifique bibliotecas que não estão sendo importadas em nenhum lugar do código.

Remova comentários de código 'morto' (blocos de código comentados que não servem mais).

Padronize os nomes de funções para snake_case e classes para PascalCase conforme o PEP 8.

Gere um relatório final das melhorias realizadas."

Dicas para execução com o Google Antigravity:
Execute uma etapa de cada vez: Não tente fazer tudo em um único comando. Peça para a IA analisar a Etapa 1, confirme as deleções e só então passe para a Etapa 2.

Backup: Antes de começar, garanta que o seu repositório Git está com o commit em dia.

Teste de Regressão: Após cada etapa, acesse o sistema no telemóvel e no PC para garantir que os agendamentos e o financeiro continuam funcionando.