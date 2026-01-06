// UI Module - Handles all UI updates and rendering
const UI = {
    /**
     * Update API status indicator
     */
    updateAPIStatus(isOnline) {
        const statusEl = document.getElementById('apiStatus');
        if (isOnline) {
            statusEl.innerHTML = '✓ API Online';
            statusEl.className = 'api-status online';
        } else {
            statusEl.innerHTML = '✗ API Offline - Start server with: python -m uvicorn app.main:app --reload';
            statusEl.className = 'api-status offline';
        }
    },

    /**
     * Update character count display
     */
    updateCharCount(length) {
        const countEl = document.getElementById('charCount');
        countEl.textContent = `${length} / ${CONFIG.MAX_TEXT_LENGTH} characters`;
        
        if (length < CONFIG.MIN_TEXT_LENGTH) {
            countEl.className = 'char-count invalid';
        } else if (length > CONFIG.MAX_TEXT_LENGTH) {
            countEl.className = 'char-count invalid';
        } else {
            countEl.className = 'char-count valid';
        }
    },

    /**
     * Show loading state
     */
    showLoading(containerId, message = 'Analyzing your argument... This may take 10-30 seconds.') {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <p class="loading-text">${message}</p>
            </div>
        `;
    },

    /**
     * Show error message
     */
    showError(containerId, message) {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <div class="error">
                ❌ ${message}
                <br><br>
                Make sure the API server is running on port 8000.
            </div>
        `;
    },

    /**
     * Display analysis results
     */
    displayResults(data, containerId, fileInfo = null) {
        const container = document.getElementById(containerId);
        const weakCategories = data.breakdown.filter(cat => cat.rubric_score < 3);
        
        let html = '<div class="results">';

        // Score Card
        html += `
            <div class="score-card">
                <div class="score-value">${data.overall_score}/100</div>
                <div class="strength-label">${data.strength_label}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${data.overall_score}%;">
                        ${data.overall_score}%
                    </div>
                </div>
            </div>
        `;

        // File Information (if file was uploaded)
        if (fileInfo) {
            html += `
                <div class="file-info">
                    <p><strong>📄 File:</strong> ${fileInfo.filename}</p>
                    <p><strong>📝 Length:</strong> ${fileInfo.text_length.toLocaleString()} characters</p>
                </div>
            `;
        }

        // Category Breakdown
        html += '<h3 class="section-title">Category Breakdown</h3>';
        html += '<div class="category-grid">';
        
        data.breakdown.forEach(category => {
            const percentage = (category.rubric_score / 5) * 100;
            html += `
                <div class="category-card">
                    <div class="category-header">
                        <span class="category-name">${category.category}</span>
                        <span class="category-score">${category.rubric_score}/5</span>
                    </div>
                    <div class="category-bar">
                        <div class="category-bar-fill" style="width: ${percentage}%"></div>
                    </div>
                    <div class="category-rationale">${category.rationale}</div>
                </div>
            `;
        });
        
        html += '</div>';

        // Suggestions for Improvement
        if (data.feedback && data.feedback.length > 0) {
            html += `
                <div class="feedback-section">
                    <h3>💡 Suggestions for Improvement</h3>
                    <ul>
                        ${data.feedback.map(suggestion => `<li>${suggestion}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // Weaknesses
        if (weakCategories.length > 0) {
            html += `
                <div class="weaknesses-section">
                    <h3>⚠️ Areas Needing Attention</h3>
                    <ul>
                        ${weakCategories.map(cat => `
                            <li><strong>${cat.category}:</strong> ${cat.rationale}</li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }

        html += '</div>';
        container.innerHTML = html;

        // Trigger animations
        setTimeout(() => {
            document.querySelectorAll('.category-bar-fill').forEach(fill => {
                fill.style.width = fill.style.width;
            });
        }, 100);
    },

    /**
     * Update file display
     */
    updateFileDisplay(fileName, fileSize) {
        const fileNameEl = document.getElementById('fileName');
        const sizeInMB = (fileSize / 1024 / 1024).toFixed(2);
        fileNameEl.textContent = `Selected: ${fileName} (${sizeInMB} MB)`;
        fileNameEl.classList.add('show');
    },

    /**
     * Clear file display
     */
    clearFileDisplay() {
        const fileNameEl = document.getElementById('fileName');
        fileNameEl.textContent = '';
        fileNameEl.classList.remove('show');
    }
};
