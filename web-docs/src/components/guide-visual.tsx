"use client";

import { useRef, useState } from "react";
import { Cross1Icon, ZoomInIcon } from "@radix-ui/react-icons";
import type { Visual } from "@/lib/visuals";

const boxes = (markers: Visual["markers"]) => markers?.map((marker) => <span className="visual-box" style={{ left: `${marker.x}%`, top: `${marker.y}%`, width: `${marker.w}%`, height: `${marker.h}%` }} key={marker.label} aria-hidden="true"><span className={`visual-badge ${marker.badge ?? "right"}`}>{marker.label}</span></span>);

export function GuideVisual({ visual }: { visual: Visual }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [failed, setFailed] = useState(false);
  const image = <div className="visual-stage"><div className="visual-image" style={visual.width ? { maxWidth: visual.width } : undefined}>{visual.srcLight && <img className="img-light" src={visual.srcLight} alt={visual.alt} loading="lazy" onError={() => setFailed(true)} />}<img className={visual.srcLight ? "img-dark" : undefined} src={visual.src} alt={visual.srcLight ? "" : visual.alt} loading="lazy" onError={() => setFailed(true)} />{visual.markersLight ? <><span className="img-light">{boxes(visual.markersLight)}</span><span className="img-dark">{boxes(visual.markers)}</span></> : boxes(visual.markers)}</div></div>;
  const legend = visual.markers?.length ? <ol className="visual-legend">{visual.markers.map((marker) => <li key={marker.label}><span>{marker.label}</span>{marker.text}</li>)}</ol> : null;
  return <figure className="guide-visual"><div className="visual-top"><span>{visual.kind}</span><button onClick={() => dialog.current?.showModal()} disabled={failed}><ZoomInIcon /> Phóng to hình</button></div>{failed ? <p className="visual-error">Chưa tải được hình. Bạn có thể đọc hướng dẫn và thử tải lại trang.</p> : <button className="visual-open" onClick={() => dialog.current?.showModal()} aria-label={`Phóng to: ${visual.alt}`}>{image}</button>}{legend}{visual.caption && <figcaption>{visual.caption}</figcaption>}<dialog ref={dialog} className="visual-dialog" onClick={(event) => { if (event.target === dialog.current) dialog.current?.close(); }}><div className="visual-dialog-bar"><strong>{visual.kind}</strong><button className="icon-button" aria-label="Đóng hình phóng to" onClick={() => dialog.current?.close()}><Cross1Icon /></button></div>{image}{legend}</dialog></figure>;
}
