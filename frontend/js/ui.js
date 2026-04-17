// UI Module - Handles all UI updates and rendering
const UI_BUILD = '20260414';

const UI = {
    /**
     * Update API status indicator
     */
    updateAPIStatus(isOnline) {
        const statusEl = document.getElementById('apiStatus');
        if (isOnline) {
            statusEl.innerHTML = `✓ API Online <span class="ui-build">(UI ${UI_BUILD})</span>`;
            statusEl.className = 'api-status online';
        } else {
            statusEl.innerHTML = `✗ API Offline <span class="ui-build">(UI ${UI_BUILD})</span> - Start server with: python -m uvicorn app.main:app --reload`;
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
    showLoading(containerId, message = 'Analyzing your argument... This may take 30-90 seconds.') {
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

        const msg = String(message || 'An unexpected error occurred.');
        const ml = msg.toLowerCase();
        const showApiHint = (
            ml.includes('failed to reach api') ||
            ml.includes('failed to fetch') ||
            ml.includes('cors') ||
            ml.includes('connection') ||
            ml.includes('connection refused') ||
            ml.includes('http error') ||
            ml.includes('status: 5') ||
            ml.includes('status: 4')
        );

        container.innerHTML = `
            <div class="error">
                ❌ ${UI.escapeHtml(msg)}
                ${showApiHint ? '<br><br>Make sure the API server is running on port 8000.' : ''}
            </div>
        `;
    },

    /** Build a lookup map: evidence_id → evidence item */
    buildEvidenceMap(data) {
        const map = {};
        (data.evidence || []).forEach(e => { map[e.evidence_id] = e; });
        (data.similar_cases || []).forEach(e => { map[e.evidence_id] = e; });
        return map;
    },

    /**
     * Rank evidence items by word-overlap relevance to a given text.
     * Returns the top-n most relevant items (different per category).
     */
    rankEvidenceFor(text, evidenceItems, n = 2) {
        if (!evidenceItems.length) return [];
        const words = new Set((text.toLowerCase().match(/[a-z]{4,}/g) || []));
        const scored = evidenceItems.map(item => {
            const evWords = (item.excerpt || '').toLowerCase().match(/[a-z]{4,}/g) || [];
            let overlap = 0;
            evWords.forEach(w => { if (words.has(w)) overlap++; });
            return { item, overlap };
        });
        scored.sort((a, b) => b.overlap - a.overlap);
        return scored.slice(0, n).map(s => s.item);
    },

    /** Extract unique citation IDs like 'E1','E2' from a rationale string */
    extractCitationIds(text) {
        // Match [E1], [e1], [E12] etc. (case-insensitive)
        const found = text.match(/\[E\d+\]/gi) || [];
        return [...new Set(found.map(t => t.replace(/[\[\]]/g, '').toUpperCase()))]; // ['E1','E2']
    },

    /** Wrap [E#] tags in styled spans inside a rationale string */
    highlightCitations(text) {
        // Strip [E#] citation tags and any surrounding parenthetical "(See [E#]...)" notes
        const cleaned = (text || '')
            .replace(/\s*\(See \[E\d+\][^)]*\)/gi, '')
            .replace(/\[E\d+\]/gi, '')
            .trim();
        return UI.escapeHtml(cleaned);
    },

    /** Best-effort: summarize an excerpt into a short, UI-friendly sentence */
    summarizeExcerpt(excerpt, maxLen = 120) {
        const raw = (excerpt || '').trim();
        if (!raw) return '';

        // Remove leading paragraph numbering like "25." or "(25)".
        let t = raw.replace(/^\s*\(?\s*\d{1,4}\s*\)?\s*[\.)]\s+/, '');

        // Prefer first sentence-ish chunk.
        const m = t.match(/^(.+?)(\.|\?|!)(\s|$)/);
        let first = m ? (m[1] + m[2]) : t;

        first = first.replace(/\s+/g, ' ').trim();
        if (first.length > maxLen) first = first.slice(0, maxLen).trimEnd() + '\u2026';
        return first;
    },

    /** Format a location label for an evidence item (prefer para over page) */
    formatEvidenceLocation(item) {
        if (!item) return '';
        if (item.para_estimate) return `Para ${item.para_estimate}`;
        if (item.page_estimate) return `Page ${item.page_estimate}`;
        return '';
    },

    /** Build ordered list of cited evidence items (uploaded docs only) */
    buildDocumentSupportItems(data) {
        const evidenceMap = UI.buildEvidenceMap(data);

        // Pull citations in order of appearance across category rationales.
        const orderedIds = [];
        const seen = new Set();
        (data.breakdown || []).forEach(cat => {
            const ids = UI.extractCitationIds((cat && cat.rationale) || '');
            ids.forEach(id => {
                if (!seen.has(id)) {
                    seen.add(id);
                    orderedIds.push(id);
                }
            });
        });

        const items = orderedIds
            .map(id => evidenceMap[id])
            .filter(Boolean);

        // De-dup by (source_id + para/page) to avoid repeats
        const uniq = [];
        const keySeen = new Set();
        items.forEach(it => {
            const loc = UI.formatEvidenceLocation(it);
            const key = `${it.source_id || ''}|${loc}|${(it.excerpt || '').slice(0, 60)}`;
            if (!keySeen.has(key)) {
                keySeen.add(key);
                uniq.push(it);
            }
        });
        return uniq.slice(0, 6);
    },

    /** Fallback: show top retrieved items when no [E#] citations were detected */
    buildFallbackSupportItems(data) {
        const all = [...(data.evidence || []), ...(data.similar_cases || [])].filter(Boolean);
        if (!all.length) return [];

        // Prefer uploaded docs first, then higher similarity score.
        all.sort((a, b) => {
            const ap = a.source === 'uploaded_doc' ? 0 : 1;
            const bp = b.source === 'uploaded_doc' ? 0 : 1;
            if (ap !== bp) return ap - bp;
            const as = Number(a.score ?? 0);
            const bs = Number(b.score ?? 0);
            return bs - as;
        });

        const out = [];
        const seen = new Set();
        for (const it of all) {
            const loc = UI.formatEvidenceLocation(it);
            const key = `${it.source || ''}|${it.source_id || ''}|${loc}|${(it.excerpt || '').slice(0, 80)}`;
            if (seen.has(key)) continue;
            seen.add(key);
            out.push(it);
            if (out.length >= 6) break;
        }
        return out;
    },

    /** Map a 0-5 rubric score to a CSS level class */
    scoreLevel(rubricScore) {
        if (rubricScore >= 4) return 'strong';
        if (rubricScore >= 3) return 'moderate';
        if (rubricScore >= 2) return 'weak';
        return 'very-weak';
    },

    /**
     * Render a compact inline blockquote for a cited evidence item.
     * Shows source label, [E#] id, title, and the actual excerpt as a styled quote.
     */
    renderInlineQuote(item) {
        const isUploaded = item.source === 'uploaded_doc';
        const sourceLabel = isUploaded ? '📄 Uploaded Document' : '⚖️ Prior Judgment';
        const raw = item.excerpt || '';
        const excerpt = raw.length > 380 ? raw.slice(0, 380).trimEnd() + '\u2026' : raw;
        const pageHtml = (isUploaded && item.page_estimate)
            ? `<span class="ev-page-badge">Page&nbsp;${item.page_estimate}</span>`
            : '';
        return `
            <div class="ev-quote ev-quote-${UI.escapeHtml(item.source)}">
                <div class="ev-quote-row1">
                    <span class="ev-badge ${UI.escapeHtml(item.source)}">${sourceLabel}</span>
                    <span class="ev-id">[${UI.escapeHtml(item.evidence_id)}]</span>
                    ${pageHtml}
                </div>
                <div class="ev-quote-row2">
                    <span class="ev-title-full">${UI.escapeHtml(item.title)}</span>
                </div>
                <blockquote class="ev-quote-text">${UI.escapeHtml(excerpt)}</blockquote>
            </div>`;
    },

    /** Render a single evidence item card */
    renderEvidenceItem(item) {
        const sourceLabel = item.source === 'uploaded_doc'
            ? '📄 Uploaded Document'
            : '⚖️ Prior Judgment';
        return `
            <div class="ev-item ev-${UI.escapeHtml(item.source)}">
                <div class="ev-item-header">
                    <span class="ev-badge ${UI.escapeHtml(item.source)}">${sourceLabel}</span>
                    <span class="ev-id">[${UI.escapeHtml(item.evidence_id)}]</span>
                    <span class="ev-title">${UI.escapeHtml(item.title)}</span>
                    <span class="ev-score">similarity: ${Number(item.score).toFixed(3)}</span>
                </div>
                <div class="ev-excerpt">${UI.escapeHtml(item.excerpt)}</div>
            </div>`;
    },

    /**
     * Display analysis results
     */
    displayResults(data, containerId, fileInfo = null) {
        const container = document.getElementById(containerId);
        const weakCategories = data.breakdown.filter(cat => cat.rubric_score < 3);
        const evidenceMap = UI.buildEvidenceMap(data);
        const hasEvidence = Object.keys(evidenceMap).length > 0;
        const docSupportShown = (data.doc_support_shown === true);
        // Ordered list of all evidence items for fallback display
        const allEvidenceItems = [...(data.evidence || []), ...(data.similar_cases || [])];

        let html = '<div class="results">';

        // ── Score Card ──────────────────────────────────────────────
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

        // ── Backend warning (e.g. fallback/template mode) ───────────
        if (data.warning) {
            html += `
                <div class="error" style="margin-top:12px;">
                    ⚠️ ${UI.escapeHtml(data.warning)}
                </div>
            `;
        }

        // ── File info ───────────────────────────────────────────────
        if (fileInfo) {
            html += `
                <div class="file-info">
                    <p><strong>📄 File:</strong> ${UI.escapeHtml(fileInfo.filename)}</p>
                    <p><strong>📝 Length:</strong> ${fileInfo.text_length.toLocaleString()} characters</p>
                </div>
            `;
        }

        // ── Category Breakdown ───────────────────────────────────────
        html += '<h3 class="section-title">Category Breakdown</h3>';
        html += '<div class="category-grid">';

        const LETTERS = ['A','B','C','D','E','F','G','H'];

        data.breakdown.forEach((category, idx) => {
            const percentage = (category.rubric_score / 5) * 100;
            const level = UI.scoreLevel(category.rubric_score);
            const letter = LETTERS[idx] || String(idx + 1);
            const icon = category.rubric_score >= 4 ? '✅' : (category.rubric_score >= 3 ? 'ℹ️' : '⚠️');
            const citationIds = UI.extractCitationIds(category.rationale);
            const citedItems = citationIds.map(id => evidenceMap[id]).filter(Boolean);
            // Fallback: rank ALL evidence by relevance to THIS category's rationale
            const fallbackItems = citedItems.length > 0
                ? citedItems
                : UI.rankEvidenceFor(category.rationale + ' ' + (category.argument_quote || ''), allEvidenceItems, 2);
            const isFallback = citedItems.length === 0 && fallbackItems.length > 0;
            const displayItems = fallbackItems;

            // Argument quote — what the user wrote relevant to this category
            const aq = (category.argument_quote || '').trim();
            const quoteHtml = aq
                ? `<div class="cat-arg-quote"><span class="cat-quote-label">📝 Your argument says:</span> \u201c${UI.escapeHtml(aq)}\u201d</div>`
                : '';

            // Judgment quote — from uploaded document
            const jq = (category.judgment_quote || '').trim();
            const jqIsNoExtract = jq.toLowerCase().startsWith('no supporting extract');
            const judgmentQuoteHtml = jq
                ? (jqIsNoExtract
                    ? `<p class="no-evidence-note">⚖️ ${UI.escapeHtml(jq)}</p>`
                    : `<div class="cat-judgment-quote"><span class="cat-quote-label">⚖️ Source document says:</span> \u201c${UI.escapeHtml(jq)}\u201d</div>`)
                : '';

            // Strengths — what was done well
            const strengths = Array.isArray(category.strengths) ? category.strengths : [];
            const strengthsHtml = strengths.length
                ? `<div class="cat-section-block cat-section-strengths">
                        <p class="ev-section-label cat-section-heading">✅ What you did well</p>
                        <ul class="cat-bullets cat-strengths">${
                            strengths.map(s => `<li>${UI.escapeHtml(s)}</li>`).join('')
                        }</ul>
                   </div>`
                : '';

            // Gaps — what caused the lost points
            const gaps = Array.isArray(category.gaps) ? category.gaps : [];
            const gapsHtml = gaps.length
                ? `<div class="cat-section-block cat-section-gaps">
                        <p class="ev-section-label cat-section-heading">❌ What cost you points</p>
                        <ul class="cat-bullets cat-gaps">${
                            gaps.map(g => `<li>${UI.escapeHtml(g)}</li>`).join('')
                        }</ul>
                   </div>`
                : '';

            // Per-category document support (computed by backend in grounded mode)
            const support = Array.isArray(category.support_detected) ? category.support_detected : [];
            const ratioPct = (category.support_ratio_percent === 0 || category.support_ratio_percent)
                ? Number(category.support_ratio_percent)
                : null;
            const ratioLabel = (category.support_ratio_label || '').trim();
            const ratioText = (ratioPct !== null && ratioLabel)
                ? `Support Ratio: <strong>${UI.escapeHtml(ratioLabel)} (${ratioPct}%)</strong>`
                : (ratioPct !== null
                    ? `Support Ratio: <strong>${ratioPct}%</strong>`
                    : '');

            // Claim counts (present only when LLM path succeeded)
            const totalClaims     = (category.total_claims != null)     ? Number(category.total_claims)     : null;
            const supportedClaims = (category.supported_claims != null) ? Number(category.supported_claims) : null;
            const claimCountText  = (totalClaims !== null && supportedClaims !== null)
                ? `Detected <strong>${totalClaims}</strong> claim${totalClaims !== 1 ? 's' : ''}: `
                  + `<strong>${supportedClaims}</strong> supported`
                : '';

            // "Not referenced" list
            const notRef = Array.isArray(category.not_referenced) ? category.not_referenced.filter(Boolean) : [];
            const notRefHtml = notRef.length
                ? `<div class="cat-not-referenced">
                       <p class="cat-not-ref-heading">⚠️ Not referenced in judgment:</p>
                       <ul class="cat-bullets cat-not-ref-list">${notRef.map(n => `<li>${UI.escapeHtml(n)}</li>`).join('')}</ul>
                   </div>`
                : '';

            // Filter out "Argument citation:" bullets — only show document citations
            const docSupport = support.filter(s => !s.startsWith('Argument citation:'));

            const shouldRenderSupport = docSupportShown && (
                docSupport.length > 0 ||
                !!claimCountText ||
                ratioPct !== null ||
                notRef.length > 0
            );

            const supportHtml = shouldRenderSupport
                ? `<div class="cat-section-block cat-section-support">
                        <p class="ev-section-label cat-section-heading">📄 Document Support Detected</p>
                        ${claimCountText ? `<p class="cat-claim-count">${claimCountText}</p>` : ''}
                        ${ratioText ? `<p class="cat-support-ratio">${ratioText}</p>` : ''}
                        ${docSupport.length > 0
                            ? `<ul class="cat-bullets cat-support">${docSupport.map(s => `<li>${UI.escapeHtml(s)}</li>`).join('')}</ul>`
                            : `<p class="no-evidence-note">ℹ️ No mapped support detected for this category.</p>`}
                        ${notRefHtml}
                   </div>`
                : '';

            const pts = category.points ?? (category.rubric_score / 5 * category.weight).toFixed(1);

            html += `
                <div class="category-card score-${level}">
                    <div class="cat-header-row cat-toggle" onclick="this.closest('.category-card').classList.toggle('cat-expanded')">
                        <span class="cat-letter">${letter}</span>
                        <div class="cat-title-block">
                            <span class="category-name">${UI.escapeHtml(category.category)}</span>
                        </div>
                        <div class="cat-score-block">
                            <span class="cat-score-fraction score-${level}">${category.rubric_score} / 5</span>
                        </div>
                        <span class="cat-chevron">&#9660;</span>
                    </div>
                    <div class="cat-body">
                        <div class="cat-points-row">
                            Points: <strong>${pts}</strong>
                        </div>
                        <div class="category-bar">
                            <div class="category-bar-fill" style="width: ${percentage}%"></div>
                        </div>
                        <div class="cat-reason-section">
                            <p class="ev-section-label cat-section-heading">📋 Why you got this score</p>
                            ${quoteHtml}
                            ${judgmentQuoteHtml}
                            <div class="category-rationale">${UI.highlightCitations(category.rationale)}</div>
                        </div>
                        ${strengthsHtml}
                        ${gapsHtml}
                        ${supportHtml}
                    </div>
                </div>
            `;
        });

        html += '</div>'; // end category-grid

        // ── Suggestions for Improvement ─────────────────────────────
        if (data.feedback && data.feedback.length > 0) {
            html += `
                <div class="feedback-section">
                    <h3>💡 Suggestions for Improvement</h3>
                    <ul>
                        ${data.feedback.map(s => `<li>${UI.escapeHtml(s)}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // ── Areas Needing Attention ──────────────────────────────────
        if (weakCategories.length > 0) {
            html += `
                <div class="weaknesses-section">
                    <h3>⚠️ Areas Needing Attention</h3>
                    <ul>
                        ${weakCategories.map(cat => `
                            <li><strong>${UI.escapeHtml(cat.category)}:</strong>
                                ${UI.highlightCitations(cat.rationale)}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }

        html += '</div>'; // end .results
        container.innerHTML = html;

        // Trigger bar animations
        setTimeout(() => {
            document.querySelectorAll('.category-bar-fill').forEach(fill => {
                fill.style.width = fill.style.width;
            });
        }, 100);
    },

    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        return String(text)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');
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
