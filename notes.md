# Восстановление настроек (после wipe пода)
1. Под: A100 80GB Secure, image ghcr.io/open-webui/open-webui:ollama, порты 8080+11434,
   env: OLLAMA_HOST=0.0.0.0:11434 OLLAMA_FLASH_ATTENTION=true OLLAMA_KV_CACHE_TYPE=q4_0
        OLLAMA_CONTEXT_LENGTH=262144 ENABLE_SIGNUP=false
2. POST /api/pull orcarouter/Qwen3.8-27B-Uncensored:q8_0  и  qwen2.5:3b
3. POST /api/create name=qwen-unc (Modelfile в репо)
4. OWUI: signup первым юзером bondarev-ds@mail.ru (станет admin)
5. POST /api/v1/configs/tool_servers  <- tool-servers.json (info.id ОБЯЗАТЕЛЕН)
6. POST /api/v1/tasks/config/update <- tasks-config.json (все поля обязательны!)
7. POST /api/v1/models/model/create <- model-entry.json
   (function_calling=default: инструменты видны модели напрямую, вызывает сама)
8. POST /api/generate {"model":"qwen-unc:latest","keep_alive":-1} — прибить в VRAM
9. Web search: включить в Admin->Settings->Web Search
