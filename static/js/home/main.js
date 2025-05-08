document.getElementById('sidebarToggle').addEventListener('click', function () {
    document.getElementById('sidebar').classList.toggle('active');
});

const chatItems = document.querySelectorAll('.chat-item');
chatItems.forEach(item => {
    item.addEventListener('click', function () {
        chatItems.forEach(i => i.classList.remove('active'));
        this.classList.add('active');
    });
});

const textarea = document.getElementById('chatInput');
textarea.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    document.getElementById('sendBtn').disabled = this.value.trim() === '';
});

document.getElementById('sendBtn').addEventListener('click', sendMessage);