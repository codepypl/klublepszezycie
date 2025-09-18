// Agent Work Interface
let agentStatus = 'inactive';
let currentContact = null;
let currentCallId = null;
let callStartTime = null;
let callTimer = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeAgentWork();
    checkForCallbacks();
    // Check for callbacks every minute
    setInterval(checkForCallbacks, 60000);
});

function initializeAgentWork() {
    // Set agent name in script
    document.getElementById('agentName').textContent = '{{ current_user.first_name or "Agent" }}';
    
    // Set today's date for callback scheduling
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('callbackDate').value = today;
    
    // Set current time + 1 hour for callback time
    const now = new Date();
    now.setHours(now.getHours() + 1);
    const timeString = now.toTimeString().slice(0, 5);
    document.getElementById('callbackTime').value = timeString;
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
    if (agentStatus !== 'active') {
        return;
    }
    
    fetch('/api/crm/agent/next-contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include'
    })
    .then(response => safeJsonParse(response))
    .then(data => {
        if (data.success && data.contact) {
            currentContact = data.contact;
            displayContact(currentContact);
            showCurrentCallPanel();
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
    document.getElementById('contactName').textContent = contact.name || '-';
    document.getElementById('contactPhone').textContent = contact.phone || '-';
    document.getElementById('contactCompany').textContent = contact.company || '-';
    document.getElementById('contactEmail').textContent = contact.email || '-';
    document.getElementById('contactNotes').textContent = contact.notes || '-';
    
    // Update script with contact name
    const scriptName = document.getElementById('scriptName');
    if (contact.name) {
        const firstName = contact.name.split(' ')[0];
        scriptName.textContent = firstName;
    } else {
        scriptName.textContent = '[IMIĘ]';
    }
    
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
        historyDiv.innerHTML = '<p class="text-muted">Brak historii połączeń</p>';
        return;
    }
    
    let historyHtml = '';
    calls.forEach(call => {
        const date = new Date(call.call_date).toLocaleString('pl-PL');
        const statusClass = getStatusClass(call.status);
        const statusText = getStatusText(call.status);
        
        historyHtml += `
            <div class="call-history-item mb-2">
                <div class="d-flex justify-content-between">
                    <span>${date}</span>
                    <span class="badge ${statusClass}">${statusText}</span>
                </div>
                ${call.notes ? `<small class="text-muted">${call.notes}</small>` : ''}
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
        'wrong_number': 'bg-dark'
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
        'wrong_number': 'Błędny numer'
    };
    return texts[status] || status;
}

function makeCall() {
    if (!currentContact) {
        showWarning('Brak kontaktu do dzwonienia');
        return;
    }
    
    // Disable call button
    const callBtn = document.getElementById('makeCallBtn');
    callBtn.disabled = true;
    callBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Dzwonienie...';
    
    // Start call via API
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
            startCallTimer();
            showOutcomePanel();
            hideCallActions();
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

function resetCallButton() {
    const callBtn = document.getElementById('makeCallBtn');
    callBtn.disabled = false;
    callBtn.innerHTML = '<i class="fas fa-phone me-2"></i>Zadzwoń';
}


function showCallbackScheduling() {
    document.getElementById('callbackScheduling').style.display = 'block';
}

function hideCallbackScheduling() {
    document.getElementById('callbackScheduling').style.display = 'none';
}

function saveCallbackOutcome() {
    const callbackDate = document.getElementById('callbackDate').value;
    const callbackTime = document.getElementById('callbackTime').value;
    
    if (!callbackDate || !callbackTime) {
        showWarning('Proszę podać datę i godzinę oddzwonienia');
        return;
    }
    
    saveCallOutcome('callback', callbackDate + ' ' + callbackTime);
}

function saveCallOutcome(outcome, callbackDateTime = null) {
    const notes = document.getElementById('callNotes').value;
    
    const data = {
        call_id: currentCallId,
        outcome: outcome,
        notes: notes
    };
    
    if (outcome === 'callback' && callbackDateTime) {
        data.callback_date = callbackDateTime;
    }
    
    // Stop call timer
    stopCallTimer();
    
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
            showSuccess(`Wynik rozmowy został zapisany!\nCzas rozmowy: ${formatDuration(data.duration_seconds)}`);
            resetOutcomePanel();
            checkForCallbacks(); // Check for new callbacks
            getNextContact();
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
    document.getElementById('callNotes').value = '';
    document.getElementById('callbackScheduling').style.display = 'none';
    
    // Show call actions
    showCallActions();
    
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

function hideCallActions() {
    document.getElementById('makeCallBtn').style.display = 'none';
}

function showCallActions() {
    document.getElementById('makeCallBtn').style.display = 'inline-block';
}

function checkForCallbacks() {
    fetch('/api/crm/agent/queue-status', {
        credentials: 'include'
    })
    .then(response => safeJsonParse(response))
    .then(data => {
        if (data.success && data.queue.callbacks > 0) {
            // Show callback alert
            const alertDiv = document.getElementById('callbackAlert');
            const callbackInfo = document.getElementById('callbackInfo');
            const countdown = document.getElementById('callbackCountdown');
            const headerCountdown = document.getElementById('callbackCountdownHeader');
            const countdownText = document.getElementById('countdownText');
            
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
        if (callStartTime) {
            const now = new Date();
            const duration = Math.floor((now - callStartTime) / 1000);
            // You could display the timer somewhere if needed
            console.log('Call duration:', formatDuration(duration));
        }
    }, 1000);
}

function stopCallTimer() {
    if (callTimer) {
        clearInterval(callTimer);
        callTimer = null;
    }
    callStartTime = null;
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

// Update countdown every second
setInterval(() => {
    const countdown = document.getElementById('callbackCountdown');
    if (countdown && countdown.textContent !== '-') {
        // Update countdown in real-time
        checkForCallbacks();
    }
}, 1000);
