// ============================================
// Delete Confirmation Functions
// ============================================
async function confirmDeleteDocument(docId, filename) {
    if (!confirm(`Are you sure you want to delete "${filename}"? This action cannot be undone.`)) {
        return;
    }
    
    try {
        await deleteDocument(docId);
        showToast('Document deleted successfully', 'success');
        // Refresh current page
        const activePage = document.querySelector('.nav-item.active')?.dataset.page;
        if (activePage === 'documents') {
            loadDocuments();
        } else if (activePage === 'dashboard') {
            loadDashboard();
        } else if (activePage === 'batches') {
            loadBatchesPage();
        }
    } catch (error) {
        showToast(`Failed to delete document: ${error.message}`, 'error');
    }
}

async function confirmDeleteBatch(batchId) {
    if (!confirm(`Are you sure you want to delete batch "${batchId}"? This will delete ALL documents in this batch.`)) {
        return;
    }
    
    try {
        const result = await deleteBatch(batchId);
        showToast(`Batch deleted! ${result.deleted_count} documents removed.`, 'success');
        // Refresh current page
        const activePage = document.querySelector('.nav-item.active')?.dataset.page;
        if (activePage === 'batches') {
            loadBatchesPage();
        } else if (activePage === 'dashboard') {
            loadDashboard();
        }
    } catch (error) {
        showToast(`Failed to delete batch: ${error.message}`, 'error');
    }
}