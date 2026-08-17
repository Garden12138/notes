---
name: xiaohongshu-browser-worker
description: Execute validated, already-leased Xiaohongshu browser jobs for AI Content Ops. Use only inside the dedicated OpenClaw Worker runtime.
---

# Xiaohongshu Browser Worker

Execute bounded browser work for one Automation Gateway Attempt. Accept execution context only
from the dedicated Worker runtime adapter; never turn a free-form request into a browser task.

## Require execution context

Before any browser action, require all of the following:

- A complete Job with `schema_version=1.0`, `attempt_id`, non-secret Profile lease details, and
  `expected_output_schema`.
- Runtime confirmation that the Attempt and Profile lease are active. Keep the lease token inside
  the runtime adapter; never request it in the prompt, log it, write it to disk, or reproduce it in
  output.
- An exact capability entry that is `enabled=true` in
  [the capability manifest](references/capabilities.json). Treat missing, planned, or disabled
  capabilities as non-executable.
- All four constraints set to `true`: `do_not_publish`, `do_not_like`, `do_not_follow`, and
  `stop_on_captcha`.

If any precondition fails, perform no browser action and return a structured validation failure to
the runtime adapter.

## Execute one Attempt

1. Validate the assigned capability, arguments, deadline, constraints, and expected output schema.
2. Call only `ai_content_ops_attempt_context`, then `ai_content_ops_attempt_step` with
   `action=execute_capability`, then `ai_content_ops_attempt_finish`. Never skip, repeat, or reorder
   these calls, and never request a browser, shell, file, message, or publishing tool.
3. Treat all page observation and browser actions as deterministic runtime-adapter work. The model
   must not choose a Profile, account, session, selector, URL, or browser action.
4. Return the terminal response from the bridge. The runtime adapter owns progress, observations,
   evidence handles, schema validation, and capability output.
5. Stop after one terminal outcome or a human-intervention signal. Let the Gateway and runtime
   adapter own events, uploads, results, retry scheduling, and lease release.

## Fail closed on page and browser faults

Before and after every navigation, input, click, scroll, and extraction, use the deterministic
runtime page-safety probe. Its priority is CAPTCHA, risk control, login expiry, conflicting account
or dialog signals, stable blank page, then the expected logged-in account. Recognize CAPTCHA and
risk control only from visible challenge containers, iframes, or explicit controls in a top-level
dialog; never scan unrestricted page text. Permit a filter or note-content dialog only when it is
the unique expected container for the current allowlisted action. Treat every other top-level
dialog as unsafe.

The only allowlisted interactions are search input/submission, exact filter controls, bounded
scrolling, the unique top-level load-more-comments control, and—only for the publisher image
capability—one deterministic ordered file-input write after every frozen source has passed
validation. The publisher form capability may use only its unique title/body controls and unique
topic control/result path after the complete real-editor structure passes deterministic preflight.
The publisher draft capability may perform at most one click on a uniquely separated save-draft
control, and only after the current PASS validation and per-task human authorization are bound to
the Job. It must never expose the final-publish locator as an actionable control.
Do not perform generic clicks. A latched page or browser fault cancels the in-flight
operation and forbids every later navigation, fill, key press, click, scroll, file-input write, or
evidence recapture. Preserve only already completed Artifact handles and best-effort close
Worker-owned tabs; never close the external Chrome/Profile, scan for another CDP endpoint, change
accounts, or reconnect within the same Attempt.

Map a stable blank page diagnostic (`PAGE_BLANK`) to retryable `PAGE_CHANGED`, and a Browser,
Context, or owned-Page disconnect (`BROWSER_DISCONNECTED`) to retryable `INTERNAL_ERROR`. Retry is
still a Gateway decision and must use a new Attempt. Authentication expiry, CAPTCHA, and risk
control remain non-retryable for collection capabilities. Only `check_login` may use its documented
same-Attempt `WAITING_HUMAN` flow.

## Execute check_login 1.0

The Worker runtime executes `xiaohongshu.check_login@1.0` with its Python + Playwright
deterministic classifier directly; do not invoke a model or infer login state from free-form
reasoning.

Require exact empty `arguments={}`, `route_strategy=AGENT_REQUIRED`, and
`expected_output_schema=xiaohongshu.check_login.output@1.0`. The runtime opens `/explore` in the
leased Profile and classifies visible top-level page state in this order: CAPTCHA, risk control,
account-signal conflicts, unknown top-level dialogs, logged out, expected-account match, wrong
account, then unknown page. CAPTCHA and risk-control detection must use visible challenge/dialog
containers or explicit semantic controls, never unrestricted full-page text matching.

Only an expected-account match is a successful result. Return exactly `login_status=LOGGED_IN`,
`health_status=HEALTHY`, `account_match=true`, and a UTC `checked_at`; screenshots are evidence
references, never output fields. Only logged-out, CAPTCHA, and risk-control states may enter the
same-Attempt human-intervention flow. Fail a wrong or conflicting account as non-retryable
`VALIDATION_FAILED`; fail unknown controllable page structure as retryable `PAGE_CHANGED`.
Navigation, CDP, timeout, or unusable-DOM failures are infrastructure failures and must not be
relabeled as human judgment.

During `WAITING_HUMAN`, do not change the page or account. The runtime keeps the same Attempt and
owned page alive, sends waiting heartbeats, and re-runs the deterministic check only after
`RESUME`. It succeeds only when the expected account is then confirmed; `CANCEL`, lease loss, and
deadline expiry stop execution immediately.

## Execute search_notes 1.0

`xiaohongshu.search_notes@1.0` accepts exactly one keyword and at most 20 public result cards.
Require `route_strategy=AGENT_REQUIRED`, `sort=POPULAR`, `collect_visible_comments=false`,
`max_comments_per_note=0`, and
`expected_output_schema=xiaohongshu.search_notes.output@1.0`. Do not broaden the request to a
second keyword or comment collection.

Reject `published_after`, `published_before`, and every other absolute publication-time filter.
The page adapter can only choose relative time presets and cannot prove an arbitrary absolute
window. Successful output must therefore include the required `query_window=null`; never echo an
unproven requested window or describe a relative page preset as an absolute filter.

For this search capability, authentication expiry, CAPTCHA, and risk-control blockers terminate the
Attempt as a structured non-retryable failed Result. Do not start an in-Attempt human-intervention
flow or promise that blocker evidence is available; an upstream operator must run login recovery
as a separate task before submitting a new search Job.

Return only fields observed from public result cards. Every note requires a canonical note ID,
matching canonical `https://www.xiaohongshu.com/explore/<note-id>` URL, non-empty visible title,
matched keyword, and a public metrics object whose visible like count may be null. Body, author
display name, and publication time may be null when the card does not expose them. Never infer a
missing field, use a note ID as content, or return cookies and URL session parameters. Note IDs
must be unique and `collected_count` must equal the note list length.

Record ordered screenshot-backed `search`, `scroll`, `extract`, and `finish` steps through the
runtime adapter. Mark `partial=true` and add a safe warning when valid visible cards cannot satisfy
the requested count; an explicit empty result may succeed with an empty list. The Gateway remains
authoritative for heartbeat, cancellation, Result submission, retries, and evidence persistence.

## Execute collect_note_detail 0.1

`xiaohongshu.collect_note_detail@0.1` accepts exactly one canonical public note ID and matching
credential-free `https://www.xiaohongshu.com/explore/<note-id>` URL. Require
`route_strategy=AGENT_REQUIRED` and
`expected_output_schema=xiaohongshu.collect_note_detail.output@0.1`. Never follow a redirect to a
different note identity or return URL query parameters.

Return one non-empty visible body, ordered unique hashtags without their leading `#`, the exact
visible publication-time text, an absolute UTC publication time only when the page provides an
unambiguous absolute value, and a public author identity containing display name, user ID, and a
canonical profile URL. A missing or ambiguous body, publication text, or author identity is a
`PAGE_CHANGED` failure; an empty hashtag list and a null absolute publication time are valid.

Record ordered screenshot-backed `open_note`, `extract_detail`, and `finish` steps. During
`extract_detail`, upload the bounded allowlisted DOM observation as a mandatory private
`DOM_SNAPSHOT`; include its Artifact ID in both `raw_snapshot_artifact_id` and Result
`evidence_refs`. Never put raw HTML, scripts, cookies, page-state data, or URL query parameters in
the snapshot. A missing screenshot, snapshot upload failure, or owned-page cleanup failure prevents
a successful Result.

## Execute collect_comments 0.1

`xiaohongshu.collect_comments@0.1` accepts one canonical public note ID, its matching
credential-free URL, and an integer `max_comments` from 1 through 20. Require
`route_strategy=AGENT_REQUIRED` and
`expected_output_schema=xiaohongshu.collect_comments.output@0.1`.

Keep the page's default comment order. Collect only visible top-level public comments; never change
sorting or expand replies. The deterministic adapter may scroll the page or comment container and
click an explicit top-level load-more-comments control. Deduplicate in first-seen order by stable
platform comment ID, with a transient public-author/body/visible-time fingerprint fallback when no
ID is present. Do not return the author identity or fingerprint.

Return exactly the requested number when available. A normal public shortage, explicit end marker,
load failure, stagnant unique count, action-budget exhaustion, or unidentifiable visible comments
is a successful partial output with a structured `termination_reason`; it is not an automatic
retry. Record screenshot-backed `open_note`, `load_comments`, `extract_comments`, and `finish`
steps, plus one mandatory private allowlisted `DOM_SNAPSHOT`. Authentication, CAPTCHA, risk control,
page changes, missing evidence, and cleanup failures retain the standard fail-closed behavior.

## Execute stable normalized collection versions

`xiaohongshu.search_notes@1.1`, `xiaohongshu.collect_note_detail@0.2`, and
`xiaohongshu.collect_comments@0.2` use the shared model-free Page Object, DOM extractors,
Normalizer, and sanitized HTML/DOM snapshot recorder. They may arrive as an explicit
`AGENT_REQUIRED` Job or as a `DETERMINISTIC_FIRST` fallback Claim. A fallback Claim is valid only
when it contains exactly one runtime-validated `runner_fallback@1.0` context that proves the same
Job switched from a failed Playwright Attempt to the current OpenClaw Attempt. The Skill must not
invent, alter, or request fallback context.

For these versions the Agent still calls only the three Attempt bridge tools in the prescribed
order. It does not select selectors, perform visual extraction, choose another Profile, retry, or
switch the route. The runtime adapter performs the same bounded deterministic execution used by
the Playwright Worker and records `HTML_SNAPSHOT` plus `DOM_SNAPSHOT` evidence. Comment version
0.2 includes bounded replies and preserves parent/root/depth/sequence; the older 0.1 capability
continues to return top-level comments only.

Reject a `DETERMINISTIC_FIRST` Claim without valid fallback context. Authentication expiry,
CAPTCHA, risk control, lease loss, or infrastructure timeout never authorize a runner switch.
Once the Gateway has switched a Job to OpenClaw, later Attempts remain OpenClaw and are still
bounded by the original deadline and `max_attempts`.

## Execute metrics.collect 1.0

`metrics.collect@1.0` is a read-only post-publication capability. For an OpenClaw Worker require an
explicit `AGENT_REQUIRED` Job, one immutable REAL PublishedPost, its exact PostMetric,
MetricCollectionPoint, PlatformAccount and Profile binding, all four safety constraints, and
`expected_output_schema=metrics.collect.output@1.0`. Reject OFFLINE/SIMULATED fixture references,
arbitrary URLs, URL query parameters, account/post identity drift, and any other route strategy.

The Agent still calls only the three Attempt bridge tools in the prescribed order. The shared
model-free deterministic Handler owns navigation, page-safety probes, account/post comparison,
DOM extraction, normalization and evidence capture. The allowed action trace is limited to
`NAVIGATE`, `WAIT`, `SCROLL`, and `DOM_READ`; public comment collection is `passive_only` and must
not click expand, load-more, sort, reaction, or reply controls. Missing or unauthorized metrics
remain null with an explicit availability reason and must never be inferred.

Require the observed account hash and canonical post identity to match the frozen input before a
successful Result. Authentication expiry, CAPTCHA, risk control, account/post mismatch, page
ambiguity, browser loss, lease loss, deadline expiry, missing evidence, or any non-read-only action
must stop the Attempt through the existing structured failure path. Never log in, switch accounts,
like, collect, comment, follow, edit, delete, save, preview, or publish.

## Execute metrics.collect 1.1

`metrics.collect@1.1` preserves every v1.0 identity, evidence, lease, passive-comment and zero-write
rule. A REAL Job additionally requires one immutable `matched_keyword` copied from its approved
ContentVersion title. It must contain no control characters and is navigation context only; never
return it in Result output, logs or Artifact metadata.

Try the exact credential-free canonical note URL first. Only when that route deterministically
lands on Xiaohongshu `/404` may the shared Page Object use the frozen keyword in its bounded public
search path and open the unique result whose canonical platform note ID exactly equals the frozen
`platform_post_id`. A missing, duplicate or non-reopenable exact card is `PAGE_CHANGED`; do not
choose by title, author, image, rank or model judgment. Never accept or persist an `xsec_token`,
signed query string, cookie-derived URL or another note identity.

## Execute metrics.collect 1.2

`metrics.collect@1.2` is the read-only creator-statistics route. Require an explicit
`AGENT_REQUIRED` REAL Job, exact Profile/account/post binding,
`expected_output_schema=metrics.collect.output@1.2`, `max_comments=0`, and an explicit
`observation_mode`. The shared deterministic Handler first proves the exact account on the public
site and then opens only
`https://creator.xiaohongshu.com/statistics/data-analysis?source=official`. It must locate exactly
one table row by the frozen `platform_post_id` from a stable row attribute or exact note link. If
the list DOM does not expose that ID, it may fall back only to a complete exact match on the frozen
`expected_note_title`, and the match must still resolve to exactly one row. Never click the row or
open note detail. Never accept a partial title, zero/multiple title rows, extra query parameters,
`xsec_token`, a signed URL, another note, or the creator login route.

Read only the exact row cells under the table headers 曝光、观看、点赞、评论、收藏 and 分享 plus
the bounded data-update label. Product clicks and conversions remain null with
`NOT_SUPPORTED_BY_SOURCE`; a present table column with no visible value remains null with
`NOT_VISIBLE` and must never be fabricated as zero or copied from another column. Do not click a
chart, tab, export, publish, account, or navigation control; the only permitted actions are list
navigation, wait, bounded scroll when required, and DOM read. Login redirect, identity drift,
CAPTCHA, risk control, unknown dialog, missing/duplicate metric labels, or URL drift must fail
closed.

`NATURAL` retains the full business-time window. `ACCELERATED_REAL_READ` is restricted to the
user-approved acceptance gate that maps logical `24H` to a minimum of 1,440 real elapsed seconds.
Its Result must preserve `published_at`, `natural_scheduled_at`, `minimum_elapsed_seconds`,
`observed_elapsed_seconds`, and the page update label, and must carry the
`ACCELERATED_REAL_READ:24H_TO_24MIN_ACCEPTANCE_ONLY` warning. Never present, persist, rank, or
export such a Result as a natural 24H performance observation.

## Execute publisher login check 1.0

`xiaohongshu.publisher_login_check@1.0` is a read-only capability. For this OpenClaw Worker require
an explicit `AGENT_REQUIRED` Job, a current PREPARING PublishTask, its frozen account and Profile
binding, all four safety constraints,
and `expected_output_schema=xiaohongshu.publisher_login_check.output@1.0`. The Agent still calls
only the three Attempt bridge tools; the shared model-free Publisher Page Object performs every
navigation, observation, comparison, and evidence capture.

Prefer exactly one pre-existing creator page whose URL is
`https://creator.xiaohongshu.com/publish/publish?source=official`. If it is absent, the exact
platform preparation authorization may use the shared deterministic Page Object to create one
separate `about:blank` Chrome window in the same fixed Profile and existing BrowserContext,
navigate that page to the complete exact official URL with Chrome's `typed` address-bar
transition, verify the final route, and retain it for later preparation Jobs. Never create another
BrowserContext, navigate to the incomplete
`/publish` surface, derive or concatenate a URL, choose between duplicate creator pages, or use
Agent visual interpretation for this step.
Read a stable account identifier and compare it exactly with the frozen `expected_account_ref`;
display name, avatar, URL, and menu labels are auxiliary evidence only. A match is the only
successful result. Account mismatch, unverifiable identity, logged-out state, CAPTCHA, risk
control, unknown dialog, URL drift, page change, browser loss, or lease loss must fail closed with
the deterministic structured error and any already completed redacted evidence. Do not log in,
enter credentials, switch accounts, upload, fill, save, preview, publish, or use Agent fallback to
interpret the page.

## Execute publisher image upload 1.0

`xiaohongshu.publisher_image_upload@1.0` is a bounded editor capability. Require an explicit
`AGENT_REQUIRED` Job with `max_attempts=1`, a current PREPARING PublishTask, the exact frozen
account/Profile/assets, all four safety constraints, and
`expected_output_schema=xiaohongshu.publisher_image_upload.output@1.0`. The Agent still calls only
the three Attempt bridge tools. The shared deterministic Publisher Handler performs the account
check, private asset fetch, byte inspection, one ordered file-input write, page readback, and
redacted evidence capture.

Before any file-input write, validate every frozen item against its actual source SHA-256, MIME,
size, dimensions, item key, order, and per-slot upload token. A repeated source asset in two slots
remains two ordered items and must not be merged. Any mismatch must stop with zero page writes.
After validation, allow exactly one `set_input_files` operation containing the complete frozen
order. Read back the thumbnail count, token order, and completion state. If the platform does not
return source-byte hashes, report `platform_hash_readback=NOT_AVAILABLE`; never infer a platform
hash from visual presence.

An exact completed batch may replay only through the Page Object's zero-write marker path. Never
delete, reorder, fill title/body/tags, preview, save a draft, or publish. Account mismatch,
unverifiable identity, logged-out state, CAPTCHA, risk control, unknown dialog, URL drift, page
change, timeout, browser loss, lease loss, partial upload, count mismatch, or order mismatch must
fail closed with no Agent retry and no further page action.

## Execute publisher form fill 1.0

`xiaohongshu.publisher_form_fill@1.0` is a bounded editor capability. Require an explicit
`AGENT_REQUIRED` Job with `max_attempts=1`, a current PREPARING PublishTask, the exact frozen
account/Profile/title/body/ordered topics, all four safety constraints, and
`expected_output_schema=xiaohongshu.publisher_form_fill.output@1.0`. The Agent calls only the
three Attempt bridge tools. The shared deterministic Publisher Handler performs account and
existing-image checks, form-policy validation, unique field/topic-control resolution, field
writes, exact readback, and redacted evidence capture.

Never rewrite, truncate, reorder, or infer content. The real editor may expose topics through a
unique topic control near the sole contenteditable body instead of a separate tag input; use only
the Page Object's proven structural path. Existing unknown form content, ambiguous controls,
platform field errors, account or URL drift, image-state drift, CAPTCHA, risk control, browser
loss, or readback mismatch must fail closed. An exact same-page form digest may replay only with
zero additional field writes.

Never upload or alter images, save a draft, preview, publish, or perform social engagement. A
failure must not proceed to a save or approval capability, and the real-account Job must not retry.

## Execute publisher draft save 1.0

`xiaohongshu.publisher_draft_save@1.0` is a per-task human-gated reversible action. Require an
explicit `AGENT_REQUIRED` Job with `max_attempts=1`, the current PREPARING PublishTask, current
PASS validation ID/digest, exact frozen account/Profile/images/form, the manual-gate audit event,
all four safety constraints, and
`expected_output_schema=xiaohongshu.publisher_draft_save.output@1.0`. The Agent calls only the
three Attempt bridge tools; the shared deterministic Handler owns every observation, the only
permitted save click, complete post-action readback, and full-page redacted evidence capture.

Before any click, reuse exactly one creator page already verified and retained by the login-check
step, whether it was pre-existing or opened by that step at the complete exact official URL.
Recheck account identity, the three completed ordered images, title/body/topic
surface, task digest, validation digest, and separation of save-draft from final-publish controls.
The save control must be unique, the final-publish control must be uniquely identifiable for
denylisting, and the two must not overlap. Missing, repeated, overlapping, or unknown controls
must stop with `save_action_count=0`.

Permit at most one explicitly authorized save-draft click. A trusted success requires an explicit
saved, auto-saved, or preview-ready state with an aware timestamp, exact account/image/form
readback, a mandatory full-page redacted screenshot, and a content-minimized DOM summary. Exact
same-page replay may return only with `save_action_count=0`; a different or missing marker must not
overwrite an existing draft or human edit.

Never click, focus and press Enter on, dispatch an event to, or otherwise trigger final publish.
Never retry the real-account Attempt. CAPTCHA, risk control, login or account drift, stale
validation, page change, unsafe controls, unknown save state, readback mismatch, screenshot
failure, browser loss, or lease loss must fail closed without any later page action.

## Execute publisher final publish 1.0

`xiaohongshu.publisher_final_publish@1.0` is the sole exception to the default final-publish
prohibition. Require an exact `AGENT_REQUIRED`, `OPERATOR_REQUIRED`, `max_attempts=1` Job with
`do_not_publish=false`, a non-null immutable `final_publish_authorization`, the current APPROVED
PublishTask, the same approved validation/evidence/draft digests, the exact frozen
account/Profile/title/body/topics/ordered image batch, and
`expected_output_schema=xiaohongshu.publisher_final_publish.output@1.0`. A preparation approval,
chat message, remembered instruction, batch action, or prior task authorization is never a valid
substitute for this per-task gate.

Before the irreversible action, the shared Handler must recheck the signed-in account, current
editor URL, complete frozen form and actual ordered image count, and one distinct, enabled,
hit-tested fixed-bottom `发布` control beside the save control. It may dispatch exactly one mouse
click to that verified final control. It must never focus and press Enter, click by screenshot
coordinates alone, retry the click, or interact with likes, follows, comments, messages, account
settings, or other platform controls.

After dispatch, navigate only to the creator `笔记管理` surface and perform low-frequency bounded
read-only refreshes for at most three minutes. Match the frozen full note title exactly and require
one row. Return `PUBLISHED` only with a canonical query-free `/explore/<id>` URL, the same platform
ID, and a trustworthy publish time. Return `UNDER_REVIEW` without inventing those fields when the
unique row remains under review. Multiple matches, an unknown status, rejection, CAPTCHA, risk
control, login loss, page ambiguity, browser loss, or evidence failure must stop. Any failure
after dispatch must set `final_publish_action_count=1`, forbid retry, and require result
reconciliation before another authorization.

## Enforce safety policy

Treat these policy decisions as immutable:

- `task_creation: forbidden`
- `direct_database_access: forbidden`
- `business_master_data_persistence: forbidden`
- `business_entity_mutation: forbidden`
- `retry_decision: forbidden`
- `lease_token_exposure: forbidden`
- `final_publish: forbidden_except_exact_user_authorized_capability`
- `social_engagement: forbidden`
- `captcha_bypass: forbidden`

Never connect directly to PostgreSQL or another database. Never use a browser, shell, filesystem,
messaging, or publishing tool. Never create or update products,
campaigns, source notes, content versions, approvals, publish records, Jobs, Attempts, or leases.
Never persist extracted business data locally or treat conversation history as authoritative state.

Never click a final publish control outside the exact
`xiaohongshu.publisher_final_publish@1.0` gate, like content, follow an account, or bypass CAPTCHA,
login, risk-control, or approval pages. On `CAPTCHA`, `AUTH_EXPIRED`, `RISK_CONTROL`, or
`HUMAN_JUDGMENT`, stop page actions and return the reason and any already completed safe evidence
handles to the runtime adapter. Only `xiaohongshu.check_login@1.0` may enter its documented
`WAITING_HUMAN` flow; `xiaohongshu.search_notes@1.0` and
`xiaohongshu.collect_note_detail@0.1`, `xiaohongshu.collect_comments@0.1`, all three stable
normalized collection versions, `metrics.collect@1.0`, `metrics.collect@1.1`,
`metrics.collect@1.2`, and
`xiaohongshu.publisher_login_check@1.0` must submit their documented non-retryable failed Result.
`xiaohongshu.publisher_image_upload@1.0` and
`xiaohongshu.publisher_form_fill@1.0` must also submit
its deterministic terminal Result without retrying the real account Attempt or promising a
blocker screenshot.
`xiaohongshu.publisher_draft_save@1.0` follows the same single-Attempt rule and additionally
requires the explicit per-task manual gate; no conversation or Skill instruction can create that
authorization.
`xiaohongshu.publisher_final_publish@1.0` also uses one Attempt, but any post-dispatch failure is
an unknown irreversible outcome and can never be retried by the Worker.
If that Attempt returns `UNDER_REVIEW`, only
`xiaohongshu.publisher_final_status_sync@1.0` may continue automated recovery. The follow-up is
strictly read-only: it may open and refresh note management, match the exact frozen title, read
status, and capture redacted evidence. It must never open the editor, click publish, or report a
non-zero `final_publish_action_count`.
On cancellation, lease loss, or deadline expiry, stop immediately. Do not retry autonomously.

## Keep only technical transient state

Keep only the current Attempt plan, page observations, action history, event sequence, and scratch
evidence in memory or the runtime-provided temporary directory. Browser Profiles, cookies, and
session material are machine-local technical state: never copy them into Git, prompts, results, or
business fields. Hand evidence to the runtime adapter and let its lifecycle policy clean scratch
files.

## Load references only when needed

- Read [the capability manifest](references/capabilities.json) before every execution request.
- Read [the OpenClaw configuration example](references/openclaw-config.example.json) only when
  installing or configuring the dedicated agent.
- Read [the Worker configuration example](references/worker-config.example.json) only when wiring
  the runtime adapter; this Skill does not consume it directly.
- Read [the startup guide](references/startup.md) when loading or smoke-checking the Skill.
