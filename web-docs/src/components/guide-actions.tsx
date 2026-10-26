"use client";

import { useEffect, useState } from "react";
import { CheckIcon, CopyIcon } from "@radix-ui/react-icons";

export function CopyPrompt({ text, command = false }: { text: string; command?: boolean }) {
  const [status, setStatus] = useState<"idle" | "copied" | "error">("idle");
  const copy = async () => { try { await navigator.clipboard.writeText(text); setStatus("copied"); } catch { setStatus("error"); } };
  return <div className="prompt-box"><div className="prompt-heading"><span>{command ? "Lệnh" : "Gửi Claude"}</span><button onClick={copy}>{status === "copied" ? <CheckIcon /> : <CopyIcon />}{status === "copied" ? "Đã sao chép" : "Sao chép"}</button></div>{command ? <pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", fontSize: 12 }}>{text}</pre> : <p>{text}</p>}{status === "error" && <small aria-live="polite">Không sao chép được, hãy chọn và sao chép thủ công.</small>}</div>;
}

export function Checklist({ items, storageKey }: { items: string[]; storageKey: string }) {
  const [checked, setChecked] = useState<number[]>([]);
  const [message, setMessage] = useState("");
  useEffect(() => { try { const data = JSON.parse(localStorage.getItem(storageKey) || "[]"); if (Array.isArray(data)) setChecked(data.filter((i) => typeof i === "number")); } catch {} }, [storageKey]);
  const toggle = (index: number) => { const next = checked.includes(index) ? checked.filter((i) => i !== index) : [...checked, index]; setChecked(next); try { localStorage.setItem(storageKey, JSON.stringify(next)); } catch { setMessage("Trình duyệt chưa lưu được tiến độ. Bạn vẫn có thể đánh dấu trong phiên này."); } };
  return <div className="checklist">{items.map((item, index) => <label key={item} className={checked.includes(index) ? "checked" : ""}><input type="checkbox" checked={checked.includes(index)} onChange={() => toggle(index)} /><span>{item}</span></label>)}<small aria-live="polite">{message}</small></div>;
}

