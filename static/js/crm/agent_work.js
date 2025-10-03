// Agent Work Interface
let agentStatus = 'inactive';
let currentContact = null;
let currentCallId = null;
let currentTwilioSid = null;  // Twilio Call SID for VoIP calls
let callStartTime = null;
let recordStartTime = null;  // Time when record handling started
let callTimer = null;
let recordTimer = null;
let isCallActive = false;  // Whether actual call is in progress

// Daily work time tracking
let dailyWorkStartTime = null;  // When work started today
let dailyWorkTimer = null;      // Timer for daily work time
let totalDailyWorkTime = 0;     // Total work time in seconds today
let lastWorkSessionStart = null; // When current work session started

// Polish holidays for 2024 and 2025
const polishHolidays = {
    2024: [
        '2024-01-01', // Nowy Rok
        '2024-01-06', // Trzech Króli
        '2024-03-31', // Wielkanoc
        '2024-05-01', // Święto Pracy
        '2024-05-03', // Święto Konstytucji
        '2024-05-19', // Zielone Świątki
        '2024-05-30', // Boże Ciało
        '2024-08-15', // Wniebowzięcie NMP
        '2024-11-01', // Wszystkich Świętych
        '2024-11-11', // Narodowe Święto Niepodległości
        '2024-12-25', // Boże Narodzenie
        '2024-12-26'  // Boże Narodzenie
    ],
    2025: [
        '2025-01-01', // Nowy Rok
        '2025-01-06', // Trzech Króli
        '2025-04-20', // Wielkanoc
        '2025-05-01', // Święto Pracy
        '2025-05-03', // Święto Konstytucji
        '2025-06-08', // Zielone Świątki
        '2025-06-19', // Boże Ciało
        '2025-08-15', // Wniebowzięcie NMP
        '2025-11-01', // Wszystkich Świętych
        '2025-11-11', // Narodowe Święto Niepodległości
        '2025-12-25', // Boże Narodzenie
        '2025-12-26'  // Boże Narodzenie
    ]
};

function isHoliday(date) {
    const year = date.getFullYear();
    const dateString = date.toISOString().split('T')[0];
    return polishHolidays[year] && polishHolidays[year].includes(dateString);
}

function isWeekend(date) {
    return date.getDay() === 0 || date.getDay() === 6; // Sunday or Saturday
}

function isWorkingDay(date) {
    return !isWeekend(date) && !isHoliday(date);
}

function getNextWorkingDay(date = new Date()) {
    let nextDay = new Date(date);
    nextDay.setDate(nextDay.getDate() + 1);
    
    while (!isWorkingDay(nextDay)) {
        nextDay.setDate(nextDay.getDate() + 1);
    }
    
    return nextDay;
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM loaded, initializing agent work...');
    initializeAgentWork();
    
    // Wait for DOM to be fully ready and check if our elements exist
    setTimeout(() => {
        const callbackAlert = document.getElementById('callbackAlert');
        if (callbackAlert) {
            console.log('✅ callbackAlert found, starting callback checks...');
            checkForCallbacks();
        } else {
            console.log('⚠️ callbackAlert not found, skipping callback checks...');
        }
    }, 500);
    
    // Check for callbacks every minute
    setInterval(() => {
        const callbackAlert = document.getElementById('callbackAlert');
        if (callbackAlert) {
            checkForCallbacks();
        }
    }, 60000);
});

function initializeAgentWork() {
    // Initialize daily work time tracking
    loadDailyWorkTime();
    
    // Disable classifier buttons on initialization (until call is ended)
    disableClassifierButtons();
    
    // Set agent name in script - will be set from template
    const agentNameElement = document.getElementById('agentName');
    if (agentNameElement) {
        agentNameElement.textContent = window.agentName || 'Agent';
    }
    
    // Set today's date for callback scheduling
    const today = new Date().toISOString().split('T')[0];
    const callbackDateElement = document.getElementById('callbackDate');
    if (callbackDateElement) {
        callbackDateElement.value = today;
    }
    
    // Set current time + 1 hour for callback time
    const now = new Date();
    now.setHours(now.getHours() + 1);
    const timeString = now.toTimeString().slice(0, 5);
    const callbackTimeElement = document.getElementById('callbackTime');
    if (callbackTimeElement) {
        callbackTimeElement.value = timeString;
    }
}

function toggleAgentStatus() {
    if (agentStatus === 'inactive') {
        startWork();
    } else {
        stopWork();
    }
}

function startWork() {
    fetch('/api/crm/agent/start-work', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include'
    })
    .then(response => safeJsonParse(response))
    .then(data => {
        if (data.success) {
            agentStatus = 'active';
            updateStatusDisplay();
            startDailyWorkTimer(); // Start daily work timer
            getNextContact();
        } else {
            showError('Błąd podczas rozpoczynania pracy: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Wystąpił błąd podczas rozpoczynania pracy');
    });
}

function stopWork() {
    // Check if there's an active call
    if (isCallActive && currentCallId) {
        showError('Nie można zatrzymać pracy podczas aktywnego połączenia. Zakończ połączenie lub zapisz wynik.');
        return;
    }
    
    // Check if WebRTC call is active
    if (window.webrtcCall && window.webrtcCall.isCallActive) {
        showError('Nie można zatrzymać pracy podczas aktywnego połączenia. Zakończ połączenie lub zapisz wynik.');
        return;
    }
    
    fetch('/api/crm/agent/stop-work', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include'
    })
    .then(response => safeJsonParse(response))
    .then(data => {
        if (data.success) {
            agentStatus = 'inactive';
            updateStatusDisplay();
            stopDailyWorkTimer(); // Stop daily work timer
            hideCurrentCallPanel();
        } else {
            showError('Błąd podczas zatrzymywania pracy: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Wystąpił błąd podczas zatrzymywania pracy');
    });
}

function updateStatusDisplay() {
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('agentStatus');
    const toggleBtn = document.getElementById('statusToggleBtn');
    
    if (agentStatus === 'active') {
        statusIndicator.innerHTML = '<i class="fas fa-circle text-success"></i>';
        statusText.textContent = 'Aktywny';
        toggleBtn.innerHTML = '<i class="fas fa-stop me-2"></i>Zatrzymaj pracę';
        toggleBtn.className = 'btn btn-danger btn-lg';
    } else {
        statusIndicator.innerHTML = '<i class="fas fa-circle text-danger"></i>';
        statusText.textContent = 'Nieaktywny';
        toggleBtn.innerHTML = '<i class="fas fa-play me-2"></i>Rozpocznij pracę';
        toggleBtn.className = 'btn btn-success btn-lg';
    }
}

function getNextContact() {
    console.log('🔍 getNextContact called, agentStatus:', agentStatus, 'selectedCampaignId:', selectedCampaignId);
    
    if (agentStatus !== 'active') {
        console.log('❌ Agent status is not active:', agentStatus);
        return;
    }
    
    if (!selectedCampaignId) {
        console.log('❌ No campaign selected');
        showWarning('Brak wybranej kampanii. Wybierz kampanię przed rozpoczęciem pracy.');
        return;
    }
    
    fetch('/api/crm/agent/next-contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            campaign_id: selectedCampaignId
        }),
        credentials: 'include'
    })
    .then(response => safeJsonParse(response))
    .then(data => {
        if (data.success && data.contact) {
            currentContact = data.contact;
            showCurrentCallPanel();
            // Wait a bit for panel to be visible before updating content
            setTimeout(() => {
                displayContact(currentContact);
            }, 100);
        } else {
            showWarning('Brak kontaktów do dzwonienia: ' + (data.message || 'Nie znaleziono kontaktów'));
            hideCurrentCallPanel();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Wystąpił błąd podczas pobierania kontaktu');
    });
}

function displayContact(contact) {
    console.log('🔍 displayContact called with:', contact);
    
    const contactName = document.getElementById('contactName');
    const contactPhone = document.getElementById('contactPhone');
    const contactCompany = document.getElementById('contactCompany');
    const contactEmail = document.getElementById('contactEmail');
    const contactNotes = document.getElementById('contactNotes');
    
    console.log('🔍 DOM elements found:', {
        contactName: !!contactName,
        contactPhone: !!contactPhone,
        contactCompany: !!contactCompany,
        contactEmail: !!contactEmail,
        contactNotes: !!contactNotes
    });
    
    if (contactName) contactName.textContent = contact.name || '-';
    if (contactPhone) contactPhone.textContent = contact.phone || '-';
    if (contactCompany) contactCompany.textContent = contact.company || '-';
    if (contactEmail) contactEmail.textContent = contact.email || '-';
    if (contactNotes) contactNotes.textContent = contact.notes || '-';
    
    // Update script with contact name
    const scriptName = document.getElementById('scriptName');
    if (scriptName) {
        if (contact.name) {
            const firstName = contact.name.split(' ')[0];
            scriptName.textContent = firstName;
        } else {
            scriptName.textContent = '[IMIĘ]';
        }
    } else {
        console.warn('Element scriptName not found in DOM');
    }
    
    // Update contact-specific variables in the existing campaign script
    const callScript = document.getElementById('callScript');
    if (callScript && contact.name) {
        console.log('🔄 Updating contact variables in script');
        
        // Replace contact-specific variables
        let currentScript = callScript.innerHTML;
        
        currentScript = currentScript.replace(/\[IMIĘ_NAZWISKO\]/g, contact.name || '');
        currentScript = currentScript.replace(/\[FIRMA\]/g, contact.company || '');
        currentScript = currentScript.replace(/\[TELEFON\]/g, contact.phone || '');
        currentScript = currentScript.replace(/\[EMAIL\]/g, contact.email || '');
        currentScript = currentScript.replace(/\[TAGI\]/g, contact.tags || '');
        currentScript = currentScript.replace(/\[NOTATKI\]/g, contact.notes || '');
        
        callScript.innerHTML = currentScript;
        console.log('✅ Contact variables updated in script');
    }
    
    // Update header based on contact type
    updateCallHeader(contact);
    
    // Start record handling timer
    startRecordTimer();
    
    // Load call history
    loadCallHistory(contact.id);
}

function loadCallHistory(contactId) {
    fetch(`/api/crm/agent/call-history/${contactId}`, {
        credentials: 'include'
    })
    .then(response => safeJsonParse(response))
    .then(data => {
        if (data.success) {
            displayCallHistory(data.calls);
        }
    })
    .catch(error => {
        console.error('Error loading call history:', error);
    });
}

function displayCallHistory(calls) {
    const historyDiv = document.getElementById('callHistory');
    
    if (calls.length === 0) {
        historyDiv.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-phone-slash fa-3x text-muted mb-3"></i>
                <p class="text-muted mb-0">Brak historii połączeń</p>
                <small class="text-muted">To jest pierwszy kontakt z tym numerem</small>
            </div>
        `;
        return;
    }
    
    let historyHtml = `
        <div class="call-history-header mb-3">
            <div class="row">
            </div>
        </div>
    `;
    
    calls.forEach((call, index) => {
        const date = new Date(call.call_date);
        const dateStr = date.toLocaleDateString('pl-PL');
        const timeStr = date.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' });
        const statusClass = getStatusClass(call.status);
        const statusText = getStatusText(call.status);
        const duration = call.duration_seconds ? formatDuration(call.duration_seconds) : '-';
        
        // Highlight if this was a successful lead
        const isLead = call.status === 'lead';
        const cardClass = isLead ? 'border-success' : '';
        const iconClass = isLead ? 'text-success' : 'text-muted';
        
        historyHtml += `
            <div class="call-history-item mb-3 p-3 border rounded ${cardClass}">
                <div class="row align-items-center">
                    <div class="col-md-1">
                        <div class="text-center">
                            <i class="fas fa-phone ${iconClass} mb-1"></i>
                            <div class="small text-muted">#${calls.length - index}</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="fw-bold">${dateStr}</div>
                        <div class="small text-muted">${timeStr}</div>
                        <div class="small text-muted">${duration}</div>
                    </div>
                    <div class="col-md-6">
                        ${call.notes ? `
                            <div class="call-notes">
                                <small class="text-muted">
                                    <i class="fas fa-sticky-note me-1"></i>Notatki:
                                </small>
                                <div class="mt-1 p-2 bg-light rounded small">
                                    ${call.notes}
                                </div>
                            </div>
                        ` : `
                            <div class="text-muted small">
                                <i class="fas fa-minus me-1"></i>Brak notatek
                            </div>
                        `}
                    </div>
                </div>
            </div>
        `;
    });
    
    historyDiv.innerHTML = historyHtml;
}

function getStatusClass(status) {
    const classes = {
        'lead': 'bg-success',
        'rejection': 'bg-danger',
        'callback': 'bg-warning',
        'no_answer': 'bg-secondary',
        'busy': 'bg-info',
        'wrong_number': 'bg-dark',
        'blacklist': 'bg-danger'
    };
    return classes[status] || 'bg-secondary';
}

function getStatusText(status) {
    const texts = {
        'lead': 'Lead',
        'rejection': 'Odmowa',
        'callback': 'Przełożenie',
        'no_answer': 'Nie odebrał',
        'busy': 'Zajęte',
        'wrong_number': 'Błędny numer',
        'blacklist': 'Czarna lista'
    };
    return texts[status] || status;
}

async function makeCall() {
    if (!currentContact) {
        showWarning('Brak kontaktu do dzwonienia');
        return;
    }
    
    // Check if Twilio is available (preferred) or WebRTC
    if (currentContact.phone) {
        console.log('📞 Using Twilio VoIP for call');
        
        // Disable call button
        const callBtn = document.getElementById('makeCallBtn');
        callBtn.disabled = true;
        callBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Dzwonienie...';
        
        try {
            // Make Twilio call
            const response = await fetch('/api/voip/twilio/make-call', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    contact_id: currentContact.id,
                    phone_number: currentContact.phone
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                currentCallId = data.call_id;
                currentTwilioSid = data.twilio_sid;
                callStartTime = new Date(data.start_time);
                isCallActive = true;
                
                console.log('✅ Twilio call started with ID:', currentCallId, 'SID:', currentTwilioSid);
                startCallTimer();
                showCallDuration();
                showOutcomePanel();
                hideCallButton();
                disableClassifierButtons();
                showEndCallButton();
                showSuccess('Połączenie Twilio rozpoczęte');
            } else {
                throw new Error(data.error || 'Błąd połączenia Twilio');
            }
            
        } catch (error) {
            console.error('❌ Twilio call error:', error);
            showError('Błąd połączenia Twilio: ' + error.message);
            resetCallButton();
        }
        
    } else if (window.webrtcCall && currentContact.phone) {
        console.log('🎯 Using WebRTC for call');
        
        // Disable call button
        const callBtn = document.getElementById('makeCallBtn');
        callBtn.disabled = true;
        callBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Dzwonienie...';
        
        try {
            // Make WebRTC call
            const success = await window.webrtcCall.makeCall(currentContact.phone, currentContact.id);
            
            if (success) {
                currentCallId = window.webrtcCall.callId;
                callStartTime = window.webrtcCall.callStartTime;
                isCallActive = true;
                
                console.log('✅ WebRTC call started with ID:', currentCallId);
                startCallTimer();
                showCallDuration();
                showOutcomePanel();
                hideCallButton();
                disableClassifierButtons(); // Disable classifiers during call
                showEndCallButton();
                showSuccess('Połączenie WebRTC rozpoczęte');
            } else {
                throw new Error('Błąd połączenia WebRTC');
            }
            
        } catch (error) {
            console.error('❌ WebRTC call error:', error);
            showError('Błąd połączenia WebRTC: ' + error.message);
            resetCallButton();
        }
        
    } else {
        console.log('📞 Using fallback API call (no WebRTC or phone number)');
        
        // Disable call button
        const callBtn = document.getElementById('makeCallBtn');
        callBtn.disabled = true;
        callBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Dzwonienie...';
        
        // Start call via API (fallback)
        fetch('/api/crm/agent/start-call', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                contact_id: currentContact.id
            })
        })
        .then(response => safeJsonParse(response))
        .then(data => {
            if (data.success) {
                currentCallId = data.call_id;
                callStartTime = new Date(data.start_time);
                isCallActive = true;
                console.log('✅ Call started with ID:', currentCallId);
                startCallTimer();
                showCallDuration();
                showOutcomePanel();
                hideCallButton();
                disableClassifierButtons(); // Disable classifiers during call
                showEndCallButton();
            } else {
                showError('Błąd podczas inicjowania połączenia: ' + data.error);
                resetCallButton();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Wystąpił błąd podczas inicjowania połączenia');
            resetCallButton();
        });
    }
}

function resetCallButton() {
    const callBtn = document.getElementById('makeCallBtn');
    callBtn.disabled = false;
    callBtn.innerHTML = '<i class="fas fa-phone me-1"></i>Zadzwoń';
}


function showCallbackScheduling() {
    console.log('📅 Showing callback scheduling panel...');
    document.getElementById('callbackScheduling').style.display = 'block';
    
    // Set intelligent default callback time (next business hour)
    const now = new Date();
    let nextHour = new Date(now);
    
    // If it's weekend or holiday, set to next working day 9 AM
    if (!isWorkingDay(now)) {
        nextHour = getNextWorkingDay(now);
        nextHour.setHours(9, 0, 0, 0);
    } else {
        // Set to next hour, but respect business hours (8:00 - 21:00)
        nextHour.setHours(now.getHours() + 1, 0, 0, 0);
        
        // If next hour is after 21:00, set to next working day 9 AM
        if (nextHour.getHours() > 21) {
            nextHour = getNextWorkingDay(now);
            nextHour.setHours(9, 0, 0, 0);
        }
        
        // If next hour is before 8:00, set to 9:00 today
        if (nextHour.getHours() < 8) {
            nextHour.setHours(9, 0, 0, 0);
        }
    }
    
    // If it's after 17:00, set to next working day 9 AM
    if (now.getHours() >= 17) {
        nextHour = getNextWorkingDay(now);
        nextHour.setHours(9, 0, 0, 0);
    }
    
    // Set date and time inputs
    const dateString = nextHour.toISOString().split('T')[0];
    const timeString = nextHour.toTimeString().slice(0, 5);
    
    document.getElementById('callbackDate').value = dateString;
    document.getElementById('callbackTime').value = timeString;
    document.getElementById('callbackNotes').value = '';  // Clear previous notes
    
    // Set up date restrictions
    setupDateRestrictions();
    
    // Focus on notes input
    document.getElementById('callbackNotes').focus();
}

function hideCallbackScheduling() {
    document.getElementById('callbackScheduling').style.display = 'none';
}

// Functions to control classifier buttons state based on call status
function enableClassifierButtons() {
    console.log('🔓 Enabling classifier buttons');
    const buttons = [
        document.querySelector('button[onclick="saveCallOutcome(\'lead\')"]'),
        document.querySelector('button[onclick="saveCallOutcome(\'rejection\')"]'),
        document.querySelector('button[onclick="saveCallOutcome(\'no_answer\')"]'),
        document.querySelector('button[onclick="saveCallOutcome(\'busy\')"]'),
        document.querySelector('button[onclick="saveCallOutcome(\'wrong_number\')"]'),
        document.querySelector('button[onclick="saveCallOutcome(\'blacklist\')"]'),
        document.querySelector('button[onclick="showCallbackScheduling()"]')
    ];
    
    buttons.forEach(button => {
        if (button) {
            button.disabled = false;
            button.classList.remove('disabled');
        }
    });
}

function disableClassifierButtons() {
    console.log('🔒 Disabling classifier buttons');
    const buttons = [
        document.querySelector('button[onclick="saveCallOutcome(\'lead\')"]'),
        document.querySelector('button[onclick="saveCallOutcome(\'rejection\')"]'),
        document.querySelector('button[onclick="saveCallOutcome(\'no_answer\')"]'),
        document.querySelector('button[onclick="saveCallOutcome(\'busy\')"]'),
        document.querySelector('button[onclick="saveCallOutcome(\'wrong_number\')"]'),
        document.querySelector('button[onclick="saveCallOutcome(\'blacklist\')"]'),
        document.querySelector('button[onclick="showCallbackScheduling()"]')
    ];
    
    buttons.forEach(button => {
        if (button) {
            button.disabled = true;
            button.classList.add('disabled');
        }
    });
}

let callbackDatePicker = null; // Global variable to store Flatpickr instance

function setupDateRestrictions() {
    console.log('🔧 Setting up date restrictions...');
    const dateInput = document.getElementById('callbackDate');
    const timeInput = document.getElementById('callbackTime');
    
    if (!dateInput) {
        console.error('❌ callbackDate input not found!');
        return;
    }
    
    console.log('📅 Initializing Flatpickr...');
    
    // Check if flatpickr is available
    if (typeof flatpickr === 'undefined') {
        console.error('❌ Flatpickr not loaded!');
        return;
    }
    
    // Initialize Flatpickr with Polish locale and restrictions
    callbackDatePicker = flatpickr(dateInput, {
        locale: "pl",
        dateFormat: "Y-m-d",
        minDate: new Date(),
        enableTime: false,
        disable: function(date) {
            // Disable weekends and holidays
            return !isWorkingDay(date);
        },
        onChange: function(selectedDates, dateStr, instance) {
            const selectedDate = new Date(dateStr);
            
            if (!isWorkingDay(selectedDate)) {
                let message = '';
                if (isWeekend(selectedDate)) {
                    message = 'Wybrana data to weekend. Proszę wybrać dzień roboczy (poniedziałek-piątek).';
                } else if (isHoliday(selectedDate)) {
                    message = 'Wybrana data to święto. Proszę wybrać dzień roboczy.';
                }
                
                showWarning(message);
                
                // Auto-correct to next working day
                const nextWorkingDay = getNextWorkingDay(selectedDate);
                instance.setDate(nextWorkingDay, false);
                
                showSuccess(`Data została automatycznie zmieniona na najbliższy dzień roboczy: ${nextWorkingDay.toLocaleDateString('pl-PL')}`);
            }
        },
        onReady: function(selectedDates, dateStr, instance) {
            // Mark weekends and holidays with CSS classes
            const calendar = instance.calendarContainer;
            const days = calendar.querySelectorAll('.flatpickr-day');
            
            days.forEach(day => {
                const dayDate = new Date(day.dateObj);
                if (isWeekend(dayDate)) {
                    day.classList.add('weekend');
                } else if (isHoliday(dayDate)) {
                    day.classList.add('holiday');
                }
            });
        }
    });
    
    // Add change event listener to validate time
    timeInput.addEventListener('change', function() {
        const selectedTime = this.value;
        const [hours, minutes] = selectedTime.split(':').map(Number);
        const totalMinutes = hours * 60 + minutes;
        
        // Check if time is within business hours (8:00 - 21:00)
        if (totalMinutes < 480 || totalMinutes > 1260) { // 8:00 = 480 minutes, 21:00 = 1260 minutes
            showWarning('Godzina oddzwonienia musi być między 8:00 a 21:00');
            
            // Auto-correct to nearest valid time
            if (totalMinutes < 480) {
                this.value = '08:00';
                showSuccess('Godzina została automatycznie zmieniona na 8:00');
            } else if (totalMinutes > 1260) {
                this.value = '21:00';
                showSuccess('Godzina została automatycznie zmieniona na 21:00');
            }
        }
    });
}

function showCallbackConfirmationModal(callbackDateTime, timezone, callbackNotes) {
    console.log('🔍 showCallbackConfirmationModal called with:', { callbackDateTime, timezone, callbackNotes });
    
    const contactName = currentContact ? `${currentContact.name || 'Brak nazwy'}` : 'Nieznany kontakt';
    const contactId = currentContact ? currentContact.id : 'Nieznany';
    const contactCompany = currentContact && currentContact.company ? ` (${currentContact.company})` : '';
    
    const callbackDateTimeObj = new Date(callbackDateTime);
    const callbackDateStr = callbackDateTimeObj.toLocaleDateString('pl-PL');
    const callbackTimeStr = callbackDateTimeObj.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' });
    
    // Populate modal content
    const content = `
        <div class="row">
            <div class="col-12">
                <h6><i class="fas fa-user me-2"></i>Dane kontaktu:</h6>
                <p class="mb-2"><strong>ID:</strong> ${contactId}</p>
                <p class="mb-2"><strong>Nazwa:</strong> ${contactName}${contactCompany}</p>
            </div>
        </div>
        <hr>
        <div class="row">
            <div class="col-12">
                <h6><i class="fas fa-calendar-alt me-2"></i>Nowy termin oddzwonienia:</h6>
                <p class="mb-2"><strong>Data:</strong> ${callbackDateStr}</p>
                <p class="mb-2"><strong>Godzina:</strong> ${callbackTimeStr}</p>
                ${callbackNotes ? `<p class="mb-2"><strong>Notatka:</strong> ${callbackNotes}</p>` : ''}
            </div>
        </div>
        <div class="alert alert-info mt-3">
            <i class="fas fa-info-circle me-2"></i>
            Połączenie zostanie przeplanowane zgodnie z powyższymi danymi.
        </div>
    `;
    
    const contentElement = document.getElementById('callbackConfirmContent');
    if (!contentElement) {
        console.error('❌ callbackConfirmContent element not found!');
        return;
    }
    contentElement.innerHTML = content;
    
    // Set up confirm button handler
    const confirmBtn = document.getElementById('confirmCallbackBtn');
    confirmBtn.onclick = function() {
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('callbackConfirmModal'));
        modal.hide();
        
        // Save callback
        saveCallOutcome('callback', callbackDateTime, timezone, callbackNotes);
    };
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('callbackConfirmModal'));
    modal.show();
}

function saveCallbackOutcome() {
    console.log('🚀 saveCallbackOutcome called');
    
    // Get date from Flatpickr instance or input field
    let callbackDate;
    if (callbackDatePicker && callbackDatePicker.selectedDates && callbackDatePicker.selectedDates.length > 0) {
        const selectedDate = callbackDatePicker.selectedDates[0];
        callbackDate = selectedDate.toISOString().split('T')[0];
        console.log('📅 Date from Flatpickr:', callbackDate);
    } else {
        callbackDate = document.getElementById('callbackDate').value;
        console.log('📅 Date from input field:', callbackDate);
    }
    
    const callbackTime = document.getElementById('callbackTime').value;
    const timezone = document.getElementById('callbackTimezone').value;
    const callbackNotes = document.getElementById('callbackNotes').value.trim();
    
    console.log('🔍 Debug saveCallbackOutcome:', {
        callbackDate,
        callbackTime,
        timezone,
        callbackNotes,
        flatpickrInstance: !!callbackDatePicker,
        flatpickrSelectedDates: callbackDatePicker ? callbackDatePicker.selectedDates : 'no instance'
    });
    
    if (!callbackDate || !callbackTime) {
        showWarning('Proszę podać datę i godzinę oddzwonienia');
        console.log('❌ Missing date or time:', { callbackDate, callbackTime });
        return;
    }
    
    // Create datetime string with timezone info
    const callbackDateTime = callbackDate + 'T' + callbackTime + ':00';
    
    // Validate that callback is not in the past
    const callbackDateTimeObj = new Date(callbackDateTime);
    const now = new Date();
    
    if (callbackDateTimeObj <= now) {
        showWarning('Data i godzina oddzwonienia nie może być w przeszłości');
        return;
    }
    
    // Validate that callback date is a working day
    const callbackDateObj = new Date(callbackDate + 'T00:00:00');
    if (!isWorkingDay(callbackDateObj)) {
        let message = '';
        if (isWeekend(callbackDateObj)) {
            message = 'Nie można zaplanować oddzwonienia na weekend. Proszę wybrać dzień roboczy.';
        } else if (isHoliday(callbackDateObj)) {
            message = 'Nie można zaplanować oddzwonienia na święto. Proszę wybrać dzień roboczy.';
        }
        showWarning(message);
        return;
    }
    
    // Validate business hours (8:00 - 21:00)
    const [hours, minutes] = callbackTime.split(':').map(Number);
    const totalMinutes = hours * 60 + minutes;
    
    if (totalMinutes < 480 || totalMinutes > 1260) { // 8:00 = 480 minutes, 21:00 = 1260 minutes
        showWarning('Godzina oddzwonienia musi być między 8:00 a 21:00');
        return;
    }
    
    // Show confirmation modal for callback scheduling
    showCallbackConfirmationModal(callbackDateTime, timezone, callbackNotes);
}

function saveCallOutcome(outcome, callbackDateTime = null, timezone = null, callbackNotes = '') {
    // Debug: Check if currentCallId is set
    if (!currentCallId) {
        showError('Błąd: Brak ID połączenia. Spróbuj ponownie zadzwonić.');
        return;
    }
    
    let notes = '';
    
    // Handle callback notes
    if (outcome === 'callback' && callbackNotes) {
        const timestamp = new Date().toLocaleString('pl-PL');
        const agentName = window.agentName || 'Agent';
        notes = `[${timestamp}] ${agentName} - Przełożenie: ${callbackNotes}`;
    }
    
    const data = {
        call_id: currentCallId,
        outcome: outcome,
        notes: notes
    };
    
    if (outcome === 'callback' && callbackDateTime) {
        data.callback_date = callbackDateTime;
        if (timezone) {
            data.timezone = timezone;
        }
    }
    
    // Calculate final durations
    let callDuration = 0;
    let recordDuration = 0;
    
    if (callStartTime && isCallActive) {
        // Calculate call duration (only if call was active)
        const now = new Date();
        callDuration = Math.floor((now - callStartTime) / 1000);
    }
    
    if (recordStartTime) {
        // Calculate record handling duration
        const now = new Date();
        recordDuration = Math.floor((now - recordStartTime) / 1000);
    }
    
    // Add durations to data
    data.call_duration_seconds = callDuration;
    data.record_duration_seconds = recordDuration;
    
    // Stop timers
    stopCallTimer();
    stopRecordTimer();
    
    console.log('💾 Saving call outcome:', data);
    
    fetch('/api/crm/agent/save-outcome', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(data)
    })
    .then(response => safeJsonParse(response))
    .then(data => {
        if (data.success) {
            const callTime = formatDuration(data.call_duration_seconds || 0);
            const recordTime = formatDuration(data.record_duration_seconds || 0);
            showSuccess(`Wynik rozmowy został zapisany!\nCzas rozmowy: ${callTime}\nCzas obsługi rekordu: ${recordTime}`);
            resetOutcomePanel();
            checkForCallbacks(); // Check for new callbacks
            
            // Auto-load next contact after 3 seconds (configurable delay)
            setTimeout(() => {
                console.log('🔄 Auto-loading next contact after saving outcome');
                getNextContact();
            }, 3000);
        } else {
            showError('Błąd podczas zapisywania wyniku: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Wystąpił błąd podczas zapisywania wyniku');
    });
}

function resetOutcomePanel() {
    // Hide outcome panel
    document.getElementById('outcomePanel').style.display = 'none';
    
    // Reset form
    document.getElementById('callbackScheduling').style.display = 'none';
    
    // Reset callback form
    document.getElementById('callbackDate').value = '';
    document.getElementById('callbackTime').value = '';
    document.getElementById('callbackNotes').value = '';
    
    // Hide call duration
    hideCallDuration();
    
    // Reset timer variables
    callStartTime = null;
    recordStartTime = null;
    isCallActive = false;
    
    // Show call button, hide end call button
    showCallButton();
    hideEndCallButton();
    disableClassifierButtons(); // Disable classifiers when panel is reset
    
    // Reset call button
    resetCallButton();
}

function showCurrentCallPanel() {
    document.getElementById('currentCallPanel').style.display = 'block';
}

function hideCurrentCallPanel() {
    document.getElementById('currentCallPanel').style.display = 'none';
}

function showOutcomePanel() {
    document.getElementById('outcomePanel').style.display = 'block';
}

function hideCallButton() {
    document.getElementById('makeCallBtn').style.display = 'none';
}

function showCallButton() {
    document.getElementById('makeCallBtn').style.display = 'inline-block';
}

function showEndCallButton() {
    document.getElementById('endCallBtn').style.display = 'inline-block';
}

function hideEndCallButton() {
    document.getElementById('endCallBtn').style.display = 'none';
}

async function endCall() {
    if (!currentCallId) {
        showWarning('Brak aktywnego połączenia');
        return;
    }
    
    // Check if Twilio call is active
    if (currentTwilioSid) {
        console.log('📞 Ending Twilio call');
        
        try {
            // End Twilio call
            const response = await fetch('/api/voip/twilio/end-call', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    call_id: currentCallId,
                    twilio_sid: currentTwilioSid
                })
            });
            
            const data = await response.json();
            if (data.success) {
                console.log('✅ Twilio call ended');
            } else {
                console.error('❌ Error ending Twilio call:', data.error);
            }
        } catch (error) {
            console.error('❌ Error ending Twilio call:', error);
        }
    }
    
    // Check if WebRTC call is active
    if (window.webrtcCall && window.webrtcCall.isCallActive) {
        console.log('🎯 Ending WebRTC call');
        
        try {
            // End WebRTC call
            await window.webrtcCall.endCall();
            console.log('✅ WebRTC call ended');
        } catch (error) {
            console.error('❌ Error ending WebRTC call:', error);
        }
    }
    
    // Stop call timer (but keep record timer running)
    isCallActive = false;
    stopCallTimer();
    
    // Show outcome panel for call classification
    showOutcomePanel();
    hideEndCallButton();
    enableClassifierButtons(); // Enable classifiers after call ends
}

// Legacy function for compatibility
function hideCallActions() {
    hideCallButton();
}

function showCallActions() {
    showCallButton();
}

function checkForCallbacks() {
    console.log('⏰ Checking for callbacks...');
    fetch('/api/crm/agent/queue-status', {
        credentials: 'include'
    })
    .then(response => safeJsonParse(response))
    .then(data => {
        console.log('📊 Queue status response:', data);
        if (data.success && data.queue.callbacks > 0) {
            // Show callback alert
            const alertDiv = document.getElementById('callbackAlert');
            const callbackInfo = document.getElementById('callbackInfo');
            const countdown = document.getElementById('callbackCountdown');
            const headerCountdown = document.getElementById('callbackCountdownHeader');
            const countdownText = document.getElementById('countdownText');
            
            if (!alertDiv) {
                console.error('❌ callbackAlert element not found!');
                return;
            }
            
            // Get next callback time
            const nextCallback = data.next_callback;
            if (nextCallback) {
                const callbackTime = new Date(nextCallback);
                const now = new Date();
                const timeDiff = callbackTime - now;
                
                if (timeDiff > 0) {
                    const hours = Math.floor(timeDiff / (1000 * 60 * 60));
                    const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
                    const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);
                    
                    const timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                    
                    // Update alert
                    callbackInfo.textContent = `Następne oddzwonienie: ${callbackTime.toLocaleString('pl-PL')}`;
                    countdown.textContent = timeString;
                    alertDiv.style.display = 'block';
                    
                    // Update header countdown
                    countdownText.textContent = timeString;
                    headerCountdown.style.display = 'block';
                } else {
                    // Time has passed, hide countdowns
                    alertDiv.style.display = 'none';
                    headerCountdown.style.display = 'none';
                }
            }
        } else {
            document.getElementById('callbackAlert').style.display = 'none';
            document.getElementById('callbackCountdownHeader').style.display = 'none';
        }
    })
    .catch(error => {
        console.error('Error checking callbacks:', error);
    });
}

// Timer functions
function startCallTimer() {
    if (callTimer) {
        clearInterval(callTimer);
    }
    
    callTimer = setInterval(() => {
        if (callStartTime && isCallActive) {
            const now = new Date();
            const duration = Math.floor((now - callStartTime) / 1000);
            updateCallDuration(duration);
            console.log('Call duration:', formatDuration(duration));
        }
    }, 1000);
}

function stopCallTimer() {
    if (callTimer) {
        clearInterval(callTimer);
        callTimer = null;
    }
    // Don't reset callStartTime here - we need it for final duration calculation
}

function startRecordTimer() {
    if (recordTimer) {
        clearInterval(recordTimer);
    }
    
    recordStartTime = new Date();
    
    recordTimer = setInterval(() => {
        if (recordStartTime) {
            const now = new Date();
            const duration = Math.floor((now - recordStartTime) / 1000);
            updateRecordDuration(duration);
        }
    }, 1000);
}

function stopRecordTimer() {
    if (recordTimer) {
        clearInterval(recordTimer);
        recordTimer = null;
    }
}

function formatDuration(seconds) {
    if (!seconds || seconds < 0) return '0:00';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

// Daily work time functions
function startDailyWorkTimer() {
    console.log('🕐 Starting daily work timer');
    lastWorkSessionStart = new Date();
    
    if (dailyWorkTimer) {
        clearInterval(dailyWorkTimer);
    }
    
    dailyWorkTimer = setInterval(() => {
        updateDailyWorkTimeDisplay();
    }, 1000);
    
    updateDailyWorkTimeDisplay();
}

function stopDailyWorkTimer() {
    console.log('🕐 Stopping daily work timer');
    
    if (dailyWorkTimer) {
        clearInterval(dailyWorkTimer);
        dailyWorkTimer = null;
    }
    
    // Save current session time
    if (lastWorkSessionStart) {
        const sessionTime = Math.floor((new Date() - lastWorkSessionStart) / 1000);
        totalDailyWorkTime += sessionTime;
        lastWorkSessionStart = null;
        console.log(`🕐 Session ended. Added ${sessionTime}s to total. Total today: ${totalDailyWorkTime}s`);
    }
}

function updateDailyWorkTimeDisplay() {
    const dailyWorkTimeElement = document.getElementById('dailyWorkTime');
    if (!dailyWorkTimeElement) return;
    
    let currentTotalTime = totalDailyWorkTime;
    
    // Add current session time if agent is working
    if (agentStatus === 'active' && lastWorkSessionStart) {
        const currentSessionTime = Math.floor((new Date() - lastWorkSessionStart) / 1000);
        currentTotalTime += currentSessionTime;
    }
    
    // Format as HH:MM:SS
    const hours = Math.floor(currentTotalTime / 3600);
    const minutes = Math.floor((currentTotalTime % 3600) / 60);
    const seconds = currentTotalTime % 60;
    
    const formattedTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    dailyWorkTimeElement.textContent = formattedTime;
}

function resetDailyWorkTime() {
    console.log('🕐 Resetting daily work time (new day)');
    totalDailyWorkTime = 0;
    lastWorkSessionStart = null;
    
    if (dailyWorkTimer) {
        clearInterval(dailyWorkTimer);
        dailyWorkTimer = null;
    }
    
    updateDailyWorkTimeDisplay();
}

function getTodayKey() {
    const today = new Date();
    return `${today.getFullYear()}-${(today.getMonth() + 1).toString().padStart(2, '0')}-${today.getDate().toString().padStart(2, '0')}`;
}

function loadDailyWorkTime() {
    const todayKey = getTodayKey();
    const savedData = localStorage.getItem(`dailyWorkTime_${todayKey}`);
    
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            totalDailyWorkTime = data.totalTime || 0;
            console.log(`🕐 Loaded daily work time for ${todayKey}: ${totalDailyWorkTime}s`);
        } catch (error) {
            console.error('Error loading daily work time:', error);
            totalDailyWorkTime = 0;
        }
    } else {
        totalDailyWorkTime = 0;
        console.log(`🕐 No saved work time for ${todayKey}, starting fresh`);
    }
    
    updateDailyWorkTimeDisplay();
}

function saveDailyWorkTime() {
    const todayKey = getTodayKey();
    const data = {
        totalTime: totalDailyWorkTime,
        lastSaved: new Date().toISOString()
    };
    
    localStorage.setItem(`dailyWorkTime_${todayKey}`, JSON.stringify(data));
    console.log(`🕐 Saved daily work time for ${todayKey}: ${totalDailyWorkTime}s`);
}

// Update countdown every second
setInterval(() => {
    const countdown = document.getElementById('callbackCountdown');
    if (countdown && countdown.textContent !== '-') {
        // Update countdown in real-time
        checkForCallbacks();
    }
}, 1000);

// Auto-save daily work time every 30 seconds
setInterval(() => {
    if (agentStatus === 'active') {
        saveDailyWorkTime();
    }
}, 30000);

// Save work time when page is being unloaded
window.addEventListener('beforeunload', () => {
    if (agentStatus === 'active') {
        stopDailyWorkTimer();
        saveDailyWorkTime();
    }
});

// Header and UI update functions
function updateCallHeader(contact) {
    const header = document.getElementById('callHeader');
    const headerTitle = document.getElementById('headerTitle');
    const callbackInfo = document.getElementById('callbackInfo');
    
    // Reset header classes
    header.className = 'admin-card-header d-flex justify-content-between align-items-center';
    callbackInfo.style.display = 'none';
    
    if (contact.priority === 'callback') {
        // Yellow header for callbacks
        header.classList.add('bg-warning', 'text-dark');
        headerTitle.textContent = 'Oddzwonienie w terminie';
        
        // Show callback info if available
        if (contact.callback_date) {
            const callbackDate = new Date(contact.callback_date);
            callbackInfo.innerHTML = `
                <i class="fas fa-clock me-1"></i>
                Zaplanowane na: ${callbackDate.toLocaleString('pl-PL')}
            `;
            callbackInfo.style.display = 'inline-block';
        }
    } else if (contact.priority === 'new') {
        // Green header for new contacts
        header.classList.add('bg-success');
        headerTitle.textContent = 'Nowy kontakt';
    } else {
        // Default header for other priorities
        headerTitle.textContent = 'Aktualne połączenie';
    }
}

// Timer display functions
function showCallDuration() {
    document.getElementById('callDurationDisplay').style.display = 'block';
}

function hideCallDuration() {
    document.getElementById('callDurationDisplay').style.display = 'none';
}

function updateCallDuration(seconds) {
    const durationElement = document.getElementById('callDuration');
    durationElement.textContent = formatDuration(seconds);
}

function updateRecordDuration(seconds) {
    const durationElement = document.getElementById('recordDuration');
    durationElement.textContent = formatDuration(seconds);
}

// Note management functions
function showAddNoteModal() {
    if (!currentContact) {
        showWarning('Brak kontaktu do dodania notatki');
        return;
    }
    
    // Set contact name in modal
    document.getElementById('modalContactName').textContent = currentContact.name || '-';
    
    // Clear previous note
    document.getElementById('contactNote').value = '';
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('addNoteModal'));
    modal.show();
}

function saveContactNote() {
    const noteText = document.getElementById('contactNote').value.trim();
    
    if (!noteText) {
        showWarning('Proszę wprowadzić notatkę');
        return;
    }
    
    if (!currentContact) {
        showWarning('Brak kontaktu');
        return;
    }
    
    // Send note to API
    fetch('/api/crm/agent/add-contact-note', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
            contact_id: currentContact.id,
            note: noteText
        })
    })
    .then(response => safeJsonParse(response))
    .then(data => {
        if (data.success) {
            showSuccess('Notatka została zapisana');
            
            // Update contact notes display
            updateContactNotes();
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addNoteModal'));
            modal.hide();
        } else {
            showError('Błąd podczas zapisywania notatki: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Wystąpił błąd podczas zapisywania notatki');
    });
}

function updateContactNotes() {
    // Reload contact data to get updated notes
    if (currentContact) {
        fetch(`/api/crm/agent/contact/${currentContact.id}`, {
            credentials: 'include'
        })
        .then(response => safeJsonParse(response))
        .then(data => {
            if (data.success && data.contact) {
                currentContact = data.contact;
                displayContact(currentContact);
            }
        })
        .catch(error => {
            console.error('Error updating contact notes:', error);
        });
    }
}

// ===== CAMPAIGN SELECTION FUNCTIONALITY =====

let selectedCampaignId = null;
let selectedCampaignData = null;

// Show campaign selection modal on page load
function showCampaignSelectionModal() {
    const modal = new bootstrap.Modal(document.getElementById('campaignSelectionModal'));
    modal.show();
    loadCampaignsForSelection();
}

// Load campaigns for selection
function loadCampaignsForSelection() {
    fetch('/api/crm/agent/campaigns')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                populateCampaignSelect(data.campaigns);
            } else {
                console.error('Error loading campaigns:', data.error);
                window.toastManager.show('Błąd ładowania kampanii: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error loading campaigns:', error);
            window.toastManager.show('Błąd ładowania kampanii', 'error');
        });
}

// Populate campaign select dropdown
function populateCampaignSelect(campaigns) {
    const select = document.getElementById('campaignSelect');
    if (!select) return;
    
    // Clear existing options except the first one
    select.innerHTML = '<option value="">-- Wybierz kampanię --</option>';
    
    if (campaigns.length === 0) {
        select.innerHTML += '<option value="" disabled>Brak dostępnych kampanii</option>';
        return;
    }
    
    // Add campaigns
    campaigns.forEach(campaign => {
        const option = document.createElement('option');
        option.value = campaign.id;
        option.textContent = `${campaign.name} (${campaign.available_contacts} dostępnych kontaktów)`;
        select.appendChild(option);
    });
}

// Handle campaign selection change
function handleCampaignSelection() {
    const select = document.getElementById('campaignSelect');
    const startBtn = document.getElementById('startWorkBtn');
    const infoCard = document.getElementById('selectedCampaignInfo');
    const infoContent = document.getElementById('campaignInfoContent');
    
    if (!select || !startBtn || !infoCard || !infoContent) return;
    
    const campaignId = select.value;
    
    if (campaignId) {
        // Enable start button
        startBtn.disabled = false;
        
        // Find campaign data
        fetch('/api/crm/agent/campaigns')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const campaign = data.campaigns.find(c => c.id == campaignId);
                    if (campaign) {
                        selectedCampaignId = campaignId;
                        selectedCampaignData = campaign;
                        
                        // Load campaign script immediately
                        loadCampaignScript(campaignId);
                        
                        // Show campaign info
                        infoContent.innerHTML = `
                            <div class="row">
                                <div class="col-md-6">
                                    <h6 class="text-primary">${campaign.name}</h6>
                                    <p class="text-muted">${campaign.description || 'Brak opisu'}</p>
                                </div>
                                <div class="col-md-6">
                                    <div class="row">
                                        <div class="col-6">
                                            <div class="text-center">
                                                <h5 class="text-success mb-0">${campaign.available_contacts}</h5>
                                                <small class="text-muted">Dostępne</small>
                                            </div>
                                        </div>
                                        <div class="col-6">
                                            <div class="text-center">
                                                <h5 class="text-info mb-0">${campaign.total_contacts}</h5>
                                                <small class="text-muted">Wszystkie</small>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row mt-2">
                                        <div class="col-4">
                                            <div class="text-center">
                                                <h6 class="text-primary mb-0">${campaign.new_contacts}</h6>
                                                <small class="text-muted">Nowe</small>
                                            </div>
                                        </div>
                                        <div class="col-4">
                                            <div class="text-center">
                                                <h6 class="text-warning mb-0">${campaign.callback_contacts}</h6>
                                                <small class="text-muted">Oddzwonienia</small>
                                            </div>
                                        </div>
                                        <div class="col-4">
                                            <div class="text-center">
                                                <h6 class="text-secondary mb-0">${campaign.potential_contacts}</h6>
                                                <small class="text-muted">Potencjalne</small>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                        infoCard.style.display = 'block';
                    }
                }
            })
            .catch(error => {
                console.error('Error loading campaign details:', error);
            });
    } else {
        // Disable start button and hide info
        startBtn.disabled = true;
        infoCard.style.display = 'none';
        selectedCampaignId = null;
        selectedCampaignData = null;
    }
}

// Load campaign script
function loadCampaignScript(campaignId) {
    fetch(`/api/crm/agent/campaign/${campaignId}/script`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.script_content) {
                console.log('📜 Loading campaign script:', data.script_content);
                displayCampaignScript(data.script_content, data.campaign_name);
            } else {
                console.log('❌ No script content available');
            }
        })
        .catch(error => {
            console.error('Error loading campaign script:', error);
        });
}

// Display campaign script
function displayCampaignScript(scriptContent, campaignName) {
    const callScript = document.getElementById('callScript');
    if (!callScript) {
        console.log('❌ callScript element not found');
        return;
    }
    
    console.log('✅ Displaying campaign script');
    
    // Replace all variables with actual data
    let processedScript = scriptContent;
    
    // Agent data
    const agentName = window.agentName || 'Agent';
    const agentFirstName = agentName.split(' ')[0];
    
    processedScript = processedScript.replace(/\[AGENT_IMIĘ\]/g, agentFirstName);
    
    // Note: Contact-specific variables will be replaced when contact is loaded
    
    callScript.innerHTML = processedScript;
    console.log('✅ Campaign script displayed');
}

// Start work with selected campaign
function startWorkWithCampaign() {
    if (!selectedCampaignId) {
        window.toastManager.show('Wybierz kampanię przed rozpoczęciem pracy', 'error');
        return;
    }
    
    // Hide modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('campaignSelectionModal'));
    modal.hide();
    
    // Show work panel
    const workPanel = document.getElementById('workPanel');
    if (workPanel) {
        workPanel.classList.add('campaign-selected');
    }
    
    // Show success message
    window.toastManager.show(`Rozpoczynasz pracę z kampanią: ${selectedCampaignData.name}`, 'success');
    
    // Note: Contact will be loaded when agent clicks "Rozpocznij pracę" button
}

// Note: loadNextContact function removed - use getNextContact() instead

// Initialize campaign selection on page load
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for DOM to be fully ready
    setTimeout(() => {
        showCampaignSelectionModal();
    }, 500);
});

// Add event listeners for campaign selection
document.addEventListener('DOMContentLoaded', function() {
    const campaignSelect = document.getElementById('campaignSelect');
    const startWorkBtn = document.getElementById('startWorkBtn');
    
    if (campaignSelect) {
        campaignSelect.addEventListener('change', handleCampaignSelection);
    }
    
    if (startWorkBtn) {
        startWorkBtn.addEventListener('click', startWorkWithCampaign);
    }
});
