const CONFIG = {
    API_BASE_URL: window.location.port === '5500' ? 'http://localhost:8000' : '/api', // Support Live Server and Nginx proxy
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
