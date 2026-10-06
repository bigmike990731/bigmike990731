import asyncio, base64, os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright

API_KEY = os.environ.get("BROWSER_API_KEY", "")
app = FastAPI(title="Real Web Browser", description="Interactive headless-Chromium browser the model can drive: open pages, click, type, scroll, read text, screenshot.")

_pw = None
_browser = None
_ctx = None
_page = None
_lock = asyncio.Lock()
MAXTEXT = 12000

async def get_page():
    global _pw, _browser, _ctx, _page
    if _page is None:
        _pw = await async_playwright().start()
        _browser = await _pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        _ctx = await _browser.new_context(
            viewport={"width": 1366, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="ru-RU")
        _page = await _ctx.new_page()
    return _page

@app.middleware("http")
async def auth(req: Request, call_next):
    if API_KEY and req.headers.get("authorization") != f"Bearer {API_KEY}":
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return await call_next(req)

class Url(BaseModel):
    url: str = Field(description="Absolute URL to open")

class Sel(BaseModel):
    selector: str = Field(description='CSS selector or visible text of the element, e.g. "a.login", "#q", "Войти"')

class TypeSel(BaseModel):
    selector: str = Field(description="CSS selector or placeholder/label text of the input")
    text: str = Field(description="Text to type")
    press_enter: bool = Field(default=False, description="Press Enter after typing")

class Scroll(BaseModel):
    direction: str = Field(default="down", description="up or down")
    pixels: int = Field(default=800)

class Js(BaseModel):
    script: str = Field(description="JavaScript to evaluate on the page")

async def page_text(page):
    try:
        txt = await page.inner_text("body", timeout=8000)
    except Exception:
        txt = ""
    return (await page.title(), page.url, txt[:MAXTEXT])

@app.post("/navigate", operation_id="browser_navigate", summary="Open a URL in the real browser; returns page title, final URL and visible text.")
async def navigate(b: Url):
    async with _lock:
        page = await get_page()
        try:
            await page.goto(b.url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1500)
        except Exception as e:
            return {"error": f"navigate failed: {e}"}
        t, u, txt = await page_text(page)
        return {"title": t, "url": u, "text": txt}

@app.post("/read", operation_id="browser_read", summary="Read the current page: title, URL, visible text.")
async def read():
    async with _lock:
        page = await get_page()
        t, u, txt = await page_text(page)
        return {"title": t, "url": u, "text": txt}

@app.post("/click", operation_id="browser_click", summary="Click an element by CSS selector or its visible text.")
async def click(b: Sel):
    async with _lock:
        page = await get_page()
        try:
            try:
                await page.click(f"text={b.selector}", timeout=4000)
            except Exception:
                await page.click(b.selector, timeout=8000)
            await page.wait_for_timeout(1200)
        except Exception as e:
            return {"error": f"click failed: {e}"}
        t, u, txt = await page_text(page)
        return {"clicked": b.selector, "title": t, "url": u, "text": txt[:4000]}

@app.post("/type", operation_id="browser_type", summary="Type text into an input (by selector or placeholder), optionally pressing Enter.")
async def typetext(b: TypeSel):
    async with _lock:
        page = await get_page()
        try:
            try:
                await page.fill(f"text={b.selector}", b.text, timeout=4000)
            except Exception:
                try:
                    await page.get_by_placeholder(b.selector).fill(b.text, timeout=4000)
                except Exception:
                    await page.fill(b.selector, b.text, timeout=8000)
            if b.press_enter:
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(1500)
        except Exception as e:
            return {"error": f"type failed: {e}"}
        t, u, txt = await page_text(page)
        return {"typed": b.selector, "title": t, "url": u, "text": txt[:4000]}

@app.post("/scroll", operation_id="browser_scroll", summary="Scroll the page up or down.")
async def scroll(b: Scroll):
    async with _lock:
        page = await get_page()
        d = b.pixels if b.direction == "down" else -b.pixels
        await page.mouse.wheel(0, d)
        await page.wait_for_timeout(800)
        t, u, txt = await page_text(page)
        return {"title": t, "url": u, "text": txt[:4000]}

@app.post("/elements", operation_id="browser_elements", summary="List interactive elements (links, buttons, inputs) with selectors the model can click or type into.")
async def elements():
    async with _lock:
        page = await get_page()
        els = await page.evaluate("""() => {
          const out=[]; const sel=e=>{const s=[];if(e.id)s.push('#'+e.id);if(e.name)s.push('[name="'+e.name+'"]');const ph=e.getAttribute('placeholder');if(ph)s.push('ph:'+ph);const t=(e.innerText||e.value||'').trim().slice(0,60);if(t)s.push('text:'+t);const cls=(e.className||'').toString().trim().split(/\\s+/).filter(Boolean).slice(0,2).join('.');s.push(e.tagName.toLowerCase()+(cls?'.'+cls:''));return s.join(' | ')};
          document.querySelectorAll('a,button,input,select,textarea,[role=button]').forEach((e,i)=>{if(i<80){const r=e.getBoundingClientRect();if(r.width>0&&r.height>0)out.push(sel(e))}});
          return out}""")
        return {"url": page.url, "elements": els}

@app.post("/screenshot", operation_id="browser_screenshot", summary="Take a PNG screenshot of the current page (base64).")
async def screenshot():
    async with _lock:
        page = await get_page()
        png = await page.screenshot(full_page=False)
        return {"url": page.url, "png_base64": base64.b64encode(png).decode()[:200000]}

@app.post("/eval", operation_id="browser_eval", summary="Run arbitrary JavaScript on the page and return the result.")
async def evaljs(b: Js):
    async with _lock:
        page = await get_page()
        try:
            r = await page.evaluate(b.script)
            return {"result": r}
        except Exception as e:
            return {"error": f"eval failed: {e}"}

@app.post("/back", operation_id="browser_back", summary="Go back to the previous page.")
async def back():
    async with _lock:
        page = await get_page()
        try:
            await page.go_back(timeout=15000)
        except Exception as e:
            return {"error": str(e)}
        t, u, txt = await page_text(page)
        return {"title": t, "url": u, "text": txt[:4000]}

@app.get("/healthz")
async def health():
    return {"ok": True}
