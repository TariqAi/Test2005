class AgentXChat {
    constructor() {
        this.apiUrl = 'http://localhost:8000';
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.ttsEnabled = true; // Always enabled for auto-play
        
        this.initializeElements();
        this.bindEvents();
        this.checkConnection();
    }

    initializeElements() {
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.voiceBtn = document.getElementById('voice-btn');
        this.ttsToggle = document.getElementById('tts-toggle');
        this.chatMessages = document.getElementById('chat-messages');
        this.connectionStatus = document.getElementById('connection-status');
        this.statusText = document.getElementById('status-text');
        this.voiceEnabled = { checked: true }; // Default voice enabled
        this.ttsEnabled = true; // Default TTS enabled
    }

    bindEvents() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.voiceBtn.addEventListener('click', () => this.toggleVoiceRecording());
        this.ttsToggle.addEventListener('click', () => this.toggleTTS());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        // Removed API URL input event since sidebar is gone
    }

    async checkConnection() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            if (response.ok) {
                this.updateConnectionStatus(true, 'Connected');
            } else {
                this.updateConnectionStatus(false, 'Connection Error');
            }
        } catch (error) {
            this.updateConnectionStatus(false, 'Offline');
        }
    }

    updateConnectionStatus(isOnline, text) {
        this.connectionStatus.className = `status-dot ${isOnline ? 'online' : 'offline'}`;
        this.statusText.textContent = text;
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        this.addMessage(message, 'user');
        this.messageInput.value = '';
        
        try {
            const response = await fetch(`${this.apiUrl}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    question: message,
                    use_voice: true // Always request TTS
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.addMessage(data.answer, 'bot');
                
                // Automatically play TTS audio when available
                if (data.audio_url) {
                    // Small delay to ensure message is rendered
                    setTimeout(() => {
                        this.playAudio(data.audio_url);
                    }, 500);
                }
            } else {
                const errorData = await response.json();
                this.addMessage(`Error: ${errorData.detail || 'Unknown error'}`, 'bot');
            }
        } catch (error) {
            this.addMessage('Connection error. Please check if the backend is running.', 'bot');
        }
    }

    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        // معالجة النص لإضافة أسطر جديدة وتنسيق أفضل
        const processedContent = this.formatMessageContent(content);
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                ${sender === 'user' 
                    ? '<i class="fas fa-user"></i>' 
                    : '<img src="/static/logo.png" alt="AgentX AI" class="avatar-logo">'}
            </div>
            <div class="message-content">
                ${processedContent}
                ${sender === 'bot' ? '<div class="audio-indicator"><i class="fas fa-volume-up audio-icon"></i></div>' : ''}
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        
        return messageDiv;
    }

    // دالة جديدة لتنسيق محتوى الرسائل
    formatMessageContent(text) {
        // تقسيم النص إلى فقرات
        const paragraphs = text.split('\n\n').filter(p => p.trim());
        
        if (paragraphs.length <= 1) {
            // نص واحد - معالجة الأسطر الجديدة
            const lines = text.split('\n').filter(line => line.trim());
            if (lines.length > 1) {
                return lines.map(line => `<p>${this.processMixedText(line.trim())}</p>`).join('');
            } else {
                return `<p>${this.processMixedText(text)}</p>`;
            }
        } else {
            // فقرات متعددة
            return paragraphs.map(paragraph => {
                const lines = paragraph.split('\n').filter(line => line.trim());
                if (lines.length > 1) {
                    return lines.map(line => `<p>${this.processMixedText(line.trim())}</p>`).join('');
                } else {
                    return `<p>${this.processMixedText(paragraph.trim())}</p>`;
                }
            }).join('');
        }
    }

    // تحسين دالة معالجة النص المختلط
    processMixedText(text) {
        // حماية الكلمات الإنجليزية والأرقام
        return text.replace(/(AgentX AI|[A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*)/g, 
            '<span class="brand-name">$1</span>');
    }

    async toggleVoiceRecording() {
        if (!this.isRecording) {
            await this.startRecording();
        } else {
            this.stopRecording();
        }
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = () => {
                this.processRecording();
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            this.voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
            this.voiceBtn.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
        } catch (error) {
            alert('Microphone access denied or not available.');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
            this.voiceBtn.style.background = 'linear-gradient(135deg, #06b6d4, #3b82f6)';
        }
    }

    async processRecording() {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('audio_file', audioBlob, 'recording.wav');

        try {
            const response = await fetch(`${this.apiUrl}/voice-query`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                this.addMessage(data.question, 'user');
                this.addMessage(data.answer, 'bot');
                
                if (this.voiceEnabled.checked && data.audio_url) {
                    this.playAudio(data.audio_url);
                }
            } else {
                this.addMessage('Sorry, I could not process your voice message.', 'bot');
            }
        } catch (error) {
            this.addMessage('Voice processing error. Please try again.', 'bot');
        }
    }

    async playAudio(audioUrl) {
        try {
            const audio = new Audio(`${this.apiUrl}${audioUrl}`);
            
            // Show audio playing indicator
            const audioIcon = document.querySelector('.message.bot-message:last-child .audio-icon');
            if (audioIcon) {
                audioIcon.style.color = '#667eea';
                audioIcon.classList.add('playing');
            }
            
            audio.onended = () => {
                if (audioIcon) {
                    audioIcon.style.color = '';
                    audioIcon.classList.remove('playing');
                }
            };
            
            audio.onerror = () => {
                if (audioIcon) {
                    audioIcon.style.color = '#ff6b6b';
                    audioIcon.classList.remove('playing');
                }
                console.error('Audio playback failed');
            };
            
            await audio.play();
        } catch (error) {
            console.error('Audio playback failed:', error);
        }
    }

    addLoadingMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system-message loading';
        messageDiv.innerHTML = `<div class="message-content">${text}</div>`;
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        return messageDiv;
    }

    removeLoadingMessage(messageDiv) {
        if (messageDiv && messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
        }
    }

    playAudio(audioUrl) {
        const audio = new Audio(`${this.apiUrl}${audioUrl}`);
        audio.play().catch(error => {
            console.error('Audio playback failed:', error);
        });
    }
}

// Initialize the chat application
document.addEventListener('DOMContentLoaded', () => {
    new AgentXChat();
});