# Поднятие платформы Qwen-чат с нуля

## 1. Создать под на RunPod (Secure Cloud, A100 80GB)
GraphQL https://api.runpod.io/graphql?api_key=KEY

- GPU: NVIDIA A100 80GB PCIe, secure cloud
- Image: runpod/open-webui-ollama:latest (официальный образ OWUI+Ollama)
- Порты: 8080 (OWUI), 11434 (Ollama)
- Env: OLLAMA_HOST=0.0.0.0:11434, OLLAMA_FLASH_ATTENTION=true,
  OLLAMA_KV_CACHE_TYPE=q4_0, OLLAMA_CONTEXT_LENGTH=262144, ENABLE_SIGNUP=false

## 2. Залить модель
POST https://POD-11434.proxy.runpod.net/api/pull  {"name":"orcarouter/Qwen3.8-27B-Uncensored:q8_0"}
POST /api/pull {"name":"qwen2.5:3b"}   (task-модель для выбора инструментов)
POST /api/create {"name":"qwen-unc","modelfile":"<содержимое Modelfile>"}
POST /api/generate {"model":"qwen-unc:latest","keep_alive":-1}  (прибить в VRAM)

## 3. Восстановить платформу
webui.db — полная база Open WebUI (аккаунт admin bondarev-ds@mail.ru,
настройки, модель «Квен Без Цензуры» с legacy FC + toolIds, переписки).
Положить в контейнер: /app/backend/data/webui.db, перезапустить контейнер.
(либо создать аккаунт заново и вставить настройки вручную — см. settings.md)

## 4. Инструменты на VPS 194.67.74.250
tools/browser-mcp  — docker compose up -d (порт 8932)
tools/terminal-mcp — systemd unit terminal-mcp.service (порт 8933)
Bearer-ключ для обоих: в .env/compose на VPS.
В OWUI: Settings → Admin → External Connections → Tool Servers —
добавить оба URL с info.id (real-browser / real-terminal).
