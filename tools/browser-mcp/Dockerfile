FROM mcr.microsoft.com/playwright:v1.55.0-noble
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn
COPY app.py .
ENV BROWSER_API_KEY=""
EXPOSE 8932
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8932"]
