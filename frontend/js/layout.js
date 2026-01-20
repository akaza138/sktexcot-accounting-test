const Layout = {
    init: () => {
        const userName = localStorage.getItem('user_name') || 'User';
        const userRole = localStorage.getItem('user_role') || 'User';

        // Sidebar with user info at bottom
        const sidebar = `
        <div class="sidebar">
            <div class="logo" style="text-align: center; padding: 20px 0;">
                <img src="../assets/img/logo.jpg" alt="SK Texcot Logo" style="height: 50px; border-radius: 8px;">
            </div>
            <nav>
                <a href="dashboard.html" class="nav-item" id="nav-dashboard">
                     <span>Dashboard</span>
                </a>
                <a href="company.html" class="nav-item" id="nav-company">
                     <span>Company Master</span>
                </a>
                <a href="sales.html" class="nav-item" id="nav-sales">
                     <span>Sales Entry</span>
                </a>
                <a href="billing.html" class="nav-item" id="nav-billing">
                     <span>Billing</span>
                </a>
                <a href="payments.html" class="nav-item" id="nav-payments">
                     <span>Payments</span>
                </a>
                <a href="ledger.html" class="nav-item" id="nav-ledger">
                     <span>Ledger</span>
                </a>
                <a href="gst.html" class="nav-item" id="nav-gst">
                     <span>GST Reports</span>
                </a>
                 <a href="tds.html" class="nav-item" id="nav-tds">
                     <span>TDS Reports</span>
                </a>
                 <a href="excel.html" class="nav-item" id="nav-excel">
                     <span>Excel Import</span>
                </a>
                <a href="trash.html" class="nav-item" id="nav-trash">
                     <span>Recent Delete</span>
                </a>
            </nav>
            
            <!-- User Info Section in Sidebar -->
            <div class="sidebar-user-section">
                <div class="user-avatar">
                   <img src="../assets/img/avatar-placeholder.png" alt="User" onerror="this.src='https://ui-avatars.com/api/?name=${encodeURIComponent(userName)}&background=007bff&color=fff'">
                </div>
                <div class="user-details">
                    <div class="user-name">${userName}</div>
                    <div class="user-role">${userRole.toUpperCase()}</div>
                </div>
                <button class="logout-btn" onclick="TrashUtils.clear(); Auth.logout();">
                    <span class="logout-icon">⏻</span> Logout
                </button>
            </div>
        </div>
        `;

        const sidebarContainer = document.getElementById('sidebar-container');
        if (sidebarContainer) {
            sidebarContainer.innerHTML = sidebar;
            Layout.highlightActiveNav();
        }


        // Header with theme toggle
        const header = `
        <header class="top-header">
            <div class="header-left"></div>
            <div class="header-right">
                <button class="theme-toggle" id="theme-toggle" onclick="Theme.toggle()" aria-label="Toggle theme">
                    <div class="theme-toggle-inner">
                        <span class="theme-icon sun">☀️</span>
                        <span class="theme-icon moon">🌙</span>
                        <span class="theme-icon cloud">☁️</span>
                        <div class="theme-slider"></div>
                    </div>
                </button>
            </div>
        </header>
        `;

        const headerContainer = document.getElementById('header-container');
        if (headerContainer) {
            headerContainer.innerHTML = header;
        }

    },

    highlightActiveNav: () => {
        const path = window.location.pathname;
        const page = path.split("/").pop();

        const map = {
            'dashboard.html': 'nav-dashboard',
            'company.html': 'nav-company',
            'sales.html': 'nav-sales',
            'billing.html': 'nav-billing',
            'payments.html': 'nav-payments',
            'ledger.html': 'nav-ledger',
            'gst.html': 'nav-gst',
            'tds.html': 'nav-tds',
            'excel.html': 'nav-excel',
            'trash.html': 'nav-trash'
        };

        const id = map[page] || 'nav-dashboard';
        const el = document.getElementById(id);
        if (el) el.classList.add('active');
    }
};

// Auto init on load
document.addEventListener('DOMContentLoaded', () => {
    Auth.checkAuth();
    Layout.init();
});
