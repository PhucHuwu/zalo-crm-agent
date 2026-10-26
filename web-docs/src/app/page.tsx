import Link from "next/link";
import { ArrowRightIcon } from "@radix-ui/react-icons";
import { cycle, guideHref, phases } from "@/lib/guides";

export default function Home() {
  return <div className="simple-home">
    <h1>Chu trình sử dụng workflow</h1>
    <p className="home-intro">Mỗi ngày Claude đọc hội thoại Zalo OA, phân tích thành khách hàng, công ty, cơ hội, ghi chú và việc cần làm trên TinaCRM, giao đúng sale theo nhãn Zalo. Gồm 3 phần: bước 1 làm trên máy, từ bước 2 gửi câu lệnh cho Claude trong tab Code.</p>
    {phases.map((phase, p) => <section className="start-choice phase-block" id={phase.id} key={phase.id}>
      <div className="phase-head"><span className="phase-index">Phần {p + 1}</span><h2>{phase.title}</h2><span className="phase-range">Bước {phase.from}–{phase.to}</span></div>
      <p className="phase-when">{phase.when}</p>
      <ol className="start-steps">
        {cycle.slice(phase.from - 1, phase.to).map((item, i) => <li key={item.slug}><Link href={guideHref(item.slug)}><span className="start-step-number">{phase.from + i}</span><div><h3>{item.shortTitle}</h3><p><span className="actor-tag">{item.actor}</span> {item.description}</p></div><ArrowRightIcon /></Link></li>)}
      </ol>
      {p === 0 && <Link className="button button-primary" href={guideHref(cycle[0].slug)}>Bắt đầu bước 1 <ArrowRightIcon /></Link>}
    </section>)}
    <p className="home-help"><Link href={guideHref("tro-giup")}>Câu hỏi thường gặp</Link></p>
  </div>;
}
