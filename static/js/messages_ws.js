document.addEventListener("DOMContentLoaded", () => {

    const otherUsernameInput = document.getElementById("chatUsername");
    const currentUserInput = document.getElementById("currentUser");
    const messageInput = document.getElementById("chatMessageInput");
    const sendButton = document.getElementById("chatSendButton");
    const chatBox = document.getElementById("chatBox");

    if (!otherUsernameInput || !currentUserInput || !messageInput || !sendButton || !chatBox) {
        return;
    }

    const OTHER_USER = otherUsernameInput.value;
    const CURRENT_USER = currentUserInput.value;

    const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
    const socketUrl = protocol + window.location.host + "/ws/chat/" + OTHER_USER + "/";

    let chatSocket = null;

    function connect() {
        chatSocket = new WebSocket(socketUrl);

        chatSocket.onmessage = (e) => {
            const data = JSON.parse(e.data);

            const div = document.createElement("div");
            div.classList.add("message");
            div.classList.add(data.sender === CURRENT_USER ? "sent" : "received");

            div.innerHTML = `
                ${data.text}
                <div class="message-time">${new Date(data.created_at).toLocaleString()}</div>
            `;

            chatBox.appendChild(div);
            chatBox.scrollTop = chatBox.scrollHeight;
        };

        chatSocket.onclose = () => {
            setTimeout(connect, 1000);
        };
    }

    connect();

    const sendMessage = () => {
        const text = messageInput.value.trim();
        if (!text || !chatSocket || chatSocket.readyState !== WebSocket.OPEN) return;

        chatSocket.send(JSON.stringify({ text }));
        messageInput.value = "";
    };

    sendButton.addEventListener("click", sendMessage);

    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            sendMessage();
        }
    });

    chatBox.scrollTop = chatBox.scrollHeight;
});