# Grok Batch Adapter — Design Spec
## render_longform.py integration
## 2026-06-30

---

## Problem

render_longform.py hits the xAI Imagine Video API at 1 RPS with weekly caps.
A 50-shot project burns the full weekly allocation in one session, leaving no
room for iteration. The xAI Batch API processes video requests asynchronously
with no rate limit impact and reduced pricing.

## Architecture

```
render_longform.py                    grok_batch_adapter.py
┌─────────────────────┐               ┌──────────────────────┐
│ --batch mode:       │               │                      │
│  parse script       │──imagine──>   │ pack_to_jsonl()      │
│  resolve refs       │   pack        │  → batch_requests.jsonl│
│  build_imagine_pack │               │                      │
│  QA pre-gates       │               │ submit_batch()       │
│  (no API calls)     │               │  → batch_id          │
│  exit with batch_id │               │                      │
└─────────────────────┘               │ poll_batch()         │
                                      │  → status + progress │
┌─────────────────────┐               │                      │
│ --collect mode:     │               │ collect_results()    │
│  load batch_id      │<──results──   │  → {shot_id: url}    │
│  download videos    │               │                      │
│  run QA gates       │               │ rebatch_failures()   │
│  concat final       │               │  → new batch_id      │
│  EU compliance      │               │                      │
└─────────────────────┘               └──────────────────────┘
```

## Batch-eligible vs Sequential

Two render paths exist. Their batch eligibility differs:

### Legacy per-shot (fully batch-able)
Every shot calls `client.video.generate()` independently. No shot depends on
a previous shot's output. The entire shot list can be submitted as one batch.

### Seamless extend-chain (partially batch-able)
- **First segment:** `client.video.generate()` — independent, batch-able
- **Extensions:** `client.video.extend(video_url=prev_url)` — each needs the
  previous segment's URL. Extensions are inherently sequential.

**Strategy for seamless:** Batch the first-segment generate. On collect, feed
the result URL into a sequential extend loop (real-time, 1 RPS). This still
saves the initial generate from rate-limit burn and gets reduced pricing on it.
Future: if xAI adds dependent-request chaining to batch, the full chain becomes
batch-able.

## JSONL Format (xAI Batch API spec)

Each line in the JSONL file:

```json
{"custom_id": "shot_b01", "method": "POST", "url": "/v1/videos/generations", "body": {"model": "grok-imagine-video-1.5", "prompt": "...", "duration": 8, "image": {"url": "https://..."}}}
```

For extensions:
```json
{"custom_id": "shot_b02_ext1", "method": "POST", "url": "/v1/videos/extensions", "body": {"model": "grok-imagine-video", "prompt": "...", "video": {"url": "https://..."}, "duration": 6}}
```

## Module: grok_batch_adapter.py

### Functions

```python
def pack_to_jsonl(
    imagine_pack: dict,
    output_path: Path,
    *,
    mode: str = "legacy",  # "legacy" | "seamless_first"
    model_override: str | None = None,
) -> Path:
    """Convert imagine_pack to xAI Batch API JSONL file.
    
    Legacy mode: one generate request per shot.
    Seamless_first mode: one generate request for first segment only.
    
    Returns path to written JSONL file.
    """

def submit_batch(
    jsonl_path: Path,
    batch_name: str,
    *,
    client: Any = None,
) -> str:
    """Submit JSONL to xAI Batch API. Returns batch_id.
    
    Uses xai_sdk.Client if provided, falls back to REST API.
    """

def poll_batch(
    batch_id: str,
    *,
    client: Any = None,
    interval_s: int = 30,
    timeout_s: int = 86400,
    callback: Callable | None = None,
) -> dict:
    """Poll batch status until complete or timeout.
    
    Returns final batch state dict with num_success, num_error, etc.
    Callback(state_dict) fires on each poll for progress reporting.
    """

def collect_results(
    batch_id: str,
    shots_dir: Path,
    *,
    client: Any = None,
    download: bool = True,
) -> dict[str, dict]:
    """Retrieve batch results, optionally download videos.
    
    Returns {custom_id: {"url": ..., "path": ..., "status": "succeeded"|"failed", "error": ...}}
    
    IMPORTANT: Video URLs expire after 1 hour. Downloads must happen
    promptly after collection.
    """

def rebatch_failures(
    results: dict[str, dict],
    imagine_pack: dict,
    output_path: Path,
    *,
    client: Any = None,
) -> str | None:
    """Re-submit failed shots as a new batch.
    
    Filters imagine_pack to only failed shot IDs, writes new JSONL,
    submits. Returns new batch_id or None if no failures.
    """

def batch_state_path(prod_dir: Path) -> Path:
    """Standard location for batch state file: prod_dir/batch_state.json"""
    return prod_dir / "batch_state.json"

def save_batch_state(prod_dir: Path, state: dict) -> None:
    """Persist batch_id, submission time, shot manifest, status."""

def load_batch_state(prod_dir: Path) -> dict | None:
    """Load saved batch state for --collect resume."""
```

### Batch State File

Written to `productions/<slug>/batch_state.json`:

```json
{
    "batch_id": "batch_abc123",
    "batch_name": "latin_video_v2",
    "submitted_at": "2026-06-30T22:15:00Z",
    "mode": "legacy",
    "model": "grok-imagine-video-1.5",
    "shot_count": 42,
    "shot_ids": ["b01", "b02", "b03", ...],
    "jsonl_path": "productions/latin_video/batch_requests.jsonl",
    "status": "submitted",
    "collected_at": null,
    "results_summary": null
}
```

## CLI Integration (render_longform.py)

### New flags

```
--batch              Submit all shots as a batch job (no real-time rendering).
                     Runs through script parse, ref resolution, QA pre-gates,
                     writes JSONL, submits batch, saves batch_state.json,
                     prints batch_id, exits.

--collect [BATCH_ID] Collect results from a completed batch. If BATCH_ID is
                     omitted, reads from batch_state.json in production dir.
                     Downloads videos, runs QA gates, concatenates final,
                     applies EU compliance label.

--batch-poll         After --batch submit, poll until complete instead of
                     exiting immediately. Prints progress every 30s.

--rebatch            After --collect, automatically re-submit any failed
                     shots as a new batch.
```

### --batch flow

```python
# In main():
if args.batch:
    # Everything up to pack assembly runs normally
    refs = resolve_refs(script, client=client)
    pack = build_imagine_pack(script, refs, seamless_opts)
    
    # Pre-render QA gates still fire (catch problems before wasting batch)
    assert_gate_0_cleared(script)
    # ... catalog continuity, ingest registry, etc.
    
    # Convert pack to JSONL
    mode = "seamless_first" if seamless_opts and seamless_opts.enabled else "legacy"
    jsonl_path = prod_dir / "batch_requests.jsonl"
    pack_to_jsonl(pack, jsonl_path, mode=mode)
    
    # Submit
    batch_id = submit_batch(jsonl_path, batch_name=slug, client=client)
    save_batch_state(prod_dir, {
        "batch_id": batch_id,
        "mode": mode,
        "shot_count": len(pack["shots"]),
        ...
    })
    
    print(f"Batch submitted: {batch_id}")
    print(f"State saved: {prod_dir / 'batch_state.json'}")
    
    if args.batch_poll:
        poll_batch(batch_id, client=client, callback=lambda s: print(f"  {s}"))
    
    return 0
```

### --collect flow

```python
if args.collect:
    batch_id = args.collect or load_batch_state(prod_dir)["batch_id"]
    
    results = collect_results(batch_id, shots_dir, client=client, download=True)
    
    succeeded = {k: v for k, v in results.items() if v["status"] == "succeeded"}
    failed = {k: v for k, v in results.items() if v["status"] == "failed"}
    
    if failed:
        print(f"[batch] {len(failed)} shots failed:")
        for sid, info in failed.items():
            print(f"  {sid}: {info['error']}")
        
        if args.rebatch:
            new_batch_id = rebatch_failures(results, pack, prod_dir / "rebatch.jsonl", client=client)
            print(f"Re-batched {len(failed)} failures: {new_batch_id}")
            return 0
    
    # From here, normal pipeline resumes:
    # - QA gates on downloaded shots
    # - Concatenation
    # - EU compliance label
    # - Package if --package
    rendered = [shots_dir / f"{sid}.mp4" for sid in pack_shot_order if sid in succeeded]
    # ... continue with existing concat + QA logic
```

## Edge Cases

1. **URL expiry:** Batch video URLs expire after 1 hour. `collect_results()` must
   download immediately. If a collect is interrupted, re-collect to get fresh URLs.

2. **Seamless extend after batch:** After collecting the first-segment generate from
   batch, the seamless extend loop runs in real-time (1 RPS). The batch saved the
   rate-limit budget for the generate; extends still hit the live API.

3. **Image uploads:** Some shots use `image_file_id` (uploaded composites) rather
   than `image_url`. These require the file to already be uploaded before batch
   submission. The `--batch` flow must run `upload_and_capture_id()` during the
   pre-submit phase and store the file_id/URL in the JSONL.

4. **Reference images:** Shots using `reference_image_file_ids` need those files
   uploaded before batch submission. Same pre-upload strategy.

5. **PromptDirector gates:** Still fire during `--batch` (before submission). A
   RED gate aborts before any batch is submitted.

6. **Mixed batches:** The xAI Batch API supports mixed endpoints in one JSONL.
   A single batch can contain generates AND extensions AND image generates.

## Dependencies

- `xai_sdk` (already in render_longform.py)
- `json`, `pathlib`, `datetime`, `time` (stdlib)
- No new external dependencies

## File Location

`DAVID/scripts/grok_batch_adapter.py` — alongside render_longform.py
