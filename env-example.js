/**
 * ENV EXAMPLE - Template pentru configurare
 * 
 * COPY THIS FILE TO env.js AND ADD YOUR HF_TOKEN
 * 
 * IMPORTANT: env.js TREBUIE sa fie in .gitignore!
 * 
 * HF Token se obtine de la: https://huggingface.co/settings/tokens
 */

// Cum să configurezi:
/*
1. Crează un cont pe Hugging Face (huggingface.co)
2. Generază un token de tip "Read" de la: https://huggingface.co/settings/tokens
3. Copiază acest fișier ca env.js
4. Setează token-ul:
*/

window.AZINEWS_CONFIG = {
    HF_TOKEN: 'hf_TA_TOKEN_TAU_AICI',
    HF_API_URL: 'https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2',
    SYSTEM_PROMPT: 'Ești un asistent AI pentru site-ul de știri românesc AziNews. Răspunzi prietenos, în limba română, despre știrile din context.'
};
