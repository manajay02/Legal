/**
 * Document Management Features - Frontend Components
 * Adds notes, organization, and preview capabilities to the existing UI
 */

// ============================================
// Document Notes & Annotations
// ============================================

class DocumentNotesManager {
    constructor(docId) {
        this.docId = docId;
        this.notes = [];
        this.annotations = [];
        this.initializeUI();
    }

    initializeUI() {
        this.createNotesPanel();
        this.setupEventListeners();
        this.loadNotes();
    }

    createNotesPanel() {
        // Add notes panel to document viewer
        const notesHTML = `
            <div id="notes-panel" class="notes-panel">
                <div class="notes-header">
                    <h3><i class="fas fa-sticky-note"></i> Notes & Annotations</h3>
                    <button id="add-note-btn" class="btn btn-primary btn-sm">
                        <i class="fas fa-plus"></i> Add Note
                    </button>
                </div>
                <div class="notes-container" id="notes-container">
                    <!-- Notes will be loaded here -->
                </div>
            </div>

            <!-- Note Editor Modal -->
            <div id="note-editor-modal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h4 id="note-modal-title">Add Note</h4>
                        <span class="close">&times;</span>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>Content:</label>
                            <textarea id="note-content" rows="6" placeholder="Enter your note..."></textarea>
                        </div>
                        <div class="form-group">
                            <label>Tags (comma-separated):</label>
                            <input type="text" id="note-tags" placeholder="important, review, question">
                        </div>
                        <div class="form-group">
                            <label>Color:</label>
                            <input type="color" id="note-color" value="#ffeb3b">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button id="save-note-btn" class="btn btn-primary">Save</button>
                        <button id="cancel-note-btn" class="btn btn-secondary">Cancel</button>
                    </div>
                </div>
            </div>
        `;

        // Insert into document viewer
        const docViewer = document.querySelector('.document-viewer');
        if (docViewer) {
            docViewer.insertAdjacentHTML('beforeend', notesHTML);
        }
    }

    setupEventListeners() {
        // Add note button
        document.getElementById('add-note-btn')?.addEventListener('click', () => {
            this.showNoteEditor();
        });

        // Save note button
        document.getElementById('save-note-btn')?.addEventListener('click', () => {
            this.saveNote();
        });

        // Cancel/close modal
        document.getElementById('cancel-note-btn')?.addEventListener('click', () => {
            this.hideNoteEditor();
        });

        document.querySelector('#note-editor-modal .close')?.addEventListener('click', () => {
            this.hideNoteEditor();
        });
    }

    async loadNotes() {
        try {
            const response = await fetch(`${API_V1_URL}/documents/${this.docId}/notes`);
            this.notes = await response.json();
            this.renderNotes();
        } catch (error) {
            console.error('Error loading notes:', error);
        }
    }

    renderNotes() {
        const container = document.getElementById('notes-container');
        if (!container) return;

        if (this.notes.length === 0) {
            container.innerHTML = '<p class="no-notes">No notes yet. Add your first note!</p>';
            return;
        }

        const notesHTML = this.notes.map(note => `
            <div class="note-item" data-note-id="${note.id}" style="border-left: 4px solid ${note.color || '#ffeb3b'}">
                <div class="note-meta">
                    <span class="note-date">${new Date(note.created_at).toLocaleDateString()}</span>
                    <div class="note-actions">
                        <button class="btn-icon edit-note" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon delete-note" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="note-content">${note.content}</div>
                ${note.tags.length > 0 ? `
                    <div class="note-tags">
                        ${note.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('');

        container.innerHTML = notesHTML;

        // Attach event listeners to note actions
        container.querySelectorAll('.delete-note').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const noteId = e.target.closest('.note-item').dataset.noteId;
                this.deleteNote(noteId);
            });
        });
    }

    showNoteEditor(note = null) {
        const modal = document.getElementById('note-editor-modal');
        const title = document.getElementById('note-modal-title');
        
        if (note) {
            title.textContent = 'Edit Note';
            document.getElementById('note-content').value = note.content;
            document.getElementById('note-tags').value = note.tags.join(', ');
            document.getElementById('note-color').value = note.color || '#ffeb3b';
            modal.dataset.noteId = note.id;
        } else {
            title.textContent = 'Add Note';
            document.getElementById('note-content').value = '';
            document.getElementById('note-tags').value = '';
            document.getElementById('note-color').value = '#ffeb3b';
            delete modal.dataset.noteId;
        }
        
        modal.style.display = 'block';
    }

    hideNoteEditor() {
        document.getElementById('note-editor-modal').style.display = 'none';
    }

    async saveNote() {
        const content = document.getElementById('note-content').value.trim();
        if (!content) return;

        const tags = document.getElementById('note-tags').value
            .split(',')
            .map(tag => tag.trim())
            .filter(tag => tag.length > 0);
        
        const color = document.getElementById('note-color').value;
        const modal = document.getElementById('note-editor-modal');
        const noteId = modal.dataset.noteId;

        try {
            const payload = { content, tags, color };
            let response;

            if (noteId) {
                // Update existing note
                response = await fetch(`${API_V1_URL}/documents/${this.docId}/notes/${noteId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            } else {
                // Create new note
                response = await fetch(`${API_V1_URL}/documents/${this.docId}/notes`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            }

            if (response.ok) {
                this.hideNoteEditor();
                this.loadNotes(); // Refresh notes list
            }
        } catch (error) {
            console.error('Error saving note:', error);
        }
    }

    async deleteNote(noteId) {
        if (!confirm('Delete this note?')) return;

        try {
            const response = await fetch(`${API_V1_URL}/documents/${this.docId}/notes/${noteId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.loadNotes(); // Refresh notes list
            }
        } catch (error) {
            console.error('Error deleting note:', error);
        }
    }
}

// ============================================
// Document Organization Manager
// ============================================

class DocumentOrganizationManager {
    constructor() {
        this.folders = [];
        this.tags = [];
        this.initializeUI();
    }

    initializeUI() {
        this.createOrganizationSidebar();
        this.loadFolders();
        this.loadTags();
    }

    createOrganizationSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) return;

        const organizationHTML = `
            <div class="organization-section">
                <div class="section-header">
                    <h4><i class="fas fa-folder"></i> Folders</h4>
                    <button id="add-folder-btn" class="btn-icon" title="Add Folder">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
                <div id="folders-tree" class="folders-tree">
                    <!-- Folders will be loaded here -->
                </div>
            </div>

            <div class="organization-section">
                <div class="section-header">
                    <h4><i class="fas fa-tags"></i> Tags</h4>
                    <button id="add-tag-btn" class="btn-icon" title="Add Tag">
                        <i class="fas fa-plus"></i>
                    </button>
                </div>
                <div id="tags-list" class="tags-list">
                    <!-- Tags will be loaded here -->
                </div>
            </div>

            <div class="organization-section">
                <div class="section-header">
                    <h4><i class="fas fa-star"></i> Favorites</h4>
                </div>
                <div id="favorites-list" class="favorites-list">
                    <a href="#" class="nav-item" data-filter="favorites">
                        <i class="fas fa-star"></i>
                        <span>Favorite Documents</span>
                    </a>
                </div>
            </div>
        `;

        // Insert before existing nav menu
        const navMenu = sidebar.querySelector('.nav-menu');
        if (navMenu) {
            navMenu.insertAdjacentHTML('afterend', organizationHTML);
        }
    }

    async loadFolders() {
        try {
            const response = await fetch(`${API_V1_URL}/folders`);
            this.folders = await response.json();
            this.renderFolders();
        } catch (error) {
            console.error('Error loading folders:', error);
        }
    }

    renderFolders() {
        const container = document.getElementById('folders-tree');
        if (!container) return;

        if (this.folders.length === 0) {
            container.innerHTML = '<p class="empty-state">No folders yet</p>';
            return;
        }

        const renderFolder = (folder, level = 0) => {
            const indent = level * 20;
            let html = `
                <div class="folder-item" style="padding-left: ${indent}px" data-folder-id="${folder.id}">
                    <div class="folder-content">
                        <i class="fas fa-folder" style="color: ${folder.color || '#ffd700'}"></i>
                        <span class="folder-name">${folder.name}</span>
                        <span class="doc-count">(${folder.document_count})</span>
                    </div>
                </div>
            `;

            // Render children
            if (folder.children && folder.children.length > 0) {
                html += folder.children.map(child => renderFolder(child, level + 1)).join('');
            }

            return html;
        };

        const foldersHTML = this.folders.map(folder => renderFolder(folder)).join('');
        container.innerHTML = foldersHTML;

        // Add click handlers for folder navigation
        container.querySelectorAll('.folder-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const folderId = e.currentTarget.dataset.folderId;
                this.filterDocumentsByFolder(folderId);
            });
        });
    }

    async loadTags() {
        try {
            const response = await fetch(`${API_V1_URL}/tags`);
            this.tags = await response.json();
            this.renderTags();
        } catch (error) {
            console.error('Error loading tags:', error);
        }
    }

    renderTags() {
        const container = document.getElementById('tags-list');
        if (!container) return;

        if (this.tags.length === 0) {
            container.innerHTML = '<p class="empty-state">No tags yet</p>';
            return;
        }

        const tagsHTML = this.tags.map(tag => `
            <div class="tag-item" data-tag-id="${tag.id}">
                <span class="tag-color" style="background-color: ${tag.color}"></span>
                <span class="tag-name">${tag.name}</span>
                <span class="doc-count">(${tag.document_count})</span>
            </div>
        `).join('');

        container.innerHTML = tagsHTML;

        // Add click handlers for tag filtering
        container.querySelectorAll('.tag-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const tagId = e.currentTarget.dataset.tagId;
                this.filterDocumentsByTag(tagId);
            });
        });
    }

    filterDocumentsByFolder(folderId) {
        // Filter documents view by folder
        console.log('Filter by folder:', folderId);
        // Implementation would filter the main documents list
    }

    filterDocumentsByTag(tagId) {
        // Filter documents view by tag
        console.log('Filter by tag:', tagId);
        // Implementation would filter the main documents list
    }
}

// ============================================
// PDF Viewer Component
// ============================================

class PDFViewer {
    constructor(docId, containerId) {
        this.docId = docId;
        this.container = document.getElementById(containerId);
        this.currentPage = 1;
        this.totalPages = 0;
        this.zoomLevel = 1.0;
        this.pages = [];
        
        this.initializeUI();
        this.loadDocument();
    }

    initializeUI() {
        this.container.innerHTML = `
            <div class="pdf-viewer">
                <div class="pdf-toolbar">
                    <div class="toolbar-group">
                        <button id="prev-page" class="btn btn-icon" title="Previous Page">
                            <i class="fas fa-chevron-left"></i>
                        </button>
                        <span class="page-controls">
                            <input type="number" id="current-page" value="1" min="1"> 
                            of 
                            <span id="total-pages">-</span>
                        </span>
                        <button id="next-page" class="btn btn-icon" title="Next Page">
                            <i class="fas fa-chevron-right"></i>
                        </button>
                    </div>
                    
                    <div class="toolbar-group">
                        <button id="zoom-out" class="btn btn-icon" title="Zoom Out">
                            <i class="fas fa-search-minus"></i>
                        </button>
                        <span id="zoom-level">100%</span>
                        <button id="zoom-in" class="btn btn-icon" title="Zoom In">
                            <i class="fas fa-search-plus"></i>
                        </button>
                        <button id="fit-width" class="btn btn-sm">Fit Width</button>
                        <button id="fit-page" class="btn btn-sm">Fit Page</button>
                    </div>

                    <div class="toolbar-group">
                        <button id="fullscreen" class="btn btn-icon" title="Fullscreen">
                            <i class="fas fa-expand"></i>
                        </button>
                        <a id="download-pdf" class="btn btn-sm" title="Download PDF">
                            <i class="fas fa-download"></i> Download
                        </a>
                    </div>
                </div>

                <div class="pdf-content">
                    <div class="pdf-sidebar">
                        <h4>Page Thumbnails</h4>
                        <div id="page-thumbnails" class="page-thumbnails">
                            <!-- Thumbnails will be loaded here -->
                        </div>
                    </div>
                    
                    <div class="pdf-main">
                        <div id="page-container" class="page-container">
                            <canvas id="pdf-canvas"></canvas>
                            <div id="annotations-overlay" class="annotations-overlay">
                                <!-- Annotations will be rendered here -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.setupEventListeners();
    }

    setupEventListeners() {
        // Page navigation
        document.getElementById('prev-page').addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.goToPage(this.currentPage - 1);
            }
        });

        document.getElementById('next-page').addEventListener('click', () => {
            if (this.currentPage < this.totalPages) {
                this.goToPage(this.currentPage + 1);
            }
        });

        document.getElementById('current-page').addEventListener('change', (e) => {
            const page = parseInt(e.target.value);
            if (page >= 1 && page <= this.totalPages) {
                this.goToPage(page);
            }
        });

        // Zoom controls
        document.getElementById('zoom-in').addEventListener('click', () => {
            this.setZoom(this.zoomLevel * 1.2);
        });

        document.getElementById('zoom-out').addEventListener('click', () => {
            this.setZoom(this.zoomLevel / 1.2);
        });

        document.getElementById('fit-width').addEventListener('click', () => {
            this.fitToWidth();
        });

        document.getElementById('fit-page').addEventListener('click', () => {
            this.fitToPage();
        });

        // Download link
        document.getElementById('download-pdf').href = `${API_V1_URL}/documents/${this.docId}/pdf`;
    }

    async loadDocument() {
        try {
            // Get document pages info
            const response = await fetch(`${API_V1_URL}/documents/${this.docId}/pages`);
            const pagesData = await response.json();
            
            this.totalPages = pagesData.total_pages;
            this.pages = pagesData.pages;
            
            document.getElementById('total-pages').textContent = this.totalPages;
            document.getElementById('current-page').max = this.totalPages;
            
            this.loadThumbnails();
            this.renderPage(1);
            
        } catch (error) {
            console.error('Error loading document:', error);
            this.container.innerHTML = '<div class="error">Failed to load document</div>';
        }
    }

    async loadThumbnails() {
        const thumbnailsContainer = document.getElementById('page-thumbnails');
        
        for (let i = 1; i <= this.totalPages; i++) {
            const thumbnail = document.createElement('div');
            thumbnail.className = 'page-thumbnail';
            thumbnail.dataset.page = i;
            
            const img = document.createElement('img');
            img.src = `${API_V1_URL}/documents/${this.docId}/preview/${i}?dpi=72`;
            img.alt = `Page ${i}`;
            img.loading = 'lazy';
            
            const label = document.createElement('span');
            label.textContent = i;
            
            thumbnail.appendChild(img);
            thumbnail.appendChild(label);
            thumbnailsContainer.appendChild(thumbnail);
            
            // Add click handler
            thumbnail.addEventListener('click', () => {
                this.goToPage(i);
            });
        }
    }

    async renderPage(pageNumber) {
        const canvas = document.getElementById('pdf-canvas');
        const ctx = canvas.getContext('2d');
        
        try {
            // Load page preview
            const img = new Image();
            img.onload = () => {
                // Set canvas size
                canvas.width = img.width * this.zoomLevel;
                canvas.height = img.height * this.zoomLevel;
                
                // Clear and draw
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                
                // Load and render annotations
                this.loadPageAnnotations(pageNumber);
            };
            
            img.src = `${API_V1_URL}/documents/${this.docId}/preview/${pageNumber}?dpi=150`;
            
            this.currentPage = pageNumber;
            document.getElementById('current-page').value = pageNumber;
            
            // Update thumbnail selection
            document.querySelectorAll('.page-thumbnail').forEach(thumb => {
                thumb.classList.toggle('active', parseInt(thumb.dataset.page) === pageNumber);
            });
            
        } catch (error) {
            console.error('Error rendering page:', error);
        }
    }

    async loadPageAnnotations(pageNumber) {
        try {
            const response = await fetch(`${API_V1_URL}/documents/${this.docId}/annotations?page_number=${pageNumber}`);
            const annotations = await response.json();
            
            this.renderAnnotations(annotations);
            
        } catch (error) {
            console.error('Error loading annotations:', error);
        }
    }

    renderAnnotations(annotations) {
        const overlay = document.getElementById('annotations-overlay');
        overlay.innerHTML = '';
        
        annotations.forEach(annotation => {
            const annotationEl = document.createElement('div');
            annotationEl.className = `annotation annotation-${annotation.type}`;
            annotationEl.style.cssText = `
                position: absolute;
                left: ${annotation.x * this.zoomLevel}px;
                top: ${annotation.y * this.zoomLevel}px;
                width: ${annotation.width * this.zoomLevel}px;
                height: ${annotation.height * this.zoomLevel}px;
                background-color: ${annotation.color}80;
                border: 2px solid ${annotation.color};
                pointer-events: auto;
                cursor: pointer;
            `;
            
            if (annotation.content) {
                annotationEl.title = annotation.content;
            }
            
            overlay.appendChild(annotationEl);
        });
    }

    goToPage(pageNumber) {
        if (pageNumber >= 1 && pageNumber <= this.totalPages) {
            this.renderPage(pageNumber);
        }
    }

    setZoom(zoomLevel) {
        this.zoomLevel = Math.max(0.25, Math.min(3.0, zoomLevel));
        document.getElementById('zoom-level').textContent = Math.round(this.zoomLevel * 100) + '%';
        this.renderPage(this.currentPage);
    }

    fitToWidth() {
        const container = document.querySelector('.pdf-main');
        const canvas = document.getElementById('pdf-canvas');
        const containerWidth = container.clientWidth - 40; // Account for padding
        
        if (this.pages[this.currentPage - 1]) {
            const pageWidth = this.pages[this.currentPage - 1].width;
            const newZoom = containerWidth / pageWidth;
            this.setZoom(newZoom);
        }
    }

    fitToPage() {
        const container = document.querySelector('.pdf-main');
        const containerWidth = container.clientWidth - 40;
        const containerHeight = container.clientHeight - 40;
        
        if (this.pages[this.currentPage - 1]) {
            const page = this.pages[this.currentPage - 1];
            const widthZoom = containerWidth / page.width;
            const heightZoom = containerHeight / page.height;
            const newZoom = Math.min(widthZoom, heightZoom);
            this.setZoom(newZoom);
        }
    }
}

// ============================================
// Integration with Main App
// ============================================

// Extend the main app to include new features
function initializeDocumentFeatures(docId) {
    // Initialize all document management features
    const notesManager = new DocumentNotesManager(docId);
    const organizationManager = new DocumentOrganizationManager();
    const pdfViewer = new PDFViewer(docId, 'document-viewer-container');
    
    return {
        notes: notesManager,
        organization: organizationManager,
        viewer: pdfViewer
    };
}

// Add to existing document detail view
function enhanceDocumentView(docId) {
    const features = initializeDocumentFeatures(docId);
    
    // Add document action buttons
    const actionsHTML = `
        <div class="document-actions">
            <button id="favorite-btn" class="btn btn-outline">
                <i class="fas fa-star"></i> Favorite
            </button>
            <button id="organize-btn" class="btn btn-outline">
                <i class="fas fa-folder-plus"></i> Add to Folder
            </button>
            <button id="tag-btn" class="btn btn-outline">
                <i class="fas fa-tag"></i> Add Tags
            </button>
        </div>
    `;
    
    const titleEl = document.querySelector('.document-title');
    if (titleEl) {
        titleEl.insertAdjacentHTML('afterend', actionsHTML);
    }
}

// Export for use in main app.js
window.DocumentFeatures = {
    NotesManager: DocumentNotesManager,
    OrganizationManager: DocumentOrganizationManager,
    PDFViewer: PDFViewer,
    initialize: initializeDocumentFeatures,
    enhance: enhanceDocumentView
};