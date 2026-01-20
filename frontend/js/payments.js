const Payments = {
    init: () => {
        Payments.loadPayments();
        Payments.loadCompanies();
        document.getElementById('paymentForm').addEventListener('submit', Payments.savePayment);
    },

    loadPayments: async () => {
        try {
            const res = await Utils.api.get(CONFIG.ENDPOINTS.PAYMENTS);
            if (res && res.success) {
                const tbody = document.querySelector('#paymentsTable tbody');
                tbody.innerHTML = res.data.map(p => `
                    <tr>
                        <td>${Utils.formatDate(p.payment_date)}</td>
                        <td>
                            <span class="status-badge" style="background:${p.payment_type === 'receipt' ? '#e8f5e9' : '#ffebee'}; color: ${p.payment_type === 'receipt' ? 'green' : 'red'}">
                                ${p.payment_type.toUpperCase()}
                            </span>
                        </td>
                        <td>${p.company ? p.company.name : '-'}</td>
                        <td>${Utils.formatCurrency(p.amount)}</td>
                        <td>${p.payment_mode}</td>
                        <td>${p.transaction_reference || '-'}</td>
                    </tr>
                `).join('');
            }
        } catch (e) { }
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

    savePayment: async (e) => {
        e.preventDefault();
        const data = {
            payment_date: document.getElementById('payment_date').value,
            payment_type: document.getElementById('payment_type').value,
            company_id: parseInt(document.getElementById('company_id').value),
            amount: parseFloat(document.getElementById('amount').value),
            payment_mode: document.getElementById('payment_mode').value,
            transaction_reference: document.getElementById('transaction_reference').value,
            notes: document.getElementById('notes').value
        };

        try {
            await Utils.api.post(CONFIG.ENDPOINTS.PAYMENTS, data);
            Utils.showToast('Payment recorded');
            Payments.closeModal();
            Payments.loadPayments();
        } catch (e) { }
    },

    openModal: () => {
        document.getElementById('paymentModal').classList.remove('hidden');
        document.getElementById('payment_date').valueAsDate = new Date();
    },

    closeModal: () => {
        document.getElementById('paymentModal').classList.add('hidden');
        document.getElementById('paymentForm').reset();
    }
};

document.addEventListener('DOMContentLoaded', () => {
    Payments.init();
});
