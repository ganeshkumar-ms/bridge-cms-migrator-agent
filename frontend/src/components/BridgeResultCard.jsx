import { useState } from 'react'

function parseRejection(data) {
  const rej = data?.rejection_details || {}
  const msg = typeof data?.message === 'string' ? data.message : ''
  let title = rej.title || data?.title || ''
  let filename = rej.filename || data?.filename || data?.document?.filename || data?.document_metadata?.filename || 'Uploaded File'
  let reason = rej.reason || rej.why || ''
  let technicalDetail = rej.technical_detail || ''
  let supported = rej.supported_formats || ''
  let howToFix = rej.how_to_fix || ''

  if (msg.includes('•') || (!reason && msg.includes('File Not Accepted'))) {
    const parts = msg.split(/\s*•\s*/)
    parts.forEach((p, idx) => {
      const part = p.trim()
      if (idx === 0 && !title) {
        title = part
      } else if (part.toLowerCase().startsWith('file:') && !filename) {
        filename = part.substring(part.indexOf(':') + 1).trim()
      } else if (part.toLowerCase().includes('why it was not accepted:') && !reason) {
        reason = part.substring(part.indexOf(':') + 1).trim()
      } else if (part.toLowerCase().includes('technical details:') && !technicalDetail) {
        technicalDetail = part.substring(part.indexOf(':') + 1).trim()
      } else if (part.toLowerCase().includes('supported formats') && !supported) {
        supported = part.substring(part.indexOf(':') + 1).trim()
      } else if (part.toLowerCase().includes('how to fix') && !howToFix) {
        howToFix = part.substring(part.indexOf(':') + 1).trim()
      }
    })
  }
  if (!title) title = 'File Not Accepted'
    const isSecurity = /credential|secret|access key|password|token/i.test(title + ' ' + reason);
  let reasonLabel = isSecurity ? 'Security & Policy Violation' : 'Reason for Rejection';
  const isFormatIssue = /format|extension|unsupported|binary|unreadable|corrupt|container|mime/i.test(title + ' ' + reason + ' ' + technicalDetail) && !isSecurity && !/empty|blank/i.test(title + ' ' + reason);
  return { title, filename, reason, reasonLabel, technicalDetail, supported: isFormatIssue ? supported : '', howToFix }
}

export default function BridgeResultCard({ data, guardrails: propGuardrails }) {
  const [copiedPayload, setCopiedPayload] = useState(false)
  const [activeTab, setActiveTab] = useState('mappings') // 'mappings' | 'payload' | 'exceptions'

  if (!data) return null
  const guardrails = propGuardrails || data?.guardrails || {}
  const traceId = data?.trace_id || guardrails?.trace_id || ''

  // 1. Structured File Rejection Card
  if (data.rejected || data.rejection_details || (typeof data.message === 'string' && data.message.includes('File Not Accepted'))) {
    const rej = parseRejection(data)
    const title = rej.title
    const filename = rej.filename
    const reason = rej.reason
    const technicalDetail = rej.technicalDetail
    const supported = rej.supported
    const howToFix = rej.howToFix

    return (
      <div className="bridgeRejectionCard">
        <div className="bridgeRejectionHeader">
          <div className="bridgeRejectionBadge">
            <span className="rejectionDot" />
            ⚠️ {title}
          </div>
          <span className="bridgeRejectionFile">
            📄 {filename} {rej.detected_type ? `(${rej.detected_type})` : ''}
          </span>
        </div>

        <div className="bridgeRejectionBody">
          {reason && (
            <div className="rejectionSection">
              <span className="rejectionLabel">{rej.reasonLabel || 'Reason for Rejection'}</span>
              <p className="rejectionValue">{reason}</p>
            </div>
          )}

          {technicalDetail && (
            <div className="rejectionSection">
              <span className="rejectionLabel">Technical Details</span>
              <p className="rejectionValue mono">{technicalDetail}</p>
            </div>
          )}

          {supported && (
            <div className="rejectionSection">
              <span className="rejectionLabel">Supported Formats for BRIDGE</span>
              <p className="rejectionValue">{supported}</p>
            </div>
          )}

          {howToFix && (
            <div className="rejectionSection fixSection">
              <span className="rejectionLabel">How to Fix & Re-upload</span>
              <p className="rejectionValue">{howToFix}</p>
            </div>
          )}

          {!reason && (
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, fontSize: '13.5px', color: '#e2e8f0' }}>
              {data.message}
            </div>
          )}
        </div>
      </div>
    )
  }

  // 2. Fallback to plain conversational response if not a migration structure
  if (data.type === 'chat' || (!data.migration_readiness && data.message)) {
    return (
      <div className="bridgeChatReply">
        {guardrails?.status === 'BLOCKED' && (
          <div style={{ marginBottom: '12px' }}>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 12px',
                borderRadius: '999px',
                fontSize: '11.5px',
                fontWeight: 700,
                background: 'rgba(239, 68, 68, 0.22)',
                color: '#f87171',
                border: '1px solid rgba(239, 68, 68, 0.65)'
              }}
            >
              <span>🛡️</span>
              <span>Guardrails: Blocked ({guardrails.triggered_rule || guardrails.rejection_reason || 'Policy Violation'})</span>
            </span>
          </div>
        )}
        <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.65, fontSize: '14.5px', color: '#f0f7ff' }}>{data.message}</div>
      </div>
    )
  }

  const mr = data.migration_readiness || {}
  const metrics = data.metrics || {}
  const mappings = Array.isArray(data.field_mappings) ? data.field_mappings : []
  const exceptions = Array.isArray(data.exceptions) ? data.exceptions : []
  const payload = data.target_payload || {}
  const checklist = Array.isArray(data.checklist) ? data.checklist : []

  const score = typeof mr.score === 'number' ? mr.score : 80
  const status = mr.status || (score >= 85 ? 'READY_TO_MIGRATE' : score < 50 ? 'SCHEMA_CONFLICTS' : 'TRANSFORMS_REQUIRED')

  const statusConfig = {
    READY_TO_MIGRATE: {
      label: 'READY TO MIGRATE',
      icon: '✓',
      badgeClass: 'statusReady',
      color: '#078cff'
    },
    TRANSFORMS_REQUIRED: {
      label: 'TRANSFORMS REQUIRED',
      icon: '⚡',
      badgeClass: 'statusWarn',
      color: '#facc15'
    },
    SCHEMA_CONFLICTS: {
      label: 'SCHEMA CONFLICTS',
      icon: '⛔',
      badgeClass: 'statusDanger',
      color: '#ff5c5c'
    }
  }[status] || {
    label: 'SCHEMA INSPECTED',
    icon: 'ℹ',
    badgeClass: 'statusWarn',
    color: '#078cff'
  }

  function handleCopyPayload() {
    const text = JSON.stringify(payload, null, 2)
    navigator.clipboard.writeText(text).then(() => {
      setCopiedPayload(true)
      setTimeout(() => setCopiedPayload(false), 2000)
    })
  }

  return (
    <div className="bridgeResultCard">
      {/* 0. GUARDRAILS STATUS BAR & TOP-RIGHT TRACE ID */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
          marginBottom: '14px',
          width: '100%'
        }}
      >
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 12px',
            borderRadius: '999px',
            fontSize: '11.5px',
            fontWeight: 700,
            background: guardrails?.status === 'BLOCKED'
              ? 'rgba(239, 68, 68, 0.22)'
              : guardrails?.status === 'REDACTED'
              ? 'rgba(52, 211, 153, 0.16)'
              : 'rgba(52, 211, 153, 0.16)',
            color: guardrails?.status === 'BLOCKED'
              ? '#f87171'
              : guardrails?.status === 'REDACTED'
              ? '#34d399'
              : '#34d399',
            border: guardrails?.status === 'BLOCKED'
              ? '1px solid rgba(239, 68, 68, 0.65)'
              : guardrails?.status === 'REDACTED'
              ? '1px solid rgba(52, 211, 153, 0.45)'
              : '1px solid rgba(52, 211, 153, 0.45)'
          }}
        >
          <span>🛡️</span>
          <span>
            {guardrails?.status === 'BLOCKED'
              ? `Guardrails: Blocked (${guardrails.triggered_rule || guardrails.rejection_reason || 'Policy Violation'})`
              : guardrails?.status === 'REDACTED'
              ? `Guardrails: ${guardrails.redacted_count || 1} Secret(s) Sanitized`
              : 'Guardrails: Passed · Verified Safe'}
          </span>
        </span>

        {traceId && (
          <span
            style={{
              fontSize: '11px',
              fontFamily: 'ui-monospace, "JetBrains Mono", Menlo, Consolas, monospace',
              fontWeight: 600,
              color: '#38bdf8',
              letterSpacing: '0.6px',
              padding: '3px 9px',
              borderRadius: '6px',
              background: 'rgba(7, 140, 255, 0.08)',
              border: '1px solid rgba(7, 140, 255, 0.24)',
              marginLeft: 'auto',
              flexShrink: 0
            }}
            title="Verification Trace Code"
          >
            {traceId}
          </span>
        )}
      </div>


      {/* Header: Migration Readiness & Score */}
      <div className="bridgeScoreHeader">
        <div className="bridgeScoreBadgeWrap">
          <span className={`bridgeStatusBadge ${statusConfig.badgeClass}`}>
            <span className="badgeDot" />
            {statusConfig.icon} {statusConfig.label}
          </span>
          <div className="bridgeScoreNumberWrap">
            <span className="bridgeScoreNumber" style={{ color: statusConfig.color }}>{score}</span>
            <span className="bridgeScoreMax">/ 100</span>
          </div>
        </div>

        <div className="bridgeScoreBarBg">
          <div
            className="bridgeScoreBarFill"
            style={{
              width: `${Math.min(100, Math.max(0, score))}%`,
              backgroundColor: statusConfig.color
            }}
          />
        </div>

        {mr.summary && (
          <p className="bridgeSummaryText">{mr.summary}</p>
        )}
      </div>

      {/* Sleek Findings Ribbon (Zero bulky boxes!) */}
      <div className="bridgeMetricsStrip">
        <div className="bridgeMetricPill">
          <div className="bridgeMetricLeft">
            <span className="metricDot map" />
            <span className="metricLabel">Mapped Fields</span>
          </div>
          <b className="metricCount map">
            {metrics.mapped_fields_count || mappings.length || 0}
          </b>
        </div>

        <div className="bridgeMetricPill">
          <div className="bridgeMetricLeft">
            <span className="metricDot trans" />
            <span className="metricLabel">Transforms</span>
          </div>
          <b className={`metricCount ${metrics.transforms_needed_count > 0 ? 'trans' : 'zero'}`}>
            {metrics.transforms_needed_count || 0}
          </b>
        </div>

        <div className="bridgeMetricPill">
          <div className="bridgeMetricLeft">
            <span className="metricDot exc" />
            <span className="metricLabel">Exceptions</span>
          </div>
          <b className={`metricCount ${exceptions.length > 0 ? 'exc' : 'zero'}`}>
            {exceptions.length}
          </b>
        </div>

        <div className="bridgeMetricPill targetPill">
          <div className="bridgeMetricLeft">
            <span className="metricDot tgt" />
            <span className="metricLabel">Target CMS</span>
          </div>
          <b className="metricText">
            {metrics.target_system ? metrics.target_system.split('/')[0].trim() : 'Headless CMS'}
          </b>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bridgeTabs">
        <button
          type="button"
          className={`bridgeTabBtn ${activeTab === 'mappings' ? 'active' : ''}`}
          onClick={() => setActiveTab('mappings')}
        >
          Schema Mapping ({mappings.length})
        </button>
        <button
          type="button"
          className={`bridgeTabBtn ${activeTab === 'payload' ? 'active' : ''}`}
          onClick={() => setActiveTab('payload')}
        >
          Target Payload (JSON)
        </button>
        {exceptions.length > 0 && (
          <button
            type="button"
            className={`bridgeTabBtn ${activeTab === 'exceptions' ? 'active' : ''}`}
            onClick={() => setActiveTab('exceptions')}
          >
            Exceptions ({exceptions.length})
          </button>
        )}
      </div>

      {/* TAB 1: FIELD MAPPINGS */}
      {activeTab === 'mappings' && (
        <div className="bridgeSection">
          <div className="bridgeMappingsList">
            {mappings.map((m, idx) => (
              <div key={idx} className="bridgeMapCard">
                <div className="bridgeMapRoute">
                  <div className="bridgeFieldCol source">
                    <span className="bridgeColTag">SOURCE</span>
                    <b className="bridgeFieldName">{m.source_field}</b>
                    <span className="bridgeTypeTag">{m.source_type || 'string'}</span>
                  </div>

                  <div className="bridgeArrowCol">
                    <span className="bridgeTransformPill">
                      {m.transform_rule || 'Direct Map'}
                    </span>
                    <span className="bridgeArrow">➔</span>
                  </div>

                  <div className="bridgeFieldCol target">
                    <span className="bridgeColTag tgt">TARGET</span>
                    <b className="bridgeFieldName tgt">{m.target_field}</b>
                    <span className="bridgeTypeTag tgt">{m.target_type || 'Symbol'}</span>
                  </div>
                </div>

                {m.sample_value && (
                  <div className="bridgeSampleBox">
                    <small>SAMPLE CONVERSION:</small>
                    <p>"{m.sample_value}"</p>
                  </div>
                )}

                {m.notes && (
                  <div className="bridgeNotes">
                    <strong>Rule:</strong> {m.notes}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 2: TARGET PAYLOAD JSON */}
      {activeTab === 'payload' && (
        <div className="bridgeSection">
          <div className="bridgePayloadBox">
            <div className="bridgePayloadHead">
              <span>HEADLESS CMS JSON PAYLOAD:</span>
              <button
                type="button"
                className="bridgeCopyBtn"
                onClick={handleCopyPayload}
              >
                {copiedPayload ? '✓ Copied' : 'Copy Payload 📋'}
              </button>
            </div>
            <pre className="bridgePayloadCode">
              {JSON.stringify(payload, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* TAB 3: EXCEPTIONS */}
      {activeTab === 'exceptions' && (
        <div className="bridgeSection">
          <div className="bridgeExceptionsList">
            {exceptions.map((exc, idx) => (
              <div key={exc.id || idx} className="bridgeExceptionCard">
                <div className="bridgeExceptionHead">
                  <span className={`bridgeSevPill sev-${(exc.severity || 'WARNING').toLowerCase()}`}>
                    {exc.severity || 'WARNING'}
                  </span>
                  <b className="bridgeExcField">{exc.field}</b>
                </div>
                <p className="bridgeExcIssue"><strong>Issue:</strong> {exc.issue}</p>
                {exc.risk && (
                  <p className="bridgeExcRisk"><strong>Risk:</strong> {exc.risk}</p>
                )}
                {exc.suggested_action && (
                  <div className="bridgeExcAction">
                    <strong>Action:</strong> {exc.suggested_action}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Checklist */}
      {checklist.length > 0 && (
        <div className="bridgeCardBox">
          <b className="bridgeCardBoxTitle">⚡ Pre-Migration Checklist</b>
          <ul className="bridgeList">
            {checklist.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

