/**
 * Simulador de Creditos com suporte a FES
 * Calcula creditos necessarios e recomenda pacotes com destaque para FES
 */

document.addEventListener('DOMContentLoaded', function () {
    const sliders = document.querySelectorAll('.modality-slider');
    const totalCreditsDisplay = document.getElementById('total-credits');
    const recommendationContainer = document.getElementById('recommendation-content');
    const fesSavingsDiv = document.getElementById('fes-savings');
    const timeSavedSpan = document.getElementById('time-saved');

    function calculateTotal() {
        let totalPerMonth = 0;
        let totalFesSessions = 0;

        document.querySelectorAll('.simulator-row').forEach(row => {
            const cost = parseInt(row.dataset.cost);
            const frequency = parseInt(row.querySelector('.modality-slider').value);
            const isFes = row.dataset.isFes === 'true';

            // Atualiza display individual
            row.querySelector('.frequency-display').textContent = `${frequency}x/semana`;

            // Calculo: credito * freq * 4 semanas
            totalPerMonth += (cost * frequency * 4);

            // Conta sessoes FES
            if (isFes) {
                totalFesSessions += frequency;
            }
        });

        totalCreditsDisplay.textContent = totalPerMonth;

        // Atualiza economia de tempo FES
        updateFesSavings(totalFesSessions);

        // Recomenda pacote
        recommendPackage(totalPerMonth, totalFesSessions > 0);
    }

    function updateFesSavings(totalFesSessions) {
        if (!fesSavingsDiv || !timeSavedSpan) return;

        // Cada sessao FES economiza 70 minutos (1h30 - 20min)
        const timeSavedMinutes = totalFesSessions * 70 * 4; // por mes
        const timeSavedHours = (timeSavedMinutes / 60).toFixed(1);

        if (totalFesSessions > 0) {
            fesSavingsDiv.style.display = 'block';
            timeSavedSpan.textContent = timeSavedHours;
        } else {
            fesSavingsDiv.style.display = 'none';
        }
    }

    function recommendPackage(totalNeeded, hasFes) {
        if (totalNeeded === 0) {
            recommendationContainer.innerHTML = '<p style="color: var(--text-secondary);">Selecione suas modalidades para receber uma recomendacao.</p>';
            return;
        }

        // Se packagesData nao estiver disponivel globalmente
        if (!window.packagesData || window.packagesData.length === 0) {
            recommendationContainer.innerHTML = '<p>Nenhum plano disponivel no momento.</p>';
            return;
        }

        // Filtra pacotes que cobrem a necessidade
        let adequatePackages = window.packagesData.filter(pkg => pkg.credits >= totalNeeded);

        if (adequatePackages.length === 0) {
            // Se nenhum plano cobre o total, pega o maior plano
            const largestPackage = [...window.packagesData].sort((a, b) => b.credits - a.credits)[0];
            const hasFesIncluded = packageHasFes(largestPackage);

            recommendationContainer.innerHTML = `
                <div style="margin-top: 1rem; animation: fadeIn 0.5s ease-out;">
                    <span style="display: inline-block; padding: 0.4rem 1rem; background: #ef4444; border-radius: 50px; font-size: 0.8rem; font-weight: 700; margin-bottom: 1rem;">NECESSIDADE ALTA</span>
                    <h3>${largestPackage.name}</h3>
                    ${hasFesIncluded ? '<span style="display: inline-block; background: rgba(255,107,53,0.2); color: #ff6b35; padding: 0.25rem 0.75rem; border-radius: 50px; font-size: 0.75rem; font-weight: 600; margin-bottom: 0.5rem;"><i class="fas fa-bolt"></i> INCLUI FES</span>' : ''}
                    <p style="margin: 0.5rem 0 1.5rem; color: var(--text-secondary);">
                        Sua necessidade excede nossos planos padrao. Recomendamos o maior pacote disponivel.
                    </p>
                    <a href="/shop/checkout/${largestPackage.id}" class="btn-primary" style="padding: 0.75rem 2rem; font-size: 1rem;">ASSINAR ESTE PLANO</a>
                </div>
            `;
            return;
        }

        // Se usuario selecionou FES, prioriza pacotes com FES
        if (hasFes) {
            const fesPackages = adequatePackages.filter(pkg => packageHasFes(pkg));
            if (fesPackages.length > 0) {
                adequatePackages = fesPackages;
            }
        }

        // Ordena por melhor custo-beneficio (menor preco entre os que atendem)
        const recommended = adequatePackages.sort((a, b) => a.price - b.price)[0];
        const leftovers = recommended.credits - totalNeeded;
        const hasFesIncluded = packageHasFes(recommended);

        let fesMessage = '';
        if (hasFes && hasFesIncluded) {
            fesMessage = `
                <div style="background: rgba(255,107,53,0.1); border: 1px solid #ff6b35; border-radius: 12px; padding: 1rem; margin: 1rem 0;">
                    <p style="color: #ff6b35; margin: 0; font-weight: 600;">
                        <i class="fas fa-bolt"></i> Este pacote inclui sessoes FES!
                    </p>
                    <p style="color: var(--text-secondary); margin: 0.5rem 0 0; font-size: 0.9rem;">
                        Voce economizara tempo com a tecnologia de eletroestimulacao.
                    </p>
                </div>
            `;
        } else if (hasFes && !hasFesIncluded) {
            // Sugere upgrade para pacote com FES
            const fesUpgrade = window.packagesData.find(pkg => packageHasFes(pkg) && pkg.credits >= totalNeeded);
            if (fesUpgrade) {
                fesMessage = `
                    <div style="background: rgba(255,107,53,0.05); border: 1px dashed #ff6b35; border-radius: 12px; padding: 1rem; margin: 1rem 0;">
                        <p style="color: #ff6b35; margin: 0; font-weight: 600;">
                            <i class="fas fa-arrow-up"></i> Upgrade sugerido: ${fesUpgrade.name}
                        </p>
                        <p style="color: var(--text-secondary); margin: 0.5rem 0 0; font-size: 0.9rem;">
                            Inclui sessoes FES para potencializar seus resultados.
                        </p>
                    </div>
                `;
            }
        }

        recommendationContainer.innerHTML = `
            <div style="margin-top: 1rem; animation: fadeIn 0.5s ease-out;">
                <span style="display: inline-block; padding: 0.4rem 1rem; background: var(--accent); border-radius: 50px; font-size: 0.8rem; font-weight: 700; margin-bottom: 1rem;">RECOMENDADO</span>
                ${hasFesIncluded ? '<span style="display: inline-block; background: rgba(255,107,53,0.2); color: #ff6b35; padding: 0.25rem 0.75rem; border-radius: 50px; font-size: 0.75rem; font-weight: 600; margin-left: 0.5rem;"><i class="fas fa-bolt"></i> INCLUI FES</span>' : ''}
                <h3 style="font-size: 1.75rem; color: white; margin-top: 0.5rem;">${recommended.name}</h3>
                <p style="margin: 0.5rem 0; color: var(--text-secondary);">
                    Cobre seus treinos e ainda sobram <strong style="color: var(--accent);">${leftovers} creditos</strong> para experimentar algo novo!
                </p>
                ${fesMessage}
                <a href="/shop/checkout/${recommended.id}" class="btn-primary" style="padding: 0.75rem 2rem; font-size: 1rem; margin-top: 1rem; display: inline-block;">
                    <i class="fas fa-shopping-cart"></i> ESCOLHER ESTE PLANO
                </a>
            </div>
        `;
    }

    /**
     * Verifica se um pacote inclui beneficios FES
     */
    function packageHasFes(pkg) {
        if (!pkg.extra_benefits) return false;

        const benefits = Array.isArray(pkg.extra_benefits) ? pkg.extra_benefits : [];
        return benefits.some(b =>
            b.toLowerCase().includes('fes') ||
            b.toLowerCase().includes('eletroestimulacao')
        );
    }

    // Event listeners
    sliders.forEach(slider => {
        slider.addEventListener('input', calculateTotal);
    });

    // Inicializa
    calculateTotal();
});

// Animacao de entrada
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);
