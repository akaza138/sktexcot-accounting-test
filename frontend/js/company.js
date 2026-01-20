const Company = {
    init: () => {
        Company.loadCompanies();
        document.getElementById('companyForm').addEventListener('submit', Company.saveCompany);
    },

    loadCompanies: async () => {
        try {
            const res = await Utils.api.get(CONFIG.ENDPOINTS.COMPANY);
            if (res && res.success) {
                const tbody = document.querySelector('#companyTable tbody');
                tbody.innerHTML = res.data.map(c => `
                    <tr onclick="Company.showDetails(${c.id})" data-company-id="${c.id}">
                        <td>${c.name}</td>
                        <td>${c.process_type}</td>
                        <td>${c.gst_number || '-'}</td>
                        <td>${c.phone || '-'}</td>
                    </tr>
                `).join('');

                // Enable search and sorting
                TableUtils.addSearchBox('companyTable', 'Search companies by name, GST, phone...');
                TableUtils.enableSorting('companyTable');

                // Default sort by company name (column 0) - alphabetically
                TableUtils.sortByColumn('companyTable', 0);
            }
        } catch (e) {
            console.error(e);
        }
    },

    showDetails: async (id) => {
        try {
            // Remove previous selection
            document.querySelectorAll('#companyTable tbody tr').forEach(row => {
                row.classList.remove('selected');
            });

            // Mark selected row
            const selectedRow = document.querySelector(`#companyTable tbody tr[data-company-id="${id}"]`);
            if (selectedRow) selectedRow.classList.add('selected');

            const c = await Utils.api.get(`${CONFIG.ENDPOINTS.COMPANY}${id}`);
            window.selectedCompanyId = id;

            document.getElementById('detail-name').textContent = c.name;
            document.getElementById('detail-process').textContent = c.process_type || '-';
            document.getElementById('detail-gst').textContent = c.gst_number || '-';
            document.getElementById('detail-pan').textContent = c.pan_number || '-';
            document.getElementById('detail-email').textContent = c.email || '-';
            document.getElementById('detail-phone').textContent = c.phone || '-';
            document.getElementById('detail-address').textContent = c.address || '-';


            document.getElementById('companyDetails').classList.remove('hidden');
        } catch (e) {
            console.error(e);
        }
    },

    openModal: () => {
        document.getElementById('companyModal').classList.remove('hidden');
        document.getElementById('companyForm').reset();
        document.getElementById('companyId').value = '';
        document.getElementById('modalTitle').innerText = 'Add Company';
    },

    closeModal: () => {
        document.getElementById('companyModal').classList.add('hidden');
    },

    saveCompany: async (e) => {
        e.preventDefault();

        const id = document.getElementById('companyId').value;
        const data = {
            name: document.getElementById('name').value,
            process_type: document.getElementById('process_type').value,
            gst_number: document.getElementById('gst_number').value || null,
            pan_number: document.getElementById('pan_number').value || null,
            email: document.getElementById('email').value || null,
            phone: document.getElementById('phone').value || null,
            address: document.getElementById('address').value || null
        };

        try {
            if (id) {
                await Utils.api.put(`${CONFIG.ENDPOINTS.COMPANY}${id}`, data);
                Utils.showToast('Company updated', 'success');
                Company.closeModal();
                Company.loadCompanies();
                // Reload the detail panel if this company is currently selected
                if (window.selectedCompanyId == id) {
                    Company.showDetails(id);
                }
            } else {
                await Utils.api.post(CONFIG.ENDPOINTS.COMPANY, data);
                Utils.showToast('Company created', 'success');
                Company.closeModal();
                Company.loadCompanies();
            }
        } catch (e) {
            Utils.showToast(e.response?.data?.detail || 'Failed to save', 'error');
        }
    },

    editCompany: async (id) => {
        try {
            const res = await Utils.api.get(`${CONFIG.ENDPOINTS.COMPANY}${id}`);
            const c = res.data;

            console.log('Editing company:', c);

            // Open modal first WITHOUT calling openModal() to avoid reset
            document.getElementById('companyModal').classList.remove('hidden');
            document.getElementById('modalTitle').innerText = 'Edit Company';

            // Now populate fields
            document.getElementById('companyId').value = c.id;
            document.getElementById('name').value = c.name || '';
            document.getElementById('process_type').value = c.process_type || 'other';
            document.getElementById('gst_number').value = c.gst_number || '';
            document.getElementById('pan_number').value = c.pan_number || '';
            document.getElementById('email').value = c.email || '';
            document.getElementById('phone').value = c.phone || '';
            document.getElementById('address').value = c.address || '';
        } catch (e) {
            console.error('Edit error:', e);
            Utils.showToast('Failed to load company', 'error');
        }
    },

    deleteCompany: async (id) => {
        if (confirm('Are you sure you want to delete this company?')) {
            try {
                // Fetch current data for trash before deleting
                const res = await Utils.api.get(`${CONFIG.ENDPOINTS.COMPANY}${id}`);
                if (res && res.success) {
                    TrashUtils.save(res.data, 'company');
                }

                await Utils.api.delete(`${CONFIG.ENDPOINTS.COMPANY}${id}`);
                Utils.showToast('Company moved to Recent Delete', 'success');
                document.getElementById('companyDetails').classList.add('hidden');
                Company.loadCompanies();
            } catch (e) {
                Utils.showToast(e.response?.data?.detail || 'Failed to delete', 'error');
            }
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    Company.init();
});
