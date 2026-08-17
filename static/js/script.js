/* ==========================================================================
   SMARTPOST - AI-POWERED POST OFFICE MANAGEMENT AND SMART DELIVERY SYSTEM
   Vanilla JavaScript Client Logic
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Sidebar Toggle
    const mobileToggle = document.getElementById('mobileToggle');
    const sidebar = document.getElementById('sidebar');

    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }

    // 2. Password Visibility Toggle
    const passwordToggles = document.querySelectorAll('.toggle-password');
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const targetInput = document.getElementById(targetId);
            if (targetInput) {
                if (targetInput.type === 'password') {
                    targetInput.type = 'text';
                    this.textContent = '👁️‍🗨️ Hide';
                } else {
                    targetInput.type = 'password';
                    this.textContent = '👁️ Show';
                }
            }
        });
    });

    // 3. Dynamic Postage Calculator on Booking Page
    const serviceSelect = document.getElementById('service_type');
    const weightInput = document.getElementById('weight');
    const declaredValueInput = document.getElementById('declared_value');

    if (serviceSelect && weightInput) {
        const updateCalculatedFees = () => {
            const service = serviceSelect.value || 'Ordinary Post';
            const weight = parseFloat(weightInput.value) || 0.5;
            const declaredValue = parseFloat(declaredValueInput ? declaredValueInput.value : 0) || 0;

            const serviceRates = {
                'Ordinary Post': { base: 15.00, perKg: 10.00, service: 5.00 },
                'Speed Post': { base: 35.00, perKg: 20.00, service: 10.00 },
                'Registered Post': { base: 25.00, perKg: 15.00, service: 8.00 },
                'Parcel': { base: 30.00, perKg: 18.00, service: 8.00 },
                'Express Parcel': { base: 50.00, perKg: 25.00, service: 15.00 },
                'International Parcel': { base: 100.00, perKg: 50.00, service: 30.00 }
            };

            const rate = serviceRates[service] || serviceRates['Ordinary Post'];
            const baseCharge = rate.base;
            const weightCharge = Math.round(weight * rate.perKg * 100) / 100;
            const serviceCharge = rate.service;

            let additionalCharge = 0.0;
            if (declaredValue > 500) {
                additionalCharge += Math.round(declaredValue * 0.01 * 100) / 100;
            }
            if (service === 'International Parcel') {
                additionalCharge += 25.00;
            }

            const total = Math.round((baseCharge + weightCharge + serviceCharge + additionalCharge) * 100) / 100;

            const baseEl = document.getElementById('calc_base');
            const weightEl = document.getElementById('calc_weight');
            const serviceEl = document.getElementById('calc_service');
            const addEl = document.getElementById('calc_additional');
            const totalEl = document.getElementById('calc_total');

            if (baseEl) baseEl.textContent = `$${baseCharge.toFixed(2)}`;
            if (weightEl) weightEl.textContent = `$${weightCharge.toFixed(2)}`;
            if (serviceEl) serviceEl.textContent = `$${serviceCharge.toFixed(2)}`;
            if (addEl) addEl.textContent = `$${additionalCharge.toFixed(2)}`;
            if (totalEl) totalEl.textContent = `$${total.toFixed(2)}`;
        };

        serviceSelect.addEventListener('change', updateCalculatedFees);
        weightInput.addEventListener('input', updateCalculatedFees);
        if (declaredValueInput) declaredValueInput.addEventListener('input', updateCalculatedFees);

        updateCalculatedFees(); // Initial calc
    }

    // 4. Alert Auto-dismiss after 5s
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 6000);
    });
});

// Helper function for interactive Chart initialization
function initChart(canvasId, type, labels, data, colors, title) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (typeof Chart === 'undefined') {
        console.warn('Chart.js CDN not loaded yet.');
        return;
    }

    new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: [{
                label: title || 'Count',
                data: data,
                backgroundColor: colors,
                borderColor: 'rgba(255, 255, 255, 0.2)',
                borderWidth: 1,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0', font: { family: 'Plus Jakarta Sans' } }
                }
            },
            scales: (type === 'pie' || type === 'doughnut') ? {} : {
                x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
                y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255, 255, 255, 0.05)' } }
            }
        }
    });
}
