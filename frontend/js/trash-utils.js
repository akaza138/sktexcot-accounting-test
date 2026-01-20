const TrashUtils = {
    STORAGE_KEY: 'sktexcot_trash',

    init: () => {
        if (!sessionStorage.getItem(TrashUtils.STORAGE_KEY)) {
            sessionStorage.setItem(TrashUtils.STORAGE_KEY, JSON.stringify({
                company: [],
                billing: [],
                sales: []
            }));
        }
    },

    save: (data, type) => {
        TrashUtils.init();
        const trash = JSON.parse(sessionStorage.getItem(TrashUtils.STORAGE_KEY));

        // Add metadata for restoration
        const item = {
            id: Date.now(), // unique trash id
            originalData: data,
            deletedAt: new Date().toISOString(),
            type: type
        };

        trash[type].unshift(item); // Add to beginning
        // Limit to 20 items per category to avoid session storage limits
        if (trash[type].length > 20) {
            trash[type].pop();
        }

        sessionStorage.setItem(TrashUtils.STORAGE_KEY, JSON.stringify(trash));
    },

    getTrash: () => {
        TrashUtils.init();
        return JSON.parse(sessionStorage.getItem(TrashUtils.STORAGE_KEY));
    },

    removeFromTrash: (trashId, type) => {
        const trash = TrashUtils.getTrash();
        trash[type] = trash[type].filter(item => item.id !== trashId);
        sessionStorage.setItem(TrashUtils.STORAGE_KEY, JSON.stringify(trash));
    },

    clear: () => {
        sessionStorage.removeItem(TrashUtils.STORAGE_KEY);
    }
};
