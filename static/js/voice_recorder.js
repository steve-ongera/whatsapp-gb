// Voice recording functionality

class VoiceRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.stream = null;
    }

    async startRecording() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(this.stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.onstop = () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                this.onRecordingComplete(audioBlob);
                this.cleanup();
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            
            return true;
        } catch (error) {
            console.error('Error accessing microphone:', error);
            alert('Please allow microphone access to record voice messages');
            return false;
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
        }
    }

    cleanup() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }

    onRecordingComplete(audioBlob) {
        // Override this method to handle the recorded audio
        console.log('Recording complete', audioBlob);
    }

    getDuration() {
        // Calculate duration based on recording time
        // This is a placeholder - you'd track actual recording time
        return 0;
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceRecorder;
}
