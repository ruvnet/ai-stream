const video = document.getElementById('video');
const shareWebcamButton = document.getElementById('shareWebcam');
const shareScreenButton = document.getElementById('shareScreen');
const shareApplicationButton = document.getElementById('shareApplication');
const startCaptureButton = document.getElementById('startCapture');
const stopCaptureButton = document.getElementById('stopCapture');
const responsesDiv = document.getElementById('responses');
const toggleSettingsButton = document.getElementById('toggleSettings');
const settingsPanel = document.querySelector('.settings-panel');
const saveSettingsButton = document.getElementById('saveSettings');
let captureInterval;
let refreshRate = 15;
let customPrompt = "Analyze this frame";
let apiKey = "";

// Handle button toggles and video stream selection
document.querySelectorAll('.btn-group-toggle .btn').forEach(button => {
    button.addEventListener('click', async (event) => {
        // Remove active class from all buttons
        document.querySelectorAll('.btn-group-toggle .btn').forEach(btn => btn.classList.remove('active'));
        
        // Add active class to the clicked button
        event.target.closest('.btn').classList.add('active');

        const selectedButtonId = event.target.querySelector('input').id;
        let stream;
        try {
            if (selectedButtonId === 'shareWebcam') {
                stream = await navigator.mediaDevices.getUserMedia({ video: true });
            } else if (selectedButtonId === 'shareScreen') {
                stream = await navigator.mediaDevices.getDisplayMedia({ video: true });
            } else if (selectedButtonId === 'shareApplication') {
                stream = await navigator.mediaDevices.getDisplayMedia({
                    video: {
                        cursor: "always",
                        displaySurface: "application"
                    }
                });
            }
            video.srcObject = stream;
        } catch (err) {
            console.error(`Error accessing ${selectedButtonId}: `, err);
        }
    });
});

// Toggle settings panel
toggleSettingsButton.addEventListener('click', () => {
    settingsPanel.style.display = settingsPanel.style.display === 'none' ? 'block' : 'none';
});

// Save settings
saveSettingsButton.addEventListener('click', () => {
    customPrompt = document.getElementById('customPrompt').value || "Analyze this frame";
    refreshRate = document.getElementById('refreshRate').value || 15;
    apiKey = document.getElementById('apiKey').value || "";
    settingsPanel.style.display = 'none';
});

// Start Capture
startCaptureButton.addEventListener('click', () => {
    captureInterval = setInterval(captureFrame, refreshRate * 1000); // Capture every `refreshRate` seconds
});

// Stop Capture
stopCaptureButton.addEventListener('click', () => {
    clearInterval(captureInterval);
});

function captureFrame() {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg');

    fetch('/process_frame', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ image: dataUrl, prompt: customPrompt, api_key: apiKey })
    })
    .then(response => response.json())
    .then(data => {
        const p = document.createElement('p');
        p.textContent = data.response;
        responsesDiv.appendChild(p);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
