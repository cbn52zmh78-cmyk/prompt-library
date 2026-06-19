# #206 Channel Positioning — Creator #4 (Compliance Explainers)

**Task:** #206 · **Channel:** ClearDesk (draft) · **Host:** Serena-001 · **Format:** `explainer-ad`

---

## Decision

| Option | Verdict | Why |
|--------|---------|-----|
| **Own channel — ClearDesk (Upon Tyne Operations)** | **RECOMMENDED** | Distinct audience (ops/back-office), host, set, and disclaimer boundary |
| **Observable sub-series** | **Reject** | Science measurement lane ≠ regulatory literacy |
| **Stonebridge-branded channel** | **Reject** | Implies assessor/certifier; Stonebridge stays B2B delivery, not YouTube face |
| **DAVID sub-series** | **Reject** | Language/archive method ≠ compliance process explainers |

---

## Architecture

```
Upon Tyne (parent)
├── DAVID · The Archive          ← language / attestation
├── Observable                   ← phenomenon / measurement
├── Blueprint [Creator #3]       ← systems / mechanisms
└── ClearDesk [Creator #4]       ← compliance / back-office literacy
```

---

## Brand lock (every concept)

```json
"brand": {
  "title": "ClearDesk",
  "subtitle": "Upon Tyne Operations — compliance, explained clearly",
  "cta": "Follow ClearDesk — one process at a time.",
  "legal_line": "Educational content only — not legal, tax, or professional advice."
}
```

| Lock | Value |
|------|-------|
| `actor_id` | `Serena-001` |
| `format_id` | `explainer-ad` |
| Set | `@Set-Studio-Interior-001` |
| Style | `@Style-Professional-Clean-001` |
| Intake block | `compliance_subject` + `sources[]` |
| Labels | `NOT LEGAL ADVICE` on regulatory-touch episodes |

---

## Playlists (at launch)

| Playlist | Contents |
|----------|----------|
| ClearDesk · Records & Audit | Trails, retention, audit readiness |
| ClearDesk · Licensing & Renewals | Packets, primary sources, deadlines |
| ClearDesk · Back-Office Processes | Approvals, handoffs, ownership |
| ClearDesk · How to Read the Rule | Regulatory language literacy |

---

## Stonebridge boundary

ClearDesk is **consumer/SMB education** — public-source literacy. It does **not**:

- Certify, assess, or guarantee compliance outcomes
- Replace Stonebridge client deliverables or RCaaS positioning
- Use C3PAO, assessor, or law-firm voice

Cross-promote in community posts only after flagship episodes ship.

---

## Doc cross-ref (#206 deliverable)

| Artifact | Path |
|----------|------|
| Channel Bible | `Creator4/brand/Creator4_Channel_Bible_v1.md` |
| Brand kit | `Creator4/brand/Upon_Tyne_Creator4_Brand_Kit_v1.md` |
| Name options | `Creator4/brand/NAME_OPTIONS.md` |
| Machine specs | `Creator4/brand/asset_specs.json` |
| About | `Creator4/brand/CHANNEL_ABOUT.md` |
| Host identity | `Creator4/productions/host_identity_v1/serena_identity_lock.json` |
| Concept template | `STUDIO/Pipeline/Concepts/compliance_explainer/template_compliance_explainer_v1.concept.json` |

**Render:** deferred — doc/brand only per #206 scope.