"""測試用的假 ASR Service。

Transcribe 的第二個接縫：以標準函式庫起一個真的 HTTP server，靠環境變數把 CLI
指過去。不 patch HTTP client、不注入 client 物件、不引 mock 框架——測試看到的
仍然只有「跑一次真 CLI、看檔案和 stdout 的 JSON」。

回應的形狀照 ASR Service 的 OpenAPI：StorageResponse、TaskSummary、TaskDetail。
"""

import json
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

CREATED_AT = "2026-08-05T09:00:00+00:00"


def parse_multipart(body, boundary):
    """把 multipart 的 body 拆成 {欄位名: (檔名, 內容)}。夠用就好，不求完整。"""
    fields = {}
    for part in body.split(b"--" + boundary):
        head, separator, payload = part.partition(b"\r\n\r\n")
        name = re.search(rb'name="([^"]*)"', head)
        if not separator or not name:
            continue
        filename = re.search(rb'filename="([^"]*)"', head)
        fields[name.group(1).decode("utf-8")] = (
            filename.group(1).decode("utf-8") if filename else None,
            payload[: -len(b"\r\n")],
        )
    return fields


class FakeAsr:
    """假服務的狀態。測試直接改 storage 與 tasks，不必透過 HTTP。"""

    def __init__(self):
        self.storage = {
            "free_bytes": 15 * 1024**3,
            "total_bytes": 30 * 1024**3,
            "used_bytes": 15 * 1024**3,
            "max_upload_mb": 4096,
        }
        self.tasks = {}
        self.uploads = []
        self.resumed = []

    @property
    def url(self):
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def create_task(self, filename, language, payload):
        task_id = f"task{len(self.tasks) + 1:04d}"
        self.uploads.append(
            {
                "task": task_id,
                "filename": filename,
                "language": language,
                "size": len(payload),
            }
        )
        self.tasks[task_id] = {
            "id": task_id,
            "original_filename": filename,
            "status": "pending",
            "language": language,
            "created_at": CREATED_AT,
            "updated_at": CREATED_AT,
            "duration_sec": None,
            "total_chunks": None,
            "completed_chunks": 0,
            "progress_pct": 0.0,
            "error_message": None,
            "chunks": [],
        }
        return self.tasks[task_id]

    def finish(self, task_id, chunks, duration_sec=None):
        """把任務標成完成並填上分段。chunks 是 (起, 訖, 文字[, 錯誤訊息])。"""
        task = self.tasks[task_id]
        task["chunks"] = [
            {
                "chunk_index": index,
                "start_sec": chunk[0],
                "end_sec": chunk[1],
                "status": "failed" if chunk[2] is None else "done",
                "text": chunk[2],
                "error_message": chunk[3] if len(chunk) > 3 else None,
            }
            for index, chunk in enumerate(chunks)
        ]
        task["status"] = "done"
        task["total_chunks"] = len(chunks)
        task["completed_chunks"] = len(chunks)
        task["progress_pct"] = 100.0
        task["duration_sec"] = duration_sec or (chunks[-1][1] if chunks else 0.0)
        return task

    def progress(self, task_id, completed, total, pct):
        self.tasks[task_id] |= {
            "status": "processing",
            "completed_chunks": completed,
            "total_chunks": total,
            "progress_pct": pct,
        }
        return self.tasks[task_id]

    def fail(self, task_id, message):
        self.tasks[task_id] |= {"status": "failed", "error_message": message}
        return self.tasks[task_id]

    # --- server 生命週期 -----------------------------------------------------

    def start(self):
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass  # pytest 的輸出不需要 access log

            def reply(self, status, payload):
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path == "/api/storage":
                    return self.reply(200, fake.storage)
                match = re.fullmatch(r"/api/tasks/([^/]+)", self.path)
                if match and match.group(1) in fake.tasks:
                    return self.reply(200, fake.tasks[match.group(1)])
                return self.reply(404, {"detail": "not found"})

            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                if self.path == "/api/tasks":
                    boundary = self.headers["Content-Type"].split("boundary=")[1]
                    fields = parse_multipart(body, boundary.encode("utf-8"))
                    filename, payload = fields["file"]
                    language = fields["language"][1].decode("utf-8")
                    return self.reply(201, fake.create_task(filename, language, payload))
                match = re.fullmatch(r"/api/tasks/([^/]+)/resume", self.path)
                if match and match.group(1) in fake.tasks:
                    task_id = match.group(1)
                    fake.resumed.append(task_id)
                    fake.tasks[task_id] |= {
                        "status": "preprocessing",
                        "error_message": None,
                    }
                    return self.reply(200, fake.tasks[task_id])
                return self.reply(404, {"detail": "not found"})

        self._server = HTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._server.shutdown()
        self._server.server_close()
        self._thread.join()
