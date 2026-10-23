/**
 * Asistentul AziNews: chat despre știrile de azi.
 * Trimite întrebarea și titlurile recente către worker-ul Cloudflare, care răspunde cu AI.
 *
 * Desktop: fereastră în colțul din dreapta jos.
 * Mobil (≤640px): panou care urcă de jos (cam 60% din ecran), cu fundal estompat;
 * câmpul de text are 16px, ca iPhone-ul să nu mărească pagina la atingere.
 * Culorile vin din variabilele site-ului (--ink, --surface...), cu rezerve pentru alte pagini.
 */
(function () {
    'use strict';

    const WORKER_URL = 'https://azinews-chatbot.garconai93.workers.dev';
    const CONTEXT_ITEMS = 25;

    const css = `
    /* buton: „soarele” galben din logo, cu steluța asistentului (ca în antetul chatului) */
    .azn-launch {
        position: fixed; right: 16px; bottom: calc(16px + env(safe-area-inset-bottom)); z-index: 9000;
        display: inline-flex; align-items: center; gap: 10px; height: 56px; padding: 6px 20px 6px 6px;
        border: 0; border-radius: 999px; cursor: pointer;
        background: var(--ink, #14213D); color: var(--paper, #fff);
        font: 650 15px/1 var(--display, system-ui, sans-serif); letter-spacing: -0.01em;
        box-shadow: 0 8px 28px rgba(8, 12, 24, .28), 0 1px 2px rgba(8, 12, 24, .2);
        transition: transform .15s ease, box-shadow .15s ease;
    }
    .azn-launch:hover { transform: translateY(-1px); box-shadow: 0 12px 32px rgba(8, 12, 24, .32), 0 1px 2px rgba(8, 12, 24, .2); }
    .azn-orb {
        width: 44px; height: 44px; flex: none; border-radius: 50%; display: grid; place-items: center;
        background: var(--azi, #FFCB3D); color: var(--azi-ink, #14213D);
        box-shadow: inset -5px -5px 0 rgba(0,0,0,.08);
    }
    .azn-orb svg { width: 22px; height: 22px; transition: transform .25s ease; }
    .azn-launch:hover .azn-orb svg { transform: rotate(18deg) scale(1.08); }
    .azn-launch:focus-visible { outline: 3px solid var(--link, #2448E0); outline-offset: 3px; }
    .azn-open .azn-launch { display: none; }
    body:has(.consent.show) .azn-launch { display: none; }

    .azn-backdrop { display: none; }
    .azn-panel {
        position: fixed; right: 16px; bottom: 16px; z-index: 9001;
        width: 380px; height: min(580px, calc(100dvh - 32px));
        display: none; flex-direction: column; overflow: hidden;
        background: var(--surface, #fff); color: var(--ink, #14213D);
        border: 1px solid var(--rule, #DADDD4); border-radius: 22px;
        box-shadow: 0 18px 60px rgba(0,0,0,.25);
        font-family: var(--display, system-ui, sans-serif);
    }
    .azn-open .azn-panel { display: flex; animation: azn-in .18s ease-out; }
    @keyframes azn-in { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: none; } }

    .azn-handle { display: none; }
    .azn-head { display: flex; align-items: center; gap: 12px; padding: 14px 12px 12px 16px; border-bottom: 1px solid var(--rule, #DADDD4); }
    .azn-avatar { width: 38px; height: 38px; border-radius: 50%; flex: none; display: grid; place-items: center; background: var(--azi, #FFCB3D); color: var(--azi-ink, #14213D); }
    .azn-avatar svg { width: 20px; height: 20px; }
    .azn-title { flex: 1; min-width: 0; }
    .azn-title b { display: block; font-size: 16px; font-weight: 700; letter-spacing: -0.01em; }
    .azn-title span { display: block; font-size: 13px; color: var(--ink-2, #4E5A70); }
    .azn-icon {
        width: 40px; height: 40px; flex: none; display: grid; place-items: center; cursor: pointer;
        border: 0; border-radius: 50%; background: transparent; color: var(--ink, #14213D);
    }
    .azn-icon:hover { background: var(--paper, #F2F3EF); }
    .azn-icon svg { width: 20px; height: 20px; }
    .azn-icon:focus-visible, .azn-chip:focus-visible, .azn-send:focus-visible { outline: 3px solid var(--link, #2448E0); outline-offset: 2px; }

    .azn-body { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 10px; overscroll-behavior: contain; }
    .azn-hello { margin: 4px 0 6px; }
    .azn-hello h3 { margin: 0 0 4px; font-size: 20px; line-height: 1.2; letter-spacing: -0.02em; }
    .azn-hello p { margin: 0; color: var(--ink-2, #4E5A70); font-size: 14px; line-height: 1.45; }
    .azn-chips { display: flex; flex-direction: column; gap: 8px; margin-top: 14px; }
    .azn-chip {
        text-align: left; cursor: pointer; padding: 11px 14px; border-radius: 14px;
        border: 1px solid var(--rule, #DADDD4); background: var(--paper, #F2F3EF); color: var(--ink, #14213D);
        font: 500 14px/1.35 var(--display, system-ui, sans-serif);
    }
    .azn-chip:hover { border-color: var(--ink-3, #636C7E); }

    .azn-msg { max-width: 88%; padding: 10px 14px; border-radius: 18px; font-size: 15px; line-height: 1.5; overflow-wrap: anywhere; }
    .azn-msg.user { align-self: flex-end; background: var(--ink, #14213D); color: var(--paper, #fff); border-bottom-right-radius: 6px; }
    .azn-msg.bot { align-self: flex-start; background: var(--paper, #F2F3EF); border-bottom-left-radius: 6px; }
    .azn-msg.bot p { margin: 0 0 8px; } .azn-msg.bot p:last-child { margin: 0; }
    .azn-msg.bot ul { margin: 4px 0 8px; padding-left: 18px; }
    .azn-msg.error { background: transparent; border: 1px dashed var(--rule, #DADDD4); color: var(--ink-2, #4E5A70); }
    .azn-msg.error button { margin-top: 8px; }
    .azn-typing { display: inline-flex; gap: 4px; padding: 4px 0; }
    .azn-typing i { width: 7px; height: 7px; border-radius: 50%; background: var(--ink-3, #636C7E); animation: azn-dot 1.2s infinite ease-in-out; }
    .azn-typing i:nth-child(2) { animation-delay: .15s; } .azn-typing i:nth-child(3) { animation-delay: .3s; }
    @keyframes azn-dot { 0%, 80%, 100% { opacity: .3; transform: translateY(0); } 40% { opacity: 1; transform: translateY(-3px); } }

    .azn-foot { border-top: 1px solid var(--rule, #DADDD4); padding: 10px 12px calc(8px + env(safe-area-inset-bottom)); }
    .azn-form { display: flex; align-items: flex-end; gap: 8px; }
    .azn-input {
        flex: 1; min-width: 0; resize: none; max-height: 120px; padding: 11px 16px; border-radius: 22px;
        border: 1px solid var(--rule, #DADDD4); background: var(--paper, #F2F3EF); color: var(--ink, #14213D);
        font: 16px/1.35 var(--display, system-ui, sans-serif); outline: none;
    }
    .azn-input:focus { border-color: var(--link, #2448E0); }
    .azn-input::placeholder { color: var(--ink-3, #636C7E); }
    .azn-send {
        width: 44px; height: 44px; flex: none; border: 0; border-radius: 50%; cursor: pointer;
        display: grid; place-items: center; background: var(--ink, #14213D); color: var(--paper, #fff);
    }
    .azn-send:disabled { opacity: .35; cursor: default; }
    .azn-send svg { width: 20px; height: 20px; }
    .azn-note { margin: 6px 4px 0; font-size: 12px; color: var(--ink-3, #636C7E); text-align: center; }

    .azn-btn {
        display: inline-flex; align-items: center; height: 36px; padding: 0 14px; border-radius: 999px; cursor: pointer;
        border: 1px solid var(--rule, #DADDD4); background: var(--surface, #fff); color: var(--ink, #14213D);
        font: 600 14px/1 var(--display, system-ui, sans-serif);
    }

    @media (max-width: 640px) {
        .azn-launch { padding: 0; width: 60px; height: 60px; justify-content: center; background: var(--azi, #FFCB3D); box-shadow: 0 0 0 3px var(--paper, #fff), 0 8px 24px rgba(8, 12, 24, .3); }
        .azn-launch .azn-orb { width: 60px; height: 60px; }
        .azn-launch .azn-orb svg { width: 26px; height: 26px; }
        .azn-launch .azn-label { display: none; }
        .azn-open .azn-backdrop { display: block; position: fixed; inset: 0; z-index: 9000; background: rgba(8, 12, 24, .45); }
        .azn-panel {
            left: 8px; right: 8px; bottom: 8px; width: auto;
            height: min(62dvh, 560px); border-radius: 22px;
        }
        .azn-open .azn-panel { animation: azn-up .22s ease-out; }
        @keyframes azn-up { from { transform: translateY(40px); opacity: .6; } to { transform: none; opacity: 1; } }
        .azn-handle { display: block; width: 40px; height: 4px; border-radius: 4px; background: var(--rule, #DADDD4); margin: 8px auto -4px; }
        .azn-chips { flex-direction: row; flex-wrap: wrap; }
        .azn-chip { padding: 9px 12px; }
    }
    @media (prefers-reduced-motion: reduce) {
        .azn-open .azn-panel, .azn-typing i { animation: none; }
    }`;

    const ICON = {
        chat: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.4-4.9A8 8 0 1 1 21 12z"/><path d="M8.5 11h.01M12 11h.01M15.5 11h.01" stroke-width="2.6"/></svg>',
        spark: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2.5l1.9 5.6 5.6 1.9-5.6 1.9L12 17.5l-1.9-5.6L4.5 10l5.6-1.9z"/><path d="M18.5 15l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z"/></svg>',
        close: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>',
        reset: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/></svg>',
        send: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg>'
    };

    const norm = s => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    const STOP = new Set('care sunt cele mele care este pentru despre dintre ultimele stiri stirile stire azi astazi acum ceva spune explica rezuma rezumat importante important noutati nou noua spunemi'.split(' '));
    const CAT_HINTS = {
        economie: ['econom', 'bani', 'pret', 'curs', 'euro', 'inflat', 'taxe', 'impozit', 'buget', 'salari', 'pensi', 'bursa', 'afaceri'],
        sport: ['sport', 'fotbal', 'meci', 'tenis', 'handbal', 'baschet', 'campionat', 'liga'],
        politica: ['politic', 'guvern', 'parlament', 'partid', 'alegeri', 'ministr', 'premier', 'presedint'],
        externe: ['extern', 'international', 'ucraina', 'rusia', 'sua', 'trump', 'europa', 'razboi', 'israel', 'iran', 'china'],
        sanatate: ['sanatat', 'spital', 'medic', 'boala', 'stiint', 'tehnolog', 'virus', 'vaccin'],
        lifestyle: ['vedet', 'showbiz', 'monden', 'film', 'muzic', 'horoscop', 'calator']
    };

    const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

    // text simplu -> HTML sigur: paragrafe, liste cu „-” sau „1.”, **bold**
    function formatAnswer(text) {
        const LIST = /^\s*([-•*]|\d+[.)])\s+/;
        const html = [];
        let list = null, para = [];
        const flushPara = () => { if (para.length) { html.push('<p>' + para.join('<br>') + '</p>'); para = []; } };
        const flushList = () => { if (list) { html.push('<ul>' + list.map(l => '<li>' + l + '</li>').join('') + '</ul>'); list = null; } };
        for (const raw of esc(text).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').split('\n')) {
            const line = raw.trim();
            if (!line) { flushPara(); flushList(); continue; }
            if (LIST.test(line)) { flushPara(); (list = list || []).push(line.replace(LIST, '')); }
            else { flushList(); para.push(line); }
        }
        flushPara(); flushList();
        return html.join('');
    }

    function suggestions() {
        const list = [];
        try {
            // „stories” vine din index.html (subiectele zilei), dacă există
            if (typeof stories !== 'undefined' && stories.length) {
                const t = stories[0].title;
                list.push({ label: 'Explică-mi subiectul principal al zilei', msg: `Explică-mi pe scurt subiectul: ${t}` });
            }
        } catch (e) {}
        list.push(
            { label: 'Care sunt cele mai importante știri de azi?', msg: 'Care sunt cele mai importante știri de azi? Dă-mi un rezumat scurt.' },
            { label: 'Ce e nou în economie?', msg: 'Ce știri economice importante au apărut azi?' },
            { label: 'Ce s-a întâmplat în sport?', msg: 'Ce știri de sport au apărut azi?' }
        );
        return list.slice(0, 4);
    }

    class AziNewsChat {
        constructor() {
            this.busy = false;
            this.lastQuestion = '';
            this.build();
        }

        build() {
            const style = document.createElement('style');
            style.textContent = css;
            document.head.appendChild(style);

            this.root = document.createElement('div');
            this.root.className = 'azn';
            this.root.innerHTML = `
                <button class="azn-launch" type="button" aria-haspopup="dialog" aria-controls="aznPanel" aria-expanded="false" aria-label="Întreabă asistentul AI"><span class="azn-orb" aria-hidden="true">${ICON.spark}</span><span class="azn-label" aria-hidden="true">Întreabă AI</span></button>
                <div class="azn-backdrop"></div>
                <section class="azn-panel" id="aznPanel" role="dialog" aria-label="Asistentul AziNews">
                    <div class="azn-handle" aria-hidden="true"></div>
                    <header class="azn-head">
                        <div class="azn-avatar">${ICON.spark}</div>
                        <div class="azn-title"><b>Asistentul AziNews</b><span>Răspunde din știrile de azi</span></div>
                        <button class="azn-icon" type="button" data-act="reset" title="Conversație nouă" aria-label="Conversație nouă">${ICON.reset}</button>
                        <button class="azn-icon" type="button" data-act="close" title="Închide" aria-label="Închide">${ICON.close}</button>
                    </header>
                    <div class="azn-body" aria-live="polite"></div>
                    <div class="azn-foot">
                        <form class="azn-form">
                            <label class="sr-only" for="aznInput">Întrebarea ta</label>
                            <textarea class="azn-input" id="aznInput" rows="1" placeholder="Întreabă ceva despre știri..." enterkeyhint="send"></textarea>
                            <button class="azn-send" type="submit" aria-label="Trimite" disabled>${ICON.send}</button>
                        </form>
                        <p class="azn-note">Poate greși. Verifică în articolul original.</p>
                    </div>
                </section>`;
            document.body.appendChild(this.root);

            this.launch = this.root.querySelector('.azn-launch');
            this.body = this.root.querySelector('.azn-body');
            this.input = this.root.querySelector('.azn-input');
            this.send = this.root.querySelector('.azn-send');

            this.launch.addEventListener('click', () => this.open());
            this.root.querySelector('.azn-backdrop').addEventListener('click', () => this.close());
            this.root.querySelector('[data-act=close]').addEventListener('click', () => this.close());
            this.root.querySelector('[data-act=reset]').addEventListener('click', () => this.welcome());
            this.root.querySelector('.azn-form').addEventListener('submit', e => { e.preventDefault(); this.ask(this.input.value); });
            this.input.addEventListener('input', () => this.resize());
            this.input.addEventListener('keydown', e => {
                if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); this.ask(this.input.value); }
            });
            this.body.addEventListener('click', e => {
                const chip = e.target.closest('[data-msg]');
                if (chip) this.ask(chip.dataset.msg);
                if (e.target.closest('[data-act=retry]')) this.ask(this.lastQuestion, true);
            });
            document.addEventListener('keydown', e => { if (e.key === 'Escape' && this.isOpen()) this.close(); });
            this.welcome();
        }

        isOpen() { return this.root.classList.contains('azn-open'); }
        isMobile() { return matchMedia('(max-width: 640px)').matches; }

        open() {
            this.root.classList.add('azn-open');
            this.launch.setAttribute('aria-expanded', 'true');
            if (this.isMobile()) document.documentElement.style.overflow = 'hidden';
            // pe mobil nu deschidem tastatura singuri: ar acoperi sugestiile
            if (!this.isMobile()) setTimeout(() => this.input.focus(), 50);
            if (!this.body.querySelector('.azn-msg')) this.welcome();
        }
        close() {
            this.root.classList.remove('azn-open');
            this.launch.setAttribute('aria-expanded', 'false');
            document.documentElement.style.overflow = '';
            this.launch.focus({ preventScroll: true });
        }

        welcome() {
            this.body.innerHTML = `
                <div class="azn-hello">
                    <h3>Salut! Ce vrei să afli?</h3>
                    <p>Te ajut să înțelegi știrile din ultimele ore: rezumate, explicații, ce s-a mai întâmplat pe un subiect.</p>
                    <div class="azn-chips">${suggestions().map(s => `<button type="button" class="azn-chip" data-msg="${esc(s.msg)}">${esc(s.label)}</button>`).join('')}</div>
                </div>`;
            this.input.value = '';
            this.resize();
        }

        resize() {
            this.input.style.height = 'auto';
            this.input.style.height = Math.min(this.input.scrollHeight, 120) + 'px';
            this.send.disabled = this.busy || !this.input.value.trim();
        }

        add(html, cls) {
            const el = document.createElement('div');
            el.className = 'azn-msg ' + cls;
            el.innerHTML = html;
            this.body.appendChild(el);
            this.body.scrollTop = this.body.scrollHeight;
            return el;
        }

        // Alegem știrile care se potrivesc cu întrebarea, nu doar ultimele apărute.
        async context(question) {
            let items = Array.isArray(window.news) && window.news.length ? window.news : [];
            if (!items.length) {
                try {
                    const r = await fetch('data/latest.json', { cache: 'no-cache' });
                    if (r.ok) items = (await r.json()).items || [];
                } catch (e) {}
            }
            if (!items.length) return 'Nu am informații despre știri momentan.';
            const q = norm(question);
            const words = new Set(q.split(/[^a-z0-9]+/).filter(w => w.length > 3 && !STOP.has(w)).map(w => w.slice(0, 6)));
            const cats = Object.keys(CAT_HINTS).filter(c => CAT_HINTS[c].some(h => q.includes(h)));
            const scored = items.slice(0, 300).map((n, i) => {
                const text = norm(n.title + ' ' + (n.content || ''));
                let score = 0;
                for (const w of words) if (text.includes(w)) score += 2;
                if (cats.includes(n.cat)) score += 3;
                return { n, score: score - i / 300 };   // la egalitate, cea mai nouă câștigă
            });
            const relevant = scored.filter(x => x.score > 0.5).sort((a, b) => b.score - a.score).slice(0, 18).map(x => x.n);
            const pool = relevant.length >= 6 ? relevant : [...relevant, ...items.slice(0, 18 - relevant.length)];
            const seen = new Set();
            return pool.filter(n => !seen.has(n.url) && seen.add(n.url)).map(n => {
                const when = (n.ts || n.fetched_at || '').slice(0, 16).replace('T', ' ');
                return `[${n.source}${when ? ', ' + when + ' UTC' : ''}] ${n.title}${n.content ? ' - ' + n.content.slice(0, 280) : ''}`;
            }).join('\n\n');
        }

        async ask(text, isRetry) {
            text = (text || '').trim();
            if (!text || this.busy) return;
            this.busy = true;
            this.lastQuestion = text;
            const hello = this.body.querySelector('.azn-hello');
            if (hello) hello.remove();
            const oldErr = this.body.querySelector('.azn-msg.error');
            if (oldErr) oldErr.remove();
            if (!isRetry) this.add(esc(text), 'user');
            this.input.value = '';
            this.resize();
            const typing = this.add('<span class="azn-typing" aria-label="Se scrie răspunsul"><i></i><i></i><i></i></span>', 'bot');
            try {
                const r = await fetch(WORKER_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text, context: await this.context(text) })
                });
                const data = await r.json().catch(() => ({}));
                if (!r.ok || !data.response) throw new Error(data.error || 'HTTP ' + r.status);
                // worker-ul vechi poate trimite „gândirea” modelului (în engleză) în loc de răspuns
                if (/^\s*(we need to|we have to|let's|let me|the user|okay,|ok,|so the user)/i.test(data.response)) throw new Error('raspuns-ciorna');
                typing.remove();
                this.add(formatAnswer(data.response), 'bot');
            } catch (e) {
                console.warn('Asistent AI:', e);
                typing.remove();
                this.add('Nu am putut răspunde acum. Încearcă din nou peste un minut.<br><button type="button" class="azn-btn" data-act="retry">Încearcă din nou</button>', 'bot error');
            } finally {
                this.busy = false;
                this.resize();
            }
        }
    }

    const start = () => new AziNewsChat();
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
    else start();
})();
