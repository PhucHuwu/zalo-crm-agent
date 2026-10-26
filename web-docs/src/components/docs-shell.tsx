"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ArrowRightIcon, ReaderIcon as BookOpenIcon, Cross1Icon, MagnifyingGlassIcon, HamburgerMenuIcon, SunIcon, MoonIcon } from "@radix-ui/react-icons";
import { guides, cycle, help, guideHref, phases } from "@/lib/guides";

const normalize = (value: string) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").toLowerCase();

export function DocsShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [menu, setMenu] = useState(false);
  const [search, setSearch] = useState(false);
  const [query, setQuery] = useState("");
  const [dark, setDark] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    try { const mode = localStorage.getItem("guide-theme"); const enabled = mode ? mode === "dark" : matchMedia("(prefers-color-scheme: dark)").matches; setDark(enabled); document.documentElement.dataset.theme = enabled ? "dark" : "light"; } catch {}
  }, []);
  useEffect(() => { if (search) { dialog.current?.showModal(); input.current?.focus(); } else dialog.current?.close(); }, [search]);
  useEffect(() => {
    const handler = (event: KeyboardEvent) => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); setSearch((value) => !value); } };
    window.addEventListener("keydown", handler); return () => window.removeEventListener("keydown", handler);
  }, []);
  const results = guides.filter((guide) => normalize([guide.title, guide.description, ...guide.sections.map((s) => `${s.title} ${s.paragraphs?.join(" ") || ""} ${s.faqs?.map((f) => `${f.question} ${f.answer}`).join(" ") || ""}`)].join(" ")).includes(normalize(query)));
  const toggleTheme = () => { const enabled = !dark; setDark(enabled); document.documentElement.dataset.theme = enabled ? "dark" : "light"; try { localStorage.setItem("guide-theme", enabled ? "dark" : "light"); } catch {} };
  return <>
    <a className="skip-link" href="#noi-dung">Đến nội dung</a>
    <header className="topbar">
      <Link href="/" className="brand"><span className="brand-symbol"><BookOpenIcon /></span><span>Hướng dẫn Zalo OA → CRM</span></Link>
      <div className="header-actions"><button className="search-trigger" onClick={() => setSearch(true)}><MagnifyingGlassIcon /><span>Tìm hướng dẫn…</span><kbd>⌘ K</kbd></button><button className="icon-button" aria-label={dark ? "Chuyển sang giao diện sáng" : "Chuyển sang giao diện tối"} onClick={toggleTheme}>{dark ? <SunIcon /> : <MoonIcon />}</button><button className="icon-button mobile-toggle" aria-label="Mở hoặc đóng mục lục" aria-expanded={menu} onClick={() => setMenu(!menu)}>{menu ? <Cross1Icon /> : <HamburgerMenuIcon />}</button></div>
    </header>
    <div className="workspace">
      <aside className={`sidebar ${menu ? "is-open" : ""}`} aria-label="Điều hướng tài liệu">
        <Link className={`overview-link ${pathname === "/" ? "active" : ""}`} href="/" onClick={() => setMenu(false)}><BookOpenIcon /> Toàn bộ chu trình</Link>
        {phases.map((phase) => <nav aria-label={phase.title} className="nav-cycle" key={phase.id}>
          <p className="nav-label nav-cycle-label">{phase.title}</p>
          {cycle.slice(phase.from - 1, phase.to).map((guide, i) => <Link onClick={() => setMenu(false)} href={guideHref(guide.slug)} key={guide.slug} className={`nav-link ${pathname === guideHref(guide.slug) ? "active" : ""}`}><span><b className="nav-step">{phase.from + i}</b>{guide.shortTitle}</span></Link>)}
        </nav>)}
        <Link onClick={() => setMenu(false)} href={guideHref(help.slug)} className={`nav-link nav-help ${pathname === guideHref(help.slug) ? "active" : ""}`}><span>{help.shortTitle}</span></Link>
      </aside>
      <main id="noi-dung" className="main-content" tabIndex={-1}>{children}</main>
    </div>
    <dialog ref={dialog} className="search-dialog" onCancel={() => setSearch(false)} onClick={(event) => { if (event.target === dialog.current) setSearch(false); }}>
      <div className="search-dialog-header"><MagnifyingGlassIcon /><label className="sr-only" htmlFor="guide-search">Tìm hướng dẫn</label><input ref={input} id="guide-search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Bạn muốn tìm hiểu điều gì?" /><button className="icon-button" aria-label="Đóng tìm kiếm" onClick={() => setSearch(false)}><Cross1Icon /></button></div>
      <div className="search-results"><p className="nav-label">{query ? `${results.length} hướng dẫn phù hợp` : "Các hướng dẫn"}</p>{results.map((guide) => <Link key={guide.slug} href={guideHref(guide.slug)} onClick={() => { setSearch(false); setQuery(""); }}><div><strong>{guide.shortTitle}</strong><p>{guide.description}</p></div><ArrowRightIcon /></Link>)}{results.length === 0 && <div className="search-empty"><strong>Chưa tìm thấy hướng dẫn</strong><p>Thử từ ngắn hơn, như “nhãn”, “token” hoặc “lịch”.</p><Link href={guideHref("tro-giup")} onClick={() => setSearch(false)}>Xem phần trợ giúp</Link></div>}</div>
    </dialog>
  </>;
}
