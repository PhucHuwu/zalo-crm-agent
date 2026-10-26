import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { ArrowLeftIcon, ArrowRightIcon, InfoCircledIcon, ExternalLinkIcon } from "@radix-ui/react-icons";
import { cycle, guides, guideHref, phaseOf, stepNumber } from "@/lib/guides";
import { Checklist, CopyPrompt } from "@/components/guide-actions";
import { GuideVisual } from "@/components/guide-visual";
import { visuals } from "@/lib/visuals";

export function generateStaticParams() { return guides.map((g) => ({ slug: g.slug })); }
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> { const { slug } = await params; const guide = guides.find((g) => g.slug === slug); return { title: guide?.title, description: guide?.description }; }

export default async function GuidePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const guide = guides.find((g) => g.slug === slug);
  if (!guide) notFound();
  const step = stepNumber(slug);
  const prev = step > 1 ? cycle[step - 2] : undefined;
  const next = step > 0 && step < cycle.length ? cycle[step] : undefined;
  const phase = phaseOf(step);
  const nextPhase = next && phaseOf(step + 1) !== phase ? phaseOf(step + 1) : undefined;
  return <div className="article-layout"><article className="article">
    <div className="breadcrumb"><Link href="/">Chu trình</Link><span>/</span>{phase && <><Link href={`/#${phase.id}`}>{phase.title}</Link><span>/</span></>}{step > 0 ? `Bước ${step} / ${cycle.length}` : "Trợ giúp"}</div>
    <header className="article-header">
      {step > 0 && <div className="cycle-progress" aria-hidden="true">{cycle.map((g, i) => <Link key={g.slug} href={guideHref(g.slug)} className={i + 1 < step ? "done" : i + 1 === step ? "current" : ""} title={`Bước ${i + 1}: ${g.shortTitle}`} />)}</div>}
      {phase && <span className="phase-tag">{phase.title} · {phase.when}</span>}
      <span className="actor-tag">{guide.actor}</span>
      <h1>{step > 0 && <span className="step-prefix">Bước {step}.</span>} {guide.title}</h1>
      <p>{guide.description}</p>
    </header>
    {guide.slug === "mo-workflow" && <p style={{ marginBottom: 28 }}><a className="button button-primary" href="https://github.com/PhucHuwu/zalo-crm-agent" target="_blank" rel="noreferrer">Mở trang tải workflow <ExternalLinkIcon /></a></p>}
    {guide.sections.map((section) => <section className="article-section" id={section.id} key={section.id}>
      <h2>{section.title}</h2>
      {section.paragraphs?.map((p) => <p key={p}>{p}</p>)}
      {section.steps && <ol className="steps">{section.steps.map((s, n) => <li key={s.title}><span className="step-number">{n + 1}</span><div><h3>{s.title}</h3><p>{s.body}</p></div></li>)}</ol>}
      {(visuals[`${guide.slug}:${section.id}`] || []).map((visual) => <GuideVisual key={visual.src} visual={visual} />)}
      {section.prompt && <CopyPrompt text={section.prompt} />}
      {section.checks && <Checklist items={section.checks} storageKey={`guide-checks:${guide.slug}:${section.id}`} />}
      {section.note && <details className="additional-info"><summary>{section.note.title}</summary><aside className="note"><InfoCircledIcon /><p>{section.note.body}</p></aside></details>}
      {section.faqs && <div className="faqs">{section.faqs.map((faq) => <details key={faq.question}><summary>{faq.question}</summary><p>{faq.answer}</p></details>)}</div>}
    </section>)}
    <nav className="article-pagination" aria-label="Bước trước và tiếp theo">
      {prev ? <Link href={guideHref(prev.slug)}><span><ArrowLeftIcon /> Bước {step - 1}</span><strong>{prev.shortTitle}</strong></Link> : <Link href="/"><span><ArrowLeftIcon /> Quay lại</span><strong>Toàn bộ chu trình</strong></Link>}
      {next ? <Link className="next-page" href={guideHref(next.slug)}><span>{nextPhase ? `Sang phần ${nextPhase.title.toLowerCase()} · ` : ""}Bước {step + 1} <ArrowRightIcon /></span><strong>{next.shortTitle}</strong></Link> : step === cycle.length ? <Link className="next-page" href="/"><span>Xong chu trình <ArrowRightIcon /></span><strong>Mỗi ngày quay lại bước {stepNumber("hang-ngay")}</strong></Link> : null}
    </nav>
  </article></div>;
}
