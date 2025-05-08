document.getElementById('sendBtn').addEventListener('click', sendMessage);

document.getElementById('chatInput').addEventListener('keypress', (e) => {
    console.log("Отправка 1");
    if (e.key === 'Enter' && !e.shiftKey) {
        console.log("Отправка");
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (message) {
        const chatHistory = document.getElementById('chatHistory');

        // Добавляем сообщение пользователя
        const userMsg = document.createElement('div');
        userMsg.className = 'message human-message';
        userMsg.textContent = message;
        chatHistory.appendChild(userMsg);

        input.value = '';
        input.style.height = 'auto';
        document.getElementById('sendBtn').disabled = true;
        chatHistory.scrollTop = chatHistory.scrollHeight;

        try {
            // Показываем индикатор печати
            const typingPromise = showTypingIndicator(chatHistory);
            console.log("SEND DATA");
            // Отправляем запрос
            const response = await fetch('/langchain_api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${jwtToken}`
                },
                body: JSON.stringify({session_id: chat_id,user_query: message})
            });

            const data = await response.json();

            // Ждем минимум 1.5 секунды (время показа индикатора)
            await typingPromise;
            console.log("PRINT DATA");
            console.log(data);
            // Добавляем ответ бота
            let text = formatMarkdownToHtml(data.response);
            console.log(text);
            // addMessageToChat('ai-message', data.response);
            addMessageToChat('ai-message', text);
            chat_id = data.session_id;
            // if (chat_id === '') {
            //     console.log("IF");
            //     loadChats();
            // }

        } catch (error) {
            console.error('Error:', error);
            // Если индикатор еще показывается, ждем его завершения
            await typingPromise;
            addMessageToChat('ai-message', 'Произошла ошибка');
        }

        scrollToBottom();
    }
}

function formatMarkdownToHtml(markdownText) {
    if (!markdownText) return '';

    // Основные преобразования с сохранением читаемого формата
    let result = markdownText
        // Заголовки - добавляем переносы строк до и после
        .replace(/^#+\s*(.*)/gm, '\n$1\n')
        // Жирный/курсив - оставляем только текст
        .replace(/(\*\*|__)(.*?)\1/g, '$2')
        .replace(/(\*|_)(.*?)\1/g, '$2')
        // Зачеркивание - убираем
        .replace(/~~(.*?)~~/g, '$1')
        // Код - добавляем отступы и переносы строк
        .replace(/`([^`]+)`/g, ' $1 ')
        .replace(/```([^`]*?)```/gs, '\n\n$1\n\n')
        // Списки - добавляем перенос строки перед каждым элементом
        .replace(/(\n|^)\s*[\*\-+]\s+(.*)/g, '\n• $2')
        .replace(/(\n|^)\s*\d+\.\s+(.*)/g, '\n$2')
        // Ссылки - оставляем текст
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        // Изображения - заменяем на текст
        .replace(/!\[([^\]]*)\]\([^)]+\)/g, '[Изображение: $1]')
        // Горизонтальные линии - добавляем переносы строк
        .replace(/^[-*_]{3,}$/gm, '\n――――――\n')
        // Удаляем лишние пустые строки (более 2 подряд)
        .replace(/\n{3,}/g, '\n\n')
        // Обрезаем пробелы в начале и конце
        .trim();

    // Гарантируем возврат строки
    return result || '';
}

function showTypingIndicator(chatHistory) {
    return new Promise((resolve) => {
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'message ai-message typing-indicator';
        typingIndicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        chatHistory.appendChild(typingIndicator);
        chatHistory.scrollTop = chatHistory.scrollHeight;

        setTimeout(() => {
            typingIndicator.remove();
            resolve();
        }, 1500);
    });
}


function addMessageToChat(className, text) {
    const chatHistory = document.getElementById('chatHistory');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${className}`;
    messageDiv.textContent = text;
    chatHistory.appendChild(messageDiv);
}

async function loadChatHistory(sessionId) {
    try {
        const response = await fetch(`${CHAT_API}${sessionId}/`, {
            headers: {
                'Authorization': `Bearer ${jwtToken}`
            }
        });

        const data = await response.json();
        renderMessages(data.messages);
    } catch (error) {
        showError('Ошибка загрузки истории');
    }
}

function renderMessages(messages) {
    console.log(messages);

    const chatHistory = document.getElementById('chatHistory');
    chatHistory.innerHTML = '';

    messages.forEach(msg => {
        const div = document.createElement('div');
        div.className = `message ${msg.role}-message`;
        let data = formatMarkdownToHtml(msg.content);
        console.log("DATA FROM HISTORY");
        console.log(data);
        // div.textContent = msg.content;
        div.textContent = data;
        chatHistory.appendChild(div);
    });

    scrollToBottom();
}

async function scrollToBottomImmediate(element = document.getElementById('chatHistory')) {
    if (!element) return;

    return new Promise(resolve => {
        // 1. Принудительный reflow
        void element.offsetHeight;

        // 2. Установка позиции
        element.scrollTop = element.scrollHeight;

        // 3. Проверка через микротаск
        Promise.resolve().then(() => {
            element.scrollTop = element.scrollHeight;
            resolve();
        });
    });
}

async function scrollToBottomSmooth(element) {
    if (!element) return;

    return new Promise(resolve => {
        requestAnimationFrame(() => {
            element.scrollTo({top: element.scrollHeight, behavior: 'smooth'});
            setTimeout(resolve, 300);
        });
    });
}

async function scrollToBottom() {
    const chatHistory = document.getElementById('chatHistory');
    if (!chatHistory) return;

    await scrollToBottomImmediate(chatHistory);
    await scrollToBottomSmooth(chatHistory);

    // 🚀 Дополнительно скроллим всю страницу вниз
    window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
}

function showWelcomeMessage() {
    const chatHistory = document.getElementById('chatHistory');
    console.log("SHOW WELCOME MESSAGE");
    chat_id = '';
    if (!chatHistory) return;

    chatHistory.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-header">
                <h3>Добро пожаловать в чат!</h3>
                <p>Я ваш виртуальный помощник. Давайте начнём общение!</p>
            </div>

            <div class="suggestions-container">
                <p class="suggestion-title">Выберите один из примеров вопросов:</p>
                <div class="suggestion-items">
                    <div class="suggestion-item">Как мне начать работу с системой?</div>
                    <div class="suggestion-item">Какие основные функции доступны?</div>
                    <div class="suggestion-item">Можешь показать пример использования?</div>
                    <div class="suggestion-item">Как я могу решить свою задачу?</div>
                </div>
            </div>
        </div>
    `;

    document.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', () => {
            const inputField = document.getElementById('chatInput');
            inputField.value = item.textContent;
            inputField.focus();

            // Активируем кнопку отправки
            const sendBtn = document.getElementById('sendBtn');
            if (sendBtn) {
                sendBtn.disabled = false;
            }

            // Имитируем ввод для активации кнопки
            const event = new Event('input', {bubbles: true});
            inputField.dispatchEvent(event);
        });
    });
}