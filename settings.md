# Настройки Open WebUI (если webui.db не поднимается)
- Модель «Квен Без Цензуры» id=qwen-unc:latest
- params.function_calling = "legacy" (исполнение инструментов через API тоже)
- meta.toolIds = ["server:real-browser","server:real-terminal"]
- TASK_MODEL = qwen2.5:3b (Admin → Settings → Tasks)
- Web search: включён
- ВАЖНО: у каждого tool server connection обязан быть info.id —
  без него id = индекс массива и toolIds у модели не цепляются.
