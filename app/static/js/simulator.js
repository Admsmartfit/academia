/**
 * Lógica do simulador de créditos
 */

document.addEventListener('DOMContentLoaded', function () {
    const sliders = document.querySelectorAll('.modality-slider');
    const totalCreditsDisplay = document.getElementById('total-credits');
    const recommendationContainer = document.getElementById('recommendation-content');

    function calculateTotal() {
        let totalPerMonth = 0;

        document.querySelectorAll('.simulator-row').forEach(row => {
            const cost = parseInt(row.dataset.cost);
            const frequency = parseInt(row.querySelector('.modality-slider').value);

            // Atualiza display individual
            row.querySelector('.frequency-display').textContent = `${frequency}x/semana`;

            // Cálculo: crédito * freq * 4 semanas
            totalPerMonth += (cost * frequency * 4);
        });

        totalCreditsDisplay.textContent = totalPerMonth;
        recommendPackage(totalPerMonth);
    }

    function recommendPackage(totalNeeded) {
        if (totalNeeded === 0) {
            recommendationContainer.innerHTML = '<p style="color: var(--text-secondary);">Selecione suas modalidades para receber uma recomendação.</p>';
            return;
        }

        // Se packagesData não estiver disponível globalmente (do JSON inlined)
        if (!window.packagesData || window.packagesData.length === 0) {
            recommendationContainer.innerHTML = '<p>Nenhum plano disponível no momento.</p>';
            return;
        }

        // Filtra pacotes que cobrem a necessidade
        const adequatePackages = window.packagesData.filter(pkg => pkg.credits >= totalNeeded);

        if (adequatePackages.length === 0) {
            // Se nenhum plano cobre o total, pega o maior plano
            const largestPackage = [...window.packagesData].sort((a, b) => b.credits - a.credits)[0];

            recommendationContainer.innerHTML = `
                <div style="margin-top: 1rem; animation: fadeIn 0.5s ease-out;">
                    <span style="display: inline-block; padding: 0.4rem 1rem; background: #ef4444; border-radius: 50px; font-size: 0.8rem; font-weight: 700; margin-bottom: 1rem;">NECESSIDADE ALTA</span>
                    <h3>${largestPackage.name}</h3>
                    <p style="margin: 0.5rem 0 1.5rem; color: var(--text-secondary);">
                        Sua necessidade excede nossos planos padrão. Recomendamos o maior pacote disponível e renovação frequente.
                    </p>
                    <a href="/shop/checkout/${largestPackage.id}" class="btn-primary" style="padding: 0.75rem 2rem; font-size: 1rem;">ASSINAR ESTE PLANO</a>
                </div>
            `;
            return;
        }

        // Encontra o mais barato entre os que cobrem o total (custo-benefício)
        const recommended = adequatePackages.sort((a, b) => a.price - b.price)[0];
        const leftovers = recommended.credits - totalNeeded;

        recommendationContainer.innerHTML = `
            <div style="margin-top: 1rem; animation: fadeIn 0.5s ease-out;">
                <span style="display: inline-block; padding: 0.4rem 1rem; background: var(--accent); border-radius: 50px; font-size: 0.8rem; font-weight: 700; margin-bottom: 1rem;">RECOMENDADO</span>
                <h3 style="font-size: 1.75rem; color: white;">${recommended.name}</h3>
                <p style="margin: 0.5rem 0 1.5rem; color: var(--text-secondary);">
                    Cobre seus treinos e ainda sobram <strong>${leftovers} créditos</strong> para experimentar algo novo!
                </p>
                <a href="/shop/checkout/${recommended.id}" class="btn-primary" style="padding: 0.75rem 2rem; font-size: 1rem;">ESCOLHER ESTE PLANO</a>
            </div>
        `;
    }

    // Event listeners
    sliders.forEach(slider => {
        slider.addEventListener('input', calculateTotal);
    });

    // Inicializa
    calculateTotal();
});

// Animação de entrada
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);
