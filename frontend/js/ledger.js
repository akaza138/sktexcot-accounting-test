const Ledger = {
    init: () => {
        Ledger.loadCompanies();
        // Set default dates (current month)
        const date = new Date();
        const firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
        const lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);

        document.getElementById('from_date').valueAsDate = firstDay;
        document.getElementById('to_date').valueAsDate = lastDay;
    },

    loadCompanies: async () => {
        try {
            const res = await Utils.api.get(CONFIG.ENDPOINTS.COMPANY);
            if (res && res.success) {
                const select = document.getElementById('company_id');
                select.innerHTML = '<option value="">Select Company</option>' +
                    res.data.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
            }
        } catch (e) { }
    },

    loadLedger: async () => {
        const companyId = document.getElementById('company_id').value;
        if (!companyId) return Utils.showToast('Select a company', 'error');

        const fromDate = document.getElementById('from_date').value;
        const toDate = document.getElementById('to_date').value;

        try {
            const query = `?from_date=${fromDate}&to_date=${toDate}`;
            const res = await Utils.api.get(`${CONFIG.ENDPOINTS.LEDGER}company/${companyId}${query}`);

            if (res && res.success) {
                const data = res.data;
                document.getElementById('ledgerSummary').classList.remove('hidden');
                document.getElementById('openingBal').innerText = Utils.formatCurrency(data.opening_balance.net);
                document.getElementById('closingBal').innerText = Utils.formatCurrency(data.closing_balance);

                const tbody = document.querySelector('#ledgerTable tbody');

                // Add Opening Row
                let html = `
                    <tr style="background:#f9f9f9; font-weight:bold;">
                        <td>${Utils.formatDate(fromDate)}</td>
                        <td>OPENING BALANCE</td>
                        <td>-</td>
                        <td>${data.opening_balance.net > 0 ? Utils.formatCurrency(data.opening_balance.net) : '-'}</td>
                        <td>${data.opening_balance.net < 0 ? Utils.formatCurrency(Math.abs(data.opening_balance.net)) : '-'}</td>
                        <td>${Utils.formatCurrency(data.opening_balance.net)}</td>
                        <td>Brought Forward</td>
                    </tr>
                `;

                html += data.entries.map(e => `
                    <tr>
                        <td>${Utils.formatDate(e.transaction_date)}</td>
                        <td><span class="status-badge" style="background:var(--primary); color:white">${e.transaction_type}</span></td>
                        <td>${e.reference_model} #${e.reference_id}</td>
                        <td>${e.debit_amount ? Utils.formatCurrency(e.debit_amount) : '-'}</td>
                        <td>${e.credit_amount ? Utils.formatCurrency(e.credit_amount) : '-'}</td>
                        <td style="font-weight:bold">${Utils.formatCurrency(e.running_balance)}</td>
                        <td>${e.narration || '-'}</td>
                    </tr>
                `).join('');

                tbody.innerHTML = html;
            }
        } catch (e) { }
    },

    printLedger: () => {
        window.print();
    }
};

document.addEventListener('DOMContentLoaded', () => {
    Ledger.init();
});
