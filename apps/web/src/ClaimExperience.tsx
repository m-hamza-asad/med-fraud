import { useEffect, useState } from 'react'
import { AlertTriangle, ArrowLeft, CheckCircle2, ChevronRight, FileCheck2, Link2 } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { api } from './api'

const money = new Intl.NumberFormat('en-AE', { style: 'currency', currency: 'AED', maximumFractionDigits: 2 })

function Status({children,tone='neutral'}:{children:React.ReactNode;tone?:string}){return <span className={`status ${tone}`}><span aria-hidden="true" className="status-dot"/>{children}</span>}
function Loading(){return <div className="skeletons" aria-label="Loading"><span/><span/><span/></div>}
function ErrorNotice({message}:{message:string}){return <div className="notice error" role="alert"><AlertTriangle/><div><strong>Something needs attention</strong><p>{message}</p></div></div>}
function Page({title,description,children}:{title:string;description:string;children:React.ReactNode}){return <main className="workspace"><Link className="back-link" to="/claims"><ArrowLeft/>Back to claims</Link><div className="page-title"><div><p className="eyebrow">Claim review</p><h1>{title}</h1><p>{description}</p></div></div>{children}</main>}

type Presentation={headline:string;why_flagged:string;comparison:string;observed_label:string;observed_display:string;expected_label:string;expected_display:string;action:string;limitations:string[];requires_linked_record:boolean;linked_claim?:{id:number;claim_id:string;service_date:string;provider:string;net_amount:string}|null;technical_reference:{rule_id:string;reason_code:string}}
type Evaluation={rule_id:string;status:string;triggered:boolean;disposition:string;evidence:any;presentation?:Presentation|null}
type ClaimPayload={claim:any;evaluation_state:string;evaluation_run_id?:number;coverage_summary:{catalogue_controls:number;controls_with_results:number;controls_unavailable:number;limited:boolean;message:string};evaluations:Evaluation[]}

function EvidenceCard({item}:{item:Evaluation}){
  const view=item.presentation
  if(!view)return null
  return <article className="evidence explanation-card">
    <div className="explanation-heading"><div><p className="eyebrow">Why this needs review</p><h3>{view.headline}</h3></div><Status tone="error">{view.action}</Status></div>
    <p className="plain-reason">{view.why_flagged}</p>
    <div className="comparison-callout"><strong>{view.comparison}</strong><span>This is a review signal, not a finding of fraud.</span></div>
    <dl className="evidence-grid">
      <div><dt>{view.observed_label}</dt><dd>{view.observed_display}</dd></div>
      <div><dt>{view.expected_label}</dt><dd>{view.expected_display}</dd></div>
      <div><dt>Claim value associated with this signal</dt><dd>{money.format(Number(item.evidence.associated_amount??0))}</dd></div>
      <div><dt>Evidence status</dt><dd>{view.requires_linked_record?(view.linked_claim?'Linked evidence available':'Supporting record not linked'):'Canonical data used'}</dd></div>
    </dl>
    <p className="value-boundary">The associated claim value is not confirmed loss, overpayment, or recoverable value.</p>
    {view.requires_linked_record&&(view.linked_claim?<div className="linked-evidence"><Link2/><div><strong>Earlier claim used for comparison</strong><Link to={`/claims/${view.linked_claim.id}`}>{view.linked_claim.claim_id}<ChevronRight/></Link><span>{view.linked_claim.service_date} · {view.linked_claim.provider} · {money.format(Number(view.linked_claim.net_amount))}</span></div></div>:<div className="notice warning" role="alert"><AlertTriangle/><div><strong>Earlier encounter not linked</strong><p>The source supplied the timing value, but this dataset does not contain the earlier claim needed to verify it. Confirm the prior encounter before taking action.</p></div></div>)}
    {view.limitations.length>0&&<section className="limitations"><strong>What this assessment could not confirm</strong><ul>{view.limitations.map(text=><li key={text}>{text}</li>)}</ul></section>}
    <section className="analyst-checklist"><strong>What to check next</strong><ol><li>Confirm the earlier admission and discharge dates.</li><li>Compare diagnosis, procedure, provider and planned-care information.</li><li>Check transfers, staged treatment, approved exceptions and other legitimate explanations.</li><li>Record the review outcome before escalation or recovery action.</li></ol></section>
    <details className="technical-details"><summary>Technical details</summary><dl><div><dt>Rule</dt><dd><Link to={`/rules/${view.technical_reference.rule_id}`}>{view.technical_reference.rule_id}</Link></dd></div><div><dt>Reason code</dt><dd><code>{view.technical_reference.reason_code}</code></dd></div><div><dt>Formula</dt><dd><code>{item.evidence.formula}</code></dd></div></dl></details>
  </article>
}

export function ClaimDetail(){
  const id=useLocation().pathname.split('/').pop()
  const[data,setData]=useState<ClaimPayload|null>(null);const[error,setError]=useState('')
  useEffect(()=>{api<ClaimPayload>(`/claims/${id}`).then(setData).catch(reason=>setError(reason.message))},[id])
  if(error)return <Page title="Claim unavailable" description="The requested claim could not be loaded."><ErrorNotice message={error}/></Page>
  if(!data)return <Page title="Loading claim" description="Retrieving the latest completed assessment."><Loading/></Page>
  const assessed=data.evaluation_state==='ASSESSED';const fired=data.evaluations.filter(item=>item.triggered);const coverage=data.coverage_summary
  const resultLabel=!assessed?'Not evaluated':fired.length?'Review needed':coverage.limited?'No signal in available controls':'No signal detected'
  const resultTone=!assessed||coverage.limited?'warning':fired.length?'error':'success'
  const context=data.claim.context??{}
  return <Page title={data.claim.claim_id} description={`${data.claim.source_profile} · service date ${data.claim.service_date} · version ${data.claim.version_id}`}>
    <section className="claim-summary human-summary"><div><Status tone={resultTone}>{resultLabel}</Status><h2>{fired[0]?.presentation?.headline??(!assessed?'Run an evaluation for this batch':coverage.limited?'No signal was found in the controls that could run':'No review reason triggered')}</h2><p>{fired[0]?.presentation?.why_flagged??coverage.message}</p></div><dl><div><dt>Submitted</dt><dd>{money.format(Number(data.claim.amounts.submitted))}</dd></div><div><dt>Net</dt><dd>{money.format(Number(data.claim.amounts.net))}</dd></div><div><dt>Paid</dt><dd>{money.format(Number(data.claim.amounts.paid))}</dd></div></dl></section>
    {assessed&&coverage.limited&&<div className="notice warning coverage-warning" role="alert"><AlertTriangle/><div><strong>Limited assessment</strong><p>{coverage.message} A missing control result is not a clean result.</p></div></div>}
    <section className="claim-context panel"><div className="section-head"><div><p className="eyebrow">Claim context</p><h2>Information available for review</h2></div></div><dl className="evidence-grid"><div><dt>Member token</dt><dd>{data.claim.member}</dd></div><div><dt>Provider token</dt><dd><Link to={`/providers/${encodeURIComponent(data.claim.provider)}`}>{data.claim.provider}</Link></dd></div><div><dt>Admission</dt><dd>{context.admission_date??'Unavailable'}</dd></div><div><dt>Discharge</dt><dd>{context.discharge_date??'Unavailable'}</dd></div><div><dt>Primary diagnosis</dt><dd>{context.diagnosis_description??'Unavailable'}{context.diagnosis_code&&<small>{context.diagnosis_code}</small>}</dd></div><div><dt>Network / TPA</dt><dd>{data.claim.network_id??'Unavailable'}</dd></div></dl></section>
    {!assessed?<div className="notice info"><FileCheck2/><div><strong>Assessment required</strong><p>Open Upload & validation and start an evaluation for this claim’s imported batch.</p></div></div>:<section className="two-col detail-grid"><article className="panel"><p className="eyebrow">Review reasons</p><h2>{fired.length?`${fired.length} reason${fired.length===1?'':'s'} needs attention`:'No active review reason'}</h2>{fired.length?fired.map(item=><EvidenceCard key={item.rule_id} item={item}/>):<div className="empty"><CheckCircle2/><h3>{coverage.limited?'No signal in the controls that could run':'No signal detected'}</h3><p>{coverage.message}</p></div>}</article><aside className="panel"><p className="eyebrow">Assessment coverage</p><h2>How much could be checked?</h2><div className="coverage-list"><div><span>Controls with a result</span><strong>{coverage.controls_with_results} / {coverage.catalogue_controls}</strong></div><div><span>Unavailable because data was missing</span><strong>{coverage.controls_unavailable}</strong></div><div><span>Evaluation run</span><strong>#{data.evaluation_run_id}</strong></div></div><p className="panel-note">Unavailable controls did not pass or fail; they could not be assessed from this dataset.</p></aside></section>}
  </Page>
}
