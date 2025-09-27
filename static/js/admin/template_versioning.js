/**
 * Template Versioning System JavaScript
 * Handles template editing, versioning, and confirmation modals
 */

class TemplateVersioningManager {
    constructor() {
        this.currentTemplate = null;
        this.isEditing = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadTemplateList();
    }

    bindEvents() {
        // Start editing button
        $(document).on('click', '.start-editing-btn', (e) => {
            const templateName = $(e.target).data('template-name');
            this.startEditing(templateName);
        });

        // Save template button
        $(document).on('click', '.save-template-btn', (e) => {
            this.saveTemplate();
        });

        // Make default checkbox change
        $(document).on('change', '#make-default-checkbox', (e) => {
            this.handleMakeDefaultChange(e.target.checked);
        });

        // Version history button
        $(document).on('click', '.version-history-btn', (e) => {
            const templateName = $(e.target).data('template-name');
            this.showVersionHistory(templateName);
        });

        // Restore to version button
        $(document).on('click', '.restore-version-btn', (e) => {
            const templateName = $(e.target).data('template-name');
            const version = $(e.target).data('version');
            this.restoreToVersion(templateName, version);
        });

        // Test email button
        $(document).on('click', '.test-email-btn', (e) => {
            const templateName = $(e.target).data('template-name');
            this.sendTestEmail(templateName);
        });

        // Delete template button
        $(document).on('click', '.delete-template-btn', (e) => {
            const templateId = $(e.target).data('template-id');
            this.deleteTemplate(templateId);
        });

        // Restore default button
        $(document).on('click', '.restore-default-btn', (e) => {
            const templateName = $(e.target).data('template-name');
            this.restoreDefault(templateName);
        });
    }

    async startEditing(templateName) {
        try {
            this.showLoading('Rozpoczynam edycję szablonu...');
            
            const response = await fetch(`/api/template-versioning/start-edit/${templateName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.currentTemplate = data.template;
                this.isEditing = true;
                this.loadTemplateEditor(data.template);
                this.showSuccess(data.message);
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('Błąd podczas rozpoczynania edycji: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async saveTemplate() {
        if (!this.currentTemplate) {
            this.showError('Brak aktywnego szablonu do zapisania');
            return;
        }

        try {
            this.showLoading('Zapisuję szablon...');

            const changes = {
                subject: $('#template-subject').val(),
                html_content: $('#template-html').val(),
                text_content: $('#template-text').val(),
                template_type: $('#template-type').val(),
                variables: $('#template-variables').val(),
                description: $('#template-description').val()
            };

            const makeDefault = $('#make-default-checkbox').is(':checked');

            const response = await fetch(`/api/template-versioning/save/${this.currentTemplate.id}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    changes: changes,
                    make_default: makeDefault
                })
            });

            const data = await response.json();
            
            if (data.success) {
                if (makeDefault) {
                    // Show confirmation modal
                    await this.showMakeDefaultModal();
                } else {
                    this.showSuccess(data.message);
                    this.loadTemplateList(); // Refresh the list
                }
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('Błąd podczas zapisywania: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async showMakeDefaultModal() {
        try {
            const response = await fetch(`/api/template-versioning/confirmation-modal/${this.currentTemplate.id}`);
            const data = await response.json();

            if (data.success) {
                const modalData = data.modal_data;
                this.showConfirmationModal(modalData);
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('Błąd podczas ładowania danych modal: ' + error.message);
        }
    }

    showConfirmationModal(modalData) {
        const modalHtml = `
            <div class="modal fade" id="makeDefaultModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">⚠️ Potwierdzenie nadpisania szablonu domyślnego</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-warning">
                                <strong>Uwaga!</strong> Zamierzasz nadpisać szablon domyślny "${modalData.template_name}".
                            </div>
                            
                            <p><strong>Obecna wersja:</strong> ${modalData.current_version}</p>
                            <p><strong>Temat:</strong> ${modalData.current_subject}</p>
                            
                            ${modalData.has_changes ? `
                                <div class="alert alert-info">
                                    <strong>Wykryto zmiany:</strong> Szablon został zmodyfikowany w stosunku do wersji domyślnej.
                                </div>
                            ` : ''}
                            
                            <p><strong>${modalData.warning_message}</strong></p>
                            
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="confirmOverwrite">
                                <label class="form-check-label" for="confirmOverwrite">
                                    Potwierdzam nadpisanie szablonu domyślnego
                                </label>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Anuluj</button>
                            <button type="button" class="btn btn-danger" id="confirmMakeDefaultBtn">
                                Tak, nadpisz szablon domyślny
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal
        $('#makeDefaultModal').remove();
        
        // Add new modal
        $('body').append(modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('makeDefaultModal'));
        modal.show();

        // Bind confirm button
        $('#confirmMakeDefaultBtn').on('click', () => {
            if ($('#confirmOverwrite').is(':checked')) {
                this.confirmMakeDefault();
                modal.hide();
            } else {
                this.showError('Musisz potwierdzić nadpisanie szablonu');
            }
        });
    }

    async confirmMakeDefault() {
        try {
            this.showLoading('Nadpisuję szablon domyślny...');

            const response = await fetch(`/api/template-versioning/make-default/${this.currentTemplate.id}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(data.message);
                this.loadTemplateList(); // Refresh the list
                this.isEditing = false;
                this.currentTemplate = null;
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('Błąd podczas nadpisywania: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async showVersionHistory(templateName) {
        try {
            this.showLoading('Ładuję historię wersji...');

            const response = await fetch(`/api/template-versioning/versions/${templateName}`);
            const data = await response.json();

            if (data.success) {
                this.displayVersionHistory(templateName, data.versions);
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('Błąd podczas ładowania historii: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    displayVersionHistory(templateName, versions) {
        let historyHtml = `
            <div class="modal fade" id="versionHistoryModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Historia wersji: ${templateName}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="table-responsive">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Wersja</th>
                                            <th>Data utworzenia</th>
                                            <th>Status</th>
                                            <th>Podgląd</th>
                                            <th>Akcje</th>
                                        </tr>
                                    </thead>
                                    <tbody>
        `;

        versions.forEach(version => {
            const statusBadges = [];
            if (version.is_default) statusBadges.push('<span class="badge bg-primary">Domyślny</span>');
            if (version.is_active) statusBadges.push('<span class="badge bg-success">Aktywny</span>');
            if (version.is_edited_copy) statusBadges.push('<span class="badge bg-warning">Kopia</span>');

            historyHtml += `
                <tr>
                    <td><strong>v${version.version}</strong></td>
                    <td>${new Date(version.created_at).toLocaleString('pl-PL')}</td>
                    <td>${statusBadges.join(' ')}</td>
                    <td><small>${version.html_preview || 'Brak podglądu'}</small></td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary restore-version-btn" 
                                data-template-name="${templateName}" 
                                data-version="${version.version}">
                            Przywróć
                        </button>
                    </td>
                </tr>
            `;
        });

        historyHtml += `
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Zamknij</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal
        $('#versionHistoryModal').remove();
        
        // Add new modal
        $('body').append(historyHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('versionHistoryModal'));
        modal.show();
    }

    async restoreToVersion(templateName, version) {
        if (!confirm(`Czy na pewno chcesz przywrócić szablon "${templateName}" do wersji ${version}?`)) {
            return;
        }

        try {
            this.showLoading(`Przywracam do wersji ${version}...`);

            const response = await fetch(`/api/template-versioning/restore/${templateName}/${version}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(data.message);
                this.loadTemplateList(); // Refresh the list
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('Błąd podczas przywracania: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async sendTestEmail(templateName) {
        const email = prompt('Podaj adres email do wysłania testu:');
        if (!email) return;

        try {
            this.showLoading('Wysyłam testowy email...');

            const response = await fetch(`/api/template-versioning/test-email/${templateName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    context: {}
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(`Testowy email został wysłany na ${email}`);
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('Błąd podczas wysyłania testu: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async deleteTemplate(templateId) {
        if (!confirm('Czy na pewno chcesz usunąć ten szablon i wszystkie jego wersje?')) {
            return;
        }

        try {
            this.showLoading('Usuwam szablon...');

            const response = await fetch(`/api/template-versioning/delete/${templateId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(data.message);
                this.loadTemplateList(); // Refresh the list
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('Błąd podczas usuwania: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async restoreDefault(templateName) {
        if (!confirm(`Czy na pewno chcesz przywrócić szablon "${templateName}" do wersji domyślnej?`)) {
            return;
        }

        try {
            this.showLoading('Przywracam szablon domyślny...');

            const response = await fetch(`/api/template-versioning/restore-default/${templateName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(data.message);
                this.loadTemplateList(); // Refresh the list
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('Błąd podczas przywracania: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    loadTemplateEditor(template) {
        // This would load the template editor interface
        // Implementation depends on your existing template editor
        console.log('Loading template editor for:', template);
    }

    loadTemplateList() {
        // This would load the list of templates
        // Implementation depends on your existing template list
        console.log('Loading template list');
    }

    handleMakeDefaultChange(isChecked) {
        if (isChecked) {
            this.showWarning('Uwaga: Zaznaczenie tej opcji spowoduje nadpisanie szablonu domyślnego po zapisaniu.');
        }
    }

    // Utility methods
    showLoading(message) {
        // Show loading indicator
        console.log('Loading:', message);
    }

    hideLoading() {
        // Hide loading indicator
        console.log('Loading finished');
    }

    showSuccess(message) {
        // Show success message
        console.log('Success:', message);
    }

    showError(message) {
        // Show error message
        console.log('Error:', message);
    }

    showWarning(message) {
        // Show warning message
        console.log('Warning:', message);
    }
}

// Initialize when DOM is ready
$(document).ready(() => {
    window.templateVersioningManager = new TemplateVersioningManager();
});
