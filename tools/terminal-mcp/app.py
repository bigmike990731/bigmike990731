import os
import subprocess
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

API_KEY = os.environ.get("TERMINAL_API_KEY", "")
app = FastAPI(
    title="Real Terminal",
    description="Execute shell commands on a Linux server and get stdout/stderr back. Use for files, packages, services, diagnostics.",
    version="0.1.0",
)

class ExecReq(BaseModel):
    command: str
    timeout: int = 60
    workdir: str = "/root"

def auth(req: Request):
    if API_KEY:
        h = req.headers.get("authorization", "")
        if h != f"Bearer {API_KEY}":
            raise HTTPException(401, "unauthorized")

@app.post("/exec", operation_id="exec_command")
def exec_command(body: ExecReq, request: Request):
    """Run a shell command. Returns stdout, stderr, exit code."""
    auth(request)
    try:
        p = subprocess.run(
            ["bash", "-lc", body.command],
            capture_output=True, text=True,
            timeout=min(body.timeout, 300),
            cwd=body.workdir if os.path.isdir(body.workdir) else "/root",
        )
        return {
            "exit_code": p.returncode,
            "stdout": p.stdout[-50000:],
            "stderr": p.stderr[-50000:],
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "stdout": "", "stderr": f"timeout after {body.timeout}s"}

@app.post("/read_file", operation_id="read_file")
def read_file(body: dict, request: Request):
    """Read a text file from the server. Args: path, optional offset/limit lines."""
    auth(request)
    path = body.get("path", "")
    try:
        with open(path, "r", errors="replace") as f:
            lines = f.readlines()
        off = int(body.get("offset", 0))
        lim = int(body.get("limit", 200))
        return {"content": "".join(lines[off:off + lim]), "total_lines": len(lines)}
    except Exception as e:
        return {"error": str(e)}

@app.post("/write_file", operation_id="write_file")
def write_file(body: dict, request: Request):
    """Write text to a file on the server. Args: path, content."""
    auth(request)
    path = body.get("path", "")
    try:
        with open(path, "w") as f:
            f.write(body.get("content", ""))
        return {"ok": True, "bytes": len(body.get("content", ""))}
    except Exception as e:
        return {"error": str(e)}

@app.get("/healthz", operation_id="healthz")
def healthz():
    return {"ok": True}
