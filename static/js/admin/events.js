// Admin Events JavaScript for Lepsze Życie Club

// Events management functions
class EventsManager {
    constructor() {
        this.currentEventId = null;
        this.currentEventData = null;
        this.currentPage = 1;
        this.currentPerPage = 10;
        this.initializeEventListeners();
        this.loadEvents();
        this.setMinDates();
        this.initializeEditFormDefaults();
        this.initializeHeroBackgroundHandlers();
    }

    initializeEventListeners() {
        // Form submissions
        const addEventForm = document.getElementById('addEventForm');
        const editEventForm = document.getElementById('editEventForm');
        const confirmDeleteBtn = document.getElementById('confirmDeleteEvent');
        
        if (addEventForm) {
            addEventForm.addEventListener('submit', (e) => this.handleAddEvent(e));
        }
        
        if (editEventForm) {
            editEventForm.addEventListener('submit', (e) => this.handleEditEvent(e));
        }
        
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', () => this.handleDeleteEvent());
        }
    }

    initializeHeroBackgroundHandlers() {
        // Add event form handlers
        const heroBackgroundType = document.getElementById('heroBackgroundType');
        if (heroBackgroundType) {
            heroBackgroundType.addEventListener('change', () => this.toggleHeroBackgroundFields('add'));
            // Trigger on load to set initial state
            this.toggleHeroBackgroundFields('add');
        }
        
        // Edit event form handlers
        const editHeroBackgroundType = document.getElementById('editHeroBackgroundType');
        if (editHeroBackgroundType) {
            editHeroBackgroundType.addEventListener('change', () => this.toggleHeroBackgroundFields('edit'));
        }
        
        // Preview handlers for add form
        const heroBackgroundImage = document.getElementById('heroBackgroundImage');
        const heroBackgroundImageUrl = document.getElementById('heroBackgroundImageUrl');
        if (heroBackgroundImage) {
            heroBackgroundImage.addEventListener('change', (e) => this.previewHeroBackgroundImage(e, 'add'));
        }
        if (heroBackgroundImageUrl) {
            heroBackgroundImageUrl.addEventListener('input', (e) => this.previewHeroBackgroundImageUrl(e, 'add'));
        }
        
        const heroBackgroundVideo = document.getElementById('heroBackgroundVideo');
        const heroBackgroundVideoFile = document.getElementById('heroBackgroundVideoFile');
        if (heroBackgroundVideo) {
            heroBackgroundVideo.addEventListener('input', (e) => this.previewHeroBackgroundVideo(e, 'add'));
        }
        if (heroBackgroundVideoFile) {
            heroBackgroundVideoFile.addEventListener('change', (e) => this.previewHeroBackgroundVideoFile(e, 'add'));
        }
        
        // Preview handlers for edit form
        const editHeroBackgroundImage = document.getElementById('editHeroBackgroundImage');
        const editHeroBackgroundImageUrl = document.getElementById('editHeroBackgroundImageUrl');
        if (editHeroBackgroundImage) {
            editHeroBackgroundImage.addEventListener('change', (e) => this.previewHeroBackgroundImage(e, 'edit'));
        }
        if (editHeroBackgroundImageUrl) {
            editHeroBackgroundImageUrl.addEventListener('input', (e) => this.previewHeroBackgroundImageUrl(e, 'edit'));
        }
        
        const editHeroBackgroundVideo = document.getElementById('editHeroBackgroundVideo');
        const editHeroBackgroundVideoFile = document.getElementById('editHeroBackgroundVideoFile');
        if (editHeroBackgroundVideo) {
            editHeroBackgroundVideo.addEventListener('input', (e) => this.previewHeroBackgroundVideo(e, 'edit'));
        }
        if (editHeroBackgroundVideoFile) {
            editHeroBackgroundVideoFile.addEventListener('change', (e) => this.previewHeroBackgroundVideoFile(e, 'edit'));
        }
    }
    
    toggleHeroBackgroundFields(formType) {
        const prefix = formType === 'add' ? '' : 'edit';
        const typeSelect = document.getElementById(`${prefix}HeroBackgroundType`);
        const imageContainer = document.getElementById(`${prefix}HeroBackgroundImageContainer`);
        const videoContainer = document.getElementById(`${prefix}HeroBackgroundVideoContainer`);
        
        if (!typeSelect) return;
        
        const selectedType = typeSelect.value;
        
        if (selectedType === 'image') {
            if (imageContainer) imageContainer.style.display = 'block';
            if (videoContainer) videoContainer.style.display = 'none';
        } else if (selectedType === 'video') {
            if (imageContainer) imageContainer.style.display = 'none';
            if (videoContainer) videoContainer.style.display = 'block';
        } else {
            if (imageContainer) imageContainer.style.display = 'none';
            if (videoContainer) videoContainer.style.display = 'none';
        }
    }

    /**
     * Toggle between file upload and URL input for hero background IMAGE
     * formType: 'add' | 'edit'
     */
    toggleHeroBackgroundImageSource(formType) {
        const prefix = formType === 'add' ? '' : 'edit';
        const fileInput = document.getElementById(`${prefix}HeroBackgroundImage`);
        const urlInput = document.getElementById(`${prefix}HeroBackgroundImageUrl`);

        if (!fileInput || !urlInput) return;

        const usingFile = fileInput.style.display !== 'none';

        if (usingFile) {
            // Switch to URL mode
            fileInput.style.display = 'none';
            urlInput.style.display = 'block';
            // Do NOT clear existing values automatically
        } else {
            // Switch back to file mode
            fileInput.style.display = 'block';
            urlInput.style.display = 'none';
        }
    }

    /**
     * Toggle between file upload and URL input for hero background VIDEO
     * formType: 'add' | 'edit'
     */
    toggleHeroBackgroundVideoSource(formType) {
        const prefix = formType === 'add' ? '' : 'edit';
        const fileInput = document.getElementById(`${prefix}HeroBackgroundVideoFile`);
        const urlInput = document.getElementById(`${prefix}HeroBackgroundVideo`);

        if (!fileInput || !urlInput) return;

        const usingFile = fileInput.style.display !== 'none';

        if (usingFile) {
            // Switch to URL mode
            fileInput.style.display = 'none';
            urlInput.style.display = 'block';
        } else {
            // Switch back to file mode
            fileInput.style.display = 'block';
            urlInput.style.display = 'none';
        }
    }
    
    previewHeroBackgroundImage(e, formType) {
        const prefix = formType === 'add' ? '' : 'edit';
        const file = e.target.files[0];
        const preview = document.getElementById(`${prefix}HeroBackgroundImagePreview`);
        const previewImg = document.getElementById(`${prefix}HeroBackgroundImagePreviewImg`);
        
        if (file && preview && previewImg) {
            const reader = new FileReader();
            reader.onload = (e) => {
                previewImg.src = e.target.result;
                preview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    }
    
    previewHeroBackgroundImageUrl(e, formType) {
        const prefix = formType === 'add' ? '' : 'edit';
        const url = e.target.value;
        const preview = document.getElementById(`${prefix}HeroBackgroundImagePreview`);
        const previewImg = document.getElementById(`${prefix}HeroBackgroundImagePreviewImg`);
        
        if (url && preview && previewImg) {
            previewImg.src = url;
            preview.style.display = 'block';
        } else if (preview) {
            preview.style.display = 'none';
        }
    }
    
    previewHeroBackgroundVideo(e, formType) {
        const prefix = formType === 'add' ? '' : 'edit';
        const url = e.target.value;
        const preview = document.getElementById(`${prefix}HeroBackgroundVideoPreview`);
        const previewVideo = document.getElementById(`${prefix}HeroBackgroundVideoPreviewVideo`);
        
        if (url && preview && previewVideo) {
            previewVideo.src = url;
            preview.style.display = 'block';
        } else if (preview) {
            preview.style.display = 'none';
        }
    }
    
    previewHeroBackgroundVideoFile(e, formType) {
        const prefix = formType === 'add' ? '' : 'edit';
        const file = e.target.files[0];
        const preview = document.getElementById(`${prefix}HeroBackgroundVideoPreview`);
        const previewVideo = document.getElementById(`${prefix}HeroBackgroundVideoPreviewVideo`);
        
        if (file && preview && previewVideo) {
            const reader = new FileReader();
            reader.onload = (e) => {
                previewVideo.src = e.target.result;
                preview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    }

    showAddEventModal() {
        document.getElementById('addEventForm').reset();
        
        // Clear Quill editor
        if (window.quillInstances && window.quillInstances['eventDescription']) {
            window.quillInstances['eventDescription'].root.innerHTML = '';
        }
        
        // Reset hero background fields
        this.resetHeroBackgroundFields('add');
        
        // Set today's date as default
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('eventDate').value = today;
        document.getElementById('eventTime').value = '18:00';
        
        // Set default hero background type
        document.getElementById('heroBackgroundType').value = 'image';
        this.toggleHeroBackgroundFields('add');
        
        const modal = new bootstrap.Modal(document.getElementById('addEventModal'));
        modal.show();
    }
    
    resetHeroBackgroundFields(formType) {
        const prefix = formType === 'add' ? '' : 'edit';
        
        // Reset image fields
        const imageInput = document.getElementById(`${prefix}HeroBackgroundImage`);
        const imageUrl = document.getElementById(`${prefix}HeroBackgroundImageUrl`);
        const imagePreview = document.getElementById(`${prefix}HeroBackgroundImagePreview`);
        if (imageInput) imageInput.value = '';
        if (imageUrl) {
            imageUrl.value = '';
            imageUrl.style.display = 'none';
        }
        if (imageInput) imageInput.style.display = 'block';
        if (imagePreview) imagePreview.style.display = 'none';
        
        // Reset video fields
        const videoInput = document.getElementById(`${prefix}HeroBackgroundVideo`);
        const videoPreview = document.getElementById(`${prefix}HeroBackgroundVideoPreview`);
        if (videoInput) videoInput.value = '';
        if (videoPreview) videoPreview.style.display = 'none';
    }

    editEvent(eventId) {
        fetch(`/api/event-schedule/${eventId}`)
            .then(response => {
                if (!response.ok) {
                    if (response.status === 401 || response.status === 403) {
                        throw new Error('Unauthorized');
                    }
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    const event = data.event;
                    this.populateEditForm(event);
                    
                    const modal = new bootstrap.Modal(document.getElementById('editEventModal'));
                    modal.show();
                } else {
                    window.toastManager.error(data.message || 'Błąd podczas ładowania wydarzenia');
                }
            })
            .catch(error => {
                console.error('Error loading event:', error);
                window.toastManager.error('Wystąpił błąd podczas ładowania wydarzenia');
            });
    }

    populateEditForm(event) {
        // Store current event data for validation
        this.currentEventData = event;
        
        
        document.getElementById('editEventId').value = event.id;
        document.getElementById('editEventTitle').value = event.title || '';
        
        // Set event type
        const eventTypeSelect = document.getElementById('editEventType');
        if (eventTypeSelect) {
            // Handle null/undefined event_type
            const eventType = event.event_type || '';
            eventTypeSelect.value = eventType;
        } else {
            console.error('❌ editEventType element not found!');
        }
        
        // For archived events, make date fields optional
        const isArchived = event.is_archived === true;
        const eventDateInput = document.getElementById('editEventDate');
        const eventTimeInput = document.getElementById('editEventTime');
        
        if (isArchived) {
            // Remove required attribute for archived events
            eventDateInput.removeAttribute('required');
            eventTimeInput.removeAttribute('required');
            
            // Update labels to remove asterisk
            const eventDateLabel = document.querySelector('label[for="editEventDate"]');
            const eventTimeLabel = document.querySelector('label[for="editEventTime"]');
            if (eventDateLabel) eventDateLabel.textContent = 'Data Wydarzenia';
            if (eventTimeLabel) eventTimeLabel.textContent = 'Godzina';
        } else {
            // Add required attribute for non-archived events
            eventDateInput.setAttribute('required', 'required');
            eventTimeInput.setAttribute('required', 'required');
            
            // Update labels to add asterisk
            const eventDateLabel = document.querySelector('label[for="editEventDate"]');
            const eventTimeLabel = document.querySelector('label[for="editEventTime"]');
            if (eventDateLabel) eventDateLabel.textContent = 'Data Wydarzenia *';
            if (eventTimeLabel) eventTimeLabel.textContent = 'Godzina *';
        }
        
        // Format dates - handle both ISO strings and Date objects
        if (event.event_date) {
            const eventDate = new Date(event.event_date);
            if (!isNaN(eventDate.getTime())) {
                document.getElementById('editEventDate').value = eventDate.toISOString().split('T')[0];
                document.getElementById('editEventTime').value = eventDate.toTimeString().slice(0, 5);
            }
        }
        
        if (event.end_date) {
            const endDate = new Date(event.end_date);
            if (!isNaN(endDate.getTime())) {
                document.getElementById('editEndDate').value = endDate.toISOString().split('T')[0];
                document.getElementById('editEndTime').value = endDate.toTimeString().slice(0, 5);
            }
        }
        
        document.getElementById('editEventLocation').value = event.location || '';
        document.getElementById('editMeetingLink').value = event.meeting_link || '';
        document.getElementById('editMaxParticipants').value = event.max_participants || '';
        
        // Set hero background type and show current background
        const heroBackgroundType = event.hero_background_type || 'image';
        document.getElementById('editHeroBackgroundType').value = heroBackgroundType;
        this.toggleHeroBackgroundFields('edit');
        this.displayCurrentHeroBackground(event);
        
        // Reset remove flag
        document.getElementById('removeHeroBackgroundFlag').value = 'false';
        
        // Set description in Quill editor
        if (window.quillInstances && window.quillInstances['editEventDescription']) {
            window.quillInstances['editEventDescription'].root.innerHTML = event.description || '';
        } else {
            // Fallback to textarea
            document.getElementById('editEventDescription').value = event.description || '';
        }
        document.getElementById('editEventActive').checked = event.is_active === true;
        document.getElementById('editEventPublished').checked = event.is_published === true;
        
        // Set minimum dates for date inputs (only for non-archived events)
        if (!isArchived) {
            this.setMinDates();
        } else {
            // Clear min dates for archived events - they can have any dates!
            const dateInputs = document.querySelectorAll('input[type="date"]');
            dateInputs.forEach(input => {
                input.removeAttribute('min');
            });
        }
        
        // Reset hero background fields
        this.resetHeroBackgroundFields('edit');
    }
    
    displayCurrentHeroBackground(event) {
        if (!event.hero_background) {
            // No background set
            document.getElementById('editHeroBackgroundCurrent').style.display = 'none';
            document.getElementById('editHeroBackgroundVideoCurrent').style.display = 'none';
            return;
        }
        
        const backgroundType = event.hero_background_type || 'image';
        const backgroundUrl = event.hero_background;
        
        if (backgroundType === 'video') {
            // Show current video
            const currentContainer = document.getElementById('editHeroBackgroundVideoCurrent');
            const currentContent = document.getElementById('editHeroBackgroundVideoCurrentContent');
            if (currentContainer && currentContent) {
                currentContent.innerHTML = `
                    <video src="${backgroundUrl}" controls class="img-thumbnail" style="max-width: 200px; max-height: 150px;"></video>
                    <div class="mt-1"><small class="text-muted">${backgroundUrl}</small></div>
                `;
                currentContainer.style.display = 'block';
            }
            document.getElementById('editHeroBackgroundCurrent').style.display = 'none';
            document.getElementById('editHeroBackgroundVideo').value = backgroundUrl;
        } else {
            // Show current image
            const currentContainer = document.getElementById('editHeroBackgroundCurrent');
            const currentContent = document.getElementById('editHeroBackgroundCurrentContent');
            if (currentContainer && currentContent) {
                currentContent.innerHTML = `
                    <img src="${backgroundUrl}" alt="Aktualne tło" class="img-thumbnail" style="max-width: 200px; max-height: 150px;">
                    <div class="mt-1"><small class="text-muted">${backgroundUrl}</small></div>
                `;
                currentContainer.style.display = 'block';
            }
            document.getElementById('editHeroBackgroundVideoCurrent').style.display = 'none';
            document.getElementById('editHeroBackgroundImageUrl').value = backgroundUrl;
        }
    }

    deleteEvent(eventId) {
        // Find the event data to check if it's archived
        const eventRow = document.querySelector(`tr[data-event-id="${eventId}"]`);
        if (!eventRow) {
            console.error('Event row not found');
            return;
        }
        
        // Check if event is archived by looking for the archive badge
        const archiveBadge = eventRow.querySelector('.admin-badge-secondary i.fa-archive');
        if (archiveBadge) {
            window.toastManager.error('Nie można usunąć zarchiwizowanego wydarzenia');
            return;
        }
        
        this.currentEventId = eventId;
        const modal = new bootstrap.Modal(document.getElementById('deleteEventModal'));
        modal.show();
    }

    handleAddEvent(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        
        // Handle hero background
        const heroBackgroundType = formData.get('hero_background_type') || 'image';
        let heroBackground = null;
        
        if (heroBackgroundType === 'image') {
            // Check for uploaded file first
            const imageFile = formData.get('hero_background_image');
            if (imageFile && imageFile.size > 0) {
                // File will be handled by FormData
                heroBackground = null; // Will be set after upload
            } else {
                // Check for URL
                const imageUrl = formData.get('hero_background_image_url');
                if (imageUrl) {
                    heroBackground = imageUrl;
                }
            }
        } else if (heroBackgroundType === 'video') {
            // Check for uploaded file first
            const videoFile = formData.get('hero_background_video_file');
            if (videoFile && videoFile.size > 0) {
                // File will be handled by FormData
                heroBackground = null; // Will be set after upload
            } else {
                // Check for URL
                const videoUrl = formData.get('hero_background_video');
                if (videoUrl) {
                    heroBackground = videoUrl;
                }
            }
        }
        
        // Check if we have a file to upload - if so, use FormData, otherwise use JSON
        const hasImageFile = formData.get('hero_background_image') && formData.get('hero_background_image').size > 0;
        const hasVideoFile = formData.get('hero_background_video_file') && formData.get('hero_background_video_file').size > 0;
        
        if (hasImageFile || hasVideoFile) {
            // Use FormData for file upload
            if (heroBackground) {
                // Ensure we override any existing hero_background value
                formData.set('hero_background', heroBackground);
            }
            formData.set('hero_background_type', heroBackgroundType);
            
            // Normalize and override date/time fields so backend gets full datetime
            const combinedEventDate = this.combineDateTime(formData.get('event_date'), formData.get('event_time'));
            if (combinedEventDate) {
                formData.set('event_date', combinedEventDate);
            }
            const combinedEndDate = this.combineDateTime(formData.get('end_date'), formData.get('end_time'));
            if (combinedEndDate) {
                formData.set('end_date', combinedEndDate);
            } else {
                // Ensure we don't accidentally send an empty string
                formData.delete('end_date');
            }
            
            // Normalize simple fields
            const location = formData.get('location');
            if (location) formData.set('location', location);
            const meetingLink = formData.get('meeting_link');
            if (meetingLink) formData.set('meeting_link', meetingLink);
            const maxParticipants = formData.get('max_participants');
            if (maxParticipants) formData.set('max_participants', maxParticipants);
            const description = formData.get('description');
            if (description) formData.set('description', description);
            formData.set('is_active', formData.get('is_active') === 'on' ? 'true' : 'false');
            formData.set('is_published', formData.get('is_published') === 'on' ? 'true' : 'false');
            
            fetch('/api/event-schedule', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.toastManager.success(data.message || 'Wydarzenie zostało dodane pomyślnie');
                    this.loadEvents();
                    bootstrap.Modal.getInstance(document.getElementById('addEventModal')).hide();
                } else {
                    window.toastManager.error(data.message || 'Błąd podczas dodawania wydarzenia');
                }
            })
            .catch(error => {
                console.error('Error adding event:', error);
                window.toastManager.error('Wystąpił błąd podczas dodawania wydarzenia');
            });
            return;
        }
        
        // Use JSON for non-file data
        const eventData = {
            title: formData.get('title'),
            event_type: formData.get('event_type'),
            event_date: this.combineDateTime(formData.get('event_date'), formData.get('event_time')),
            end_date: this.combineDateTime(formData.get('end_date'), formData.get('end_time')),
            location: formData.get('location'),
            meeting_link: formData.get('meeting_link'),
            max_participants: formData.get('max_participants') ? parseInt(formData.get('max_participants')) : null,
            hero_background_type: heroBackgroundType,
            hero_background: heroBackground,
            description: formData.get('description'),
            is_active: formData.get('is_active') === 'on',
            is_published: formData.get('is_published') === 'on'
        };

        // Validate dates
        const validationErrors = this.validateEventDates(eventData);
        if (validationErrors.length > 0) {
            window.toastManager.error(validationErrors.join('<br>'));
            return;
        }
        
        // Remove null/empty values, but keep required fields
        const requiredFields = ['event_type']; // Fields that should not be removed even if empty
        Object.keys(eventData).forEach(key => {
            if (eventData[key] === null || eventData[key] === '') {
                if (!requiredFields.includes(key)) {
                    delete eventData[key];
                }
            }
        });

        fetch('/api/event-schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(eventData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.success(data.message || 'Wydarzenie zostało dodane pomyślnie');
                this.loadEvents();
                bootstrap.Modal.getInstance(document.getElementById('addEventModal')).hide();
            } else {
                window.toastManager.error(data.message || 'Błąd podczas dodawania wydarzenia');
            }
        })
        .catch(error => {
            console.error('Error adding event:', error);
            window.toastManager.error('Wystąpił błąd podczas dodawania wydarzenia');
        });
    }

    handleEditEvent(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        
        // Handle hero background
        const heroBackgroundType = formData.get('hero_background_type') || 'image';
        let heroBackground = null;
        const removeHeroBackground = formData.get('remove_hero_background') === 'true';
        
        if (removeHeroBackground) {
            heroBackground = null;
        } else if (heroBackgroundType === 'image') {
            // Check for uploaded file first
            const imageFile = formData.get('hero_background_image');
            if (imageFile && imageFile.size > 0) {
                // File will be handled by FormData
                heroBackground = null; // Will be set after upload
            } else {
                // Check for URL
                const imageUrl = formData.get('hero_background_image_url');
                if (imageUrl) {
                    heroBackground = imageUrl;
                } else {
                    // Keep existing if no new value provided
                    heroBackground = this.currentEventData?.hero_background || null;
                }
            }
        } else if (heroBackgroundType === 'video') {
            // Check for uploaded file first
            const videoFile = formData.get('hero_background_video_file');
            if (videoFile && videoFile.size > 0) {
                // File will be handled by FormData
                heroBackground = null; // Will be set after upload
            } else {
                // Check for URL
                const videoUrl = formData.get('hero_background_video');
                if (videoUrl) {
                    heroBackground = videoUrl;
                } else {
                    // Keep existing if no new value provided
                    heroBackground = this.currentEventData?.hero_background || null;
                }
            }
        }
        
        // Check if we have a file to upload - if so, use FormData, otherwise use JSON
        const hasImageFile = formData.get('hero_background_image') && formData.get('hero_background_image').size > 0;
        const hasVideoFile = formData.get('hero_background_video_file') && formData.get('hero_background_video_file').size > 0;
        
        if (hasImageFile || hasVideoFile) {
            // Use FormData for file upload
            if (heroBackground) {
                // Ensure we override any existing hero_background value
                formData.set('hero_background', heroBackground);
            }
            formData.set('hero_background_type', heroBackgroundType);
            if (removeHeroBackground) {
                formData.set('remove_hero_background', 'true');
            }

            // Normalize and override date/time fields so backend gets full datetime
            const combinedEventDate = this.combineDateTime(formData.get('event_date'), formData.get('event_time'));
            if (combinedEventDate) {
                formData.set('event_date', combinedEventDate);
            }
            const combinedEndDate = this.combineDateTime(formData.get('end_date'), formData.get('end_time'));
            if (combinedEndDate) {
                formData.set('end_date', combinedEndDate);
            } else {
                // Ensure we don't accidentally send an empty string
                formData.delete('end_date');
            }
            
            const eventId = formData.get('id');
            
            fetch(`/api/event-schedule/${eventId}`, {
                method: 'PUT',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.toastManager.success(data.message || 'Wydarzenie zostało zaktualizowane pomyślnie');
                    this.loadEvents();
                    bootstrap.Modal.getInstance(document.getElementById('editEventModal')).hide();
                } else {
                    window.toastManager.error(data.message || 'Błąd podczas aktualizacji wydarzenia');
                }
            })
            .catch(error => {
                console.error('Error updating event:', error);
                window.toastManager.error('Wystąpił błąd podczas aktualizacji wydarzenia');
            });
            return;
        }
        
        const eventData = {
            title: formData.get('title'),
            event_type: formData.get('event_type'),
            event_date: this.combineDateTime(formData.get('event_date'), formData.get('event_time')),
            end_date: this.combineDateTime(formData.get('end_date'), formData.get('end_time')),
            location: formData.get('location'),
            meeting_link: formData.get('meeting_link'),
            max_participants: formData.get('max_participants') ? parseInt(formData.get('max_participants')) : null,
            hero_background_type: heroBackgroundType,
            hero_background: heroBackground,
            description: formData.get('description'),
            is_active: formData.get('is_active') === 'on',
            is_published: formData.get('is_published') === 'on',
            is_archived: this.currentEventData?.is_archived || false
        };
        
        if (removeHeroBackground) {
            eventData.remove_hero_background = true;
        }

        // NO VALIDATION FOR ARCHIVED EVENTS - they can have any dates!
        if (eventData.is_archived !== true) {
            // Only validate dates for non-archived events
            const validationErrors = this.validateEventDates(eventData);
            if (validationErrors.length > 0) {
                window.toastManager.error(validationErrors.join('<br>'));
                return;
            }
        }

        // Remove null/empty values, but keep required fields
        const requiredFields = ['event_type']; // Fields that should not be removed even if empty
        Object.keys(eventData).forEach(key => {
            if (eventData[key] === null || eventData[key] === '') {
                if (!requiredFields.includes(key)) {
                    delete eventData[key];
                }
            }
        });

        const eventId = formData.get('id');

        fetch(`/api/event-schedule/${eventId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(eventData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.success(data.message || 'Wydarzenie zostało zaktualizowane pomyślnie');
                this.loadEvents();
                bootstrap.Modal.getInstance(document.getElementById('editEventModal')).hide();
            } else {
                window.toastManager.error(data.message || 'Błąd podczas aktualizacji wydarzenia');
            }
        })
        .catch(error => {
            console.error('Error updating event:', error);
            window.toastManager.error('Wystąpił błąd podczas aktualizacji wydarzenia');
        });
    }

    handleDeleteEvent() {
        if (!this.currentEventId) return;

        fetch(`/api/event-schedule/${this.currentEventId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.success(data.message || 'Wydarzenie zostało usunięte pomyślnie');
                this.loadEvents();
                bootstrap.Modal.getInstance(document.getElementById('deleteEventModal')).hide();
            } else {
                window.toastManager.error(data.message || 'Błąd podczas usuwania wydarzenia');
            }
        })
        .catch(error => {
            console.error('Error deleting event:', error);
            window.toastManager.error('Wystąpił błąd podczas usuwania wydarzenia');
        });
    }

    loadEvents() {
        // Build query parameters from filters
        const params = new URLSearchParams();
        
        const searchValue = document.getElementById('searchInput')?.value?.trim();
        const archivedFilter = document.getElementById('archivedFilter')?.value;
        const publishedFilter = document.getElementById('publishedFilter')?.value;
        
        if (searchValue) {
            params.append('search', searchValue);
        }
        
        if (archivedFilter === 'true') {
            params.append('show_archived', 'true');
        } else if (archivedFilter === 'false') {
            params.append('show_archived', 'false');
        }
        // For 'all' - don't add show_archived parameter, backend will show all
        
        if (publishedFilter !== 'all') {
            params.append('show_published', publishedFilter);
        }
        
        // Add pagination parameters
        params.append('page', this.currentPage);
        params.append('per_page', this.currentPerPage);
        
        const url = `/api/event-schedule${params.toString() ? '?' + params.toString() : ''}`;
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success && data.events) {
                    this.displayEvents(data.events);
                    // Update pagination if data provided
                    if (data.pagination) {
                        this.updatePagination(data.pagination);
                    }
                    // Update active filters count after successful load
                    if (typeof updateActiveFiltersCount === 'function') {
                        updateActiveFiltersCount();
                    }
                } else {
                    console.error('API returned error:', data.message);
                    this.displayError(data.message || 'Wystąpił błąd podczas ładowania wydarzeń');
                }
            })
            .catch(error => {
                console.error('Error loading events:', error);
                this.displayError('Wystąpił błąd podczas ładowania wydarzeń');
            });
    }

    displayEvents(events) {
        const container = document.getElementById('eventsTableContainer');
        
        if (!events || events.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-calendar-alt fa-3x text-muted mb-3"></i>
                    <p class="text-muted">Brak wydarzeń w systemie</p>
                </div>
            `;
            return;
        }

        const tableHTML = `
            <div class="table-responsive">
                <table id="eventsTable" class="table admin-table bulk-delete-table" data-delete-endpoint="/api/bulk-delete/events">
                    <thead>
                        <tr>
                            <th>
                                <input type="checkbox" id="selectAll">
                            </th>
                            <th>ID</th>
                            <th>Tytuł</th>
                            <th>Typ</th>
                            <th>Data</th>
                            <th>Lokalizacja</th>
                            <th>Data utworzenia</th>
                            <th>Status</th>
                            <th>Akcje</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${events.map(event => this.createEventRow(event)).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = tableHTML;
        
        // Initialize bulk delete for the dynamically created table
        this.initializeBulkDelete();
    }
    
    initializeBulkDelete() {
        const table = document.getElementById('eventsTable');
        if (table && table.classList.contains('bulk-delete-table')) {
            const deleteEndpoint = table.dataset.deleteEndpoint;
            if (deleteEndpoint) {
                new BulkDelete('eventsTable', deleteEndpoint);
            }
        }
    }
    
    updatePagination(paginationData) {
        const paginationContainer = document.getElementById('pagination');
        if (paginationContainer) {
            if (paginationContainer.paginationInstance) {
                // Update existing pagination
                paginationContainer.paginationInstance.setData(paginationData);
            } else {
                // Check if SimplePagination class is available
                if (typeof SimplePagination === 'undefined') {
                    console.error('SimplePagination class not available. Make sure simple-paginate.js is loaded.');
                    return;
                }
                
                // Initialize pagination for the first time
                paginationContainer.paginationInstance = new SimplePagination('pagination', {
                    showInfo: true,
                    showPerPage: true,
                    perPageOptions: [5, 10, 25, 50, 100],
                    defaultPerPage: 10,
                    maxVisiblePages: 5
                });
                
                // Set callbacks
                paginationContainer.paginationInstance.setPageChangeCallback((page) => {
                    this.currentPage = page;
                    this.loadEvents();
                });
                
                paginationContainer.paginationInstance.setPerPageChangeCallback((newPage, perPage) => {
                    this.currentPage = newPage;
                    this.currentPerPage = perPage;
                    this.loadEvents();
                });
                
                paginationContainer.paginationInstance.setData(paginationData);
            }
        }
    }

    createEventRow(event) {
        const eventDate = new Date(event.event_date);
        const formattedDate = eventDate.toLocaleDateString('pl-PL', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
            timeZone: 'Europe/Warsaw'
        });

        // Format created_at date
        const createdDate = event.created_at ? new Date(event.created_at) : null;
        const formattedCreatedDate = createdDate ? createdDate.toLocaleDateString('pl-PL', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
            timeZone: 'Europe/Warsaw'
        }) : '-';

        const statusBadges = [];
        
        // Archival status (highest priority)
        if (event.is_archived) {
            statusBadges.push('<span class="badge admin-badge admin-badge-secondary"><i class="fas fa-archive me-1"></i>Archiwalne</span>');
        } else {
            // Active/Inactive status
            if (event.is_active) {
                statusBadges.push('<span class="badge admin-badge admin-badge-success"><i class="fas fa-check-circle me-1"></i>Aktywne</span>');
            } else {
                statusBadges.push('<span class="badge admin-badge admin-badge-danger"><i class="fas fa-times-circle me-1"></i>Nieaktywne</span>');
            }
        }
        
        // Published status
        if (event.is_published) {
            statusBadges.push('<span class="badge admin-badge admin-badge-primary"><i class="fas fa-eye me-1"></i>Opublikowane</span>');
        } else {
            statusBadges.push('<span class="badge admin-badge admin-badge-secondary"><i class="fas fa-eye-slash me-1"></i>Nieopublikowane</span>');
        }

        return `
            <tr data-event-id="${event.id}" data-item-id="${event.id}">
                <td>
                    <input type="checkbox" name="itemIds" value="${event.id}">
                </td>
                <td>
                    <span class="badge admin-badge admin-badge-primary">${event.id}</span>
                </td>
                <td>
                    <strong>${event.title}</strong>
                </td>
                <td>
                    <span class="badge admin-badge admin-badge-secondary">${this.getEventTypeLabel(event.event_type)}</span>
                </td>
                <td>${formattedDate}</td>
                <td>${event.location || '-'}</td>
                <td>${formattedCreatedDate}</td>
                <td>${statusBadges.join(' ')}</td>
                <td>
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm admin-btn-outline" onclick="eventsManager.editEvent(${event.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        ${!event.is_archived ? `
                        <button class="btn btn-sm admin-btn-danger" onclick="eventsManager.deleteEvent(${event.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                        ` : `
                        <button class="btn btn-sm admin-btn-secondary" disabled title="Nie można usunąć zarchiwizowanego wydarzenia">
                            <i class="fas fa-archive"></i>
                        </button>
                        `}
                    </div>
                </td>
            </tr>
        `;
    }

    getEventTypeLabel(type) {
        const types = {
            'workshop': 'Warsztat',
            'webinar': 'Webinar',
            'meeting': 'Spotkanie',
            'conference': 'Konferencja',
            'other': 'Inne'
        };
        return types[type] || (type || 'Nieokreślony');
    }

    displayError(message) {
        const container = document.getElementById('eventsTableContainer');
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                <p class="text-danger">${message}</p>
                <button class="btn admin-btn" onclick="eventsManager.loadEvents()">
                    <i class="fas fa-refresh me-2"></i>Spróbuj ponownie
                </button>
            </div>
        `;
    }

    combineDateTime(date, time) {
        if (!date || !time) return null;
        return `${date}T${time}`;
    }
    
    validateEventDates(eventData) {
        const now = new Date();
        const errors = [];
        
        // Skip validation for archived events - FIRST CHECK!
        if (eventData.is_archived === true) {
            return errors;
        }
        
        // Validate event date
        if (eventData.event_date) {
            const eventDate = new Date(eventData.event_date);
            if (eventDate < now) {
                errors.push('Data rozpoczęcia wydarzenia nie może być w przeszłości');
            }
        }
        
        // Validate end date
        if (eventData.end_date) {
            const endDate = new Date(eventData.end_date);
            if (endDate < now) {
                errors.push('Data zakończenia wydarzenia nie może być w przeszłości');
            }
            
            // Check if end date is after event date
            if (eventData.event_date) {
                const eventDate = new Date(eventData.event_date);
                if (endDate < eventDate) {
                    errors.push('Data zakończenia wydarzenia nie może być wcześniejsza niż data rozpoczęcia');
                }
            }
        }
        
        return errors;
    }
    
    setMinDates() {
        // Set minimum date to today for all date inputs
        const today = new Date().toISOString().split('T')[0];
        const now = new Date();
        const currentTime = now.toTimeString().slice(0, 5);
        
        const dateInputs = [
            'eventDate', 'endDate', 'editEventDate', 'editEndDate'
        ];
        
        const timeInputs = [
            'eventTime', 'endTime', 'editEventTime', 'editEndTime'
        ];
        
        dateInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.min = today;
            }
        });
        
        // Set minimum time for time inputs
        timeInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                // For today's date, set minimum time to current time
                const dateInput = input.id.replace('Time', 'Date').replace('edit', 'edit');
                const dateInputElement = document.getElementById(dateInput);
                if (dateInputElement && dateInputElement.value === today) {
                    input.min = currentTime;
                } else {
                    input.min = '00:00';
                }
            }
        });
    }
    
    initializeEditFormDefaults() {
        // Set default required attributes for edit form (will be overridden by populateEditForm)
        const eventDateInput = document.getElementById('editEventDate');
        const eventTimeInput = document.getElementById('editEventTime');
        
        if (eventDateInput) {
            eventDateInput.setAttribute('required', 'required');
        }
        if (eventTimeInput) {
            eventTimeInput.setAttribute('required', 'required');
        }
    }
}

// Global functions for onclick handlers
function showAddEventModal() {
    if (window.eventsManager) {
        window.eventsManager.showAddEventModal();
    }
}

function editEvent(eventId) {
    if (window.eventsManager) {
        window.eventsManager.editEvent(eventId);
    }
}

// Make editEvent available globally
window.editEvent = editEvent;

// Filter functions
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('archivedFilter').value = 'false';
    document.getElementById('publishedFilter').value = 'all';
    
    // Hide active filters count
    const activeFiltersCount = document.getElementById('activeFiltersCount');
    if (activeFiltersCount) {
        activeFiltersCount.style.display = 'none';
    }
    
    if (window.eventsManager) {
        window.eventsManager.loadEvents();
    }
}

function applyFilters() {
    if (window.eventsManager) {
        window.eventsManager.loadEvents();
        updateActiveFiltersCount();
    }
}

function updateActiveFiltersCount() {
    const searchValue = document.getElementById('searchInput')?.value?.trim();
    const archivedFilter = document.getElementById('archivedFilter')?.value;
    const publishedFilter = document.getElementById('publishedFilter')?.value;
    
    let activeCount = 0;
    
    if (searchValue) activeCount++;
    if (archivedFilter && archivedFilter !== 'false') activeCount++;
    if (publishedFilter && publishedFilter !== 'all') activeCount++;
    
    const activeFiltersCount = document.getElementById('activeFiltersCount');
    if (activeFiltersCount) {
        if (activeCount > 0) {
            activeFiltersCount.textContent = `${activeCount} aktywny`;
            activeFiltersCount.style.display = 'inline';
        } else {
            activeFiltersCount.style.display = 'none';
        }
    }
}

// Add event listeners for filters
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const archivedFilter = document.getElementById('archivedFilter');
    const publishedFilter = document.getElementById('publishedFilter');
    const applyFiltersBtn = document.getElementById('applyFilters');
    const clearFiltersBtn = document.getElementById('clearFilters');
    
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', applyFilters);
    }
    
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearFilters);
    }
    
    // Auto-apply filters on change (optional - you can remove this if you prefer manual apply)
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                applyFilters();
            }, 500); // Debounce search
        });
    }
    
    if (archivedFilter) {
        archivedFilter.addEventListener('change', applyFilters);
    }
    
    if (publishedFilter) {
        publishedFilter.addEventListener('change', applyFilters);
    }
    
    // Note: Edit parameter handling is now done in event_schedule.html template
    // to ensure eventsManager is initialized before opening modal
});


function deleteEvent(eventId) {
    if (window.eventsManager) {
        window.eventsManager.deleteEvent(eventId);
    }
}

// Global helpers for hero background source toggles (used by inline onclick in templates)
function toggleHeroBackgroundImageSource(formType) {
    if (window.eventsManager && typeof window.eventsManager.toggleHeroBackgroundImageSource === 'function') {
        window.eventsManager.toggleHeroBackgroundImageSource(formType);
    }
}

function toggleHeroBackgroundVideoSource(formType) {
    if (window.eventsManager && typeof window.eventsManager.toggleHeroBackgroundVideoSource === 'function') {
        window.eventsManager.toggleHeroBackgroundVideoSource(formType);
    }
}

// Expose globally
window.toggleHeroBackgroundImageSource = toggleHeroBackgroundImageSource;
window.toggleHeroBackgroundVideoSource = toggleHeroBackgroundVideoSource;

// Remove hero background function
function removeHeroBackground() {
    const flag = document.getElementById('removeHeroBackgroundFlag');
    if (flag) {
        flag.value = 'true';
    }
    
    // Hide current background display
    const currentImage = document.getElementById('editHeroBackgroundCurrent');
    const currentVideo = document.getElementById('editHeroBackgroundVideoCurrent');
    if (currentImage) currentImage.style.display = 'none';
    if (currentVideo) currentVideo.style.display = 'none';
    
    // Clear input fields
    const imageInput = document.getElementById('editHeroBackgroundImage');
    const imageUrl = document.getElementById('editHeroBackgroundImageUrl');
    const videoInput = document.getElementById('editHeroBackgroundVideo');
    if (imageInput) imageInput.value = '';
    if (imageUrl) imageUrl.value = '';
    if (videoInput) videoInput.value = '';
    
    // Hide previews
    const imagePreview = document.getElementById('editHeroBackgroundImagePreview');
    const videoPreview = document.getElementById('editHeroBackgroundVideoPreview');
    if (imagePreview) imagePreview.style.display = 'none';
    if (videoPreview) videoPreview.style.display = 'none';
    
    if (window.toastManager) {
        window.toastManager.info('Tło zostanie usunięte po zapisaniu wydarzenia');
    }
}

// Make function globally available
window.removeHeroBackground = removeHeroBackground;


