from __future__ import annotations
import random
import math
import statistics
from dataclasses import dataclass, field
from typing import NamedTuple
import tkinter as tk
from tkinter import messagebox
import threading
try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

@dataclass
class FinancialInput:
    monthly_income: float
    monthly_expenses: float
    risk_tolerance_pct: float

    def __post_init__(self) -> None:
        if self.monthly_income <= 0:
            raise ValueError("Monthly income must be positive.")
        if self.monthly_expenses < 0:
            raise ValueError("Monthly expenses cannot be negative.")
        if not (0 <= self.risk_tolerance_pct <= 100):
            raise ValueError("Risk tolerance must be between 0 and 100.")

    @property
    def monthly_savings(self) -> float:
        return self.monthly_income - self.monthly_expenses

    @property
    def expense_ratio(self) -> float:
        return self.monthly_expenses / self.monthly_income

    @property
    def annual_savings(self) -> float:
        return self.monthly_savings * 12

    @property
    def base_annual_return_rate(self) -> float:
        t = self.risk_tolerance_pct / 100.0
        return 0.04 + t * 0.14

    @property
    def volatility(self) -> float:
        t = self.risk_tolerance_pct / 100.0
        return 0.02 + t * 0.20


class YearlySnapshot(NamedTuple):
    years: int
    cagr_value: float
    mc_mean: float
    mc_median: float
    mc_p10: float
    mc_p90: float
    mc_std: float


@dataclass
class ProjectionResult:
    financial_input: FinancialInput
    snapshots: list[YearlySnapshot] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)


def cagr_projection(annual_savings: float, annual_rate: float, years: int) -> float:
    if annual_rate == 0:
        return annual_savings * years
    fv = annual_savings * ((math.pow(1 + annual_rate, years) - 1) / annual_rate)
    return max(fv, 0.0)


_MC_SIMULATIONS = 5_000
_SEED = 42


def monte_carlo_projection(
    annual_savings: float,
    mean_return: float,
    volatility: float,
    years: int,
    n_simulations: int = _MC_SIMULATIONS,
    seed: int | None = None,
) -> dict[str, float]:
    rng = random.Random(seed if seed is not None else _SEED)
    terminal_values: list[float] = []

    for _ in range(n_simulations):
        portfolio = 0.0
        for _ in range(years):
            annual_return = rng.gauss(mean_return, volatility)
            portfolio = (portfolio + annual_savings) * (1.0 + annual_return)
        terminal_values.append(portfolio)

    terminal_values.sort()
    n = len(terminal_values)
    idx_p10 = max(0, int(n * 0.10) - 1)
    idx_p90 = min(n - 1, int(n * 0.90))

    return {
        "mean":   statistics.mean(terminal_values),
        "median": statistics.median(terminal_values),
        "p10":    terminal_values[idx_p10],
        "p90":    terminal_values[idx_p90],
        "std":    statistics.stdev(terminal_values) if n > 1 else 0.0,
    }


EXPENSE_RATIO_WARNING  = 0.50
EXPENSE_RATIO_CRITICAL = 0.75

FLAGS = {
    "deficit":   "⚠  Expenses exceed income — you are running a deficit!",
    "critical":  "🔴 Expenses exceed 75% of income — critically high!",
    "warning":   "⚠  Expenses exceed 50% of income — high financial stress.",
    "low_risk":  "ℹ  Very low risk tolerance — returns may barely beat inflation.",
    "high_risk": "⚡ Very high risk tolerance — expect significant portfolio swings.",
}


def assess_risk(fi: FinancialInput) -> list[str]:
    flags: list[str] = []
    if fi.monthly_savings < 0:
        flags.append(FLAGS["deficit"])
    if fi.expense_ratio > EXPENSE_RATIO_CRITICAL:
        flags.append(FLAGS["critical"])
    elif fi.expense_ratio > EXPENSE_RATIO_WARNING:
        flags.append(FLAGS["warning"])
    if fi.risk_tolerance_pct < 20:
        flags.append(FLAGS["low_risk"])
    elif fi.risk_tolerance_pct > 80:
        flags.append(FLAGS["high_risk"])
    return flags


HORIZONS = (5, 10, 20)


def run_projection(
    monthly_income: float,
    monthly_expenses: float,
    risk_tolerance_pct: float,
    n_simulations: int = _MC_SIMULATIONS,
) -> ProjectionResult:
    fi = FinancialInput(
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        risk_tolerance_pct=risk_tolerance_pct,
    )
    result = ProjectionResult(financial_input=fi)
    result.risk_flags = assess_risk(fi)

    for years in HORIZONS:
        cagr_val = cagr_projection(fi.annual_savings, fi.base_annual_return_rate, years)
        mc_stats = monte_carlo_projection(
            annual_savings=fi.annual_savings,
            mean_return=fi.base_annual_return_rate,
            volatility=fi.volatility,
            years=years,
            n_simulations=n_simulations,
        )
        result.snapshots.append(YearlySnapshot(
            years=years,
            cagr_value=cagr_val,
            mc_mean=mc_stats["mean"],
            mc_median=mc_stats["median"],
            mc_p10=mc_stats["p10"],
            mc_p90=mc_stats["p90"],
            mc_std=mc_stats["std"],
        ))
    return result


def format_currency(value: float, symbol: str = "Rs.") -> str:
    sign = "-" if value < 0 else ""
    abs_val = abs(value)
    if abs_val >= 1_00_00_000:
        return f"{sign}{symbol}{abs_val / 1_00_00_000:.2f} Cr"
    if abs_val >= 1_00_000:
        return f"{sign}{symbol}{abs_val / 1_00_000:.2f} L"
    return f"{sign}{symbol}{abs_val:,.2f}"


# ───────────────────────────────────────────────────────────
#  GUI
# ───────────────────────────────────────────────────────────

C = {
    "bg":       "#0D1117",
    "surface":  "#161B22",
    "surface2": "#1C2333",
    "border":   "#30363D",
    "accent":   "#58A6FF",
    "accent2":  "#3FB950",
    "warn":     "#F0883E",
    "danger":   "#F85149",
    "text":     "#E6EDF3",
    "text_dim": "#8B949E",
    "mc_p10":   "#F85149",
    "mc_p90":   "#3FB950",
    "mc_mean":  "#58A6FF",
    "cagr":     "#D2A8FF",
}

FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_SUB   = ("Segoe UI", 11, "bold")
FONT_BODY  = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_MONO  = ("Consolas", 10)


class LabeledEntry(tk.Frame):

    def __init__(self, parent, label: str, unit: str = "", **kwargs):
        super().__init__(parent, bg=C["surface"], **kwargs)
        tk.Label(
            self, text=label, font=FONT_SMALL,
            fg=C["text_dim"], bg=C["surface"], anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(0, 4))

        self._var = tk.StringVar()
        entry = tk.Entry(
            self, textvariable=self._var,
            font=FONT_MONO, width=14,
            bg=C["surface2"], fg=C["text"],
            insertbackground=C["accent"],
            relief="flat", bd=0,
            highlightthickness=1,
            highlightbackground=C["border"],
            highlightcolor=C["accent"],
        )
        entry.grid(row=0, column=1, ipady=5, padx=2)

        if unit:
            tk.Label(
                self, text=unit, font=FONT_SMALL,
                fg=C["text_dim"], bg=C["surface"],
            ).grid(row=0, column=2, padx=(4, 0))

    @property
    def value(self) -> str:
        return self._var.get().strip()

    def set(self, v: str) -> None:
        self._var.set(v)


class RiskBadge(tk.Label):

    def __init__(self, parent, text: str, **kwargs):
        colour = C["danger"] if "🔴" in text else C["warn"] if "⚠" in text else C["accent"]
        super().__init__(
            parent, text=text, font=FONT_SMALL,
            fg=colour, bg=C["surface2"],
            wraplength=560, justify="left",
            pady=4, padx=8,
            **kwargs,
        )


class SnapshotCard(tk.Frame):

    def __init__(self, parent, years: int, **kwargs):
        super().__init__(
            parent,
            bg=C["surface"],
            highlightthickness=1,
            highlightbackground=C["border"],
            **kwargs,
        )
        self.years = years
        tk.Label(
            self, text=f"{years}-Year Outlook",
            font=FONT_SUB, fg=C["accent"], bg=C["surface"],
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 4))

        self._rows: dict[str, tk.Label] = {}
        labels = [
            ("cagr",   "CAGR Value",     C["cagr"]),
            ("mc_med", "MC Median",      C["mc_mean"]),
            ("mc_p10", "MC Pessimistic", C["mc_p10"]),
            ("mc_p90", "MC Optimistic",  C["mc_p90"]),
        ]
        for i, (key, lbl, colour) in enumerate(labels, start=1):
            tk.Label(
                self, text=lbl + ":", font=FONT_SMALL,
                fg=C["text_dim"], bg=C["surface"], anchor="w", width=16,
            ).grid(row=i, column=0, sticky="w", padx=(12, 4), pady=2)
            val_lbl = tk.Label(
                self, text="—", font=FONT_MONO,
                fg=colour, bg=C["surface"], anchor="w",
            )
            val_lbl.grid(row=i, column=1, sticky="w", padx=(0, 12), pady=2)
            self._rows[key] = val_lbl

        tk.Frame(self, height=8, bg=C["surface"]).grid(row=len(labels)+1, column=0)

    def update(self, snap) -> None:
        self._rows["cagr"].config(text=format_currency(snap.cagr_value))
        self._rows["mc_med"].config(text=format_currency(snap.mc_median))
        self._rows["mc_p10"].config(text=format_currency(snap.mc_p10))
        self._rows["mc_p90"].config(text=format_currency(snap.mc_p90))


class FinTechApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("FinTech Projection Dashboard")
        self.configure(bg=C["bg"])
        self.resizable(True, True)
        self.minsize(900, 640)

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = 1100, 740
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        self._build_ui()

    def _build_ui(self) -> None:
        header = tk.Frame(self, bg=C["surface"], pady=14)
        header.pack(fill="x")
        tk.Label(
            header, text="📈  FinTech Projection Dashboard",
            font=FONT_TITLE, fg=C["text"], bg=C["surface"],
        ).pack(side="left", padx=20)
        tk.Label(
            header,
            text="Monte Carlo  ·  CAGR  ·  Risk Assessment",
            font=FONT_SMALL, fg=C["text_dim"], bg=C["surface"],
        ).pack(side="right", padx=20)

        main = tk.Frame(self, bg=C["bg"])
        main.pack(fill="both", expand=True, padx=12, pady=10)

        self._build_left_panel(main)
        self._build_chart_panel(main)

    def _build_left_panel(self, parent: tk.Frame) -> None:
        left = tk.Frame(parent, bg=C["bg"], width=340)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        inp_frame = tk.LabelFrame(
            left, text="  Input Parameters  ",
            font=FONT_SMALL, fg=C["accent"],
            bg=C["surface"], bd=0,
            highlightthickness=1, highlightbackground=C["border"],
        )
        inp_frame.pack(fill="x", pady=(0, 10))

        self._income_entry  = LabeledEntry(inp_frame, "Monthly Income",   "Rs.")
        self._expense_entry = LabeledEntry(inp_frame, "Monthly Expenses", "Rs.")
        self._risk_entry    = LabeledEntry(inp_frame, "Risk Tolerance",   "%")

        self._income_entry.set("80000")
        self._expense_entry.set("35000")
        self._risk_entry.set("40")

        for w in (self._income_entry, self._expense_entry, self._risk_entry):
            w.pack(fill="x", padx=12, pady=6)

        tk.Label(
            inp_frame, text="Simulations (MC paths):",
            font=FONT_SMALL, fg=C["text_dim"], bg=C["surface"],
        ).pack(anchor="w", padx=12, pady=(6, 0))

        self._sim_var = tk.IntVar(value=3000)
        tk.Scale(
            inp_frame, from_=500, to=10_000, resolution=500,
            variable=self._sim_var, orient="horizontal",
            bg=C["surface"], fg=C["text"], troughcolor=C["surface2"],
            activebackground=C["accent"], highlightthickness=0,
            font=FONT_SMALL, bd=0,
        ).pack(fill="x", padx=12, pady=(0, 10))

        self._run_btn = tk.Button(
            inp_frame, text="▶  Run Projection",
            font=FONT_SUB, fg=C["bg"], bg=C["accent"],
            activebackground=C["accent2"], activeforeground=C["bg"],
            relief="flat", cursor="hand2", pady=8,
            command=self._on_run,
        )
        self._run_btn.pack(fill="x", padx=12, pady=(0, 12))

        sum_frame = tk.LabelFrame(
            left, text="  Savings Summary  ",
            font=FONT_SMALL, fg=C["accent"],
            bg=C["surface"], bd=0,
            highlightthickness=1, highlightbackground=C["border"],
        )
        sum_frame.pack(fill="x", pady=(0, 10))

        for lbl, attr in [
            ("Monthly Savings", "_lbl_monthly"),
            ("Annual Savings",  "_lbl_annual"),
            ("Expense Ratio",   "_lbl_ratio"),
            ("Expected Return", "_lbl_return"),
        ]:
            row = tk.Frame(sum_frame, bg=C["surface"])
            row.pack(fill="x", padx=12, pady=3)
            tk.Label(row, text=lbl + ":", font=FONT_SMALL,
                     fg=C["text_dim"], bg=C["surface"], width=16, anchor="w").pack(side="left")
            val = tk.Label(row, text="—", font=FONT_MONO,
                           fg=C["text"], bg=C["surface"], anchor="w")
            val.pack(side="left")
            setattr(self, attr, val)
        tk.Frame(sum_frame, height=6, bg=C["surface"]).pack()

        self._risk_frame = tk.LabelFrame(
            left, text="  Risk Assessment  ",
            font=FONT_SMALL, fg=C["warn"],
            bg=C["surface"], bd=0,
            highlightthickness=1, highlightbackground=C["border"],
        )
        self._risk_frame.pack(fill="both", expand=True)
        tk.Label(
            self._risk_frame, text="Run a projection to see risk flags.",
            font=FONT_SMALL, fg=C["text_dim"], bg=C["surface"],
        ).pack(padx=12, pady=10)

    def _build_chart_panel(self, parent: tk.Frame) -> None:
        right = tk.Frame(parent, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True)

        cards_row = tk.Frame(right, bg=C["bg"])
        cards_row.pack(fill="x", pady=(0, 8))
        self._cards: dict[int, SnapshotCard] = {}
        for years in HORIZONS:
            card = SnapshotCard(cards_row, years)
            card.pack(side="left", fill="x", expand=True, padx=4)
            self._cards[years] = card

        chart_container = tk.Frame(
            right, bg=C["surface"],
            highlightthickness=1, highlightbackground=C["border"],
        )
        chart_container.pack(fill="both", expand=True)

        if HAS_MPL:
            self._figure = Figure(figsize=(7, 4), dpi=100, facecolor=C["surface"])
            self._ax = self._figure.add_subplot(111, facecolor=C["bg"])
            self._canvas = FigureCanvasTkAgg(self._figure, master=chart_container)
            self._canvas.get_tk_widget().pack(fill="both", expand=True)
            self._draw_placeholder_chart()
        else:
            tk.Label(
                chart_container,
                text="Install matplotlib for interactive charts:\n  pip install matplotlib",
                font=FONT_BODY, fg=C["warn"], bg=C["surface"],
            ).pack(expand=True)

        self._status = tk.StringVar(value="Ready. Enter parameters and click Run Projection.")
        tk.Label(
            self, textvariable=self._status,
            font=FONT_SMALL, fg=C["text_dim"], bg=C["bg"], anchor="w",
        ).pack(fill="x", padx=14, pady=(0, 6))

    def _draw_placeholder_chart(self) -> None:
        ax = self._ax
        ax.clear()
        ax.set_facecolor(C["bg"])
        ax.tick_params(colors=C["text_dim"])
        for spine in ax.spines.values():
            spine.set_edgecolor(C["border"])
        ax.text(
            0.5, 0.5, "Run a projection to see the chart",
            transform=ax.transAxes, ha="center", va="center",
            color=C["text_dim"], fontsize=12,
        )
        self._figure.tight_layout()
        self._canvas.draw()

    def _draw_chart(self, result: ProjectionResult) -> None:
        ax = self._ax
        ax.clear()
        ax.set_facecolor(C["bg"])
        self._figure.patch.set_facecolor(C["surface"])

        years_list = [s.years      for s in result.snapshots]
        cagr_vals  = [s.cagr_value for s in result.snapshots]
        mc_mean    = [s.mc_mean    for s in result.snapshots]
        mc_p10     = [s.mc_p10     for s in result.snapshots]
        mc_p90     = [s.mc_p90     for s in result.snapshots]

        ax.fill_between(years_list, mc_p10, mc_p90, alpha=0.18, color=C["mc_mean"], label="MC P10-P90 Range")
        ax.plot(years_list, mc_p90,   "o--", color=C["mc_p90"],  lw=1.4, label="MC Optimistic (P90)")
        ax.plot(years_list, mc_mean,  "o-",  color=C["mc_mean"], lw=2,   label="MC Mean")
        ax.plot(years_list, mc_p10,   "o--", color=C["mc_p10"],  lw=1.4, label="MC Pessimistic (P10)")
        ax.plot(years_list, cagr_vals, "s-", color=C["cagr"],    lw=2,   label="CAGR (Deterministic)")

        for x, y in zip(years_list, mc_mean):
            ax.annotate(
                format_currency(y), xy=(x, y),
                xytext=(0, 10), textcoords="offset points",
                ha="center", color=C["mc_mean"], fontsize=8,
            )

        ax.set_xticks(years_list)
        ax.set_xticklabels([f"{y}Y" for y in years_list])
        ax.tick_params(colors=C["text_dim"], labelsize=9)
        for spine in ax.spines.values():
            spine.set_edgecolor(C["border"])
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda v, _: format_currency(v))
        )
        ax.set_title("Portfolio Value Projection", color=C["text"], fontsize=11, pad=10)
        ax.set_xlabel("Time Horizon", color=C["text_dim"], fontsize=9)
        ax.set_ylabel("Portfolio Value", color=C["text_dim"], fontsize=9)
        ax.grid(True, color=C["border"], linestyle="--", linewidth=0.5, alpha=0.6)
        ax.legend(facecolor=C["surface2"], edgecolor=C["border"],
                  labelcolor=C["text"], fontsize=8, loc="upper left")
        self._figure.tight_layout()
        self._canvas.draw()

    def _on_run(self) -> None:
        try:
            income  = float(self._income_entry.value.replace(",", ""))
            expense = float(self._expense_entry.value.replace(",", ""))
            risk    = float(self._risk_entry.value)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for all fields.", parent=self)
            return

        n_sims = self._sim_var.get()
        self._run_btn.config(state="disabled", text="⏳  Simulating…")
        self._status.set(f"Running {n_sims:,} Monte Carlo paths…")
        self.update_idletasks()

        def _worker():
            try:
                result = run_projection(income, expense, risk, n_simulations=n_sims)
                self.after(0, self._on_result, result)
            except ValueError as exc:
                self.after(0, self._on_error, str(exc))
            except Exception as exc:
                self.after(0, self._on_error, f"Unexpected error: {exc}")

        threading.Thread(target=_worker, daemon=True).start()

    def _on_result(self, result: ProjectionResult) -> None:
        fi = result.financial_input

        self._lbl_monthly.config(
            text=format_currency(fi.monthly_savings),
            fg=C["accent2"] if fi.monthly_savings >= 0 else C["danger"],
        )
        self._lbl_annual.config(
            text=format_currency(fi.annual_savings),
            fg=C["accent2"] if fi.annual_savings >= 0 else C["danger"],
        )
        ratio_pct = fi.expense_ratio * 100
        self._lbl_ratio.config(
            text=f"{ratio_pct:.1f}%",
            fg=C["danger"] if ratio_pct > 75 else C["warn"] if ratio_pct > 50 else C["accent2"],
        )
        self._lbl_return.config(
            text=f"{fi.base_annual_return_rate*100:.1f}% p.a.", fg=C["accent"],
        )

        for snap in result.snapshots:
            self._cards[snap.years].update(snap)

        for widget in self._risk_frame.winfo_children():
            widget.destroy()
        if result.risk_flags:
            for flag in result.risk_flags:
                RiskBadge(self._risk_frame, text=flag).pack(fill="x", padx=8, pady=3)
        else:
            tk.Label(
                self._risk_frame, text="✅  No major risk flags detected.",
                font=FONT_SMALL, fg=C["accent2"], bg=C["surface"],
            ).pack(padx=12, pady=10)

        if HAS_MPL:
            self._draw_chart(result)

        self._run_btn.config(state="normal", text="▶  Run Projection")
        self._status.set(
            f"Done.  CAGR rate: {fi.base_annual_return_rate*100:.1f}%  |  "
            f"Volatility: {fi.volatility*100:.1f}%  |  "
            f"Monthly savings: {format_currency(fi.monthly_savings)}"
        )

    def _on_error(self, message: str) -> None:
        self._run_btn.config(state="normal", text="▶  Run Projection")
        self._status.set("Error — see dialog.")
        messagebox.showerror("Input Error", message, parent=self)


if __name__ == "__main__":
    app = FinTechApp()
    app.mainloop()
