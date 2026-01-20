// Table Utilities - Sorting and Search
const TableUtils = {
    // Add sorting to table headers
    enableSorting: (tableId) => {
        const table = document.getElementById(tableId);
        if (!table) return;

        const headers = table.querySelectorAll('thead th');
        headers.forEach((header, index) => {
            // Skip action column
            if (header.textContent.toLowerCase().includes('action')) return;

            header.style.cursor = 'pointer';
            header.style.userSelect = 'none';
            header.innerHTML += ' <span class="sort-icon">⇅</span>';

            header.addEventListener('click', () => {
                TableUtils.sortTable(tableId, index);
            });
        });
    },

    // Sort table by column
    sortTable: (tableId, columnIndex) => {
        const table = document.getElementById(tableId);
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const header = table.querySelectorAll('thead th')[columnIndex];

        // Determine sort direction
        const isAsc = header.classList.contains('sort-asc');

        // Remove all sort classes
        table.querySelectorAll('thead th').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
            const icon = th.querySelector('.sort-icon');
            if (icon) icon.textContent = '⇅';
        });

        // Sort rows
        rows.sort((a, b) => {
            const aText = a.cells[columnIndex]?.textContent.trim() || '';
            const bText = b.cells[columnIndex]?.textContent.trim() || '';

            // Try to parse as number or date
            const aNum = parseFloat(aText.replace(/[₹,]/g, ''));
            const bNum = parseFloat(bText.replace(/[₹,]/g, ''));

            if (!isNaN(aNum) && !isNaN(bNum)) {
                return isAsc ? bNum - aNum : aNum - bNum;
            }

            // Check if date
            const aDate = new Date(aText);
            const bDate = new Date(bText);
            if (!isNaN(aDate) && !isNaN(bDate)) {
                return isAsc ? bDate - aDate : aDate - bDate;
            }

            // String comparison
            return isAsc
                ? bText.localeCompare(aText)
                : aText.localeCompare(bText);
        });

        // Update UI
        header.classList.add(isAsc ? 'sort-desc' : 'sort-asc');
        const icon = header.querySelector('.sort-icon');
        if (icon) icon.textContent = isAsc ? '▼' : '▲';

        // Re-append sorted rows
        rows.forEach(row => tbody.appendChild(row));
    },

    // Add search box above table
    addSearchBox: (tableId, placeholder = 'Search...') => {
        const table = document.getElementById(tableId);
        if (!table) return;

        // Check if search already exists
        if (table.previousElementSibling?.classList.contains('table-search-wrapper')) {
            return;
        }

        const searchWrapper = document.createElement('div');
        searchWrapper.className = 'table-search-wrapper';
        searchWrapper.innerHTML = `
            <div class="search-box">
                <input type="text" 
                       id="${tableId}-search" 
                       class="search-input" 
                       placeholder="${placeholder}">
                <span class="search-icon">🔍</span>
            </div>
        `;

        table.parentNode.insertBefore(searchWrapper, table);

        const searchInput = document.getElementById(`${tableId}-search`);
        searchInput.addEventListener('input', (e) => {
            TableUtils.searchTable(tableId, e.target.value);
        });
    },

    // Search/filter table rows
    searchTable: (tableId, query) => {
        const table = document.getElementById(tableId);
        const tbody = table.querySelector('tbody');
        const rows = tbody.querySelectorAll('tr');
        const searchTerm = query.toLowerCase();

        let visibleCount = 0;

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(searchTerm)) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        // Show "no results" message
        TableUtils.updateNoResultsMessage(tableId, visibleCount, query);
    },

    // Show/hide no results message
    updateNoResultsMessage: (tableId, visibleCount, query) => {
        const table = document.getElementById(tableId);
        const tbody = table.querySelector('tbody');

        let noResultsRow = tbody.querySelector('.no-results-row');

        if (visibleCount === 0 && query) {
            if (!noResultsRow) {
                noResultsRow = document.createElement('tr');
                noResultsRow.className = 'no-results-row';
                noResultsRow.innerHTML = `
                    <td colspan="100%" style="text-align:center; padding:40px; color:var(--text-light);">
                        No results found for "${query}"
                    </td>
                `;
                tbody.appendChild(noResultsRow);
            }
        } else {
            if (noResultsRow) {
                noResultsRow.remove();
            }
        }
    },

    // Trigger sort on a specific column (for default sorting)
    sortByColumn: (tableId, columnIndex) => {
        const table = document.getElementById(tableId);
        if (!table) return;

        const header = table.querySelectorAll('thead th')[columnIndex];
        if (header) {
            // Trigger click to sort ascending by default
            header.click();
        }
    }
};
