const Dashboard = {
    init: async () => {
        await Dashboard.loadSummary();
        await Dashboard.loadCharts();
    },

    loadSummary: async () => {
        try {
            const res = await Utils.api.get(CONFIG.ENDPOINTS.DASHBOARD);
            if (res && res.success) {
                Dashboard.renderKPIs(res.data);
            }
        } catch (e) {
            console.error("Failed to load dashboard summary", e);
        }
    },

    renderKPIs: (data) => {
        const container = document.getElementById('kpi-container');

        const kpis = [
            { label: 'Total Sales', value: Utils.formatCurrency(data.sales_total) },
            { label: 'Total Purchases', value: Utils.formatCurrency(data.purchase_total) },
            { label: 'Receivables', value: Utils.formatCurrency(data.receivables) },
            { label: 'Payables', value: Utils.formatCurrency(data.payables) },
            { label: 'Cash Balance', value: Utils.formatCurrency(data.cash_balance) },
            { label: 'Bank Balance', value: Utils.formatCurrency(data.bank_balance) },
            { label: 'GST Payable', value: Utils.formatCurrency(data.gst_payable) },
            { label: 'TDS Deducted', value: Utils.formatCurrency(data.tds_deducted) },
        ];

        container.innerHTML = kpis.map(k => `
            <div class="kpi-card">
                <h3>${k.label}</h3>
                <div class="value">${k.value}</div>
            </div>
        `).join('');
    },

    loadCharts: async () => {
        try {
            const res = await Utils.api.get(CONFIG.ENDPOINTS.CHARTS);
            if (res && res.success) {
                Dashboard.renderCharts(res.data);
            }
        } catch (e) {
            console.error("Failed to load charts", e);
        }
    },

    renderCharts: (data) => {
        // Sales vs Purchase Trend
        const ctx = document.getElementById('salesChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar', // Changed to Bar for better visibility of single data points
            data: {
                labels: data.sales_vs_purchase.labels,
                datasets: [
                    {
                        label: 'Sales',
                        data: data.sales_vs_purchase.sales,
                        backgroundColor: '#2563eb', // Solid Blue
                        borderRadius: 4
                    },
                    {
                        label: 'Purchases',
                        data: data.sales_vs_purchase.purchases,
                        backgroundColor: '#10b981', // Solid Green
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: true, text: 'Sales vs Purchase (Monthly)' }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

        // Credit (Payables) vs Debit (Receivables)
        if (data.credit_debit) {
            const ctx2 = document.getElementById('creditDebitChart').getContext('2d');

            // Check if data is all zero
            const totalVal = data.credit_debit.data.reduce((a, b) => a + b, 0);
            const chartData = totalVal > 0 ? data.credit_debit.data : [1]; // Placeholder if empty
            const chartColors = totalVal > 0 ? ['#ef4444', '#3b82f6'] : ['#e2e8f0']; // Gray if empty
            const chartLabels = totalVal > 0 ? ["Payable", "Receivable"] : ["No Outstanding Data"];

            new Chart(ctx2, {
                type: 'doughnut',
                data: {
                    labels: chartLabels,
                    datasets: [{
                        data: chartData,
                        backgroundColor: chartColors,
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: { display: true, text: 'Outstanding Balance' },
                        legend: { position: 'bottom' },
                        tooltip: { enabled: totalVal > 0 }
                    }
                }
            });
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    Dashboard.init();
});
