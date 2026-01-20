const Sales = {
    init: () => {
        Sales.loadInvoices();
        Sales.loadCompanies();

        // Set default date
        document.getElementById('invoice_date').valueAsDate = new Date();

        document.getElementById('salesForm').addEventListener('submit', Sales.saveInvoice);
    },

    loadInvoices: async () => {
        try {
            const res = await Utils.api.get(CONFIG.ENDPOINTS.SALES);
            if (res && res.success) {
                const tbody = document.querySelector('#salesTable tbody');
                tbody.innerHTML = res.data.map(s => `
                    <tr>
                        <td>${Utils.formatDate(s.invoice_date)}</td>
                        <td>${s.invoice_number}</td>
                        <td>${s.company ? s.company.name : '-'}</td>
                        <td>${Utils.formatCurrency(s.total_amount)}</td>
                        <td>
                            <span class="status-badge ${s.payment_status}">${s.payment_status}</span>
                        </td>
                        <td>
                            <button onclick="Sales.viewInvoice(${s.id})">View/Edit</button>
                            <button onclick="Sales.deleteInvoice(${s.id})" style="color:red">Delete</button>
                        </td>
                    </tr>
                `).join('');
            }
        } catch (e) {
            console.error(e);
        }
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

    showForm: () => {
        document.getElementById('listView').classList.add('hidden');
        document.getElementById('formView').classList.remove('hidden');
        document.getElementById('salesForm').reset();
        document.getElementById('invoice_date').valueAsDate = new Date();
        document.getElementById('salesId').value = '';
        document.getElementById('formTitle').innerText = 'Create Invoice';
        Sales.calculateTotal();
    },

    showList: () => {
        document.getElementById('listView').classList.remove('hidden');
        document.getElementById('formView').classList.add('hidden');
    },

    calculateTotal: () => {
        const qty = parseFloat(document.getElementById('quantity').value) || 0;
        const rate = parseFloat(document.getElementById('rate').value) || 0;
        const gstRate = parseFloat(document.getElementById('gst_rate').value) || 0;

        const base = qty * rate;
        const gst = base * (gstRate / 100);
        const total = base + gst;

        document.getElementById('displayTotal').innerText = Utils.formatCurrency(total);
    },

    saveInvoice: async (e) => {
        e.preventDefault();

        const id = document.getElementById('salesId').value;
        const data = {
            invoice_date: document.getElementById('invoice_date').value,
            company_id: parseInt(document.getElementById('company_id').value),
            process_type: document.getElementById('process_type').value,
            item_description: document.getElementById('item_description').value,
            quantity: parseFloat(document.getElementById('quantity').value),
            rate: parseFloat(document.getElementById('rate').value),
            gst_type: document.getElementById('gst_type').value,
            gst_rate: parseFloat(document.getElementById('gst_rate').value),
            amount_paid: parseFloat(document.getElementById('amount_paid').value) || 0,
            payment_mode: document.getElementById('payment_mode').value || null
        };

        try {
            if (id) {
                // calls PUT /sales/{id}
                await Utils.api.put(`${CONFIG.ENDPOINTS.SALES}${id}`, data);
                Utils.showToast('Invoice updated');
            } else {
                await Utils.api.post(CONFIG.ENDPOINTS.SALES, data);
                Utils.showToast('Invoice created');
            }
            Sales.showList();
            Sales.loadInvoices();
        } catch (e) { }
    },

    viewInvoice: async (id) => {
        // Should implement pre-filling form similar to Company
        // For brevity, similar logic to editCompany.
        // Fetch, set values, showForm()
        try {
            const res = await Utils.api.get(`${CONFIG.ENDPOINTS.SALES}${id}`);
            const s = res.data;
            document.getElementById('salesId').value = s.id;
            document.getElementById('invoice_date').value = s.invoice_date;
            document.getElementById('company_id').value = s.company_id;
            document.getElementById('process_type').value = s.process_type;
            document.getElementById('item_description').value = s.item_description;
            document.getElementById('quantity').value = s.quantity;
            document.getElementById('rate').value = s.rate;
            document.getElementById('gst_type').value = s.gst_type;
            document.getElementById('gst_rate').value = s.gst_rate;
            document.getElementById('amount_paid').value = s.amount_paid;
            document.getElementById('payment_mode').value = s.payment_mode;

            Sales.calculateTotal();
            document.getElementById('formTitle').innerText = 'Edit Invoice';

            document.getElementById('listView').classList.add('hidden');
            document.getElementById('formView').classList.remove('hidden');

        } catch (e) { }
    },

    deleteInvoice: async (id) => {
        if (confirm('Delete invoice? This will remove ledger entries.')) {
            try {
                // Fetch current data for trash before deleting
                const res = await Utils.api.get(`${CONFIG.ENDPOINTS.SALES}${id}`);
                if (res && res.success) {
                    TrashUtils.save(res.data, 'sales');
                }

                await Utils.api.delete(`${CONFIG.ENDPOINTS.SALES}${id}`);
                Utils.showToast('Invoice moved to Recent Delete', 'success');
                Sales.loadInvoices();
            } catch (e) {
                console.error('Delete error:', e);
                const errorMsg = e.response?.data?.detail || e.message || 'Failed to delete invoice. You may not have permission.';
                Utils.showToast(errorMsg, 'error');
            }
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    Sales.init();
});
