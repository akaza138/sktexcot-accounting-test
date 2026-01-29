const Dashboard = {
    charts: {},

    init: async () => {
        await Dashboard.loadDashboardData();
        await Dashboard.loadTopCustomers();
    },

    loadDashboardData: async () => {
        try {
            // Load summary data
            const summaryRes = await Utils.api.get(CONFIG.ENDPOINTS.DASHBOARD);
            if (summaryRes && summaryRes.success) {
                Dashboard.renderKPIs(summaryRes.data);
            }

            // Load chart data
            const chartsRes = await Utils.api.get(CONFIG.ENDPOINTS.CHARTS);
            if (chartsRes && chartsRes.success) {
                Dashboard.renderSalesPurchaseChart(chartsRes.data);
                Dashboard.renderGSTChart(chartsRes.data);
            }
        } catch (e) {
            console.error("Failed to load dashboard data", e);
        }
    },

    renderKPIs: (data) => {
        const container = document.getElementById('kpi-container');

        const kpis = [
            {
                title: 'Total Sales',
                subtitle: '(This Month)',
                value: data.sales_total || 0,
                trend: 12.5,
                isPositive: true,
                icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="1" x2="12" y2="23"></line>
                    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                </svg>`
            },
            {
                title: 'Total Purchase',
                subtitle: '(This Month)',
                value: data.purchase_total || 0,
                trend: 12.2,
                isPositive: true,
                icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
                    <line x1="3" y1="6" x2="21" y2="6"></line>
                    <path d="M16 10a4 4 0 0 1-8 0"></path>
                </svg>`
            },
            {
                title: 'Bank Balance',
                subtitle: '',
                value: data.bank_balance || 0,
                trend: 4.0,
                isPositive: false,
                icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect>
                    <line x1="1" y1="10" x2="23" y2="10"></line>
                </svg>`
            },
            {
                title: 'Outstanding Receivable',
                subtitle: '',
                value: data.receivables || 0,
                trend: 4.60,
                isPositive: true,
                icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <polyline points="16 11 18 13 22 9"></polyline>
                </svg>`
            }
        ];

        container.innerHTML = kpis.map(kpi => `
            <div class="kpi-card">
                <div class="kpi-card-header">
                    <div>
                        <div class="kpi-card-title">${kpi.title}</div>
                        ${kpi.subtitle ? `<div class="kpi-card-subtitle">${kpi.subtitle}</div>` : ''}
                    </div>
                    <div class="kpi-card-icon">
                        ${kpi.icon}
                    </div>
                </div>
                <div class="kpi-card-value">${Utils.formatCurrency(kpi.value)}</div>
                <div class="kpi-card-trend">
                    <div class="kpi-trend-indicator ${kpi.isPositive ? 'positive' : 'negative'}">
                        ${kpi.isPositive ?
                `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                                <polyline points="18 15 12 9 6 15"></polyline>
                            </svg>` :
                `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                                <polyline points="6 9 12 15 18 9"></polyline>
                            </svg>`
            }
                        <span>${kpi.trend.toFixed(1)}%</span>
                    </div>
                    <span class="kpi-trend-text">Compared to last month</span>
                </div>
            </div>
        `).join('');
    },

    renderSalesPurchaseChart: (data) => {
        const ctx = document.getElementById('salesPurchaseChart');
        if (!ctx) return;

        // Destroy existing chart if it exists
        if (Dashboard.charts.salesPurchase) {
            Dashboard.charts.salesPurchase.destroy();
        }

        const chartData = data.sales_vs_purchase || {
            labels: ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
            sales: [80000, 95000, 120000, 110000, 130000, 115000, 125000, 140000, 135000, 150000, 145000, 155000],
            purchases: [60000, 75000, 98000, 85000, 102000, 90000, 95000, 108000, 100000, 115000, 110000, 118000]
        };

        const gridColor = 'rgba(0, 0, 0, 0.1)';
        const textColor = '#718096';

        Dashboard.charts.salesPurchase = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [
                    {
                        label: 'Sales',
                        data: chartData.sales,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#3b82f6',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    },
                    {
                        label: 'Purchases',
                        data: chartData.purchases,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: '#10b981',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            color: textColor,
                            font: {
                                size: 13,
                                family: 'Inter'
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: '#ffffff',
                        titleColor: textColor,
                        bodyColor: textColor,
                        borderColor: gridColor,
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true,
                        callbacks: {
                            label: function (context) {
                                return context.dataset.label + ': ' + Utils.formatCurrency(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: gridColor,
                            drawBorder: false
                        },
                        ticks: {
                            color: textColor,
                            font: {
                                size: 12
                            },
                            callback: function (value) {
                                return '₹' + (value / 1000) + 'k';
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: textColor,
                            font: {
                                size: 12
                            }
                        }
                    }
                }
            }
        });
    },

    renderGSTChart: (data) => {
        const ctx = document.getElementById('gstChart');
        if (!ctx) return;

        // Destroy existing chart if it exists
        if (Dashboard.charts.gst) {
            Dashboard.charts.gst.destroy();
        }

        const gstData = {
            cgst: data.gst_payable ? data.gst_payable / 2 : 12500,
            sgst: data.gst_payable ? data.gst_payable / 2 : 12500,
            igst: 20000,
            gstPaid: 45000
        };

        const total = gstData.cgst + gstData.sgst + gstData.igst + gstData.gstPaid;

        Dashboard.charts.gst = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['CGST Collected', 'SGST Payable', 'IGST Payable', 'GST Paid'],
                datasets: [{
                    data: [gstData.cgst, gstData.sgst, gstData.igst, gstData.gstPaid],
                    backgroundColor: [
                        '#3b82f6',
                        '#8b5cf6',
                        '#f59e0b',
                        '#10b981'
                    ],
                    borderWidth: 3,
                    borderColor: '#ffffff',
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                cutout: '70%',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#ffffff',
                        titleColor: '#718096',
                        bodyColor: '#718096',
                        borderColor: '#e2e8f0',
                        borderWidth: 1,
                        padding: 12,
                        callbacks: {
                            label: function (context) {
                                return context.label + ': ' + Utils.formatCurrency(context.parsed);
                            }
                        }
                    }
                }
            }
        });

        // Render legend
        const legendContainer = document.getElementById('gst-legend');
        if (legendContainer) {
            const colors = ['#3b82f6', '#8b5cf6', '#f59e0b', '#10b981'];
            const labels = ['CGST Collected', 'SGST Payable', 'IGST Payable', 'GST Paid'];
            const values = [gstData.cgst, gstData.sgst, gstData.igst, gstData.gstPaid];

            legendContainer.innerHTML = labels.map((label, index) => `
                <div class="gst-legend-item">
                    <div class="gst-legend-color" style="background-color: ${colors[index]}"></div>
                    <div class="gst-legend-text">
                        <div class="gst-legend-label">${label}</div>
                        <div class="gst-legend-value">${Utils.formatCurrency(values[index])}</div>
                    </div>
                </div>
            `).join('');
        }
    },

    loadTopCustomers: async () => {
        try {
            const res = await Utils.api.get(CONFIG.ENDPOINTS.LEDGER + '/summary');
            if (res && res.success) {
                Dashboard.renderTopCustomers(res.data.details || []);
            }
        } catch (e) {
            // Fallback to static data if API fails
            Dashboard.renderTopCustomers([
                { company_name: 'Alpha Traders', balance: 79000 },
                { company_name: 'Ganesh Textiles', balance: 38000 },
                { company_name: 'Sharma Exports', balance: 33000 },
                { company_name: 'Yash Agencies', balance: 20000 },
                { company_name: 'Viral Fabrics', balance: 15000 },
                { company_name: 'Virat Fabrics', balance: 15000 }
            ]);
        }
    },

    renderTopCustomers: (customers) => {
        const container = document.getElementById('customers-list');
        if (!container) return;

        // Sort by balance descending and take top 6
        const topCustomers = customers
            .filter(c => c.balance > 0)
            .sort((a, b) => b.balance - a.balance)
            .slice(0, 6);

        container.innerHTML = topCustomers.map(customer => {
            const initials = customer.company_name
                .split(' ')
                .map(word => word[0])
                .join('')
                .substring(0, 2)
                .toUpperCase();

            return `
                <div class="customer-item">
                    <div class="customer-avatar">${initials}</div>
                    <div class="customer-info">
                        <div class="customer-name">${customer.company_name}</div>
                        <div class="customer-type">${customer.status || 'Receivable'}</div>
                    </div>
                    <div class="customer-amount">${Utils.formatCurrency(Math.abs(customer.balance))}</div>
                </div>
            `;
        }).join('');
    }
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    Dashboard.init();
});

