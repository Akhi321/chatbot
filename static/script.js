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
                canvasContainer.style.marginTop = "25px";
                canvasContainer.style.background = "linear-gradient(135deg, rgba(15, 50, 80, 0.6) 0%, rgba(20, 70, 100, 0.6) 100%)";
                canvasContainer.style.padding = "24px";
                canvasContainer.style.borderRadius = "16px";
                canvasContainer.style.width = "100%";
                canvasContainer.style.maxWidth = "100%";
                canvasContainer.style.border = "2px solid rgba(0, 150, 220, 0.5)";
                canvasContainer.style.backdropFilter = "blur(12px)";
                canvasContainer.style.animation = `slideInUp 0.6s ease-out ${index * 0.12}s forwards`;
                canvasContainer.style.opacity = "0";
                canvasContainer.style.boxShadow = "0 8px 40px rgba(0, 150, 220, 0.2), inset 0 1px 3px rgba(100, 200, 255, 0.2)";
                
                const titleDiv = document.createElement("div");
                titleDiv.style.fontSize = "14px";
                titleDiv.style.fontWeight = "800";
                titleDiv.style.color = "#00d4ff";
                titleDiv.style.marginBottom = "18px";
                titleDiv.style.textTransform = "uppercase";
                titleDiv.style.letterSpacing = "1.5px";
                titleDiv.style.borderBottom = "2px solid rgba(0, 200, 255, 0.4)";
                titleDiv.style.paddingBottom = "10px";
                titleDiv.style.textShadow = "0 0 10px rgba(0, 200, 255, 0.3)";
                titleDiv.innerText = chartData.title;
                canvasContainer.appendChild(titleDiv);
                
                const canvasWrapper = document.createElement("div");
                canvasWrapper.style.position = "relative";
                canvasWrapper.style.height = "450px";
                canvasWrapper.style.width = "100%";
                
                const canvas = document.createElement("canvas");
                canvasWrapper.appendChild(canvas);
                canvasContainer.appendChild(canvasWrapper);
                bubbleDiv.appendChild(canvasContainer);

                const gradientColors = [
                    { bg: 'rgba(0, 150, 220, 0.7)', border: 'rgb(0, 200, 255)' },
                    { bg: 'rgba(0, 180, 240, 0.7)', border: 'rgb(50, 220, 255)' },
                    { bg: 'rgba(0, 120, 200, 0.7)', border: 'rgb(0, 180, 220)' }
                ];
                
                const gradientColor = gradientColors[index % 3];

                new Chart(canvas, {
                    type: 'bar',
                    data: {
                        labels: chartData.labels,
                        datasets: [{
                            label: chartData.title,
                            data: chartData.data,
                            backgroundColor: gradientColor.bg,
                            borderColor: gradientColor.border,
                            borderWidth: 3,
                            borderRadius: 8,
                            hoverBackgroundColor: gradientColor.border,
                            hoverBorderWidth: 4,
                        }]
                    },
                    options: {
                        indexAxis: chartData.labels.length > 5 ? 'y' : 'x',
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: {
                            duration: 1200,
                            easing: 'easeInOutQuart'
                        },
                        plugins: {
                            legend: {
                                display: true,
                                position: 'top',
                                labels: {
                                    color: '#00d4ff',
                                    font: { size: 13, weight: '700' },
                                    padding: 18,
                                    usePointStyle: true,
                                    pointStyle: 'circle',
                                    textShadow: '0 0 8px rgba(0, 200, 255, 0.3)'
                                }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(10, 30, 50, 0.98)',
                                padding: 16,
                                cornerRadius: 10,
                                titleFont: { size: 14, weight: 'bold' },
                                bodyFont: { size: 13 },
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
                                    color: 'rgba(0, 150, 220, 0.2)',
                                    drawBorder: false,
                                    lineWidth: 1.5
                                },
                                ticks: {
                                    color: 'rgba(0, 200, 255, 0.8)',
                                    font: { size: 12, weight: '600' }
                                }
                            },
                            x: {
                                grid: {
                                    display: false,
                                    drawBorder: false
                                },
                                ticks: {
                                    color: 'rgba(0, 200, 255, 0.8)',
                                    font: { size: 12, weight: '600' }
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
