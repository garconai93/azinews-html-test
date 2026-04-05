/**
 * AziNews AI Chatbot - Widget de chat cu Hugging Face Inference API
 * Design: tema întunecată cu accent albastru
 */

(function() {
    'use strict';

    // ============================================
    // CONFIGURAȚIE - Cloudflare Worker
    // ============================================
    const WORKER_URL = 'https://azinews-chatbot.garconai93.workers.dev';
    const SYSTEM_PROMPT = 'Ești un asistent AI pentru site-ul de știri românesc AziNews. Răspunzi prietenos, în limba română, despre știrile din context. Nu inventa informații. Răspunzi scurt și la obiect.';

    // ============================================
    // CSS STILURI
    // ============================================
    const styles = `
        /* Chat Button - Fixed bottom right */
        .azinews-chat-btn {
            position: fixed;
            bottom: 24px;
            right: 24px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #58a6ff 0%, #1f6feb 100%);
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(88, 166, 255, 0.4);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            transition: all 0.3s ease;
        }

        .azinews-chat-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 30px rgba(88, 166, 255, 0.6);
        }

        .azinews-chat-btn.active {
            transform: rotate(180deg);
        }

        /* Chat Panel */
        .azinews-chat-panel {
            position: fixed;
            bottom: 100px;
            right: 24px;
            width: 380px;
            height: 550px;
            max-height: calc(100vh - 150px);
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            z-index: 10000;
            display: none;
            flex-direction: column;
            overflow: hidden;
        }

        .azinews-chat-panel.open {
            display: flex;
            animation: slideUp 0.3s ease;
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Chat Header */
        .azinews-chat-header {
            background: linear-gradient(135deg, #58a6ff 0%, #1f6feb 100%);
            padding: 16px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .azinews-chat-header-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .azinews-chat-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: rgba(255,255,255,0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }

        .azinews-chat-header-text h3 {
            color: #fff;
            margin: 0;
            font-size: 16px;
            font-weight: 600;
        }

        .azinews-chat-header-text span {
            color: rgba(255,255,255,0.8);
            font-size: 12px;
        }

        .azinews-chat-close {
            background: none;
            border: none;
            color: #fff;
            cursor: pointer;
            font-size: 24px;
            padding: 4px;
            line-height: 1;
            opacity: 0.8;
            transition: opacity 0.2s;
        }

        .azinews-chat-close:hover {
            opacity: 1;
        }

        /* Chat Messages */
        .azinews-chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .azinews-chat-messages::-webkit-scrollbar {
            width: 6px;
        }

        .azinews-chat-messages::-webkit-scrollbar-track {
            background: transparent;
        }

        .azinews-chat-messages::-webkit-scrollbar-thumb {
            background: #30363d;
            border-radius: 3px;
        }

        /* Message Bubbles */
        .azinews-message {
            display: flex;
            gap: 10px;
            max-width: 85%;
        }

        .azinews-message.user {
            align-self: flex-end;
            flex-direction: row-reverse;
        }

        .azinews-message.bot {
            align-self: flex-start;
        }

        .azinews-message-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: #21262d;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            flex-shrink: 0;
        }

        .azinews-message.user .azinews-message-avatar {
            background: #58a6ff;
        }

        .azinews-message-content {
            background: #21262d;
            padding: 12px 16px;
            border-radius: 16px;
            border-top-left-radius: 4px;
            color: #f0f6fc;
            font-size: 14px;
            line-height: 1.5;
        }

        .azinews-message.user .azinews-message-content {
            background: #58a6ff;
            border-top-left-radius: 16px;
            border-top-right-radius: 4px;
        }

        /* Typing Indicator */
        .azinews-typing {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 0;
        }

        .azinews-typing-dots {
            display: flex;
            gap: 4px;
        }

        .azinews-typing-dots span {
            width: 8px;
            height: 8px;
            background: #8b949e;
            border-radius: 50%;
            animation: typingBounce 1.4s infinite ease-in-out;
        }

        .azinews-typing-dots span:nth-child(1) { animation-delay: 0s; }
        .azinews-typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .azinews-typing-dots span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typingBounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-6px); }
        }

        /* Chat Input */
        .azinews-chat-input-area {
            padding: 16px;
            background: #0d1117;
            border-top: 1px solid #30363d;
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }

        .azinews-chat-input {
            flex: 1;
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 12px 16px;
            color: #f0f6fc;
            font-size: 14px;
            resize: none;
            max-height: 120px;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            outline: none;
            transition: border-color 0.2s;
        }

        .azinews-chat-input:focus {
            border-color: #58a6ff;
        }

        .azinews-chat-input::placeholder {
            color: #8b949e;
        }

        .azinews-chat-send {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: #58a6ff;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            flex-shrink: 0;
        }

        .azinews-chat-send:hover {
            background: #4393e6;
            transform: scale(1.05);
        }

        .azinews-chat-send:disabled {
            background: #30363d;
            cursor: not-allowed;
            transform: none;
        }

        .azinews-chat-send svg {
            width: 20px;
            height: 20px;
            fill: #fff;
        }

        /* Welcome Message */
        .azinews-welcome {
            text-align: center;
            padding: 40px 20px;
            color: #8b949e;
        }

        .azinews-welcome-icon {
            font-size: 48px;
            margin-bottom: 16px;
        }

        .azinews-welcome h4 {
            color: #f0f6fc;
            margin: 0 0 8px 0;
            font-size: 18px;
        }

        .azinews-welcome p {
            margin: 0;
            font-size: 14px;
            line-height: 1.5;
        }

        .azinews-welcome-suggestions {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: center;
            margin-top: 20px;
        }

        .azinews-welcome-suggestion {
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 20px;
            padding: 8px 16px;
            font-size: 13px;
            color: #58a6ff;
            cursor: pointer;
            transition: all 0.2s;
        }

        .azinews-welcome-suggestion:hover {
            background: #30363d;
            border-color: #58a6ff;
        }

        /* Error Toast */
        .azinews-error-toast {
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            background: #f85149;
            color: #fff;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            z-index: 10001;
            animation: fadeInUp 0.3s ease;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateX(-50%) translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
        }

        /* Responsive */
        @media (max-width: 480px) {
            .azinews-chat-panel {
                width: calc(100vw - 32px);
                right: 16px;
                bottom: 90px;
                height: calc(100vh - 130px);
            }

            .azinews-chat-btn {
                bottom: 20px;
                right: 20px;
                width: 56px;
                height: 56px;
                font-size: 24px;
            }
        }
    `;

    // ============================================
    // HTML TEMPLATE
    // ============================================
    const chatHTML = `
        <style>${styles}</style>
        
        <!-- Chat Button -->
        <button class="azinews-chat-btn" id="azinewsChatBtn" title="Chat AI 💬">
            💬
        </button>
        
        <!-- Chat Panel -->
        <div class="azinews-chat-panel" id="azinewsChatPanel">
            <div class="azinews-chat-header">
                <div class="azinews-chat-header-info">
                    <div class="azinews-chat-avatar">🤖</div>
                    <div class="azinews-chat-header-text">
                        <h3>AziNews AI</h3>
                        <span>Asistent virtual</span>
                    </div>
                </div>
                <button class="azinews-chat-close" id="azinewsChatClose">×</button>
            </div>
            
            <div class="azinews-chat-messages" id="azinewsMessages">
                <div class="azinews-welcome">
                    <div class="azinews-welcome-icon">🔍</div>
                    <h4>Bună! Sunt AziNews AI</h4>
                    <p>Îți pot răspunde despre știrile de azi, rezuma conținut sau explica subiecte din newsfeed.</p>
                    <div class="azinews-welcome-suggestions">
                        <div class="azinews-welcome-suggestion" data-msg="Care sunt cele mai importante știri azi?">📰 Știri de azi</div>
                        <div class="azinews-welcome-suggestion" data-msg="Rezumă știrile despre Rusia și Ucraina">🌍 Rezumat Rusia-Ucraina</div>
                        <div class="azinews-welcome-suggestion" data-msg="Ce a mai fost în știri despre sport?">⚽ Știri sport</div>
                    </div>
                </div>
            </div>
            
            <div class="azinews-chat-input-area">
                <textarea 
                    class="azinews-chat-input" 
                    id="azinewsChatInput" 
                    placeholder="Scrie o întrebare..."
                    rows="1"
                ></textarea>
                <button class="azinews-chat-send" id="azinewsChatSend" title="Trimite">
                    <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
                </button>
            </div>
        </div>
    `;

    // ============================================
    // NEWS CONTEXT (va fi încărcat din all_news.json)
    // ============================================
    let newsContext = '';

    // ============================================
    // CLASA PRINCIPALĂ
    // ============================================
    class AziNewsChatbot {
        constructor() {
            this.panel = null;
            this.messagesEl = null;
            this.inputEl = null;
            this.sendBtn = null;
            this.isOpen = false;
            this.isLoading = false;
            this.conversationHistory = [];
            this.init();
        }

        async init() {
            // Inject HTML
            document.body.insertAdjacentHTML('beforeend', chatHTML);
            
            // Get elements
            this.panel = document.getElementById('azinewsChatPanel');
            this.messagesEl = document.getElementById('azinewsMessages');
            this.inputEl = document.getElementById('azinewsChatInput');
            this.sendBtn = document.getElementById('azinewsChatSend');
            
            // Load news context
            await this.loadNewsContext();
            
            // Setup event listeners
            this.setupEvents();
            
            // Auto-resize textarea
            this.inputEl.addEventListener('input', () => this.autoResize());
        }

        async loadNewsContext() {
            try {
                const response = await fetch('all_news.json');
                const news = await response.json();
                
                // Build context string
                newsContext = news.map(n => 
                    `[${n.source}] ${n.date} ${n.time}\nTitlu: ${n.title}\nConținut: ${n.content}`
                ).join('\n\n');
                
                console.log('✅ Context știri încărcat:', news.length, 'știri');
            } catch (error) {
                console.error('❌ Eroare la încărcarea știrilor:', error);
                newsContext = 'Nu am putut încărca știrile. Încearcă mai târziu.';
            }
        }

        setupEvents() {
            // Toggle chat
            document.getElementById('azinewsChatBtn').addEventListener('click', () => this.toggle());
            document.getElementById('azinewsChatClose').addEventListener('click', () => this.close());
            
            // Send message
            this.sendBtn.addEventListener('click', () => this.sendMessage());
            this.inputEl.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            // Welcome suggestions
            document.querySelectorAll('.azinews-welcome-suggestion').forEach(btn => {
                btn.addEventListener('click', () => {
                    const msg = btn.dataset.msg;
                    this.inputEl.value = msg;
                    this.sendMessage();
                });
            });
        }

        toggle() {
            this.isOpen = !this.isOpen;
            const btn = document.getElementById('azinewsChatBtn');
            
            if (this.isOpen) {
                this.panel.classList.add('open');
                btn.classList.add('active');
                this.inputEl.focus();
            } else {
                this.panel.classList.remove('open');
                btn.classList.remove('active');
            }
        }

        close() {
            this.isOpen = false;
            this.panel.classList.remove('open');
            document.getElementById('azinewsChatBtn').classList.remove('active');
        }

        autoResize() {
            this.inputEl.style.height = 'auto';
            this.inputEl.style.height = Math.min(this.inputEl.scrollHeight, 120) + 'px';
        }

        async sendMessage() {
            const message = this.inputEl.value.trim();
            if (!message || this.isLoading) return;
            
            // Clear input
            this.inputEl.value = '';
            this.autoResize();
            
            // Remove welcome if exists
            const welcome = this.messagesEl.querySelector('.azinews-welcome');
            if (welcome) welcome.remove();
            
            // Add user message
            this.addMessage(message, 'user');
            
            // Show typing indicator
            this.showTyping();
            this.isLoading = true;
            this.sendBtn.disabled = true;
            
            try {
                const response = await this.getAIResponse(message);
                this.hideTyping();
                this.addMessage(response, 'bot');
            } catch (error) {
                this.hideTyping();
                this.showError('Eroare: ' + error.message);
                this.addMessage('Scuze, am întâmpinat o problemă. Te rog încearcă din nou.', 'bot');
            } finally {
                this.isLoading = false;
                this.sendBtn.disabled = false;
            }
        }

        async getAIResponse(userMessage) {
            // Fetch news from all_news.json
            let newsContext = 'Nu am informații despre știri momentan.';
            try {
                const response = await fetch('all_news.json');
                if (response.ok) {
                    const news = await response.json();
                    if (news && news.length > 0) {
                        newsContext = news.slice(0, 20).map(n => {
                            const title = n.title || '';
                            const source = n.source || '';
                            const content = (n.content || '').substring(0, 300);
                            return `${source}: ${title}${content ? ' - ' + content : ''}`;
                        }).join('\n\n');
                    }
                }
            } catch (e) {
                console.log('Could not load news:', e);
            }

            // Build prompt with context
            const prompt = `${SYSTEM_PROMPT}\n\nIată știrile disponibile:\n${newsContext}\n\nÎntrebare: ${userMessage}`;

            const response = await fetch(WORKER_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: userMessage,
                    context: newsContext
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `Eroare: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.response) {
                return data.response;
            }
            
            throw new Error('Răspuns invalid de la server');
        }

        addMessage(content, type) {
            const messageEl = document.createElement('div');
            messageEl.className = `azinews-message ${type}`;
            
            const avatar = type === 'user' ? '👤' : '🤖';
            
            messageEl.innerHTML = `
                <div class="azinews-message-avatar">${avatar}</div>
                <div class="azinews-message-content">${this.formatMessage(content)}</div>
            `;
            
            this.messagesEl.appendChild(messageEl);
            this.scrollToBottom();
        }

        formatMessage(text) {
            // Basic formatting
            return text
                .replace(/\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code style="background:#21262d;padding:2px 6px;border-radius:4px;">$1</code>');
        }

        showTyping() {
            const typingEl = document.createElement('div');
            typingEl.className = 'azinews-message bot';
            typingEl.id = 'azinewsTyping';
            typingEl.innerHTML = `
                <div class="azinews-message-avatar">🤖</div>
                <div class="azinews-message-content">
                    <div class="azinews-typing">
                        <div class="azinews-typing-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                </div>
            `;
            this.messagesEl.appendChild(typingEl);
            this.scrollToBottom();
        }

        hideTyping() {
            const typingEl = document.getElementById('azinewsTyping');
            if (typingEl) typingEl.remove();
        }

        showError(message) {
            // Remove existing toast
            const existing = document.querySelector('.azinews-error-toast');
            if (existing) existing.remove();
            
            const toast = document.createElement('div');
            toast.className = 'azinews-error-toast';
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => toast.remove(), 5000);
        }

        scrollToBottom() {
            this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
        }
    }

    // ============================================
    // INITIALIZARE
    // ============================================
    // Start chatbot when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => new AziNewsChatbot());
    } else {
        new AziNewsChatbot();
    }

})();
