"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { OverlayLoading } from "@/components/ui/overlay-loading";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";

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
    <main className="mx-auto max-w-5xl p-6 md:p-10 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Homework Crawler</h1>
          <p className="mt-1 text-sm text-muted-foreground">Fastcampus 과제 수집 대시보드</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>수집 설정</CardTitle>
            <CardDescription>시험 ID와 파일 형식을 선택하고 수집을 시작하세요.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium mb-1">시험 ID</label>
                <Input value={examId} onChange={(e) => setExamId(e.target.value)} placeholder="예: 1234" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">파일 형식</label>
                <Select value={format} onValueChange={setFormat}>
                  <SelectTrigger>
                    <SelectValue placeholder="파일 형식 선택" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="csv">CSV</SelectItem>
                    <SelectItem value="xlsx">XLSX</SelectItem>
                    <SelectItem value="json">JSON</SelectItem>
                    <SelectItem value="xml">XML</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="mt-6 flex items-center gap-3">
              <Button disabled={!canStart} onClick={startCrawl} className="bg-primary hover:bg-primary/90">
                {isRunning ? "실행 중..." : "수집 시작"}
              </Button>
              <Button variant="outline" disabled={!isRunning} onClick={stopCrawl}>
                중지
              </Button>
              <div className="ml-auto w-1/2">
                <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
                  <span>진행률</span>
                  <span>{progress}%</span>
                </div>
                <Progress value={progress} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>다운로드</CardTitle>
            <CardDescription>수집이 완료되면 파일을 내려받을 수 있어요.</CardDescription>
          </CardHeader>
          <CardContent>
            {downloadPath ? (
              <a
                href={`${BACKEND_URL}/api/download/${encodeURIComponent(downloadPath)}`}
                className="inline-block rounded-md bg-green-600 px-4 py-2 text-white hover:bg-green-700"
              >
                결과 다운로드
              </a>
            ) : (
              <p className="text-sm text-muted-foreground">아직 생성된 파일이 없습니다.</p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>실시간 로그</CardTitle>
          <CardDescription>수집 진행 상황을 실시간으로 확인하세요.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-72 overflow-auto rounded-md border bg-white p-3 text-sm dark:bg-neutral-900">
            {logs.length === 0 ? (
              <div className="text-muted-foreground">아직 로그가 없습니다. 수집을 시작해보세요.</div>
            ) : (
              logs.map((l, i) => (
                <div key={i} className="whitespace-pre-wrap">
                  {l}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      <OverlayLoading visible={connecting && isRunning} title="연결중" description="로그가 곧 도착합니다..." />
    </main>
  );
}
