"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { OverlayLoading } from "@/components/ui/overlay-loading";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { Mail, Github } from "lucide-react";

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
        // 백엔드에서 첫 응답이 도착하면 대기 오버레이 즉시 해제
        setConnecting(false);
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
    <main className="mx-auto max-w-6xl p-6 md:p-10 space-y-8">
      {/* 브랜드 히어로 */}
      <section className="overflow-hidden rounded-3xl bg-gradient-to-r from-[#ff0a54] to-[#c0126a] p-8 text-white shadow-lg">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="inline-flex items-center rounded-full bg-white/15 px-3 py-1 text-xs backdrop-blur-md">
              Fastcampus Persona
            </div>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight md:text-4xl">Homework Crawler</h1>
            <p className="mt-1 text-white/85">Fastcampus LMS 과제 수집 대시보드</p>
          </div>
          <div className="mt-4 md:mt-0">
            <div className="rounded-2xl bg-white/10 px-4 py-3 text-sm">
              시험 ID를 입력하고 수집을 시작하면 실시간 로그와 진행률을 확인할 수 있어요.
            </div>
          </div>
        </div>
      </section>

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

      {/* 푸터 */}
      <footer className="mt-8 rounded-3xl border bg-white/70 p-6 text-sm dark:bg-neutral-900/70">
        <div className="grid gap-4 md:grid-cols-3 md:items-center">
          <div>
            <div className="text-base font-semibold">Fastcampus</div>
            <div className="mt-1 text-muted-foreground">© {new Date().getFullYear()} Fastcampus. All rights reserved.</div>
          </div>
          <div>
            <div className="font-medium">개발자</div>
            <div className="mt-1">성명기 Myeonggi seong</div>
            <div className="text-muted-foreground">교육운영/관리 매니저 (Learning Experience Manager)</div>
            <div className="text-muted-foreground whitespace-nowrap">운영파트 | 취업교육팀 | 인재성장교육그룹 | 커리어교육사업본부 | Day1 B2G</div>
          </div>
          <div className="flex flex-wrap items-center gap-3 md:justify-end">
            <a
              href="mailto:myeonggi.seong@day1company.co.kr"
              className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-white shadow hover:bg-primary/90"
            >
              <Mail className="h-4 w-4" /> myeonggi.seong@day1company.co.kr
            </a>
            <a
              href="https://github.com/SUNGMYEONGGI"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-md border px-3 py-2 shadow-sm hover:bg-accent"
            >
              <Github className="h-4 w-4" /> GitHub
            </a>
          </div>
        </div>
      </footer>

      <OverlayLoading visible={connecting && isRunning && logs.length === 0} title="연결중" description="로그가 곧 도착합니다..." />
    </main>
  );
}
