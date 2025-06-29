// N-gram Chinese Text Analyzer - Frontend JavaScript

class NgramAnalyzer {
    constructor() {
        this.currentResults = [];
        this.filenames = [];
        this.currentLang = this.getCurrentLanguage();
        this.initializeEventListeners();
        this.initializeTooltips();
        this.initializeLanguageSwitcher();
    }

    getCurrentLanguage() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('lang') || 'ko';
    }

    initializeEventListeners() {
        // File input change
        document.getElementById('fileInput').addEventListener('change', (e) => {
            this.handleFileSelection(e);
        });

        // Analyze button
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.analyzeFiles();
        });

        // Wordcloud button
        document.getElementById('wordcloudBtn').addEventListener('click', () => {
            this.generateWordcloud();
        });

        // Download button
        document.getElementById('downloadBtn').addEventListener('click', () => {
            this.showDownloadModal();
        });

        // Apply highlight button
        document.getElementById('applyBtn').addEventListener('click', () => {
            this.showFileSelectionModal();
        });

        // Mode selection
        document.getElementById('modeSelect').addEventListener('change', (e) => {
            this.handleModeChange(e.target.value);
        });

        // Sort selection
        document.getElementById('sortSelect').addEventListener('change', () => {
            this.applyFilter();
        });

        // Include all common checkbox
        document.getElementById('includeAll').addEventListener('change', () => {
            this.applyFilter();
        });

        // Download modal confirm button
        document.getElementById('confirmDownloadBtn').addEventListener('click', () => {
            this.downloadResults();
        });

        // Apply highlight modal confirm button
        document.getElementById('applyHighlightBtn').addEventListener('click', () => {
            this.applyHighlight();
        });
    }

    initializeLanguageSwitcher() {
        // 언어 변경 버튼들에 이벤트 리스너 추가
        const langButtons = document.querySelectorAll('.lang-btn');
        langButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const lang = btn.getAttribute('data-lang');
                this.changeLanguage(lang);
            });
        });
    }

    changeLanguage(lang) {
        // URL 파라미터 업데이트
        const url = new URL(window.location);
        url.searchParams.set('lang', lang);
        window.history.pushState({}, '', url);
        
        // 페이지 새로고침으로 언어 변경
        window.location.reload();
    }

    initializeTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    handleFileSelection(event) {
        const files = event.target.files;
        if (files.length < 2) {
            this.showAlert(LOCALE.needTwo, 'danger');
            event.target.value = '';
            this.hideSelectedFilesInfo();
            return;
        }
        
        // 선택된 파일 정보 표시
        this.showSelectedFilesInfo(files);
        
        // Enable analyze button
        document.getElementById('analyzeBtn').disabled = false;
    }

    showSelectedFilesInfo(files) {
        const infoDiv = document.getElementById('selectedFilesInfo');
        const listDiv = document.getElementById('selectedFilesList');
        
        // 파일 목록 생성
        const fileList = Array.from(files).map(file => {
            const fileName = file.name.replace(/\.[^/.]+$/, ""); // 확장자 제거
            return `<span class="badge bg-primary me-1 mb-1">${fileName}</span>`;
        }).join('');
        
        listDiv.innerHTML = fileList;
        infoDiv.style.display = 'block';
    }

    hideSelectedFilesInfo() {
        const infoDiv = document.getElementById('selectedFilesInfo');
        infoDiv.style.display = 'none';
    }

    async analyzeFiles() {
        const files = document.getElementById('fileInput').files;
        const minN = parseInt(document.getElementById('minN').value);
        const maxN = parseInt(document.getElementById('maxN').value);

        if (files.length < 2) {
            this.showAlert(LOCALE.needTwo, 'danger');
            return;
        }

        if (minN < 1 || maxN < minN) {
            this.showAlert(LOCALE.ngramRangeError || 'N-gram 범위가 올바르지 않습니다.', 'danger');
            return;
        }

        this.showLoadingModal(LOCALE.analyzing);

        const formData = new FormData();
        formData.append('min_n', minN);
        formData.append('max_n', maxN);
        
        for (let file of files) {
            formData.append('files', file);
        }

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                this.currentResults = result.results;
                this.filenames = result.filenames;
                this.displayResults(result.results);
                this.updateDataCount(result.data_count);
                this.enableActionButtons();
                this.setupFileCheckboxes();
                this.showAlert(LOCALE.analysisComplete || '분석이 완료되었습니다.', 'success');
            } else {
                throw new Error(result.detail || LOCALE.analysisError);
            }
        } catch (error) {
            this.showAlert(error.message, 'danger');
        } finally {
            this.hideLoadingModal();
        }
    }

    displayResults(results) {
        const resultsArea = document.getElementById('resultsArea');
        
        if (!results || results.length === 0) {
            resultsArea.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="fas fa-exclamation-triangle fa-3x mb-3"></i>
                    <p>${LOCALE.noValidData}</p>
                </div>
            `;
            return;
        }

        // Create table
        const table = document.createElement('table');
        table.className = 'table table-striped table-hover';
        
        // Create header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        headerRow.innerHTML = `
            <th style="width: 40%">N-gram</th>
            ${this.filenames.map(name => `<th class="text-center">${name}</th>`).join('')}
        `;
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Create body
        const tbody = document.createElement('tbody');
        results.forEach(result => {
            const row = document.createElement('tr');
            row.className = 'ngram-row';
            
            const parts = result.split(':');
            const ngram = parts[0].trim();
            const frequencies = parts.slice(1).join(':').split(',').map(p => p.trim());
            
            row.innerHTML = `
                <td class="ngram-text">${ngram}</td>
                ${this.filenames.map((name, index) => {
                    const freq = frequencies.find(f => f.startsWith(name + ':'))?.split(':')[1] || '0';
                    return `<td class="frequency-cell">${freq}</td>`;
                }).join('')}
            `;
            tbody.appendChild(row);
        });
        
        table.appendChild(tbody);
        resultsArea.innerHTML = '';
        resultsArea.appendChild(table);
    }

    setupFileCheckboxes() {
        const fileCheckboxes = document.getElementById('fileCheckboxes');
        fileCheckboxes.innerHTML = '';
        
        this.filenames.forEach(filename => {
            const div = document.createElement('div');
            div.className = 'form-check file-checkbox';
            div.innerHTML = `
                <input class="form-check-input" type="checkbox" id="file_${filename}" value="${filename}" checked>
                <label class="form-check-label" for="file_${filename}">${filename}</label>
            `;
            fileCheckboxes.appendChild(div);
        });

        // Add event listeners to checkboxes
        fileCheckboxes.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.applyFilter();
            });
        });
    }

    handleModeChange(mode) {
        const commonControls = document.getElementById('commonControls');
        if (mode === 'common') {
            commonControls.style.display = 'block';
        } else {
            commonControls.style.display = 'none';
        }
        this.applyFilter();
    }

    async applyFilter() {
        if (this.currentResults.length === 0) {
            return;
        }

        const mode = document.getElementById('modeSelect').value;
        const sortOption = document.getElementById('sortSelect').value;
        
        let selectedFiles = [];
        if (mode === 'common') {
            selectedFiles = Array.from(document.querySelectorAll('#fileCheckboxes input[type="checkbox"]:checked'))
                .map(cb => cb.value);
        }
        
        const includeAllCommon = document.getElementById('includeAll').checked;

        this.showLoadingModal(LOCALE.processing);

        const formData = new FormData();
        formData.append('mode', mode);
        formData.append('selected_files', JSON.stringify(selectedFiles));
        formData.append('include_all_common', includeAllCommon);
        formData.append('sort_option', sortOption);

        try {
            const response = await fetch('/api/filter', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                this.currentResults = result.results;
                this.displayResults(result.results);
                this.updateDataCount(result.data_count);
            } else {
                throw new Error(result.detail || LOCALE.filterError || '필터링 중 오류가 발생했습니다.');
            }
        } catch (error) {
            this.showAlert(error.message, 'danger');
        } finally {
            this.hideLoadingModal();
        }
    }

    async generateWordcloud() {
        if (this.currentResults.length === 0) {
            this.showAlert(LOCALE.noValidData, 'danger');
            return;
        }

        this.showLoadingModal(LOCALE.generatingWordcloud);

        const formData = new FormData();
        formData.append('ngrams_data', JSON.stringify(this.currentResults));

        try {
            const response = await fetch('/api/wordcloud', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                
                // Open wordcloud in new window
                const newWindow = window.open(url, '_blank');
                if (!newWindow) {
                    // If popup blocked, create download link
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'wordcloud.png';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                }
            } else {
                const result = await response.json();
                throw new Error(result.detail || LOCALE.wordcloudError);
            }
        } catch (error) {
            this.showAlert(error.message, 'danger');
        } finally {
            this.hideLoadingModal();
        }
    }

    showDownloadModal() {
        const modal = new bootstrap.Modal(document.getElementById('downloadModal'));
        modal.show();
    }

    async downloadResults() {
        if (this.currentResults.length === 0) {
            this.showAlert(LOCALE.noValidData, 'danger');
            return;
        }

        const format = document.querySelector('input[name="downloadFormat"]:checked').value;
        
        this.showLoadingModal(LOCALE.downloading);

        const formData = new FormData();
        formData.append('results_data', JSON.stringify(this.currentResults));
        formData.append('format_type', format);

        try {
            const response = await fetch('/api/download', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                
                // 파일 확장자 설정
                let extension = format;
                if (format === 'docx') extension = 'docx';
                else if (format === 'hwp') extension = 'hwp';
                else if (format === 'html') extension = 'html';
                
                a.download = `ngram_analysis.${extension}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } else {
                const result = await response.json();
                throw new Error(result.detail || LOCALE.downloadError);
            }
        } catch (error) {
            this.showAlert(error.message, 'danger');
        } finally {
            this.hideLoadingModal();
            bootstrap.Modal.getInstance(document.getElementById('downloadModal')).hide();
        }
    }

    showFileSelectionModal() {
        if (this.filenames.length === 0) {
            this.showAlert(LOCALE.analyzeFirst || '먼저 파일을 분석해주세요.', 'danger');
            return;
        }

        const fileSelectionList = document.getElementById('fileSelectionList');
        fileSelectionList.innerHTML = '';
        
        this.filenames.forEach(filename => {
            const div = document.createElement('div');
            div.className = 'form-check mb-2';
            div.innerHTML = `
                <input class="form-check-input" type="radio" name="selectedFile" id="highlight_${filename}" value="${filename}">
                <label class="form-check-label" for="highlight_${filename}">${filename}</label>
            `;
            fileSelectionList.appendChild(div);
        });

        const modal = new bootstrap.Modal(document.getElementById('fileSelectionModal'));
        modal.show();
    }

    async applyHighlight() {
        const selectedFile = document.querySelector('input[name="selectedFile"]:checked');
        if (!selectedFile) {
            this.showAlert(LOCALE.selectFile || '파일을 선택해주세요.', 'danger');
            return;
        }

        const filename = selectedFile.value;
        const selectedNgrams = this.currentResults.map(result => result.split(':')[0].trim());

        // 선택된 N-gram이 있는지 확인
        if (selectedNgrams.length === 0) {
            this.showAlert('분석 결과가 없습니다.', 'danger');
            return;
        }

        this.showLoadingModal(LOCALE.applyingHighlight);

        const formData = new FormData();
        formData.append('file_name', filename);
        formData.append('selected_ngrams', JSON.stringify(selectedNgrams));
        formData.append('lang', this.currentLang);

        try {
            console.log('Sending highlight request:', {
                file_name: filename,
                selected_ngrams: selectedNgrams,
                lang: this.currentLang
            });

            const response = await fetch('/api/apply-highlight', {
                method: 'POST',
                body: formData
            });

            console.log('Response status:', response.status);

            if (response.ok) {
                const html = await response.text();
                console.log('Received HTML length:', html.length);
                
                // Open result in new window
                const newWindow = window.open('', '_blank');
                newWindow.document.write(html);
                newWindow.document.close();
            } else {
                const result = await response.json();
                console.error('Highlight error:', result);
                throw new Error(result.detail || LOCALE.highlightError);
            }
        } catch (error) {
            console.error('Highlight application error:', error);
            this.showAlert(error.message, 'danger');
        } finally {
            this.hideLoadingModal();
            bootstrap.Modal.getInstance(document.getElementById('fileSelectionModal')).hide();
        }
    }

    updateDataCount(count) {
        const dataCountElement = document.getElementById('dataCount');
        dataCountElement.textContent = LOCALE.dataCount.replace('{count}', count);
    }

    enableActionButtons() {
        document.getElementById('wordcloudBtn').disabled = false;
        document.getElementById('downloadBtn').disabled = false;
        document.getElementById('applyBtn').disabled = false;
    }

    showLoadingModal(message) {
        document.getElementById('loadingMessage').textContent = message;
        const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
        modal.show();
    }

    hideLoadingModal() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
        if (modal) {
            modal.hide();
        }
    }

    showAlert(message, type) {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());

        // Create new alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert at the top of the container
        const container = document.querySelector('.container-fluid');
        container.insertBefore(alertDiv, container.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ngramAnalyzer = new NgramAnalyzer();
});
