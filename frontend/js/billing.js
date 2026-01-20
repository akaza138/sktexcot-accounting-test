const Billing = {
    init: () => {
        Billing.loadBills();
        Billing.loadVendors();
        document.getElementById('bill_date').valueAsDate = new Date();
        document.getElementById('billingForm').addEventListener('submit', Billing.saveBill);
    },

    loadBills: async () => {
        try {
            const res = await Utils.api.get(CONFIG.ENDPOINTS.BILLING);
            if (res && res.success) {
                const tbody = document.querySelector('#billingTable tbody');
                tbody.innerHTML = res.data.map(b => {
                    const days = Math.floor((new Date() - new Date(b.bill_date)) / (1000 * 60 * 60 * 24));
                    const aging = days === 0 ? 'Today' : `${days} days`;
                    return `
                    <tr>
                        <td>${Utils.formatDate(b.bill_date)}</td>
                        <td>${b.bill_number}</td>
                        <td>${b.vendor ? b.vendor.name : '-'}</td>
                        <td>${b.process_type || '-'}</td>
                        <td>${b.customer_name || '-'}</td>
                        <td>${Utils.formatCurrency(b.base_amount)}</td>
                        <td>${Utils.formatCurrency(b.gst_amount)}</td>
                        <td>${Utils.formatCurrency(b.total_amount)}</td>
                        <td>${Utils.formatCurrency(b.amount_paid)}</td>
                        <td>${Utils.formatCurrency(b.amount_due)}</td>
                        <td><span style="color:${days > 30 ? 'red' : 'inherit'}">${aging}</span></td>
                        <td>${b.payment_mode ? b.payment_mode.toUpperCase() : '-'}</td>
                        <td>
                             <div class="action-buttons">
                                 <button class="edit-btn" onclick="Billing.editBill(${b.id})">Edit</button>
                                 <button class="delete-btn" onclick="Billing.deleteBill(${b.id})">Delete</button>
                             </div>
                        </td>
                    </tr>
                `}).join('');
            }
        } catch (e) { }
    },

    loadVendors: async () => {
        try {
            // ... existing loadVendors ...
            // Optimization: Fetch once or check if empty
            const res = await Utils.api.get(CONFIG.ENDPOINTS.COMPANY);
            if (res && res.success) {
                const select = document.getElementById('vendor_id');
                // Keep existing selection if any
                const current = select.value;
                select.innerHTML = '<option value="">Select Vendor</option>' +
                    res.data.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
                if (current) select.value = current;
            }
        } catch (e) { }
    },

    showForm: () => {
        document.getElementById('listView').classList.add('hidden');
        document.getElementById('formView').classList.remove('hidden');
        document.getElementById('billingForm').reset();
        document.getElementById('bill_date').valueAsDate = new Date();
        document.getElementById('billId').value = '';
        document.getElementById('formTitle').innerText = 'Record Bill';
        Billing.calculateTotal();
    },

    showList: () => {
        document.getElementById('listView').classList.remove('hidden');
        document.getElementById('formView').classList.add('hidden');
    },

    calculateTotal: () => {
        const qty = parseFloat(document.getElementById('quantity').value) || 0;
        const rate = parseFloat(document.getElementById('rate').value) || 0;
        const gstRate = parseFloat(document.getElementById('gst_rate').value) || 0;
        const tdsApplicable = document.getElementById('tds_applicable').value === 'true';
        const tdsRate = parseFloat(document.getElementById('tds_rate').value) || 0;

        const base = qty * rate;
        const gst = base * (gstRate / 100);
        let tds = 0;
        if (tdsApplicable) {
            tds = base * (tdsRate / 100);
        }

        const total = base + gst - tds;
        document.getElementById('displayTotal').innerText = Utils.formatCurrency(total);
    },

    saveBill: async (e) => {
        e.preventDefault();

        const id = document.getElementById('billId').value;
        const data = {
            bill_number: document.getElementById('bill_number').value,
            bill_date: document.getElementById('bill_date').value,
            vendor_id: parseInt(document.getElementById('vendor_id').value),
            customer_name: document.getElementById('customer_name').value,
            process_type: document.getElementById('process_type').value,
            item_description: document.getElementById('item_description').value,
            quantity: parseFloat(document.getElementById('quantity').value),
            rate: parseFloat(document.getElementById('rate').value),
            gst_type: document.getElementById('gst_type').value,
            gst_rate: parseFloat(document.getElementById('gst_rate').value),
            tds_applicable: document.getElementById('tds_applicable').value === 'true',
            tds_rate: parseFloat(document.getElementById('tds_rate').value),
            tds_file_date: document.getElementById('tds_file_date').value || null,
            amount_paid: parseFloat(document.getElementById('amount_paid').value) || 0,
            payment_mode: document.getElementById('payment_mode').value || null
        };

        try {
            if (id) {
                await Utils.api.put(`${CONFIG.ENDPOINTS.BILLING}${id}`, data);
                Utils.showToast('Bill updated');
            } else {
                await Utils.api.post(CONFIG.ENDPOINTS.BILLING, data);
                Utils.showToast('Bill recorded');
            }
            Billing.showList();
            Billing.loadBills();
        } catch (e) { }
    },

    editBill: async (id) => {
        try {
            const res = await Utils.api.get(`${CONFIG.ENDPOINTS.BILLING}${id}`);
            if (res && res.success) {
                const bill = res.data;

                Billing.showForm();
                document.getElementById('formTitle').innerText = 'Edit Bill';
                document.getElementById('billId').value = bill.id;
                document.getElementById('bill_number').value = bill.bill_number;
                document.getElementById('bill_date').value = bill.bill_date; // Assuming YYYY-MM-DD
                await Billing.loadVendors();
                document.getElementById('vendor_id').value = bill.vendor_id;
                document.getElementById('customer_name').value = bill.customer_name || '';
                document.getElementById('process_type').value = bill.process_type || '';
                document.getElementById('item_description').value = bill.item_description || '';
                document.getElementById('quantity').value = bill.quantity;
                document.getElementById('rate').value = bill.rate;
                document.getElementById('gst_type').value = bill.gst_type;
                document.getElementById('gst_rate').value = bill.gst_rate;
                document.getElementById('tds_applicable').value = bill.tds_applicable.toString();
                document.getElementById('tds_rate').value = bill.tds_rate;
                document.getElementById('tds_file_date').value = bill.tds_file_date || '';
                document.getElementById('amount_paid').value = bill.amount_paid;
                document.getElementById('payment_mode').value = bill.payment_mode || '';

                Billing.calculateTotal();
            }
        } catch (e) { console.error(e); }
    },

    deleteBill: async (id) => {
        if (confirm('Are you sure you want to delete this bill? It will be moved to Recent Delete.')) {
            try {
                // Try to fetch current data for trash before deleting
                try {
                    const res = await Utils.api.get(`${CONFIG.ENDPOINTS.BILLING}${id}`);
                    if (res && res.success) {
                        TrashUtils.save(res.data, 'billing');
                    }
                } catch (trashErr) {
                    console.warn('Failed to save to trash, proceeding with deletion:', trashErr);
                }

                await Utils.api.delete(`${CONFIG.ENDPOINTS.BILLING}${id}`);
                Utils.showToast('Bill moved to Recent Delete', 'success');
                Billing.loadBills();
            } catch (e) {
                console.error('Delete error:', e);
                const errorMsg = e.response?.data?.detail || e.message || 'Failed to delete bill.';
                Utils.showToast(errorMsg, 'error');
            }
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    Billing.init();
});
