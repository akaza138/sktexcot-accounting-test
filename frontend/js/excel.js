const Excel = {
    // Current Preview Data
    data: null,

    uploadFile: async () => {
        const fileInput = document.getElementById('excelFile');
        const file = fileInput.files[0];
        if (!file) return Utils.showToast('Please select a file', 'error');

        const formData = new FormData();
        formData.append('file', file);

        document.getElementById('uploadStatus').innerText = 'Uploading...';

        try {
            const res = await Utils.api.upload(CONFIG.ENDPOINTS.EXCEL_UPLOAD, formData);
            if (res && res.success) {
                Excel.data = res.data;
                Excel.data.companies = res.companies || [];  // Store companies list
                Excel.renderPreview(res.data, res.companies);
                document.getElementById('previewArea').classList.remove('hidden');
                document.getElementById('uploadStatus').innerText = `File parsed successfully. Found ${res.companies ? res.companies.length : 0} companies.`;
            } else {
                if (res.errors) Utils.showToast(res.errors.join('\n'), 'error');
            }
        } catch (e) {
            document.getElementById('uploadStatus').innerText = 'Upload failed.';
        }
    },

    renderPreview: (data, companies) => {
        const container = document.getElementById('previewContent');
        let html = '';

        // Show companies found
        if (companies && companies.length > 0) {
            html += `<div style="background:#f0f9ff; padding:15px; margin-bottom:20px; border-radius:8px;">`;
            html += `<h3 style="margin-top:0; color:#1e5bb8;">📋 Companies Found (${companies.length})</h3>`;
            html += `<p style="font-size:14px; color:#6b7280;">These companies will be automatically created if they don't exist:</p>`;
            html += `<div style="display:flex; flex-wrap:wrap; gap:8px;">`;
            companies.forEach(c => {
                html += `<span style="background:white; padding:6px 12px; border-radius:4px; border:1px solid #e5e7eb; font-size:13px;">${c}</span>`;
            });
            html += `</div></div>`;
        }

        if (data.sales) {
            html += `<h3>Sales Data (${data.sales.length} rows)</h3>`;
            html += `<div class="table-container" style="max-height:300px; overflow-y:auto; margin-bottom:20px;">`;
            html += `<table class="data-table"><thead><tr>`;
            // Headers
            if (data.sales.length > 0) {
                Object.keys(data.sales[0]).forEach(k => html += `<th>${k}</th>`);
            }
            html += `</tr></thead><tbody>`;
            // Rows
            data.sales.slice(0, 10).forEach(row => { // Show first 10
                html += `<tr>`;
                Object.values(row).forEach(v => html += `<td>${v || '-'}</td>`);
                html += `</tr>`;
            });
            html += `</tbody></table></div>`;
        }

        container.innerHTML = html;
    },

    confirmImport: async () => {
        if (!Excel.data) return;

        if (confirm('Are you sure you want to import this data? Companies will be created automatically.')) {
            try {
                const res = await Utils.api.post(CONFIG.ENDPOINTS.EXCEL_IMPORT, Excel.data);
                if (res && res.success) {
                    const msg = `Imported ${res.imported_count} sales records. Created ${res.companies_created} new companies.`;
                    Utils.showToast(msg, 'success');
                    if (res.errors && res.errors.length > 0) {
                        console.warn('Import warnings:', res.errors);
                    }
                    document.getElementById('previewArea').classList.add('hidden');
                    document.getElementById('excelFile').value = '';
                } else {
                    if (res.errors) alert('Import Errors:\n' + res.errors.join('\n'));
                }
            } catch (e) { }
        }
    }
};
