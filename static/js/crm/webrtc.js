/**
 * WebRTC Integration for CRM Agent Calls
 * Provides VoIP calling functionality through browser
 */

class WebRTCCall {
    constructor() {
        this.peerConnection = null;
        this.localStream = null;
        this.remoteStream = null;
        this.callId = null;
        this.isCallActive = false;
        this.callStartTime = null;
        
        // WebRTC Configuration
        this.rtcConfig = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' }
            ]
        };
        
        // Initialize WebRTC when page loads
        this.init();
    }
    
    async init() {
        try {
            // Check if browser supports WebRTC
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('WebRTC nie jest obsługiwane w tej przeglądarce');
            }
            
            console.log('🎯 WebRTC initialized successfully');
            this.updateCallStatus('WebRTC gotowy do połączeń');
            
        } catch (error) {
            console.error('❌ WebRTC initialization failed:', error);
            this.updateCallStatus('Błąd inicjalizacji WebRTC: ' + error.message);
        }
    }
    
    async makeCall(phoneNumber, contactId) {
        try {
            console.log('📞 Rozpoczynam połączenie z:', phoneNumber);
            this.updateCallStatus('Inicjalizacja połączenia...');
            
            // Get user media (microphone)
            this.localStream = await navigator.mediaDevices.getUserMedia({
                audio: true,
                video: false
            });
            
            console.log('🎤 Mikrofon uzyskany');
            
            // Create peer connection
            this.peerConnection = new RTCPeerConnection(this.rtcConfig);
            
            // Add local stream to peer connection
            this.localStream.getTracks().forEach(track => {
                this.peerConnection.addTrack(track, this.localStream);
            });
            
            // Handle remote stream
            this.peerConnection.ontrack = (event) => {
                console.log('🔊 Otrzymano zdalny strumień audio');
                this.remoteStream = event.streams[0];
                this.playRemoteAudio();
            };
            
            // Handle ICE candidates
            this.peerConnection.onicecandidate = (event) => {
                if (event.candidate) {
                    console.log('🧊 ICE candidate:', event.candidate);
                    // Send ICE candidate to server/VoIP gateway
                    this.sendIceCandidate(event.candidate);
                }
            };
            
            // Handle connection state changes
            this.peerConnection.onconnectionstatechange = () => {
                console.log('🔗 Connection state:', this.peerConnection.connectionState);
                this.handleConnectionStateChange();
            };
            
            // Start call via CRM API
            const response = await fetch('/api/crm/agent/start-call', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    contact_id: contactId,
                    phone_number: phoneNumber,
                    webrtc_enabled: true
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.callId = data.call_id;
                this.callStartTime = new Date(data.start_time);
                this.isCallActive = true;
                
                console.log('✅ Połączenie rozpoczęte z ID:', this.callId);
                this.updateCallStatus('Połączenie nawiązane');
                
                // Update UI
                this.updateCallUI(true);
                
                // Start call timer
                this.startCallTimer();
                
                return true;
            } else {
                throw new Error(data.error || 'Błąd rozpoczęcia połączenia');
            }
            
        } catch (error) {
            console.error('❌ Błąd połączenia:', error);
            this.updateCallStatus('Błąd połączenia: ' + error.message);
            this.endCall();
            return false;
        }
    }
    
    async endCall() {
        try {
            console.log('📴 Kończenie połączenia...');
            
            // Stop local stream
            if (this.localStream) {
                this.localStream.getTracks().forEach(track => {
                    track.stop();
                });
                this.localStream = null;
            }
            
            // Close peer connection
            if (this.peerConnection) {
                this.peerConnection.close();
                this.peerConnection = null;
            }
            
            // Stop remote audio
            if (this.remoteStream) {
                const audioElement = document.getElementById('remoteAudio');
                if (audioElement) {
                    audioElement.srcObject = null;
                }
                this.remoteStream = null;
            }
            
            // Update status
            this.isCallActive = false;
            this.updateCallStatus('Połączenie zakończone');
            this.updateCallUI(false);
            
            // Stop timer
            this.stopCallTimer();
            
            console.log('✅ Połączenie zakończone');
            
        } catch (error) {
            console.error('❌ Błąd kończenia połączenia:', error);
        }
    }
    
    playRemoteAudio() {
        // Create audio element for remote stream
        let audioElement = document.getElementById('remoteAudio');
        if (!audioElement) {
            audioElement = document.createElement('audio');
            audioElement.id = 'remoteAudio';
            audioElement.autoplay = true;
            audioElement.controls = false;
            audioElement.style.display = 'none';
            document.body.appendChild(audioElement);
        }
        
        audioElement.srcObject = this.remoteStream;
        audioElement.play().catch(error => {
            console.error('❌ Błąd odtwarzania zdalnego audio:', error);
        });
    }
    
    handleConnectionStateChange() {
        const state = this.peerConnection.connectionState;
        
        switch (state) {
            case 'connected':
                this.updateCallStatus('Połączono');
                break;
            case 'disconnected':
                this.updateCallStatus('Rozłączono');
                break;
            case 'failed':
                this.updateCallStatus('Błąd połączenia');
                this.endCall();
                break;
            case 'closed':
                this.updateCallStatus('Połączenie zamknięte');
                break;
        }
    }
    
    updateCallStatus(message) {
        const statusElement = document.getElementById('call-status-text');
        if (statusElement) {
            statusElement.textContent = message;
        }
        
        const statusContainer = document.getElementById('call-status');
        if (statusContainer) {
            statusContainer.style.display = 'block';
        }
        
        console.log('📞 Status:', message);
    }
    
    updateCallUI(isActive) {
        const makeCallBtn = document.getElementById('makeCallBtn');
        const endCallBtn = document.getElementById('endCallBtn');
        
        if (isActive) {
            if (makeCallBtn) {
                makeCallBtn.style.display = 'none';
            }
            if (endCallBtn) {
                endCallBtn.style.display = 'inline-block';
            }
        } else {
            if (makeCallBtn) {
                makeCallBtn.style.display = 'inline-block';
                makeCallBtn.disabled = false;
                makeCallBtn.innerHTML = '<i class="fas fa-phone me-1"></i>Zadzwoń';
            }
            if (endCallBtn) {
                endCallBtn.style.display = 'none';
            }
        }
    }
    
    startCallTimer() {
        this.callTimer = setInterval(() => {
            if (this.callStartTime && this.isCallActive) {
                const now = new Date();
                const duration = Math.floor((now - this.callStartTime) / 1000);
                const minutes = Math.floor(duration / 60);
                const seconds = duration % 60;
                
                this.updateCallStatus(`Połączono - ${minutes}:${seconds.toString().padStart(2, '0')}`);
            }
        }, 1000);
    }
    
    stopCallTimer() {
        if (this.callTimer) {
            clearInterval(this.callTimer);
            this.callTimer = null;
        }
    }
    
    // Send ICE candidate to server (for future VoIP gateway integration)
    async sendIceCandidate(candidate) {
        try {
            await fetch('/api/crm/agent/ice-candidate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    call_id: this.callId,
                    candidate: candidate
                })
            });
        } catch (error) {
            console.error('❌ Błąd wysyłania ICE candidate:', error);
        }
    }
    
    // Get call duration
    getCallDuration() {
        if (this.callStartTime && this.isCallActive) {
            const now = new Date();
            return Math.floor((now - this.callStartTime) / 1000);
        }
        return 0;
    }
}

// Global WebRTC instance
let webrtcCall = null;

// Initialize WebRTC when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    webrtcCall = new WebRTCCall();
});

// Export for use in other scripts
window.WebRTCCall = WebRTCCall;
window.webrtcCall = webrtcCall;
