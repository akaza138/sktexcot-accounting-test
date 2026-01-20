const Trash = {
    init: () => {
        Trash.renderAll();
    },

    renderAll: () => {
        const trash = TrashUtils.getTrash();
        Trash.renderType('company', trash.company);
        Trash.renderType('billing', trash.billing);
        Trash.renderType('sales', trash.sales);
    },

    renderType: (type, items) => {
        const tbody = document.getElementById(`tbody-${type}`);
        if (!items || items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="empty-trash">No deleted items in ${type}</td></tr>`;
            return;
        }

        tbody.innerHTML = items.map(item => {
            const data = item.originalData;
            const deletedAt = new Date(item.deletedAt).toLocaleString();

            if (type === 'company') {
                return `
                    <tr>
                        <td>${data.name}</td>
                        <td>${data.gst_number || '-'}</td>
                        <td>${deletedAt}</td>
                        <td>
                            <button class="restore-btn" onclick="Trash.restore('${item.id}', 'company')">Restore</button>
                        </td>
                    </tr>
                `;
            } else if (type === 'billing') {
                return `
                    <tr>
                        <td>${data.bill_number}</td>
                        <td>${data.vendor ? data.vendor.name : 'Unknown Vendor'}</td>
                        <td>${Utils.formatCurrency(data.total_amount)}</td>
                        <td>${deletedAt}</td>
                        <td>
                            <button class="restore-btn" onclick="Trash.restore('${item.id}', 'billing')">Restore</button>
                        </td>
                    </tr>
                `;
            } else if (type === 'sales') {
                return `
                    <tr>
                        <td>${data.invoice_number}</td>
                        <td>${data.customer_name || '-'}</td>
                        <td>${Utils.formatCurrency(data.total_amount)}</td>
                        <td>${deletedAt}</td>
                        <td>
                            <button class="restore-btn" onclick="Trash.restore('${item.id}', 'sales')">Restore</button>
                        </td>
                    </tr>
                `;
            }
        }).join('');
    },

    restore: async (trashId, type) => {
        const trash = TrashUtils.getTrash();
        const item = trash[type].find(i => i.id == trashId);

        if (!item) {
            Utils.showToast('Item not found in trash', 'error');
            return;
        }

        const data = item.originalData;

        // Prepare data for recreate (remove ID and auto-fields)
        const recreateData = { ...data };
        delete recreateData.id;
        delete recreateData.created_at;
        delete recreateData.updated_at;
        delete recreateData.created_by;

        // Handle nested objects mapping to IDs for POST
        if (type === 'billing' && data.vendor_id) {
            recreateData.vendor_id = data.vendor_id;
        }
        if (type === 'sales' && data.company_id) {
            recreateData.company_id = data.company_id;
        }

        try {
            let endpoint = '';
            if (type === 'company') endpoint = CONFIG.ENDPOINTS.COMPANY;
            else if (type === 'billing') endpoint = CONFIG.ENDPOINTS.BILLING;
            else if (type === 'sales') endpoint = CONFIG.ENDPOINTS.SALES;

            const res = await Utils.api.post(endpoint, recreateData);
            if (res && res.success) {
                Utils.showToast(`${type.charAt(0).toUpperCase() + type.slice(1)} restored successfully`, 'success');
                TrashUtils.removeFromTrash(item.id, type);
                Trash.renderAll();
            }
        } catch (e) {
            Utils.showToast(e.response?.data?.detail || 'Restoration failed', 'error');
            console.error(e);
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    Trash.init();
});
