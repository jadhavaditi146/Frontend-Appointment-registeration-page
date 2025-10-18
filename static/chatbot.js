const chatbotButton = document.getElementById("chatbot-button");
const chatbotPopup = document.getElementById("chatbot-popup");
const closeBtn = document.getElementById("close-btn");
const sendBtn = document.getElementById("send-btn");
const input = document.getElementById("chatbot-input");
const messages = document.getElementById("chatbot-messages");

// Toggle chatbot popup
chatbotButton.addEventListener("click", () => {
  chatbotPopup.classList.toggle("hidden");
});

// Close button
closeBtn.addEventListener("click", () => {
  chatbotPopup.classList.add("hidden");
});

// Send message
sendBtn.addEventListener("click", async () => {
  const userText = input.value.trim();
  if (!userText) return;

  addMessage("You", userText);
  input.value = "";

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userText })
    });

    const data = await response.json();
    addMessage("AI", data.reply, true);
  } catch (err) {
    addMessage("AI", "❌ Error fetching response. Please try again.", true);
  }
});

// Add message to chat
function addMessage(sender, text, isHTML = false) {
  const div = document.createElement("div");
  div.classList.add("py-2", "px-3", "rounded-lg", "max-w-[80%]");

  if (sender === "AI") {
    div.classList.add("bg-blue-100", "text-gray-900", "self-start");
    div.innerHTML = `<strong>${sender}:</strong><br>${text}`;
  } else {
    div.classList.add("bg-blue-600", "text-white", "self-end");
    div.textContent = `${sender}: ${text}`;
  }

  // Add flex container if not present
  if (!messages.classList.contains("flex") || !messages.classList.contains("flex-col")) {
    messages.classList.add("flex", "flex-col", "space-y-2");
  }

  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

// Optional: allow Enter key to send message
input.addEventListener("keypress", function(e) {
  if (e.key === "Enter") sendBtn.click();
});
