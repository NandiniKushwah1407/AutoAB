# locustfile.py — AutoAB Traffic Simulator
# ─────────────────────────────────────────────────────────────────────────────
# Simulates realistic users visiting Version A (control) and Version B
# (treatment) of the demo apps, firing events directly to the AutoAB backend.
#
# Prerequisites:
#   pip install locust requests
#
# Quick start:
#   # 1. Start the backend
#   docker compose -f ../docker-compose.yml up -d
#
#   # 2. Create an experiment and grab its UUID, then run:
#   EXPERIMENT_ID=<uuid> locust -f locustfile.py --headless \
#       -u 100 -r 10 --run-time 5m --host http://localhost:8000
#
#   # 3. Watch the AutoAB dashboard fill up with data!
#
# Environment variables:
#   EXPERIMENT_ID   (required) UUID of the running experiment
#   CONVERSION_RATE_A   control conversion rate   (default 0.08 = 8%)
#   CONVERSION_RATE_B   treatment conversion rate (default 0.12 = 12%)
#   AVG_SESSION_SEC     mean session length in sec (default 65)
# ─────────────────────────────────────────────────────────────────────────────

import os
import random
import time
import uuid
from datetime import datetime, timezone

from locust import HttpUser, TaskSet, task, between, events


# ── Configuration ────────────────────────────────────────────────────────────

EXPERIMENT_ID = os.environ.get("EXPERIMENT_ID", "REPLACE_WITH_EXPERIMENT_ID")

CONVERSION_RATE_A = float(os.environ.get("CONVERSION_RATE_A", "0.08"))   # 8%
CONVERSION_RATE_B = float(os.environ.get("CONVERSION_RATE_B", "0.12"))   # 12%

AVG_SESSION_SEC   = float(os.environ.get("AVG_SESSION_SEC", "65"))

DEVICES  = ["desktop", "mobile", "tablet"]
DEVICE_W = [0.60,       0.30,     0.10]

COUNTRIES = ["US", "GB", "IN", "CA", "DE", "FR", "AU", "BR"]

# Revenue distribution for Pro plan clicks (log-normal around $9)
PRO_PLAN_VALUE = 9.0


# ── Helpers ──────────────────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_session_id() -> str:
    return str(uuid.uuid4())


def random_device() -> str:
    return random.choices(DEVICES, weights=DEVICE_W, k=1)[0]


def random_country() -> str:
    return random.choice(COUNTRIES)


# ── Shared event builder ──────────────────────────────────────────────────────

def build_event(session_id: str, group: str, event_type: str, **kwargs) -> dict:
    """Build a single event payload matching the AutoAB EventPayload schema."""
    return {
        "experiment_id": EXPERIMENT_ID,
        "session_id":    session_id,
        "group":         group,
        "event_type":    event_type,
        "timestamp":     now_iso(),
        "value":         kwargs.get("value"),
        "duration":      kwargs.get("duration"),
        "scroll_depth":  kwargs.get("scroll_depth"),
        "device":        kwargs.get("device", random_device()),
        "country":       kwargs.get("country", random_country()),
        "metadata":      kwargs.get("metadata", {}),
    }


# ── Task Sets ─────────────────────────────────────────────────────────────────

class UserJourney(TaskSet):
    """
    Simulates one complete user session:
        page_view → scroll → (maybe click) → (maybe convert) → session_end
    """

    group: str          # set by parent User class
    conv_rate: float    # set by parent User class

    def on_start(self):
        self.session_id = make_session_id()
        self.device     = random_device()
        self.country    = random_country()
        self.session_start = time.time()

    # ── helpers ──

    def _post_batch(self, events: list[dict]):
        """Send a batch of events to the AutoAB backend."""
        with self.client.post(
            "/events/batch",
            json={"events": events},
            catch_response=True,
            name=f"[{self.group}] POST /events/batch",
        ) as resp:
            if resp.status_code not in (200, 201):
                resp.failure(f"Batch failed: {resp.status_code} {resp.text[:120]}")
            else:
                resp.success()

    def _ev(self, event_type: str, **kwargs) -> dict:
        return build_event(
            session_id=self.session_id,
            group=self.group,
            event_type=event_type,
            device=self.device,
            country=self.country,
            **kwargs,
        )

    # ── main task ──

    @task
    def full_session(self):
        events_to_send = []

        # ① Page view
        events_to_send.append(self._ev("page_view"))

        # ② Simulate reading time (0.5–4 s between events)
        time.sleep(random.uniform(0.3, 1.0))

        # ③ Scroll (most users scroll at least a bit)
        scroll_pct = random.betavariate(2, 1.5) * 100  # skewed toward middle
        events_to_send.append(self._ev("scroll_depth", scroll_depth=round(scroll_pct, 1)))

        # ④ CTA / link click (~55% of visitors)
        clicked = random.random() < 0.55
        if clicked:
            time.sleep(random.uniform(0.2, 0.8))
            events_to_send.append(self._ev("click", metadata={"element": "hero_cta"}))

        # ⑤ Rage-click (3% of sessions — frustrated users)
        if random.random() < 0.03:
            events_to_send.append(self._ev("rage_click", metadata={"element": "plan_pro_btn"}))

        # ⑥ Form submit (~20% of clickers)
        if clicked and random.random() < 0.20:
            time.sleep(random.uniform(1.0, 3.0))
            events_to_send.append(self._ev("form_submit", metadata={"form": "signup"}))

        # ⑦ Conversion — driven by configured rate
        converted = random.random() < self.conv_rate
        if converted:
            # Pro plan click → revenue event
            if random.random() < 0.35:
                value = PRO_PLAN_VALUE
                events_to_send.append(self._ev("plan_click", value=value, metadata={"plan": "pro"}))
            else:
                value = 0.0  # free tier signup
            events_to_send.append(self._ev("conversion", value=value))

        # ⑧ Session end (always fires)
        duration_sec = max(5.0, random.gauss(AVG_SESSION_SEC, 20))
        events_to_send.append(self._ev(
            "session_end",
            duration=round(duration_sec, 1),
            scroll_depth=round(scroll_pct, 1),
        ))

        # ── Send the whole session as one batch ──
        self._post_batch(events_to_send)

        # ── Pause between sessions (think time) ──
        time.sleep(random.uniform(0.5, 2.0))


# ── User classes ─────────────────────────────────────────────────────────────

class ControlUser(HttpUser):
    """Simulates a user seeing Version A (control — blue button)."""
    tasks = [UserJourney]
    wait_time = between(1, 4)
    weight = 50  # 50% of virtual users go to control

    def on_start(self):
        # Inject group & conversion rate into the task set
        for task_set in self.tasks:
            task_set.group     = "control"
            task_set.conv_rate = CONVERSION_RATE_A


class TreatmentUser(HttpUser):
    """Simulates a user seeing Version B (treatment — red button + urgency)."""
    tasks = [UserJourney]
    wait_time = between(1, 4)
    weight = 50  # 50% of virtual users go to treatment

    def on_start(self):
        for task_set in self.tasks:
            task_set.group     = "treatment"
            task_set.conv_rate = CONVERSION_RATE_B


# ── Locust event hooks ────────────────────────────────────────────────────────

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("\n" + "═" * 60)
    print("  AutoAB Traffic Simulator started")
    print(f"  Experiment ID : {EXPERIMENT_ID}")
    print(f"  Control rate  : {CONVERSION_RATE_A*100:.1f}%")
    print(f"  Treatment rate: {CONVERSION_RATE_B*100:.1f}%")
    print(f"  Avg session   : {AVG_SESSION_SEC:.0f}s")
    print("═" * 60 + "\n")

    if EXPERIMENT_ID == "REPLACE_WITH_EXPERIMENT_ID":
        print("⚠️  WARNING: EXPERIMENT_ID is not set!")
        print("   Events will be rejected by the backend.")
        print("   Run:  EXPERIMENT_ID=<uuid> locust -f locustfile.py ...\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n" + "═" * 60)
    print("  AutoAB simulation complete.")
    print("  Check your dashboard → GET /analysis/<experiment_id>/results")
    print("═" * 60 + "\n")
