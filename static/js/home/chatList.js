// Глобальные переменные
let chats = []; // Храним все чаты в памяти
let nextTempId = -1; // Для временных ID до сохранения на сервере
let currentActiveChatId = null; // Текущий активный чат

// 1. Вспомогательные функции
function showLoadingState(isLoading) {
    const btn = document.getElementById('newChatBtn');
    if (btn) {
        if (isLoading) {
            btn.disabled = true;
            btn.innerHTML = 'Создание...';
        } else {
            btn.disabled = false;
            btn.innerHTML = 'Новый чат';
        }
    }
}

function showEmptyChatMessage() {
    const chatHistory = document.getElementById('chatHistory');
    if (chatHistory) {
        chatHistory.innerHTML = '<div class="empty-message">Выберите чат или создайте новый</div>';
    }
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    const container = document.getElementById('chatContainer') || document.body;
    container.appendChild(errorDiv);
    setTimeout(() => errorDiv.remove(), 3000);
}

// 2. Функции работы с чатами
async function loadChats() {
    try {
        showLoadingState(true);
        const response = await fetch('/langchain_api/chat/sessions/', {
            headers: {
                'Accept': 'application/json',
                'Authorization': `Bearer ${jwtToken}`
            }
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        // Получаем данные и сохраняем как есть (объект с sessions)
        chats = await response.json();
        console.log("Server response:", chats);

        updateChatListUI();

        if (chats.sessions && chats.sessions.length > 0) {
            currentActiveChatId = chats.sessions[0].session_id;
            setActiveChat(currentActiveChatId);
            chat_id = currentActiveChatId;
            console.log("ACTIVE CHAT");
            console.log(currentActiveChatId);
            await loadChatHistory(currentActiveChatId);
        } else {
            showEmptyChatMessage();
        }
    } catch (error) {
        console.error('Ошибка загрузки чатов:', error);
        showError('Не удалось загрузить список чатов');
        showWelcomeMessage();
    } finally {
        showLoadingState(false);
    }
}

// Функции работы с UI
function updateChatListUI() {
    const chatList = document.getElementById('chatList');
    if (!chatList) {
        console.error('Chat list element not found');
        return;
    }

    console.log("Raw chats data:", chats); // Логируем исходные данные

    // Получаем массив сессий из объекта
    const sessionsArray = chats?.sessions || [];
    console.log("Sessions array:", sessionsArray);

    // Очищаем список перед обновлением
    chatList.innerHTML = '';

    if (sessionsArray.length === 0) {
        chatList.innerHTML = '<div class="no-chats">Нет активных чатов</div>';
        return;
    }

    // Создаем элементы для каждой сессии
    sessionsArray.forEach(session => {
        const chatItem = document.createElement('div');
        chatItem.className = `chat-item ${session.session_id === currentActiveChatId ? 'active' : ''}`;
        chatItem.textContent = session.first_message || "Новый чат";
        chatItem.dataset.sessionId = session.session_id;

        // Добавляем кнопки для удаления и редактирования
        const deleteButton = document.createElement('button');
        deleteButton.textContent = 'Удалить';
        deleteButton.onclick = (e) => {
            e.stopPropagation();
            deleteChat(session.session_id);
        };

        const editButton = document.createElement('button');
        editButton.textContent = 'Редактировать';
        editButton.onclick = (e) => {
            e.stopPropagation();
            editChatTitle(session.session_id);
        };

        chatItem.appendChild(deleteButton);
        chatItem.appendChild(editButton);

        chatItem.addEventListener('click', () => {
            currentActiveChatId = session.session_id;
            setActiveChat(session.session_id);
            loadChatHistory(session.session_id);
            chat_id = session.session_id;
        });

        chatList.appendChild(chatItem);
    });
}

async function createNewChat() {
    if (!jwtToken) {
        showError('Требуется авторизация');
        return;
    }

    // Создаем временный объект чата
    const tempId = 'temp-' + Date.now(); // Генерируем уникальный временный ID
    const newChat = {
        session_id: tempId,  // Используем session_id вместо id
        first_message: 'Новый чат',  // Используем first_message вместо title
        isTemp: true
    };

    // Оптимистичное обновление UI
    if (!chats.sessions) {
        chats.sessions = []; // Инициализируем sessions, если его нет
    }
    chats.sessions.unshift(newChat); // Добавляем в начало массива sessions

    updateChatListUI();
    currentActiveChatId = tempId;
    setActiveChat(tempId);
    chat_id = '';

    // Очищаем историю чата и показываем приветствие
    document.getElementById('chatHistory').innerHTML = '';
    showWelcomeMessage();
    showLoadingState(false);
}

function setActiveChat(sessionId) {
    // Убираем класс active у всех элементов
    document.querySelectorAll('.chat-item').forEach(item => {
        item.classList.remove('active');
    });

    // Добавляем класс active к выбранному чату
    const selectedChat = document.querySelector(`.chat-item[data-session-id="${sessionId}"]`);
    if (selectedChat) {
        selectedChat.classList.add('active');
    }
}

// Удаление чата
async function deleteChat(sessionId) {
    try {
        const response = await fetch(`/langchain_api/chat-history/${sessionId}/`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${jwtToken}`
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Ошибка удаления');
        }

        // Обновляем UI
        chats.sessions = chats.sessions.filter(c => c.session_id !== sessionId);
        updateChatListUI();

    } catch (error) {
        console.error('Delete error:', error);
        showError(error.message);
    }
}

// Редактирование названия
async function editChatTitle(sessionId) {
    const newTitle = prompt('Введите новое название:');
    if (!newTitle) return;

    try {
        const response = await fetch(`/langchain_api/chat-history/${sessionId}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${jwtToken}`
            },
            body: JSON.stringify({ title: newTitle })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Ошибка обновления');
        }

        // Обновляем UI
        const chat = chats.sessions.find(c => c.session_id === sessionId);
        if (chat) chat.first_message = newTitle;
        updateChatListUI();

    } catch (error) {
        console.error('Edit error:', error);
        showError(error.message);
    }
}

// 5. Инициализация приложения
function initializeChatApp() {
    // Проверяем необходимые элементы DOM
    if (!document.getElementById('chatList') ||
        !document.getElementById('newChatBtn') ||
        !document.getElementById('chatHistory')) {
        console.error('Не найдены необходимые элементы DOM');
        return;
    }

    // Назначаем обработчики событий
    document.getElementById('newChatBtn').addEventListener('click', createNewChat);

    // Загружаем чаты
    loadChats();
}

// Запускаем приложение после загрузки DOM
document.addEventListener('DOMContentLoaded', initializeChatApp);

// Удаление чата
async function deleteChat(sessionId) {
    try {
        const response = await fetch(`/langchain_api/chat-history/${sessionId}/`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${jwtToken}`
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Ошибка удаления');
        }

        // Обновляем UI
        chats.sessions = chats.sessions.filter(c => c.session_id !== sessionId);
        updateChatListUI();

    } catch (error) {
        console.error('Delete error:', error);
        showError(error.message);
    }
}

// Редактирование названия
async function editChatTitle(sessionId) {
    const newTitle = prompt('Введите новое название:');
    if (!newTitle) return;

    try {
        const response = await fetch(`/langchain_api/chat-history/${sessionId}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${jwtToken}`
            },
            body: JSON.stringify({ title: newTitle })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Ошибка обновления');
        }

        // Обновляем UI
        const chat = chats.sessions.find(c => c.session_id === sessionId);
        if (chat) chat.first_message = newTitle;
        updateChatListUI();

    } catch (error) {
        console.error('Edit error:', error);
        showError(error.message);
    }
}

function updateChatListUI() {
    const chatList = document.getElementById('chatList');
    if (!chatList) return;

    chatList.innerHTML = '';

    if (!chats.sessions || chats.sessions.length === 0) {
        chatList.innerHTML = '<div class="no-chats">Нет активных чатов</div>';
        return;
    }

    chats.sessions.forEach(session => {
        const chatItem = document.createElement('div');
        chatItem.className = `chat-item ${session.session_id === currentActiveChatId ? 'active' : ''}`;

        // Название чата
        const titleSpan = document.createElement('span');
        titleSpan.className = 'chat-title';
        titleSpan.textContent = session.first_message || "Новый чат";
        chatItem.appendChild(titleSpan);

        // Контейнер для кнопок
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'chat-actions';

        // Кнопка редактирования
        const editBtn = document.createElement('button');
        editBtn.className = 'chat-btn btn-edit';
        editBtn.innerHTML = '<i>✏️</i>'; // или используйте иконку из FontAwesome
        editBtn.onclick = (e) => {
            e.stopPropagation();
            editChatTitle(session.session_id);
        };

        // Кнопка удаления
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'chat-btn btn-delete';
        deleteBtn.innerHTML = '<i>🗑️</i>'; // или используйте иконку из FontAwesome
        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            deleteChat(session.session_id);
        };

        actionsDiv.appendChild(editBtn);
        actionsDiv.appendChild(deleteBtn);
        chatItem.appendChild(actionsDiv);

        // Обработчик клика по элементу чата
        chatItem.addEventListener('click', () => {
            currentActiveChatId = session.session_id;
            setActiveChat(session.session_id);
            loadChatHistory(session.session_id);
        });

        chatList.appendChild(chatItem);
    });
}