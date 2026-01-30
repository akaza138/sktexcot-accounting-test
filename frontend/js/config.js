const CONFIG = {
    // Use direct connection for local development, nginx proxy for production/EC2
    API_BASE_URL: (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.port === '5500')
        ? 'http://localhost:8000'
        : '/api',
    ENDPOINTS: {
        LOGIN: '/auth/login',
        REFRESH: '/auth/refresh',
        ME: '/auth/me',
        DASHBOARD: '/dashboard/summary',
        CHARTS: '/dashboard/charts',
        COMPANY: '/company/',
        SALES: '/sales/',
        BILLING: '/billing/',
        PAYMENTS: '/payments/',
        LEDGER: '/ledger/',
        GST: '/gst/summary',
        TDS: '/tds/summary',
        EXCEL_UPLOAD: '/excel/upload',
        EXCEL_IMPORT: '/excel/import'
    }
};
