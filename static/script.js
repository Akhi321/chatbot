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
                canvasContainer.style.marginTop = "20px";
                canvasContainer.style.background = "linear-gradient(135deg, rgba(30, 30, 30, 0.8) 0%, rgba(40, 40, 40, 0.8) 100%)";
                canvasContainer.style.padding = "20px";
                canvasContainer.style.borderRadius = "14px";
                canvasContainer.style.width = "100%";
                canvasContainer.style.maxWidth = "100%";
                canvasContainer.style.border = "1px solid rgba(80, 80, 80, 0.5)";
                canvasContainer.style.backdropFilter = "blur(10px)";
                canvasContainer.style.animation = `slideInUp 0.5s ease-out ${index * 0.1}s forwards`;
                canvasContainer.style.opacity = "0";
                
                const titleDiv = document.createElement("div");
                titleDiv.style.fontSize = "13px";
                titleDiv.style.fontWeight = "700";
                titleDiv.style.color = "#e8e8e8";
                titleDiv.style.marginBottom = "16px";
                titleDiv.style.textTransform = "uppercase";
                titleDiv.style.letterSpacing = "1px";
                titleDiv.style.borderBottom = "2px solid rgba(100, 100, 100, 0.6)";
                titleDiv.style.paddingBottom = "8px";
                titleDiv.innerText = chartData.title;
                canvasContainer.appendChild(titleDiv);
                
                const canvas = document.createElement("canvas");
                canvas.style.maxHeight = "450px";
                canvas.style.minHeight = "350px";
                canvasContainer.appendChild(canvas);
                bubbleDiv.appendChild(canvasContainer);

                const gradientColor = index % 3 === 0 
                    ? { bg: 'rgba(100, 100, 100, 0.8)', border: 'rgb(150, 150, 150)' }
                    : index % 3 === 1
                    ? { bg: 'rgba(80, 80, 80, 0.8)', border: 'rgb(130, 130, 130)' }
                    : { bg: 'rgba(110, 110, 110, 0.8)', border: 'rgb(160, 160, 160)' };

                new Chart(canvas, {
                    type: 'bar',
                    data: {
                        labels: chartData.labels,
                        datasets: [{
                            label: chartData.title,
                            data: chartData.data,
                            backgroundColor: gradientColor.bg,
                            borderColor: gradientColor.border,
                            borderWidth: 2.5,
                            borderRadius: 8,
                            hoverBackgroundColor: gradientColor.border,
                            hoverBorderWidth: 3,
                        }]
                    },
                    options: {
                        indexAxis: chartData.labels.length > 5 ? 'y' : 'x',
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: {
                            duration: 1000,
                            easing: 'easeInOutQuart'
                        },
                        plugins: {
                            legend: {
                                display: true,
                                position: 'top',
                                labels: {
                                    color: '#c0c0c0',
                                    font: { size: 12, weight: '600' },
                                    padding: 15,
                                    usePointStyle: true,
                                    pointStyle: 'circle'
                                }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(20, 20, 20, 0.95)',
                                padding: 14,
                                cornerRadius: 8,
                                titleFont: { size: 13, weight: 'bold' },
                                bodyFont: { size: 12 },
                                borderColor: gradientColor.border,
                                borderWidth: 2,
                                callbacks: {
                                    label: function(context) {
                                        return context.dataset.label + ': ' + context.parsed.y.toFixed(2);
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                grid: {
                                    color: 'rgba(80, 80, 80, 0.3)',
                                    drawBorder: false,
                                    lineWidth: 1
                                },
                                ticks: {
                                    color: 'rgba(180, 180, 180, 0.8)',
                                    font: { size: 11, weight: '500' }
                                }
                            },
                            x: {
                                grid: {
                                    display: false,
                                    drawBorder: false
                                },
                                ticks: {
                                    color: 'rgba(180, 180, 180, 0.8)',
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
