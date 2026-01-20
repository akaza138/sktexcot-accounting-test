const Permissions = {
    // Get current user's role
    getRole: () => {
        return localStorage.getItem('user_role');
    },

    // Check if user can create new records
    canCreate: () => {
        const role = Permissions.getRole();
        return role === 'owner' || role === 'accountant';
    },

    // Check if user can edit existing records
    canEdit: () => {
        const role = Permissions.getRole();
        return role === 'owner' || role === 'accountant';
    },

    // Check if user can delete records (Owner only)
    canDelete: () => {
        const role = Permissions.getRole();
        return role === 'owner';
    },

    // Check if user can upload files/Excel
    canUpload: () => {
        const role = Permissions.getRole();
        return role === 'owner' || role === 'accountant';
    },

    // Check if user can download/export data
    canDownload: () => {
        const role = Permissions.getRole();
        return role === 'owner' || role === 'accountant';
    },

    // Check if user is read-only (Merchandiser)
    isReadOnly: () => {
        const role = Permissions.getRole();
        return role === 'merchandiser';
    },

    // Apply permissions to the current page
    applyPermissions: () => {
        // Hide create buttons if user can't create
        if (!Permissions.canCreate()) {
            document.querySelectorAll('.btn-create, .requires-create').forEach(el => {
                el.style.display = 'none';
            });
        }

        // Hide edit buttons if user can't edit
        if (!Permissions.canEdit()) {
            document.querySelectorAll('.btn-edit, .requires-edit').forEach(el => {
                el.style.display = 'none';
            });
        }

        // Hide delete buttons if user can't delete
        if (!Permissions.canDelete()) {
            document.querySelectorAll('.btn-delete, .requires-delete').forEach(el => {
                el.style.display = 'none';
            });
        }

        // Hide upload buttons if user can't upload
        if (!Permissions.canUpload()) {
            document.querySelectorAll('.btn-upload, .requires-upload').forEach(el => {
                el.style.display = 'none';
            });
        }

        // Hide download buttons if user can't download
        if (!Permissions.canDownload()) {
            document.querySelectorAll('.btn-download, .requires-download').forEach(el => {
                el.style.display = 'none';
            });
        }

        // Add read-only class to body if user is merchandiser
        if (Permissions.isReadOnly()) {
            document.body.classList.add('read-only-mode');
        }
    }
};
