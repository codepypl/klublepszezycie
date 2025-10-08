/**
 * Enhanced Import contacts functionality with 5-step process:
 * 1. File upload with drag & drop
 * 1a. File analysis with lightbox
 * 2. Column mapping
 * 3. Preview mapping results
 * 4. Campaign selection
 * 5. Import to database
 */

let fileData = null;
let fileInfo = null;
let columns = [];
let isImporting = false;
let currentImportFileId = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // First check if import is in progress and disable auto-refresh
    disableAutoRefreshDuringImport();
    
    // Then initialize import functionality
    initializeImport();
});

function initializeImport() {
    // Step 1: File Upload with Drag & Drop
    setupDragAndDrop();
    setupFileSelection();
    setupFileAnalysis();

    // Step 2: Column Mapping
    setupColumnMapping();
    
    // Step 3: Preview Mapping
    setupPreviewMapping();
    
    // Step 4: Campaign Selection
    setupCampaignSelection();
    
    // Step 5: Import Process
    setupImportProcess();
    
    // Show step 1 by default
    showStep1();
}

// ===== STEP 1: FILE UPLOAD =====

function setupDragAndDrop() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('importFile');
    
    if (!dropZone || !fileInput) return;
    
    // Drag & Drop events
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    });
    
    // Click to select file
    dropZone.addEventListener('click', function() {
        fileInput.click();
    });
}

function setupFileSelection() {
    const fileInput = document.getElementById('importFile');
    const selectFileBtn = document.getElementById('selectFileBtn');
    
    if (!fileInput) return;
    
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });
    
    if (selectFileBtn) {
        selectFileBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            fileInput.click();
        });
    }
}

function handleFileSelection(file) {
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const fileInfo = document.getElementById('fileInfo');
    const dropZone = document.getElementById('dropZone');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const importFile = document.getElementById('importFile');
    const csvSeparatorGroup = document.getElementById('csvSeparatorGroup');
    
    if (!fileName || !fileSize || !fileInfo || !dropZone || !analyzeBtn || !importFile) return;
    
    // Validate file type
    const allowedTypes = ['.xlsx', '.xls', '.csv'];
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    
    if (!allowedTypes.includes(fileExtension)) {
        window.toastManager.show('Nieprawidłowy typ pliku. Obsługiwane formaty: .xlsx, .xls, .csv', 'error');
        return;
    }
    
    // Update file info display
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    fileInfo.style.display = 'block';
    dropZone.classList.add('has-file');
    analyzeBtn.disabled = false;
    
    // Show CSV separator for CSV files
    if (fileExtension === '.csv') {
        csvSeparatorGroup.style.display = 'block';
    } else {
        csvSeparatorGroup.style.display = 'none';
    }
    
    // Set file in input
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    importFile.files = dataTransfer.files;
    
    // Setup remove file functionality
    setupRemoveFile();
}

function setupRemoveFile() {
    const removeFile = document.getElementById('removeFile');
    if (!removeFile) return;
    
    removeFile.addEventListener('click', function(e) {
        e.stopPropagation();
        resetFileSelection();
    });
}

function resetFileSelection() {
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const fileInfo = document.getElementById('fileInfo');
    const dropZone = document.getElementById('dropZone');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const importFile = document.getElementById('importFile');
    const csvSeparatorGroup = document.getElementById('csvSeparatorGroup');
    
    if (!fileName || !fileSize || !fileInfo || !dropZone || !analyzeBtn || !importFile) return;
    
    fileInfo.style.display = 'none';
    dropZone.classList.remove('has-file');
    analyzeBtn.disabled = true;
    csvSeparatorGroup.style.display = 'none';
    importFile.value = '';
}

function setupFileAnalysis() {
    const importForm = document.getElementById('importForm');
    if (!importForm) return;
    
    importForm.addEventListener('submit', function(e) {
        e.preventDefault();
        handleFileAnalysis();
    });
}

function handleFileAnalysis() {
    const fileInput = document.getElementById('importFile');
    const csvSeparatorInput = document.getElementById('csvSeparator');
    const file = fileInput.files[0];
    
    if (!file) {
        window.toastManager.show('Proszę wybrać plik', 'warning');
        return;
    }
    
    // Show lightbox for analysis
    showImportLightbox();
    updateImportLightbox(10, 'Analizowanie pliku...');
    
    // Disable auto-refresh during import
    isImporting = true;
    localStorage.setItem('crm_import_in_progress', 'true');
    disableAllAutoRefresh();
    
    const formData = new FormData();
    formData.append('file', file);
    
    // Add CSV separator if file is CSV
    const fileName = file.name.toLowerCase();
    if (fileName.endsWith('.csv') && csvSeparatorInput) {
        formData.append('csv_separator', csvSeparatorInput.value);
    }
    
    updateImportLightbox(30, 'Wczytywanie pliku...');
    
    fetch('/api/crm/analyze-file', {
        method: 'POST',
        body: formData,
        credentials: 'include'
    })
    .then(response => safeJsonParse(response))
    .then(data => {
        if (data.success) {
            updateImportLightbox(70, 'Przetwarzanie danych...');
            
            // Store file info
            fileData = data.sample_data;
            fileInfo = {
                total_rows: data.total_rows,
                file_type: data.file_type
            };
            columns = data.columns;
            currentImportFileId = data.import_file_id;
            
            updateImportLightbox(90, 'Przygotowywanie mapowania...');
            
            // Populate column mappings
            populateColumnMappings();
            
            updateImportLightbox(100, 'Analiza zakończona!');
            
            setTimeout(() => {
                hideImportLightbox();
            showStep2();
                
                // Show analysis results
                const totalRows = fileInfo?.total_rows || 0;
                const columnsCount = columns?.length || 0;
                window.toastManager.show(
                    `Plik przeanalizowany: ${totalRows} rekordów, ${columnsCount} kolumn`,
                    'success'
                );
            }, 500);
            
        } else {
            hideImportLightbox();
            window.toastManager.show('Błąd analizy pliku: ' + data.error, 'error');
            resetImportState();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        hideImportLightbox();
        window.toastManager.show('Wystąpił błąd podczas analizy pliku: ' + error.message, 'error');
        resetImportState();
    });
}

// ===== STEP 2: COLUMN MAPPING =====

function setupColumnMapping() {
    const mappingForm = document.getElementById('mappingForm');
    const backToStep1 = document.getElementById('backToStep1');
    
    if (mappingForm) {
        mappingForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleColumnMapping(e);
        });
    }
    
    if (backToStep1) {
        backToStep1.addEventListener('click', function() {
            showStep1();
        });
    }
}

function handleColumnMapping(e) {
    e.preventDefault();
    
    const mapping = {
        name: document.getElementById('nameColumn').value,
        phone: document.getElementById('phoneColumn').value,
        email: document.getElementById('emailColumn').value,
        company: document.getElementById('companyColumn').value,
        notes: document.getElementById('notesColumn').value,
        tags: document.getElementById('tagsColumn').value
    };
    
    // Validate required fields - only phone is required
    if (!mapping.phone) {
        window.toastManager.show('Proszę wybrać kolumnę dla telefonu', 'warning');
        return;
    }
    
    currentMapping = mapping;
    showStep3();
    loadPreviewData();
}

function populateColumnMappings() {
    const selects = ['nameColumn', 'phoneColumn', 'emailColumn', 'companyColumn', 'notesColumn', 'tagsColumn'];
    
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        const currentValue = select.value;
        
        // Clear existing options except first
        select.innerHTML = selectId === 'phoneColumn' 
            ? '<option value="">Wybierz kolumnę</option>' 
            : '<option value="">Pomiń</option>';
        
        // Add column options
        columns.forEach(column => {
            const option = document.createElement('option');
            option.value = column;
            option.textContent = column;
            select.appendChild(option);
        });
        
        // Restore previous selection
        select.value = currentValue;
    });
}


// ===== STEP 3: PREVIEW MAPPING =====

function setupPreviewMapping() {
    const backToStep2 = document.getElementById('backToStep2');
    const refreshPreview = document.getElementById('refreshPreview');
    const previewRowsCount = document.getElementById('previewRowsCount');
    
    if (backToStep2) {
        backToStep2.addEventListener('click', function() {
            showStep2();
        });
    }
    
    if (refreshPreview) {
        refreshPreview.addEventListener('click', function() {
            loadPreviewData();
        });
    }
    
    if (previewRowsCount) {
        previewRowsCount.addEventListener('change', function() {
            loadPreviewData();
        });
    }
}

function loadPreviewData() {
    if (!currentMapping || !fileInfo || !currentImportFileId) {
        window.toastManager.show('Brak danych do podglądu', 'warning');
        return;
    }
    
    const previewContent = document.getElementById('previewContent');
    const previewRowsCount = document.getElementById('previewRowsCount');
    
    if (!previewContent || !previewRowsCount) return;
    
    // Show loading
    previewContent.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Ładowanie podglądu...</span>
            </div>
            <p class="mt-2 text-muted">Ładowanie podglądu mapowania...</p>
        </div>
    `;
    
    const rowsCount = parseInt(previewRowsCount.value) || 20;
    
    fetch('/api/crm/preview-mapping', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
            import_file_id: currentImportFileId,
            mapping: currentMapping,
            rows_count: rowsCount
        })
    })
    .then(response => safeJsonParse(response))
    .then(data => {
        if (data.success) {
            displayPreviewData(data.preview_data);
        } else {
            previewContent.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Błąd ładowania podglądu: ${data.error}
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        previewContent.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Wystąpił błąd podczas ładowania podglądu: ${error.message}
            </div>
        `;
    });
}

function displayPreviewData(previewData) {
    const previewContent = document.getElementById('previewContent');
    if (!previewContent || !previewData || !Array.isArray(previewData) || previewData.length === 0) {
        previewContent.innerHTML = '<div class="alert alert-warning">Brak danych do wyświetlenia</div>';
        return;
    }
    
    let html = `
        <div class="table-responsive">
            <table class="table table-striped table-sm">
                <thead class="table-dark">
                    <tr>
                        <th>Wiersz</th>
                        <th>Imię i nazwisko</th>
                        <th>Telefon</th>
                        <th>Email</th>
                        <th>Firma</th>
                        <th>Notatki</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    previewData.forEach((item, index) => {
        // Handle direct mapping format from preview_mapping endpoint
        html += `
            <tr>
                <td><span class="badge bg-secondary">${index + 1}</span></td>
                <td>${item.name || '<span class="text-muted">-</span>'}</td>
                <td>${item.phone || '<span class="text-danger">BRAK</span>'}</td>
                <td>${item.email || '<span class="text-muted">-</span>'}</td>
                <td>${item.company || '<span class="text-muted">-</span>'}</td>
                <td>${item.notes || '<span class="text-muted">-</span>'}</td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    previewContent.innerHTML = html;
}

// ===== STEP 4: CAMPAIGN SELECTION =====

function setupCampaignSelection() {
    const backToStep3 = document.getElementById('backToStep3');
    const proceedToImport = document.getElementById('proceedToImport');
    
    if (backToStep3) {
        backToStep3.addEventListener('click', function() {
            showStep3();
        });
    }
    
    if (proceedToImport) {
        proceedToImport.addEventListener('click', function() {
            if (validateCampaignSelection()) {
                performImport();
            }
        });
    }
    
    // Note: loadCampaignsForImport() will be called in showStep4()
}

function loadCampaignsForImport() {
    fetch('/api/crm/campaigns')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                populateCampaignSelect(data.campaigns);
            } else {
                window.toastManager.show('Błąd podczas ładowania kampanii: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error loading campaigns:', error);
            window.toastManager.show('Błąd podczas ładowania kampanii', 'error');
        });
}

function populateCampaignSelect(campaigns) {
    const select = document.getElementById('campaignSelect');
    if (!select) return;
    
    // Clear existing options
    select.innerHTML = '<option value="">Wybierz kampanię</option>';
    
    // Check if campaigns is valid array
    if (!campaigns || !Array.isArray(campaigns)) {
        console.warn('Invalid campaigns data:', campaigns);
        return;
    }
    
    // Add all campaigns with status indicator
    campaigns.forEach(campaign => {
        const option = document.createElement('option');
        option.value = campaign.id;
        option.textContent = campaign.name + (campaign.is_active ? '' : ' (nieaktywna)');
        select.appendChild(option);
    });
}

function validateCampaignSelection() {
    const campaignSelect = document.getElementById('campaignSelect');
    const campaignId = campaignSelect.value;
    
    if (!campaignId) {
        window.toastManager.show('Proszę wybrać kampanię', 'warning');
        campaignSelect.focus();
        return false;
    }
    
    return true;
}

// ===== STEP 5: IMPORT PROCESS =====

function setupImportProcess() {
    const startImport = document.getElementById('startImport');
    
    if (startImport) {
        startImport.addEventListener('click', function() {
            if (window.validateMapping()) {
                showStep4(); // Show campaign selection first
            }
        });
    }
}

async function performImport() {
    console.log('🔍 performImport - checking data:');
    console.log('  window.currentMapping:', window.currentMapping);
    console.log('  fileInfo:', fileInfo);
    console.log('  currentImportFileId:', currentImportFileId);
    
    if (!window.currentMapping || !fileInfo || !currentImportFileId) {
        window.toastManager.show('Brak danych do importu', 'warning');
        return;
    }
    
    // Get selected campaign
    const campaignSelect = document.getElementById('campaignSelect');
    const campaignId = campaignSelect.value;
    
    if (!campaignId) {
        window.toastManager.show('Proszę wybrać kampanię', 'warning');
        return;
    }
    
    showStep5(); // Show import progress
    updateImportStatus(0, 'Rozpoczynanie importu...');
    
    try {
        // Step 1: Extract file to database (if not already done)
        updateImportLightbox(10, 'Wyciąganie danych z pliku...');
        
        const extractResponse = await fetch('/api/crm/extract-file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                import_file_id: currentImportFileId
            })
        });
        
        const extractData = await safeJsonParse(extractResponse);
        
        console.log('🔍 extractData response:', extractData);
        
        if (!extractData.success) {
            throw new Error(extractData.error);
        }
        
        currentImportFileId = extractData.import_file_id;
        console.log('🔍 currentImportFileId after extract:', currentImportFileId);
        
        // Step 2: Process records with mapping
        updateImportLightbox(30, 'Przetwarzanie rekordów...');
        
        const requestBody = {
            import_file_id: currentImportFileId,
            mapping: window.currentMapping,
            campaign_id: parseInt(campaignId)
        };
        
        console.log('🔍 performImport - request body:', requestBody);
        
        const processResponse = await fetch('/api/crm/process-import', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(requestBody)
        });
        
        const processData = await safeJsonParse(processResponse);
        
        if (processData.success) {
            updateImportLightbox(90, 'Finalizowanie importu...');
            updateImportLightbox(100, `Import zakończony! Zaimportowano: ${processData.imported}, Pominięto: ${processData.skipped}`);
            
            setTimeout(() => {
                hideImportLightbox();
                resetImportState();
                showStep1();
                
                // Show success message
                window.toastManager.show(
                    `Import zakończony pomyślnie! Zaimportowano: ${processData.imported_count} kontaktów, Pominięto: ${processData.failed_count}`,
                    'success'
                );
                
                // Refresh contacts list
                if (typeof refreshContacts === 'function') {
                    refreshContacts();
                } else {
                    // Fallback to page reload
                    window.location.reload();
                }
            }, 1500);
            
        } else {
            throw new Error(processData.error);
        }
        
    } catch (error) {
        console.error('Import error:', error);
        hideImportLightbox();
        window.toastManager.show('Błąd importu: ' + error.message, 'error');
        resetImportState();
    }
}

// ===== STEP NAVIGATION =====

function showStep1() {
    hideAllSteps();
    const step1 = document.getElementById('importStep1');
    if (step1) step1.style.display = 'block';
    
    // Stop auto-refresh
    if (typeof stopContactsAutoRefresh === 'function') {
        stopContactsAutoRefresh();
    }
}

function showStep2() {
    hideAllSteps();
    const step2 = document.getElementById('importStep2');
    if (step2) step2.style.display = 'block';
}

function showStep3() {
    hideAllSteps();
    const step3 = document.getElementById('importStep3');
    if (step3) step3.style.display = 'block';
    
    // NO auto-refresh in step 3 (Preview) - it would interfere with loading
    // Auto-refresh only happens in step 4 (Import Progress)
}

function showStep4() {
    hideAllSteps();
    const step4 = document.getElementById('importStep4');
    if (step4) step4.style.display = 'block';
    
    // Load campaigns for selection
    loadCampaignsForImport();
}

function showStep5() {
    hideAllSteps();
    const step5 = document.getElementById('importStep5');
    if (step5) step5.style.display = 'block';
    
    // Start auto-refresh in step 5
    if (typeof setupContactsAutoRefresh === 'function') {
        setupContactsAutoRefresh();
    }
}

function hideAllSteps() {
    const steps = ['importStep1', 'importStep2', 'importStep3', 'importStep4', 'importStep5'];
    steps.forEach(stepId => {
        const step = document.getElementById(stepId);
        if (step) step.style.display = 'none';
    });
}

// ===== UTILITY FUNCTIONS =====

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function resetImportState() {
    isImporting = false;
    localStorage.removeItem('crm_import_in_progress');
    
    // Stop auto-refresh
    if (typeof stopContactsAutoRefresh === 'function') {
        stopContactsAutoRefresh();
    }
    
    // Clear data
    fileData = null;
    fileInfo = null;
    columns = [];
    currentImportFileId = null;
    window.currentMapping = null;
    
    // Reset file selection
    resetFileSelection();
}

function disableAutoRefreshDuringImport() {
    const isImportInProgress = localStorage.getItem('crm_import_in_progress') === 'true';
    if (isImportInProgress) {
        isImporting = true;
        if (typeof disableAllAutoRefresh === 'function') {
            disableAllAutoRefresh();
        }
    }
}

function disableAllAutoRefresh() {
    // Disable global refresh system
    // Auto-refresh is now handled by refreshAfterCRUD() system
}

function enableAllAutoRefresh() {
    // Enable global refresh system
    // Auto-refresh is now handled by refreshAfterCRUD() system
}

// ===== IMPORT STATUS FUNCTIONS =====

function showImportLightbox() {
    // Show step 5 (import progress) instead of lightbox
    showStep5();
}

function updateImportLightbox(progress, message) {
    updateImportStatus(progress, message);
}

function updateImportStatus(progress, message) {
    const statusElement = document.getElementById('importStatus');
    const messageElement = document.getElementById('importMessage');
    
    if (statusElement) {
        statusElement.textContent = message;
    }
    
    if (messageElement) {
        messageElement.textContent = `Postęp: ${progress}%`;
    }
}

function hideImportLightbox() {
    // Hide step 5 and reset to step 1
    hideAllSteps();
    showStep1();
}
