// static/main.js

function sendMessage() {
    const userInput = document.getElementById('user-input').value;
    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML += `<div class="message"><strong>You:</strong> ${userInput}</div>`;
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userInput }),
    })
    .then(response => response.json())
    .then(data => {
        chatBox.innerHTML += `<div class="message"><strong>GPT-3.5:</strong> ${data.response}</div>`;
        document.getElementById('user-input').value = '';
    })
    .catch(error => {
        chatBox.innerHTML += `<div class="message"><strong>Error:</strong> ${error}</div>`;
    });
}
