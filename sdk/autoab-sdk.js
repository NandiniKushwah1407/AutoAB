/**
 * AutoAB Tracking SDK  v1.0
 * -----------------------------------------------------------
 * Drop this script onto any page to start tracking user events.
 *
 * Usage:
 *   <script src="http://localhost:8000/sdk/autoab-sdk.js"
 *           data-experiment-id="your-exp-id"
 *           data-group="control"
 *           data-api-base="http://localhost:8000">
 *   </script>
 *
 * Custom events from your app code:
 *   window.autoab.track("form_submit", { form_id: "checkout" });
 *   window.autoab.convert(79.99);   // Fire a conversion with revenue
 */

(function () {
  "use strict";

  // ── Read config from script tag ──────────────────────────────
  const script        = document.currentScript;
  const EXPERIMENT_ID = script.getAttribute("data-experiment-id");
  const GROUP         = script.getAttribute("data-group");          // "control" | "treatment"
  const API_BASE      = (script.getAttribute("data-api-base") || "http://localhost:8000").replace(/\/$/, "");
  const BATCH_MS      = parseInt(script.getAttribute("data-batch-interval") || "5000");

  if (!EXPERIMENT_ID || !GROUP) {
    console.warn("[AutoAB] ⚠️  Missing data-experiment-id or data-group. SDK inactive.");
    return;
  }

  // ── Session ID (persists for the browser session) ────────────
  const SESSION_KEY = `autoab_sid_${EXPERIMENT_ID}`;
  let sessionId = sessionStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = "s_" + Math.random().toString(36).slice(2, 9) + "_" + Date.now();
    sessionStorage.setItem(SESSION_KEY, sessionId);
  }

  const sessionStart = Date.now();
  let   eventQueue   = [];
  let   maxScroll    = 0;
  let   clickTimes   = [];

  // ── Helpers ──────────────────────────────────────────────────
  function getDevice() {
    const w = window.innerWidth;
    return w < 768 ? "mobile" : w < 1024 ? "tablet" : "desktop";
  }

  function getCountry() {
    try { return Intl.DateTimeFormat().resolvedOptions().timeZone.split("/")[0]; }
    catch (_) { return null; }
  }

  // ── Core: push an event to the queue ─────────────────────────
  function push(eventType, extras) {
    eventQueue.push(Object.assign({
      experiment_id: EXPERIMENT_ID,
      session_id:    sessionId,
      group:         GROUP,
      event_type:    eventType,
      page_url:      window.location.href,
      device:        getDevice(),
      country:       getCountry(),
      referrer:      document.referrer || null,
      timestamp:     new Date().toISOString(),
    }, extras || {}));
  }

  // ── Public API ───────────────────────────────────────────────
  window.autoab = {
    /** Track any custom event */
    track: function (eventType, data) { push(eventType, data); },

    /** Fire a conversion event (e.g. purchase, sign-up) */
    convert: function (value) { push("conversion", { value: value || null }); },

    /** Get current session ID */
    sessionId: function () { return sessionId; },
  };

  // ── Auto-track: Page View ────────────────────────────────────
  push("page_view");

  // ── Auto-track: Clicks ───────────────────────────────────────
  document.addEventListener("click", function (e) {
    const el = e.target.closest("button, a, [data-track]") || e.target;
    push("click", {
      element_id: el.id || el.getAttribute("data-track") || el.tagName.toLowerCase(),
    });
  }, true);

  // ── Auto-track: Scroll Depth ─────────────────────────────────
  window.addEventListener("scroll", function () {
    const scrollable = document.body.scrollHeight - window.innerHeight;
    if (scrollable > 0) {
      const depth = Math.round((window.scrollY / scrollable) * 100);
      if (depth > maxScroll) maxScroll = depth;
    }
  }, { passive: true });

  // ── Auto-track: Rage Clicks (frustration signal) ─────────────
  document.addEventListener("click", function () {
    const now = Date.now();
    clickTimes = clickTimes.filter(function (t) { return now - t < 1000; });
    clickTimes.push(now);
    if (clickTimes.length >= 3) {
      push("rage_click");
      clickTimes = [];
    }
  }, true);

  // ── Auto-track: Form Submits ─────────────────────────────────
  document.addEventListener("submit", function (e) {
    push("form_submit", {
      element_id: e.target.id || e.target.getAttribute("name") || "unknown_form",
    });
  }, true);

  // ── Auto-track: Session End (before unload) ──────────────────
  window.addEventListener("beforeunload", function () {
    push("session_end", {
      duration:     Math.round((Date.now() - sessionStart) / 1000),
      scroll_depth: maxScroll,
    });
    flush(true);  // synchronous send
  });

  // ── Flush queue to backend ───────────────────────────────────
  function flush(sync) {
    if (eventQueue.length === 0) return;
    var batch = eventQueue.slice();
    eventQueue = [];
    var body  = JSON.stringify({ events: batch });
    var url   = API_BASE + "/events/batch";

    if (sync && navigator.sendBeacon) {
      // sendBeacon works even during page unload
      navigator.sendBeacon(url, new Blob([body], { type: "application/json" }));
    } else {
      fetch(url, {
        method:    "POST",
        headers:   { "Content-Type": "application/json" },
        body:      body,
        keepalive: true,
      }).catch(function () {});  // Silent fail — don't disrupt the user
    }
  }

  // Flush every BATCH_MS milliseconds (default 5 seconds)
  setInterval(flush, BATCH_MS);

  console.log("[AutoAB] ✅ Tracking active | Experiment:", EXPERIMENT_ID, "| Group:", GROUP);

})();
