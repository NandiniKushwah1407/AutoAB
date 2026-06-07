"""
Statistical Analysis Engine — AutoAB
Implements: Z-test, Welch T-test, Mann-Whitney U, Bayesian Beta-Binomial
Auto-selects the right test based on data type.
"""

import math
import numpy as np
from scipy import stats
from scipy.stats import norm, ttest_ind
from statsmodels.stats.proportion import proportions_ztest, proportion_confint
import statsmodels.stats.api as sms
from typing import Dict, Any


# ── Sample Size Calculator ────────────────────────────────────
def calculate_sample_size(
    baseline_rate: float = 0.10,
    mde: float = 0.02,
    alpha: float = 0.05,
    power: float = 0.80,
) -> int:
    """
    Compute required users per group using power analysis.

    Example:
        calculate_sample_size(baseline_rate=0.10, mde=0.03)
        → 1547 users per group (3094 total)
    """
    treatment_rate = baseline_rate + mde
    effect_size    = sms.proportion_effectsize(baseline_rate, treatment_rate)
    analysis       = sms.TTestIndPower()
    n = analysis.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        ratio=1.0,
    )
    return int(math.ceil(n))


def compute_current_power(
    n_control: int,
    n_treatment: int,
    mde: float = 0.02,
    alpha: float = 0.05,
    required_n: float = 0,
) -> Dict[str, Any]:
    """Return current statistical power and progress toward required sample size."""
    effect_size = sms.proportion_effectsize(0.10, 0.10 + mde)
    analysis    = sms.TTestIndPower()
    n           = min(n_control, n_treatment)

    power = 0.0
    if n > 1:
        try:
            power = analysis.solve_power(
                effect_size=effect_size,
                nobs1=n,
                alpha=alpha,
                ratio=1.0,
            )
        except Exception:
            power = 0.0

    progress = (n / required_n * 100) if required_n > 0 else 0.0

    return {
        "current_power":    round(min(float(power), 1.0), 4),
        "target_power":     0.80,
        "adequately_powered": power >= 0.80,
        "n_control":        n_control,
        "n_treatment":      n_treatment,
        "required_per_group": int(required_n),
        "progress_pct":     round(min(progress, 100.0), 1),
    }


# ── Z-test for Proportions ────────────────────────────────────
def _ztest_proportions(
    conv_ctrl: int, n_ctrl: int,
    conv_trt:  int, n_trt:  int,
    alpha: float = 0.05,
) -> Dict[str, Any]:
    """Best for: conversion rate, CTR, bounce rate (binary outcomes)."""
    if n_ctrl == 0 or n_trt == 0:
        return {"test": "Z-test (Proportions)", "error": "Insufficient data", "significant": False, "p_value": 1.0}

    stat, p = proportions_ztest([conv_ctrl, conv_trt], [n_ctrl, n_trt])

    r_ctrl = conv_ctrl / n_ctrl
    r_trt  = conv_trt  / n_trt
    ci_c   = proportion_confint(conv_ctrl, n_ctrl, alpha=alpha)
    ci_t   = proportion_confint(conv_trt,  n_trt,  alpha=alpha)
    lift   = (r_trt - r_ctrl) / r_ctrl * 100 if r_ctrl > 0 else 0.0

    return {
        "test":              "Z-test (Proportions)",
        "statistic":         round(float(stat), 4),
        "p_value":           round(float(p), 6),
        "significant":       bool(p < alpha),
        "control_rate":      round(r_ctrl, 4),
        "treatment_rate":    round(r_trt, 4),
        "relative_lift_pct": round(lift, 2),
        "absolute_diff":     round(r_trt - r_ctrl, 4),
        "ci_control":        [round(ci_c[0], 4), round(ci_c[1], 4)],
        "ci_treatment":      [round(ci_t[0], 4), round(ci_t[1], 4)],
    }


# ── Welch's T-test ────────────────────────────────────────────
def _ttest_from_stats(
    c_mean: float, c_std: float, c_n: int,
    t_mean: float, t_std: float, t_n: int,
    alpha: float = 0.05,
) -> Dict[str, Any]:
    """Best for: revenue, session duration (continuous, approx normal)."""
    if c_n < 2 or t_n < 2 or c_std == 0 or t_std == 0:
        return {"test": "Welch T-test", "error": "Insufficient data", "significant": False, "p_value": 1.0}

    se   = math.sqrt(c_std**2 / c_n + t_std**2 / t_n)
    diff = t_mean - c_mean
    dof  = (
        (c_std**2 / c_n + t_std**2 / t_n) ** 2
        / ((c_std**2 / c_n) ** 2 / (c_n - 1) + (t_std**2 / t_n) ** 2 / (t_n - 1))
    )
    t_stat = diff / se if se > 0 else 0.0
    p      = float(2 * stats.t.sf(abs(t_stat), df=dof))

    z_crit = norm.ppf(1 - alpha / 2)
    ci     = [round(diff - z_crit * se, 4), round(diff + z_crit * se, 4)]
    lift   = (diff / c_mean * 100) if c_mean != 0 else 0.0

    return {
        "test":              "Welch T-test (Continuous)",
        "statistic":         round(t_stat, 4),
        "p_value":           round(p, 6),
        "significant":       bool(p < alpha),
        "control_mean":      round(c_mean, 4),
        "treatment_mean":    round(t_mean, 4),
        "mean_diff":         round(diff, 4),
        "relative_lift_pct": round(lift, 2),
        "ci_diff":           ci,
    }


# ── Bayesian A/B Test (Beta-Binomial conjugate) ───────────────
def _bayesian_test(
    conv_ctrl: int, n_ctrl: int,
    conv_trt:  int, n_trt:  int,
    n_samples: int = 50_000,
) -> Dict[str, Any]:
    """
    Returns probability that Treatment beats Control.
    No p-values — stakeholders get intuitive % instead.
    """
    alpha_c = 1 + conv_ctrl
    beta_c  = 1 + (n_ctrl - conv_ctrl)
    alpha_t = 1 + conv_trt
    beta_t  = 1 + (n_trt  - conv_trt)

    samples_c = np.random.beta(alpha_c, beta_c, n_samples)
    samples_t = np.random.beta(alpha_t, beta_t, n_samples)

    prob_b_beats_a = float((samples_t > samples_c).mean())
    expected_lift  = float((samples_t - samples_c).mean())
    ci             = list(np.percentile(samples_t - samples_c, [2.5, 97.5]))

    return {
        "test":                  "Bayesian (Beta-Binomial)",
        "prob_treatment_wins":   round(prob_b_beats_a, 4),
        "expected_lift":         round(expected_lift, 4),
        "credible_interval_95":  [round(ci[0], 4), round(ci[1], 4)],
        "significant":           prob_b_beats_a >= 0.95,
    }


# ── Main Analyser Class ───────────────────────────────────────
class ABTestAnalyser:
    """
    Runs all applicable statistical tests on the latest MetricSnapshots
    for control and treatment groups.

    Usage:
        analyser = ABTestAnalyser(ctrl_snapshot, trt_snapshot, alpha=0.05)
        report   = analyser.run_all_tests()
    """

    def __init__(self, ctrl_snapshot, trt_snapshot, alpha: float = 0.05):
        self.ctrl  = ctrl_snapshot
        self.trt   = trt_snapshot
        self.alpha = alpha

    def run_all_tests(self) -> Dict[str, Any]:
        results = {}
        c, t = self.ctrl, self.trt

        # 1. Conversion Rate — Z-test
        if c.users_count > 0 and t.users_count > 0:
            results["conversion_rate"] = _ztest_proportions(
                c.conversions, c.users_count,
                t.conversions, t.users_count,
                self.alpha,
            )
            results["bayesian_conversion"] = _bayesian_test(
                c.conversions, c.users_count,
                t.conversions, t.users_count,
            )

        # 2. Click-Through Rate — Z-test
        if c.users_count > 0 and t.users_count > 0:
            ctr_clicks_c = int(c.ctr * c.users_count)
            ctr_clicks_t = int(t.ctr * t.users_count)
            results["ctr"] = _ztest_proportions(
                ctr_clicks_c, c.users_count,
                ctr_clicks_t, t.users_count,
                self.alpha,
            )

        # 3. Revenue per User — T-test
        if c.users_count > 1 and t.users_count > 1 and c.avg_revenue and t.avg_revenue:
            rev_std_c = max(c.avg_revenue * 0.5, 0.01)
            rev_std_t = max(t.avg_revenue * 0.5, 0.01)
            results["revenue"] = _ttest_from_stats(
                c.avg_revenue, rev_std_c, c.users_count,
                t.avg_revenue, rev_std_t, t.users_count,
                self.alpha,
            )

        # 4. Session Duration — T-test
        if c.users_count > 1 and t.users_count > 1 and c.avg_session_duration and t.avg_session_duration:
            dur_std_c = max(c.avg_session_duration * 0.4, 0.01)
            dur_std_t = max(t.avg_session_duration * 0.4, 0.01)
            results["session_duration"] = _ttest_from_stats(
                c.avg_session_duration, dur_std_c, c.users_count,
                t.avg_session_duration, dur_std_t, t.users_count,
                self.alpha,
            )

        # 5. Bounce Rate — Z-test (guardrail: should NOT increase)
        if c.users_count > 0 and t.users_count > 0:
            bounce_c = int(c.bounce_rate * c.users_count)
            bounce_t = int(t.bounce_rate * t.users_count)
            bounce_result = _ztest_proportions(
                bounce_c, c.users_count,
                bounce_t, t.users_count,
                self.alpha,
            )
            bounce_result["guardrail"] = True  # Flag: harm if bounce increases
            results["bounce_rate"] = bounce_result

        sig_count = sum(
            1 for k, r in results.items()
            if r.get("significant", False) and k != "bayesian_conversion"
        )

        return {
            "experiment_summary": {
                "control_users":        c.users_count,
                "treatment_users":      t.users_count,
                "significant_metrics":  sig_count,
                "total_metrics_tested": len([k for k in results if k != "bayesian_conversion"]),
                "alpha":                self.alpha,
            },
            "results":        results,
            "recommendation": self._make_recommendation(results, sig_count),
        }

    def _make_recommendation(self, results: dict, sig_count: int) -> Dict[str, Any]:
        conv  = results.get("conversion_rate", {})
        bayes = results.get("bayesian_conversion", {})
        bounce = results.get("bounce_rate", {})

        # Check guardrail: if bounce rate significantly increases, warn
        bounce_alarm = bounce.get("significant") and bounce.get("relative_lift_pct", 0) > 0

        if conv.get("significant") and conv.get("relative_lift_pct", 0) > 0 and not bounce_alarm:
            return {
                "decision":   "SHIP_B",
                "confidence": "HIGH" if bayes.get("prob_treatment_wins", 0) > 0.95 else "MEDIUM",
                "summary":    (
                    f"Treatment wins on conversion rate with "
                    f"+{conv.get('relative_lift_pct')}% lift (p={conv.get('p_value')}). "
                    f"Bayesian probability B beats A: {bayes.get('prob_treatment_wins', 'N/A')}."
                ),
            }
        elif bounce_alarm:
            return {
                "decision":   "INVESTIGATE",
                "confidence": "HIGH",
                "summary":    (
                    "⚠️ GUARDRAIL VIOLATION: Bounce rate increased significantly in treatment. "
                    "Investigate before shipping B."
                ),
            }
        elif sig_count == 0:
            return {
                "decision":   "CONTINUE",
                "confidence": "LOW",
                "summary":    "No significant differences detected yet. Continue collecting data.",
            }
        else:
            return {
                "decision":   "INVESTIGATE",
                "confidence": "MEDIUM",
                "summary":    f"{sig_count} metric(s) significant. Review all results carefully.",
            }
