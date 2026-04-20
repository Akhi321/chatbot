document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const sendButton = document.getElementById("send-btn");
    const userInput = document.getElementById("user-input");
    const chatbox = document.getElementById("chatbox");

    function appendMessage(sender, text) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender);
        
        const bubbleDiv = document.createElement("div");
        bubbleDiv.classList.add("bubble");
        
        bubbleDiv.innerText = text;
        bubbleDiv.innerHTML = bubbleDiv.innerHTML.replace(/\n/g, "<br>");
        
        messageDiv.appendChild(bubbleDiv);
        chatbox.appendChild(messageDiv);
        
        chatbox.scrollTop = chatbox.scrollHeight;
        return messageDiv;
    }

    function showTypingIndicator() {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", "bot");
        messageDiv.id = "typing-indicator";
        
        const bubbleDiv = document.createElement("div");
        bubbleDiv.classList.add("bubble");
        bubbleDiv.innerHTML = `
            <div class="loading-dots">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        `;
        
        messageDiv.appendChild(bubbleDiv);
        chatbox.appendChild(messageDiv);
        chatbox.scrollTop = chatbox.scrollHeight;
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById("typing-indicator");
        if (indicator) {
            indicator.remove();
        }
    }

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const message = userInput.value.trim();
        if (!message) return;
        
        appendMessage("user", message);
        userInput.value = "";
        showTypingIndicator();
        sendButton.disabled = true;
        
        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ message: message })
            });
            
            removeTypingIndicator();
            
            if (response.ok) {
                const data = await response.json();
                appendMessage("bot", data.response);
            } else {
                appendMessage("bot", "Sorry, something went wrong on the server. Please try again.");
            }
        } catch (error) {
            removeTypingIndicator();
            appendMessage("bot", "Sorry, I could not reach the server. Please try again.");
            console.error(error);
        } finally {
            sendButton.disabled = false;
            userInput.focus();
        }
    });
});
