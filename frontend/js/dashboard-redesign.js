// Dashboard Redesign - Chart.js and Interactions

// Profile Dropdown Toggle
function toggleProfileMenu() {
    const menu = document.getElementById('profileMenu');
    menu.classList.toggle('show');
}

// Sidebar Toggle for Mobile
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('show');
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    const profileDropdown = document.querySelector('.profile-dropdown');
    const menu = document.getElementById('profileMenu');
    if (menu && !profileDropdown.contains(e.target)) {
        menu.classList.remove('show');
    }
});

// Sample Data
const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const salesData = [3200000, 3500000, 3800000, 4100000, 3900000, 4300000, 4500000, 4200000, 4400000, 4700000, 4600000, 4800000];
const purchasesData = [2100000, 2300000, 2500000, 2700000, 2600000, 2800000, 2950000, 2850000, 2900000, 3000000, 2950000, 3100000];
const profitData = salesData.map((sales, i) => sales - purchasesData[i]);

const sparkline1Data = [3.2, 3.5, 3.3, 3.8, 4.1, 3.9, 4.3];
const sparkline2Data = [2.1, 2.3, 2.2, 2.5, 2.7, 2.6, 2.8];
const sparkline3Data = [1.5, 1.4, 1.3, 1.2, 1.1, 1.3, 1.2];
const sparkline4Data = [1.1, 1.0, 0.95, 0.9, 0.85, 0.9, 0.89];

// Chart.js Default Config
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.color = '#6B7280';

// Sparkline Charts
function createSparkline(canvasId, data, color) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['', '', '', '', '', '', ''],
            datasets: [{
                data: data,
                borderColor: color,
                backgroundColor: `${color}20`,
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            },
            scales: {
                x: { display: false },
                y: { display: false }
            }
        }
    });
}

// Line Chart: Sales vs Purchases
function createLineChart() {
    const ctx = document.getElementById('lineChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: monthLabels,
            datasets: [
                {
                    label: 'Sales',
                    data: salesData,
                    borderColor: '#1E5BB8',
                    backgroundColor: '#1E5BB820',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Purchases',
                    data: purchasesData,
                    borderColor: '#F59E0B',
                    backgroundColor: '#F59E0B20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    align: 'end'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: (context) => {
                            return `${context.dataset.label}: ₹${(context.parsed.y / 100000).toFixed(2)}L`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: (value) => `₹${(value / 100000).toFixed(0)}L`
                    },
                    grid: {
                        color: '#F3F4F6'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Column Chart: Monthly Profit
function createColumnChart() {
    const ctx = document.getElementById('columnChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: monthLabels,
            datasets: [{
                label: 'Profit',
                data: profitData,
                backgroundColor: '#10B981',
                borderRadius: 6,
                barThickness: 24
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            return `Profit: ₹${(context.parsed.y / 100000).toFixed(2)}L`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => `₹${(value / 100000).toFixed(0)}L`
                    },
                    grid: {
                        color: '#F3F4F6'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Donut Chart: Invoice Status
function createDonutChart() {
    const ctx = document.getElementById('donutChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Paid', 'Partially Paid', 'Overdue', 'Unpaid'],
            datasets: [{
                data: [45, 25, 15, 15],
                backgroundColor: ['#10B981', '#F59E0B', '#EF4444', '#6B7280'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            return `${label}: ${value}%`;
                        }
                    }
                }
            },
            cutout: '70%'
        }
    });
}

// Horizontal Bar Chart: Top Customers
function createBarChart() {
    const ctx = document.getElementById('barChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Kissimo Fashion', 'Urban Threads', 'Style Hub', 'Textile Corp', 'Fashion Forward'],
            datasets: [{
                label: 'Revenue',
                data: [8500000, 7200000, 6800000, 5900000, 5500000],
                backgroundColor: '#1E5BB8',
                borderRadius: 6,
                barThickness: 20
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            return `Revenue: ₹${(context.parsed.x / 100000).toFixed(2)}L`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => `₹${(value / 100000).toFixed(0)}L`
                    },
                    grid: {
                        color: '#F3F4F6'
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Populate Recent Transactions Table
function populateTransactionsTable() {
    const tbody = document.getElementById('transactionsTable');
    if (!tbody) return;

    const transactions = [
        { date: '20 Jan 2026', type: 'Sale', party: 'Kissimo Fashion', amount: 245000, status: 'paid' },
        { date: '19 Jan 2026', type: 'Purchase', party: 'Textile Mills', amount: 180000, status: 'partial' },
        { date: '18 Jan 2026', type: 'Sale', party: 'Urban Threads', amount: 320000, status: 'paid' },
        { date: '17 Jan 2026', type: 'Purchase', party: 'Dye Works', amount: 95000, status: 'unpaid' },
        { date: '16 Jan 2026', type: 'Sale', party: 'Style Hub', amount: 180000, status: 'paid' },
        { date: '15 Jan 2026', type: 'Purchase', party: 'Fabric Suppliers', amount: 210000, status: 'partial' }
    ];

    const statusBadges = {
        paid: 'badge-success',
        partial: 'badge-warning',
        unpaid: 'badge-danger'
    };

    const statusLabels = {
        paid: 'Paid',
        partial: 'Partially Paid',
        unpaid: 'Unpaid'
    };

    tbody.innerHTML = transactions.map(t => `
        <tr>
            <td>${t.date}</td>
            <td>${t.type}</td>
            <td>${t.party}</td>
            <td>₹${t.amount.toLocaleString('en-IN')}</td>
            <td><span class="badge ${statusBadges[t.status]}">${statusLabels[t.status]}</span></td>
        </tr>
    `).join('');
}

// Populate Overdue Invoices Table
function populateOverdueTable() {
    const tbody = document.getElementById('overdueTable');
    if (!tbody) return;

    const overdueInvoices = [
        { invoice: 'INV-2024-1254', party: 'Fashion Forward', dueDate: '10 Jan 2026', amount: 125000, days: 10 },
        { invoice: 'INV-2024-1248', party: 'Retail Group', dueDate: '12 Jan 2026', amount: 89000, days: 8 },
        { invoice: 'INV-2024-1239', party: 'Metro Stores', dueDate: '15 Jan 2026', amount: 156000, days: 5 },
        { invoice: 'INV-2024-1232', party: 'Style Hub', dueDate: '17 Jan 2026', amount: 78000, days: 3 }
    ];

    tbody.innerHTML = overdueInvoices.map(inv => `
        <tr>
            <td>${inv.invoice}</td>
            <td>${inv.party}</td>
            <td>${inv.dueDate}</td>
            <td>₹${inv.amount.toLocaleString('en-IN')}</td>
            <td><span class="badge badge-danger">${inv.days} days</span></td>
        </tr>
    `).join('');
}

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    // Create all charts
    createSparkline('sparkline1', sparkline1Data, '#1E5BB8');
    createSparkline('sparkline2', sparkline2Data, '#F59E0B');
    createSparkline('sparkline3', sparkline3Data, '#10B981');
    createSparkline('sparkline4', sparkline4Data, '#EF4444');

    createLineChart();
    createColumnChart();
    createDonutChart();
    createBarChart();

    // Populate tables
    populateTransactionsTable();
    populateOverdueTable();

    console.log('Dashboard initialized successfully!');
});
