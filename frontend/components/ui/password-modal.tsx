"use client";

import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type PasswordModalProps = {
  visible: boolean;
  examId: string;
  format: string;
  onConfirm: (password: string) => void;
  onCancel: () => void;
  errorMessage?: string;
};

export function PasswordModal({ visible, examId, format, onConfirm, onCancel, errorMessage }: PasswordModalProps) {
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (visible) setPassword("");
  }, [visible]);

  if (!visible) return null;
  return (
    <div className="fixed inset-0 z-[1050] flex items-center justify-center bg-neutral-900/80">
      <div className="w-[92%] max-w-md rounded-2xl bg-white p-6 text-foreground shadow-2xl dark:bg-neutral-900">
        <div className="text-lg font-semibold">보안 확인</div>
        <div className="mt-1 text-sm text-muted-foreground">수집을 시작하려면 비밀번호를 입력해주세요.</div>

        <div className="mt-4 rounded-xl border bg-muted/20 p-4">
          <div className="text-sm font-medium">미리보기</div>
          <div className="mt-2 grid grid-cols-3 gap-2 text-sm">
            <div className="text-muted-foreground">시험 ID</div>
            <div className="col-span-2 break-all">{examId || "-"}</div>
            <div className="text-muted-foreground">파일 형식</div>
            <div className="col-span-2 uppercase">{format}</div>
          </div>
        </div>

        <div className="mt-4">
          <label className="mb-1 block text-sm font-medium">비밀번호</label>
          <Input
            type="password"
            placeholder="비밀번호를 입력하세요"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") onConfirm(password);
            }}
          />
          {errorMessage ? <div className="mt-2 text-sm text-red-600">{errorMessage}</div> : null}
        </div>

        <div className="mt-5 flex items-center justify-end gap-2">
          <Button variant="outline" onClick={onCancel}>취소</Button>
          <Button className="bg-primary hover:bg-primary/90" onClick={() => onConfirm(password)}>확인</Button>
        </div>
      </div>
    </div>
  );
}


