// script.js

document.addEventListener('DOMContentLoaded', function () {
    const loginDialog = document.getElementById('login-dialog');
    const loginForm = document.getElementById('login-form');
    const registerButton = document.getElementById('register-button');
    const logoutButton = document.getElementById('logout-button');
    const newChatButton = document.getElementById('new-chat-button');
    const chatListUl = document.getElementById('chat-list-ul');
    const messagesDiv = document.getElementById('messages');
    const inputMessage = document.getElementById('input-message');
    const sendButton = document.getElementById('send-button');
    const noChatDiv = document.getElementById('no-chat');
  
    let token = localStorage.getItem('token');
    let currentChatId = null;
  
    // Show or hide the login modal
    function toggleLoginDialog(show) {
      loginDialog.style.display = show ? 'block' : 'none';
    }
  
    // Check login status
    function checkLogin() {
      if (!token) {
        toggleLoginDialog(true);
        noChatDiv.style.display = 'none';
        document.querySelector('.chat-window').style.display = 'none';
      } else {
        toggleLoginDialog(false);
        document.querySelector('.chat-window').style.display = 'flex';
        noChatDiv.style.display = 'flex';
        fetchChats();
      }
    }
  
    // Login
    loginForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const username = loginForm.username.value;
      const password = loginForm.password.value;
      login(username, password);
    });
  
    function login(username, password) {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
  
      fetch('/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData.toString()
      })
        .then(res => res.json())
        .then(data => {
          if (data.access_token) {
            token = data.access_token;
            localStorage.setItem('token', token);
            toggleLoginDialog(false);
            document.querySelector('.chat-window').style.display = 'flex';
            noChatDiv.style.display = 'flex';
            fetchChats();
          } else {
            alert('Login failed');
          }
        })
        .catch(() => {
          alert('Login failed');
        });
    }
  
    // Register
    registerButton.addEventListener('click', function () {
      const username = loginForm.username.value;
      const password = loginForm.password.value;
      register(username, password);
    });
  
    function register(username, password) {
      fetch('/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username,
          password
        })
      })
        .then(res => res.json())
        .then(data => {
          if (data.message === 'Registration successful') {
            login(username, password);
          } else {
            alert('Registration failed');
          }
        })
        .catch(() => {
          alert('Registration failed');
        });
    }
  
    // Logout
    logoutButton.addEventListener('click', function () {
      token = null;
      localStorage.removeItem('token');
      toggleLoginDialog(true);
      document.querySelector('.chat-window').style.display = 'none';
      noChatDiv.style.display = 'none';
      chatListUl.innerHTML = '';
      messagesDiv.innerHTML = '';
    });
  
    // Fetch chat list
    function fetchChats() {
      fetch('/chats', {
        headers: {
          'Authorization': 'Bearer ' + token
        }
      })
        .then(res => res.json())
        .then(data => {
          chatListUl.innerHTML = '';
          data.forEach(chat => {
            const li = document.createElement('li');
            li.textContent = 'Chat ' + chat.id;
            li.dataset.chatId = chat.id;
            li.addEventListener('click', function () {
              selectChat(chat.id);
            });
            chatListUl.appendChild(li);
          });
        })
        .catch(() => {
          alert('Failed to fetch chats');
        });
    }
  
    // Create new chat
    newChatButton.addEventListener('click', function () {
      fetch('/chats', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + token
        }
      })
        .then(res => res.json())
        .then(() => {
          fetchChats();
        })
        .catch(() => {
          alert('Failed to create chat');
        });
    });
  
    // Select chat
    function selectChat(chatId) {
      currentChatId = chatId;
      fetchMessages();
      noChatDiv.style.display = 'none';
      document.querySelector('.chat-window').style.display = 'flex';
    }
  
    // Fetch messages
    function fetchMessages() {
      fetch(`/chats/${currentChatId}/messages`, {
        headers: {
          'Authorization': 'Bearer ' + token
        }
      })
        .then(res => res.json())
        .then(data => {
          messagesDiv.innerHTML = '';
          data.forEach(message => {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message message-' + message.sender;
            const contentSpan = document.createElement('span');
            contentSpan.className = 'message-content';
            if (message.sender === 'ai') {
              // 使用 marked 解析并渲染 Markdown，并通过 DOMPurify 清理
              contentSpan.innerHTML = DOMPurify.sanitize(marked.parse(message.content));
            } else {
              // 用户消息作为纯文本插入
              contentSpan.textContent = message.content;
            }
            messageDiv.appendChild(contentSpan);
            messagesDiv.appendChild(messageDiv);
          });
          messagesDiv.scrollTop = messagesDiv.scrollHeight;
        })
        .catch(() => {
          alert('Failed to fetch messages');
        });
    }
  
  
    // Send message
    sendButton.addEventListener('click', function () {
      const content = inputMessage.value.trim();
      if (content === '' || !currentChatId) return;
      fetch(`/chats/${currentChatId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + token
        },
        body: JSON.stringify({ content })
      })
        .then(res => res.json())
        .then(data => {
          // 显示用户消息
          const userMessageDiv = document.createElement('div');
          userMessageDiv.className = 'message message-user';
          const userContentSpan = document.createElement('span');
          userContentSpan.className = 'message-content';
          userContentSpan.textContent = content;
          userMessageDiv.appendChild(userContentSpan);
          messagesDiv.appendChild(userMessageDiv);
  
          // 显示 AI 回复
          const aiMessageDiv = document.createElement('div');
          aiMessageDiv.className = 'message message-ai';
          const aiContentSpan = document.createElement('span');
          aiContentSpan.className = 'message-content';
          // 使用 marked 解析并渲染 Markdown，并通过 DOMPurify 清理
          aiContentSpan.innerHTML = DOMPurify.sanitize(marked.parse(data.reply));
          aiMessageDiv.appendChild(aiContentSpan);
          messagesDiv.appendChild(aiMessageDiv);
  
          messagesDiv.scrollTop = messagesDiv.scrollHeight;
          inputMessage.value = '';
        })
        .catch(() => {
          alert('Failed to send message');
        });
    });
  
    // Initialize
    checkLogin();
  });