"""DataWorth KZ — financial engine for the Data Value Frontier (DVF).

Decision setting (behavioural scoring): for each existing card client the bank decides whether to
CONTINUE the credit line for the next period (approve) or FREEZE it (reject), using a PD model.

Per client i with exposure EAD_i, outcome y_i (1 = default next month), approved a_i ∈ {0,1}:
    profit_i = a_i * [ (1 - y_i) * m * EAD_i  -  y_i * LGD * EAD_i ]
    Π(S)     = Σ_i profit_i  -  N * c_op                         (model financial result)
    C(S)     = N * Σ_{g ∈ S \\ S0} c_g  +  λ * P(S) * N           (data acquisition/processing + privacy charge)
    V(S)     = Π(S) - Π(S0) - C(S)                               (net economic value of data set S)
EAD_i = max(BILL_AMT1_i, 0) + CCF * max(LIMIT_BAL_i - BILL_AMT1_i, 0)
Bayes threshold for a calibrated PD: approve iff PD_i < m / (m + LGD).
All monetary parameters are ASSUMPTIONS (scenario inputs), not measured facts.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np


@dataclass
class FinParams:
    margin: float = 0.10          # m: net margin on exposure over the horizon, if no default
    lgd: float = 0.75             # loss given default (unsecured cards)
    ccf: float = 0.50             # credit conversion factor for undrawn limit
    op_cost: float = 0.0          # c_op: operating cost per client (identical for all data sets)
    data_cost_bp: float = 0.0     # c_g: cost per extra data GROUP per client, in bp of mean EAD
    privacy_lambda_bp: float = 0.0  # λ: privacy charge per extra raw FIELD per client, bp of mean EAD

    def as_dict(self):
        return asdict(self)


def ead(limit_bal, bill_amt1, ccf):
    limit_bal, bill_amt1 = np.asarray(limit_bal, float), np.asarray(bill_amt1, float)
    drawn = np.clip(bill_amt1, 0, None)
    return drawn + ccf * np.clip(limit_bal - drawn, 0, None)


def bayes_threshold(p: FinParams) -> float:
    return p.margin / (p.margin + p.lgd)


def decision_profit(y, pd_hat, exposure, threshold, p: FinParams) -> dict:
    y, pd_hat, exposure = np.asarray(y), np.asarray(pd_hat), np.asarray(exposure)
    a = pd_hat < threshold
    good, bad = (y == 0), (y == 1)
    margin_income = p.margin * exposure[a & good].sum()
    realized_loss = p.lgd * exposure[a & bad].sum()
    model_ecl = float((pd_hat[a] * p.lgd * exposure[a]).sum())       # ECL = PD × LGD × EAD (model-based)
    missed_margin = p.margin * exposure[~a & good].sum()             # opportunity cost of wrong rejections
    avoided_loss = p.lgd * exposure[~a & bad].sum()
    n = len(y)
    pi = margin_income - realized_loss - n * p.op_cost
    return {"profit": float(pi), "profit_per_client": float(pi / n), "approval_rate": float(a.mean()),
            "bad_rate_approved": float(y[a].mean()) if a.any() else 0.0,
            "margin_income": float(margin_income), "realized_loss": float(realized_loss),
            "model_ecl_approved": model_ecl, "missed_margin_false_reject": float(missed_margin),
            "avoided_loss_true_reject": float(avoided_loss),
            "return_on_exposure": float(pi / exposure.sum()), "threshold": float(threshold)}


def best_threshold(y, pd_hat, exposure, p: FinParams, grid=None) -> float:
    grid = np.linspace(0.02, 0.80, 157) if grid is None else grid
    prof = [decision_profit(y, pd_hat, exposure, t, p)["profit"] for t in grid]
    return float(grid[int(np.argmax(prof))])


def profit_curve(y, pd_hat, exposure, p: FinParams, grid=None):
    """Vectorised Π(t) for every threshold t in grid (approve iff PD < t). Equivalent to
    calling decision_profit for each t, but O(n log n). Returns (grid, profits)."""
    grid = np.linspace(0.02, 0.80, 157) if grid is None else np.asarray(grid)
    y, pd_hat, exposure = np.asarray(y), np.asarray(pd_hat), np.asarray(exposure, float)
    order = np.argsort(pd_hat, kind="mergesort")
    contrib = np.where(y[order] == 0, p.margin * exposure[order], -p.lgd * exposure[order])
    cum = np.concatenate([[0.0], np.cumsum(contrib)])
    k = np.searchsorted(pd_hat[order], grid, side="left")   # number of clients with PD < t
    return grid, cum[k] - len(y) * p.op_cost


def best_threshold_fast(y, pd_hat, exposure, p: FinParams, grid=None) -> float:
    g, prof = profit_curve(y, pd_hat, exposure, p, grid)
    return float(g[int(np.argmax(prof))])


def data_cost_per_client(n_extra_groups: int, n_extra_fields: int, mean_ead: float, p: FinParams) -> float:
    return (n_extra_groups * p.data_cost_bp + n_extra_fields * p.privacy_lambda_bp) * 1e-4 * mean_ead


def net_value(profit_S, profit_S0, n_clients, n_extra_groups, n_extra_fields, mean_ead, p: FinParams) -> dict:
    c = data_cost_per_client(n_extra_groups, n_extra_fields, mean_ead, p) * n_clients
    gross = profit_S - profit_S0
    return {"gross_value": float(gross), "data_cost": float(c), "net_value": float(gross - c),
            "break_even_cost_per_client": float(gross / n_clients)}
