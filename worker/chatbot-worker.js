/**
 * Worker Cloudflare pentru asistentul AziNews (azinews-chatbot.garconai93.workers.dev).
 *
 * Primește: POST {"message": "întrebarea", "context": "știrile relevante, una pe paragraf"}
 * Răspunde: {"response": "text"} sau {"error": "mesaj"} cu status 4xx/5xx
 *
 * Instalare: Cloudflare -> Workers & Pages -> azinews-chatbot -> Edit code -> lipește -> Deploy.
 * Secret necesar: Settings -> Variables and Secrets -> GROQ_API_KEY (tip Secret).
 *
 * De ce: modelele gpt-oss întorc „gândirea” separat (message.reasoning). O cerem ascunsă
 * (include_reasoning: false), cu efort mic, și nu o trimitem niciodată cititorului.
 */

const MODEL = 'openai/gpt-oss-20b';
const MAX_MESSAGE = 500;      // caractere
const MAX_CONTEXT = 14000;    // caractere

const SYSTEM = `Ești asistentul site-ului de știri AziNews.ro. Reguli:
- Răspunzi DOAR în limba română, prietenos și la obiect.
- Folosești DOAR știrile primite în mesaj. Nu inventa fapte, cifre sau citate.
- Dacă știrile nu conțin răspunsul, spune sincer asta într-o propoziție și sugerează ce poate căuta cititorul.
- Când enumeri mai multe știri, folosește o listă cu „- ” și pune sursa la final, în paranteză, de exemplu (Digi24).
- Maxim 150 de cuvinte. Fără introduceri de tipul „Iată răspunsul”. Nu descrie cum ai gândit.`;

// Ca worker-ul vechi: acceptă cereri de pe orice site (azinews.ro, site-ul de test, aplicația Android).
function cors() {
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    };
}

function json(body, status, origin) {
    return new Response(JSON.stringify(body), {
        status,
        headers: { 'Content-Type': 'application/json; charset=utf-8', ...cors(origin) },
    });
}

export default {
    async fetch(request, env) {
        const origin = request.headers.get('Origin') || '';
        if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors(origin) });
        if (request.method !== 'POST') return json({ error: 'Folosește POST.' }, 405, origin);
        if (!env.GROQ_API_KEY) return json({ error: 'Lipsește cheia GROQ_API_KEY în worker.' }, 500, origin);

        let body;
        try { body = await request.json(); } catch { return json({ error: 'Cerere invalidă.' }, 400, origin); }
        const message = String(body.message || '').trim().slice(0, MAX_MESSAGE);
        const context = String(body.context || '').trim().slice(0, MAX_CONTEXT);
        if (!message) return json({ error: 'Întrebarea e goală.' }, 400, origin);

        const groq = await fetch('https://api.groq.com/openai/v1/chat/completions', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${env.GROQ_API_KEY}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: MODEL,
                messages: [
                    { role: 'system', content: SYSTEM },
                    { role: 'user', content: `Știrile disponibile:\n\n${context || '(nu există știri)'}\n\nÎntrebarea cititorului: ${message}` },
                ],
                temperature: 0.3,
                max_tokens: 1200,
                reasoning_effort: 'low',
                include_reasoning: false,
            }),
        });

        if (!groq.ok) {
            const detail = await groq.text().catch(() => '');
            console.log('Groq', groq.status, detail.slice(0, 300));
            return json({ error: groq.status === 429 ? 'Prea multe întrebări acum. Încearcă peste un minut.' : 'Serviciul AI nu răspunde.' }, 502, origin);
        }
        const data = await groq.json();
        // DOAR răspunsul final; „gândirea” (message.reasoning) nu ajunge la cititor
        const answer = (data.choices?.[0]?.message?.content || '').trim();
        if (!answer) return json({ error: 'Nu am putut formula un răspuns.' }, 502, origin);
        return json({ response: answer }, 200, origin);
    },
};
