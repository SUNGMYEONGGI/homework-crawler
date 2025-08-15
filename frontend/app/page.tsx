"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { OverlayLoading } from "@/components/ui/overlay-loading";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export default function Page() {
  const [examId, setExamId] = useState("");
  const [format, setFormat] = useState("csv");
  const [logs, setLogs] = useState<string[]>([]);
  const [progress, setProgress] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [downloadPath, setDownloadPath] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    const wsUrl = BACKEND_URL.replace(/^http/, "ws") + "/ws";
    setConnecting(true);
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.type === "log") {
          setLogs((prev) => [...prev, data.message]);
        } else if (data.type === "progress") {
          setProgress(Math.round((data.progress ?? 0) * 100));
        } else if (data.type === "complete") {
          setIsRunning(false);
          setDownloadPath(data.file_path);
        } else if (data.type === "error") {
          setIsRunning(false);
          setLogs((prev) => [...prev, `ERROR: ${data.message}`]);
        }
      } catch (e) {
        // ignore non-json
      }
    };
    ws.onopen = () => setConnecting(false);
    ws.onerror = () => setConnecting(false);
    ws.onclose = () => setConnecting(false);
    wsRef.current = ws;
    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, []);

  const canStart = useMemo(() => !!examId && !isRunning, [examId, isRunning]);

  const startCrawl = async () => {
    setLogs([]);
    setProgress(0);
    setDownloadPath(null);
    setIsRunning(true);
    setConnecting(true);
    const res = await fetch(`${BACKEND_URL}/api/crawl`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ exam_id: examId, file_format: format }),
    });
    if (!res.ok) {
      const msg = await res.json().catch(() => ({}));
      setIsRunning(false);
      setLogs((prev) => [...prev, `요청 실패: ${msg?.detail ?? res.statusText}`]);
      setConnecting(false);
    }
  };

  const stopCrawl = async () => {
    await fetch(`${BACKEND_URL}/api/stop`, { method: "POST" });
    setIsRunning(false);
  };

  return (
    <main className="mx-auto max-w-3xl p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Homework Crawler</h1>
      <section className="grid gap-4 sm:grid-cols-3">
        <div className="sm:col-span-2">
          <label className="block text-sm font-medium mb-1">시험 ID</label>
          <input
            value={examId}
            onChange={(e) => setExamId(e.target.value)}
            placeholder="예: 1234"
            className="w-full rounded border px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">파일 형식</label>
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value)}
            className="w-full rounded border px-3 py-2"
          >
            <option value="csv">CSV</option>
            <option value="xlsx">XLSX</option>
            <option value="json">JSON</option>
            <option value="xml">XML</option>
          </select>
        </div>
      </section>

      <section className="flex items-center gap-3">
        <button
          disabled={!canStart}
          onClick={startCrawl}
          className="rounded bg-black px-4 py-2 text-white disabled:opacity-40"
        >
          {isRunning ? "실행 중..." : "수집 시작"}
        </button>
        <button
          disabled={!isRunning}
          onClick={stopCrawl}
          className="rounded border px-4 py-2 disabled:opacity-40"
        >
          중지
        </button>
        <div className="ml-auto text-sm">진행률: {progress}%</div>
      </section>

      {downloadPath && (
        <a
          href={`${BACKEND_URL}/api/download/${encodeURIComponent(downloadPath)}`}
          className="inline-block rounded bg-green-600 px-4 py-2 text-white"
        >
          결과 다운로드
        </a>
      )}

      <section>
        <div className="text-sm font-medium mb-2">로그</div>
        <div className="h-64 overflow-auto rounded border bg-white p-3 text-sm">
          {logs.map((l, i) => (
            <div key={i} className="whitespace-pre-wrap">
              {l}
            </div>
          ))}
        </div>
      </section>
      <OverlayLoading visible={connecting && isRunning} title="연결중" description="로그가 곧 도착합니다..." />
    </main>
  );
}
