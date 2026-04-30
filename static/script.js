document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const sendButton = document.getElementById("send-btn");
    const userInput = document.getElementById("user-input");
    const chatbox = document.getElementById("chatbox");

    function appendMessage(sender, text, charts = []) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender);
        
        const bubbleDiv = document.createElement("div");
        bubbleDiv.classList.add("bubble");

        bubbleDiv.innerText = text;
        bubbleDiv.innerHTML = bubbleDiv.innerHTML.replace(/\n/g, "<br>");

        if (charts && charts.length > 0) {
            charts.forEach((chartData, index) => {
                const canvasContainer = document.createElement("div");
                canvasContainer.style.marginTop = "15px";
                canvasContainer.style.background = "linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.08) 100%)";
                canvasContainer.style.padding = "16px";
                canvasContainer.style.borderRadius = "12px";
                canvasContainer.style.width = "100%";
                canvasContainer.style.maxWidth = "450px";
                canvasContainer.style.border = "1px solid rgba(102, 126, 234, 0.3)";
                canvasContainer.style.backdropFilter = "blur(10px)";
                
                const titleDiv = document.createElement("div");
                titleDiv.style.fontSize = "12px";
                titleDiv.style.fontWeight = "600";
                titleDiv.style.color = "#a0aec0";
                titleDiv.style.marginBottom = "12px";
                titleDiv.style.textTransform = "uppercase";
                titleDiv.style.letterSpacing = "0.5px";
                titleDiv.innerText = chartData.title;
                canvasContainer.appendChild(titleDiv);
                
                const canvas = document.createElement("canvas");
                canvas.style.maxHeight = "300px";
                canvasContainer.appendChild(canvas);
                bubbleDiv.appendChild(canvasContainer);

                const gradientColor = index % 2 === 0 
                    ? { bg: 'rgba(102, 126, 234, 0.7)', border: 'rgb(102, 126, 234)' }
                    : { bg: 'rgba(118, 75, 162, 0.7)', border: 'rgb(118, 75, 162)' };

                new Chart(canvas, {
                    type: 'bar',
                    data: {
                        labels: chartData.labels,
                        datasets: [{
                            label: chartData.title,
                            data: chartData.data,
                            backgroundColor: gradientColor.bg,
                            borderColor: gradientColor.border,
                            borderWidth: 2,
                            borderRadius: 6,
                            hoverBackgroundColor: gradientColor.border,
                            hoverBorderWidth: 3,
                        }]
                    },
                    options: {
                        indexAxis: chartData.labels.length > 5 ? 'y' : 'x',
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                padding: 12,
                                cornerRadius: 8,
                                titleFont: { size: 13, weight: 'bold' },
                                bodyFont: { size: 12 },
                                borderColor: gradientColor.border,
                                borderWidth: 1,
                                callbacks: {
                                    label: function(context) {
                                        return ' ' + context.parsed.y.toFixed(2);
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: {
                                    color: 'rgba(102, 126, 234, 0.1)',
                                    drawBorder: false
                                },
                                ticks: {
                                    color: 'rgba(224, 231, 255, 0.6)',
                                    font: { size: 11, weight: '500' }
                                }
                            },
                            x: {
                                grid: {
                                    display: false,
                                    drawBorder: false
                                },
                                ticks: {
                                    color: 'rgba(224, 231, 255, 0.6)',
                                    font: { size: 11, weight: '500' }
                                }
                            }
                        }
                    }
                });
            });
        }
        
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
                appendMessage("bot", data.response, data.charts);
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
