# -*- coding: utf-8 -*-
"""
Rich 스타일 인터랙티브 중고차 경매 프리토타입 (Terminal용) — v3
변경점 (v2 → v3):
  • 일정 종료 시 "최종 요약" 자동 출력
    - 초기(베이스라인) 최소비용 예상 vs 최종(실제 입력 기반) 예상 비교
    - 목표 달성 여부/미달·초과 대수
    - 총 예상 지출, 평균단가, 차이(원/%) 표시
  • 일자별 실제 입력 이력(매입대수/당일 기대단가/일자지출) 테이블 출력
  • v2의 "상한가 최소 스프레드(>= 시작가×(1+MIN_SPREAD))" 규칙 유지
변경점 (부대비용 및 순이익 계산 추가):
  • MIN_ADDITIONAL_COST_PER_UNIT: 대당 최소 부대비용(40만원) 추가
  • DEFAULT_SALE_MARGIN_PCT: 기대단가 대비 판매 마진율(기본 10%) 추가 (판매가 가정용)
  • 최종 요약 및 일자별 결과 테이블에 예상 순이익 및 수익률 계산/표시
변경점 (부대비용 상세 내역 표시):
  • 최종 요약에 부대비용 상세 내역(이전비, 상품화, 운송비)을 별도 테이블로 표시
변경점 (차량별 부대비용 표시):
  • 모든 계획/결과 테이블에 "대당 부대비용" 컬럼을 추가하여 각 차량의 부대비용을 명확히 표시
변경점 (변동 비율 적용):
  • 이전 등록비가 '차량가 기준 7% 내외'로 변경됨
  • 부대비용 및 판매 마진율을 커맨드라인 인자로 입력 가능
  • 이전비는 기대단가에 지정된 비율을 곱해 동적으로 계산되며, 이 값이 총 부대비용에 포함됨
"""
import sys, math, json, argparse, textwrap
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from rich import box

console = Console()

# ===== 기본 설정 =====
DEFAULT_TARGET = 10               # 주간 목표 수량
DEFAULT_BASE_PRICE = 1500.0       # (만원) 기대 단가 베이스
SUPPLY_SENSITIVITY = 0.08         # 공급 ↑ → 기대단가 ↓ 민감도
NOISE_SIGMA = 0.03                # 날짜별 가격 변동(표준편차, 비율)
GLOBAL_SEED = 42                  # 날짜별 가격 노이즈 재현성

# 시작가/상한가 정책 파라미터
OPEN_FACTOR = 0.97    # 기대단가 * OPEN_FACTOR = 시작가
MIN_SPREAD  = 0.01    # 상한가 >= 시작가 * (1 + MIN_SPREAD)

# ===== 추가된 비용 및 이익 계산 관련 기본값 설정 (이제 커맨드라인 인자로 변경 가능) =====
DEFAULT_REGISTRATION_TAX_RATE = 0.07 # 이전 등록비 비율 (차량가 기준 7%)
DEFAULT_COMMODITIZATION_COST  = 10.0  # (만원) 기본 상품화 (세차, 정비)
DEFAULT_TRANSPORTATION_COST   = 5.0   # (만원) 운송비
DEFAULT_SALE_MARGIN_PCT       = 0.10  # 판매 예상가 계산을 위한 기본 마진율 (기대단가의 10%)

DEFAULT_SCHEDULE = [
    ("2025-08-14", 2),
    ("2025-08-15", 1),
    ("2025-08-16", 4),
    ("2025-08-17", 6),
    ("2025-08-18", 3),
    ("2025-08-19", 5),
    ("2025-08-20", 3),
]

@dataclass
class DayInfo:
    idx: int
    date: str
    supply: int
    exp_price: float  # 기대단가(만원)
    open_bid: float   # 시작가(만원)
    cap_bid: float    # 상한가(만원)
    cap_from_spread: bool  # 최소 스프레드로 cap 결정 여부
    sale_price: float # 판매 예상가(만원)
    reg_cost: float   # 이전 등록비 (만원) - 동적으로 계산
    fixed_additional_cost: float # 상품화 + 운송비 (만원)
    total_additional_cost: float # 총 부대비용 (만원)

def _rng_for_day(idx: int):
    import random
    return random.Random(GLOBAL_SEED * 1000 + idx)

def expected_price(base: float, supply: int, max_supply: int, idx: int) -> float:
    """공급 로그스케일 하향 + 날짜 고정 노이즈"""
    base_adj = base * (1 - SUPPLY_SENSITIVITY * math.log(1 + supply) / math.log(1 + max_supply))
    noise = _rng_for_day(idx).gauss(0, NOISE_SIGMA)
    price = base_adj * (1 + noise)
    return round(price, 1)

def pressure_cap_multiplier(fill_ratio: float) -> float:
    """남은 목표/공급 비율에 따른 상한가 계수"""
    if fill_ratio < 0.45:
        return 0.97
    elif fill_ratio < 0.60:
        return 1.00
    elif fill_ratio < 0.75:
        return 1.05
    else:
        return 1.10

def build_day_infos(schedule: List[Tuple[int, str, int]], base_price: float, cap_mult: float, sale_margin_pct: float,
                    reg_tax_rate: float, fixed_comm_cost: float, fixed_trans_cost: float) -> List[DayInfo]:
    max_supply = max(s for _, _, s in schedule) if schedule else 1
    infos: List[DayInfo] = []
    for idx, date, s in schedule:
        p = expected_price(base_price, s, max_supply, idx)
        open_bid = round(p * OPEN_FACTOR, 1)
        cap_raw = p * cap_mult
        cap_floor = open_bid * (1 + MIN_SPREAD)
        cap_bid_val = cap_raw if cap_raw >= cap_floor else cap_floor
        cap_bid = round(cap_bid_val, 1)
        sale_price = round(p * (1 + sale_margin_pct), 1) # 기대단가에 마진율을 더해 판매 예상가 계산

        # 동적으로 이전 등록비 계산 및 총 부대비용 산출
        reg_cost = round(p * reg_tax_rate, 1)
        fixed_additional_cost = fixed_comm_cost + fixed_trans_cost
        total_additional_cost = reg_cost + fixed_additional_cost
        
        infos.append(DayInfo(
            idx, date, s, p, open_bid, cap_bid,
            cap_from_spread=(cap_bid_val==cap_floor),
            sale_price=sale_price,
            reg_cost=reg_cost,
            fixed_additional_cost=fixed_additional_cost,
            total_additional_cost=total_additional_cost
        ))
    return infos

def greedy_min_cost_plan(day_infos: List[DayInfo], target_units: int) -> Dict[str, int]:
    """기대단가가 싼 날부터 채우는 최소비용 그리디"""
    order = sorted(day_infos, key=lambda d: d.exp_price)
    remaining = target_units
    plan: Dict[str, int] = {d.date: 0 for d in day_infos}
    for d in order:
        if remaining <= 0:
            break
        buy = min(d.supply, remaining)
        plan[d.date] = buy
        remaining -= buy
    return plan

def summarize(day_infos: List[DayInfo], plan: Dict[str, int]) -> Dict[str, float]:
    total_units = sum(plan.values())
    spend = 0.0
    total_profit = 0.0 # 총 예상 순이익
    for d in day_infos:
        qty = plan.get(d.date, 0)
        spend += qty * d.exp_price
        # 예상 순이익 = (판매 예상가 - 기대단가 - 대당 총 부대비용) * 수량
        profit_per_unit = d.sale_price - d.exp_price - d.total_additional_cost
        total_profit += qty * profit_per_unit

    avg_price = spend / total_units if total_units else 0.0
    avg_profit_per_unit = total_profit / total_units if total_units else 0.0
    avg_roi = (total_profit / spend * 100.0) if spend else 0.0 # 투자 수익률 (ROI)

    return {
        "units": total_units,
        "spend": round(spend, 1),
        "avg_price": round(avg_price, 1),
        "total_profit": round(total_profit, 1),
        "avg_profit_per_unit": round(avg_profit_per_unit, 1),
        "avg_roi": round(avg_roi, 1),
    }

def fmt_money(x: float) -> str:
    return f"{x:,.1f}"

def risk_level_and_tips(fill_ratio: float, days_left: int):
    if fill_ratio < 0.45:
        return ("낮음", "green", [
            "- 시작가 유지, 상한가 보수적(가격 규율).",
            "- 컨디션 상위 위주 선별 입찰.",
        ])
    elif fill_ratio < 0.60:
        return ("보통", "yellow3", [
            "- 상한가 0~2% 상향 검토(단계적).",
            "- 동일 트림/연식 내 대체 옵션 확대.",
        ])
    elif fill_ratio < 0.75:
        return ("높음", "dark_orange", [
            "- 상한가 3~5% 상향, 인기 사양 프리미엄 허용.",
            "- 외부 소싱(직거래/제휴딜러) 병행.",
            "- 미달 시 다음날 조기입찰(프리바이).",
        ])
    else:
        return ("매우 높음", "red", [
            "- 상한가 7~10% 상향, 즉시낙찰 옵션 검토.",
            "- 차종/연식 대체(동급 준중형) 허용.",
            "- 다음주 차입(rollover) 및 인도 일정 커뮤니케이션.",
        ])

def render_plan_table(title: str, day_infos: List[DayInfo], plan: Dict[str, int]):
    table = Table(title=title, title_style="bold cyan", box=box.SIMPLE_HEAVY)
    table.add_column("날짜", style="bold")
    table.add_column("매물수", justify="right")
    table.add_column("계획수량", justify="right", style="bold")
    table.add_column("기대단가(만)", justify="right", style="cyan")
    table.add_column("시작가(만)", justify="right")
    table.add_column("상한가(만)", justify="right", style="bright_yellow")
    table.add_column("판매 예상가(만)", justify="right", style="green")
    table.add_column("대당 부대비용(만)", justify="right", style="dim")
    table.add_column("대당 순이익(만)", justify="right", style="magenta")
    table.add_column("일자 예상지출(만)", justify="right", style="magenta")

    for d in day_infos:
        qty = plan.get(d.date, 0)
        day_spend = round(qty * d.exp_price, 1)
        profit_per_unit = d.sale_price - d.exp_price - d.total_additional_cost
        day_profit = round(qty * profit_per_unit, 1)

        cap_style = "bright_yellow"
        cap_val = fmt_money(d.cap_bid)
        if d.cap_from_spread:
            cap_val = f"{cap_val}*"
            cap_style = "yellow3"
        table.add_row(
            d.date, f"{d.supply}", f"{qty}",
            fmt_money(d.exp_price),
            fmt_money(d.open_bid),
            f"[{cap_style}]{cap_val}[/]",
            fmt_money(d.sale_price),
            fmt_money(d.total_additional_cost), # 대당 총 부대비용 표시
            fmt_money(profit_per_unit),
            fmt_money(day_spend),
        )

    summ = summarize(day_infos, plan)
    table.add_section()
    table.add_row(
        "[b]합계[/b]",
        f"{sum(d.supply for d in day_infos)}",
        f"{summ['units']}",
        "",
        "",
        "",
        "",
        "",
        fmt_money(summ['total_profit']),
        fmt_money(summ["spend"]),
        end_section=True
    )
    caption = (
        f"평균단가(만): [b]{fmt_money(summ['avg_price'])}[/b]  |  "
        f"총 예상 순이익(만): [b]{fmt_money(summ['total_profit'])}[/b]  |  "
        f"평균 ROI: [b]{fmt_money(summ['avg_roi'])}%[/b]  |  "
        f"[dim]* 상한가가 최소 스프레드 규칙으로 결정됨[/dim]"
    ) if summ["units"] > 0 else "[dim]* 상한가가 최소 스프레드 규칙으로 결정될 수 있습니다[/dim]"
    table.caption = caption
    console.print(table)

def render_risk(fill_ratio: float, days_left: int):
    level, color, tips = risk_level_and_tips(fill_ratio, days_left)
    body = "[b]리스크:[/b] [bold {}]{}[/]  (남은 일수: {})\n{}".format(
        color, level, days_left, "\n".join(tips)
    )
    console.print(Panel(body, title="리스크/대비책", border_style=color))

class AuctionCLI:
    def __init__(self, target:int, base_price:float, schedule_pairs: List[Tuple[str,int]],
                 reg_rate: float, comm_cost: float, trans_cost: float, sale_margin: float):
        self.schedule_full = [(i, d, s) for i, (d, s) in enumerate(schedule_pairs)]
        self.base_price = base_price
        self.target_total = target
        self.bought: Dict[str, int] = {}
        self.cursor = 0
        self.history: List[Dict] = []
        
        # 비용 및 마진율 변수화
        self.reg_rate = reg_rate
        self.comm_cost = comm_cost
        self.trans_cost = trans_cost
        self.sale_margin = sale_margin
        
        # 초기 베이스라인(전체 기간 기준 최소비용 예상) 계산/저장
        total_supply = sum(s for _, _, s in self.schedule_full) or 1
        init_fill = self.target_total / total_supply
        cap_mult_init = pressure_cap_multiplier(init_fill)
        self.baseline_infos = build_day_infos(
            self.schedule_full, self.base_price, cap_mult_init, self.sale_margin,
            self.reg_rate, self.comm_cost, self.trans_cost
        )
        self.baseline_plan  = greedy_min_cost_plan(self.baseline_infos, self.target_total)
        self.baseline_summ  = summarize(self.baseline_infos, self.baseline_plan)

    def fmt_header(self, title="현재 계획"):
        total_bought = sum(self.bought.values())
        remain_target = max(0, self.target_total - total_bought)
        summary = f"누적 매입: [bold]{total_bought}대[/] / 목표: [bold]{self.target_total}대[/] / 남은 목표: [bold]{remain_target}대[/]"
        console.print(Panel(summary, title=title, border_style="cyan"))

    def remaining(self):
        total_bought = sum(self.bought.values())
        remain_target = max(0, self.target_total - total_bought)
        remain_schedule = self.schedule_full[self.cursor:]
        return total_bought, remain_target, remain_schedule

    def plan_for(self, remain_schedule, remain_target):
        cap_mult = pressure_cap_multiplier(
            (remain_target / max(1, sum(s for _, _, s in remain_schedule))) if remain_schedule else 1.0
        )
        infos = build_day_infos(
            remain_schedule, self.base_price, cap_mult, self.sale_margin,
            self.reg_rate, self.comm_cost, self.trans_cost
        )
        plan = greedy_min_cost_plan(infos, remain_target)
        return infos, plan

    def show_state(self, title="현재 계획"):
        total_bought, remain_target, remain_schedule = self.remaining()
        infos, plan = self.plan_for(remain_schedule, remain_target)
        self.fmt_header(title)
        if remain_schedule:
            render_plan_table(f"남은 기간 계획 (다음 {len(remain_schedule)}일)", infos, plan)
            fill_ratio = (remain_target / max(1, sum(d.supply for d in infos))) if infos else 1.0
            render_risk(fill_ratio, days_left=len(infos))
        else:
            if remain_target > 0:
                console.print(Panel("[red][b]경고[/b][/red] 일정 종료. 목표 미달입니다.", border_style="red"))
            else:
                console.print(Panel("✅ 목표 달성! 수고했습니다.", border_style="green"))

    def step(self, user_input: Optional[str] = None):
        if self.cursor >= len(self.schedule_full):
            console.print(Rule("[bold]일정 종료[/bold]"))
            self.show_state("최종 결과")
            self.print_final_summary()
            return False

        idx, date, supply = self.schedule_full[self.cursor]
        remain_schedule = self.schedule_full[self.cursor:]
        total_bought, remain_target, _ = self.remaining()
        infos, plan = self.plan_for(remain_schedule, remain_target)
        today_info = next(d for d in infos if d.date == date)

        # 오늘 안내
        body = (
            f"[b]{date}[/b]\n"
            f"매물수: [bold]{supply}대[/]\n"
            f"권장 시작가: [bold cyan]{fmt_money(today_info.open_bid)}만[/]  "
            f"상한가: [bold yellow]{fmt_money(today_info.cap_bid)}만[/]  "
            f"기대단가: {fmt_money(today_info.exp_price)}만\n"
            f"예상 판매가: [bold green]{fmt_money(today_info.sale_price)}만[/]  "
            f"(남은 목표 [bold]{remain_target}대[/] / 남은 공급 [bold]{sum(s for _,_,s in remain_schedule)}대[/])\n\n"
            "[dim]입력: 0~매물수, plan, undo, help, quit[/dim]"
        )
        console.print(Rule())
        console.print(Panel(body, title="오늘 진행", border_style="white"))

        if user_input is None:
            try:
                user_input = console.input("[bold]> [/]")
            except (EOFError, KeyboardInterrupt):
                user_input = "quit"

        cmd = (user_input or "").strip()

        if cmd.lower() in ("help", "h", "?"):
            help_text = textwrap.dedent(f"""
            사용법:
              • 0~{supply} : 오늘 실제 매입 대수 입력
              • plan       : 현재 남은 기간 최소비용 계획/리스크 다시 보기
              • undo       : 직전 일자 입력 취소(한 단계 되돌리기)
              • quit       : 즉시 종료(현재까지 요약 표시)
            """).strip()
            console.print(Panel(help_text, title="도움말", border_style="blue"))
            return True

        if cmd.lower() in ("plan", "p"):
            self.show_state("즉시 재계획 미리보기")
            return True

        if cmd.lower() in ("undo", "u"):
            if self.cursor == 0:
                console.print(Panel("되돌릴 이전 입력이 없습니다.", border_style="yellow"))
                return True
            self.cursor -= 1
            _, prev_date, _ = self.schedule_full[self.cursor]
            if prev_date in self.bought:
                del self.bought[prev_date]
            self.history = [h for h in self.history if h["date"] != prev_date]
            self.show_state("한 단계 되돌림")
            return True

        if cmd.lower() in ("quit", "q"):
            console.print(Panel("사용자에 의해 중단되었습니다.", border_style="yellow"))
            self.show_state("중간 결과")
            self.print_final_summary(final=False)
            return False

        try:
            n = int(cmd)
        except ValueError:
            console.print(Panel("알 수 없는 명령입니다. help 를 입력해 보세요.", border_style="yellow"))
            return True

        if not (0 <= n <= supply):
            console.print(Panel(f"유효하지 않은 매입 대수입니다. 0~{supply} 사이로 입력하세요.", border_style="yellow"))
            return True

        self.bought[date] = n
        self.history.append({
            "date": date,
            "supply": supply,
            "bought": n,
            "exp_price": today_info.exp_price,
            "open_bid": today_info.open_bid,
            "cap_bid": today_info.cap_bid,
            "sale_price": today_info.sale_price,
            "total_additional_cost": today_info.total_additional_cost
        })
        self.cursor += 1
        self.show_state(f"{date} 입력 반영")

        if self.cursor >= len(self.schedule_full):
            console.print(Rule("[bold]모든 날짜 입력 완료[/bold]"))
            self.show_state("최종 결과")
            self.print_final_summary()
            return False
        return True

    def print_final_summary(self, final:bool=True):
        b = self.baseline_summ
        base_units, base_spend, base_avg = b["units"], b["spend"], b["avg_price"]
        base_total_profit = b["total_profit"]
        base_avg_roi = b["avg_roi"]

        total_units = sum(h["bought"] for h in self.history)
        total_spend = sum(h["bought"] * h["exp_price"] for h in self.history)
        avg_price = (total_spend / total_units) if total_units else 0.0

        actual_total_profit = sum(h["bought"] * (h["sale_price"] - h["exp_price"] - h["total_additional_cost"]) for h in self.history)
        actual_avg_profit_per_unit = (actual_total_profit / total_units) if total_units else 0.0
        actual_avg_roi = (actual_total_profit / total_spend * 100.0) if total_spend else 0.0

        target = self.target_total
        delta_units = total_units - target
        achieved = total_units >= target

        spend_diff = base_spend - total_spend
        spend_diff_pct = (spend_diff / base_spend * 100.0) if base_spend else 0.0

        profit_diff = actual_total_profit - base_total_profit
        profit_diff_pct = (profit_diff / base_total_profit * 100.0) if base_total_profit else 0.0

        title = "최종 요약" if final else "중간 요약"
        border = "green" if achieved else "red"
        status = "✅ 목표 달성" if achieved else "⚠️ 목표 미달"
        body = (
            f"[b]{status}[/b]\n"
            f"- 목표: [b]{target}대[/], 결과: [b]{total_units}대[/]  "
            f"({'+' if delta_units>=0 else ''}{delta_units}대)\n"
            f"- 초기 최소비용 예상 지출: [bold cyan]{base_spend:,.1f}만[/]  "
            f"(평균 {base_avg:,.1f}만)  "
            f"[dim]→ 예상 순이익: {fmt_money(base_total_profit)}만 (ROI: {fmt_money(base_avg_roi)}%)[/dim]\n"
            f"- 최종(입력기반) 예상 지출: [bold magenta]{total_spend:,.1f}만[/]  "
            f"(평균 {avg_price:,.1f}만)  "
            f"[dim]→ 예상 순이익: {fmt_money(actual_total_profit)}만 (ROI: {fmt_money(actual_avg_roi)}%)[/dim]\n"
            f"- 지출 차이(초기→최종): [bold]{spend_diff:,.1f}만[/] "
            f"({spend_diff_pct:+.1f}%)  "
            f"[dim]양수=절감, 음수=증가[/dim]\n"
            f"- 순이익 차이(초기→최종): [bold]{profit_diff:,.1f}만[/] "
            f"({profit_diff_pct:+.1f}%)  "
            f"[dim]양수=증가, 음수=감소[/dim]\n"
        )
        console.print(Panel(body, title=title, border_style=border))

        table = Table(title="일자별 결과(입력 기준)", box=box.SIMPLE_HEAVY, title_style="bold cyan")
        table.add_column("날짜", style="bold")
        table.add_column("매물수", justify="right")
        table.add_column("매입", justify="right", style="bold")
        table.add_column("당일 기대단가(만)", justify="right", style="cyan")
        table.add_column("판매 예상가(만)", justify="right", style="green")
        table.add_column("대당 부대비용(만)", justify="right", style="dim")
        table.add_column("대당 순이익(만)", justify="right", style="magenta")
        table.add_column("당일 예상지출(만)", justify="right", style="magenta")
        for h in self.history:
            spend_day = h["bought"] * h["exp_price"]
            profit_per_unit = h["sale_price"] - h["exp_price"] - h["total_additional_cost"]
            table.add_row(
                h["date"],
                f"{h['supply']}",
                f"{h['bought']}",
                f"{h['exp_price']:,.1f}",
                f"{h['sale_price']:,.1f}",
                f"{h['total_additional_cost']:,.1f}",
                f"{profit_per_unit:,.1f}",
                f"{spend_day:,.1f}",
            )
        table.add_section()
        table.add_row(
            "[b]합계[/b]",
            f"{sum(h['supply'] for h in self.history)}",
            f"{total_units}",
            "",
            "",
            "",
            f"{actual_total_profit:,.1f}",
            f"{total_spend:,.1f}",
        )
        if total_units > 0:
            table.caption = (
                f"평균단가(만): [b]{fmt_money(avg_price)}[/b]  |  "
                f"총 순이익(만): [b]{actual_total_profit:,.1f}[/b]  |  "
                f"평균 ROI: [b]{actual_avg_roi:,.1f}%[/b]"
            )
        console.print(table)

        base_table = Table(title="초기 최소비용 계획(요약)", box=box.MINIMAL_DOUBLE_HEAD)
        base_table.add_column("지표")
        base_table.add_column("값", justify="right")
        base_table.add_row("목표 대수", f"{target}")
        base_table.add_row("예상 지출(만)", f"{base_spend:,.1f}")
        base_table.add_row("평균단가(만)", f"{base_avg:,.1f}")
        base_table.add_row("예상 순이익(만)", f"{base_total_profit:,.1f}")
        base_table.add_row("예상 ROI(%)", f"{base_avg_roi:,.1f}")
        console.print(base_table)

        cost_table = Table(title="대당 부대비용 구성 (만원)", box=box.MINIMAL_DOUBLE_HEAD)
        cost_table.add_column("항목")
        cost_table.add_column("값", justify="right")
        cost_table.add_row("이전 등록비", f"(차량가 {self.reg_rate:.1%} 내외)")
        cost_table.add_row("기본 상품화", f"{self.comm_cost:,.1f}")
        cost_table.add_row("운송비", f"{self.trans_cost:,.1f}")
        cost_table.add_section()
        cost_table.add_row("[b]총 합계(변동)[/b]", f"[b]매입가에 따라 변동[/b]")
        console.print(cost_table)


def parse_args(argv):
    import argparse
    ap = argparse.ArgumentParser(description="Rich 인터랙티브 중고차 경매 프리토타입 v3 (부대비용 및 순이익 반영)")
    ap.add_argument("--target", type=int, default=DEFAULT_TARGET, help="주간 목표 대수 (기본 10)")
    ap.add_argument("--base-price", type=float, default=DEFAULT_BASE_PRICE, help="기본 기대 단가(만원, 기본 1500)")
    ap.add_argument("--schedule-json", type=str, default="", help="스케줄 JSON 파일 경로 (예: [{\"date\":\"2025-08-14\",\"supply\":2}, ...])")
    ap.add_argument("--demo", type=str, default="", help="비대화식 데모 입력 (예: '2025-08-14=1,2025-08-15=0,2025-08-16=2')")
    ap.add_argument("--reg-rate", type=float, default=DEFAULT_REGISTRATION_TAX_RATE, help="이전 등록비 비율 (기본 0.07, 즉 7%)")
    ap.add_argument("--comm-cost", type=float, default=DEFAULT_COMMODITIZATION_COST, help="기본 상품화 비용(만원, 기본 10)")
    ap.add_argument("--trans-cost", type=float, default=DEFAULT_TRANSPORTATION_COST, help="운송비(만원, 기본 5)")
    ap.add_argument("--sale-margin", type=float, default=DEFAULT_SALE_MARGIN_PCT, help="판매 예상 마진율 (기본 0.10, 즉 10%)")
    return ap.parse_args(argv)

def load_schedule(args) -> List[Tuple[str,int]]:
    if args.schedule_json:
        with open(args.schedule_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [(d["date"], int(d["supply"])) for d in data]
    return DEFAULT_SCHEDULE

def run_demo(cli: "AuctionCLI", demo_str: str):
    mapping = {}
    for token in demo_str.split(","):
        token = token.strip()
        if not token:
            continue
        if "=" not in token:
            console.print(f"[dim]무시: {token}[/dim]")
            continue
        k, v = token.split("=", 1)
        mapping[k.strip()] = int(v.strip())

    console.print(Rule("[bold]데모 모드 시작[/bold]"))
    cli.show_state("초기 최소비용 계획")
    cont = True
    while cont:
        if cli.cursor >= len(cli.schedule_full):
            break
        _, date, supply = cli.schedule_full[cli.cursor]
        n = mapping.get(date, 0)
        console.print(f"[dim]데모 입력: {date}에 {n}대 매입[/dim]")
        cont = cli.step(str(n))

def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    schedule = load_schedule(args)
    cli = AuctionCLI(
        args.target, args.base_price, schedule,
        args.reg_rate, args.comm_cost, args.trans_cost, args.sale_margin
    )

    cli.show_state("초기 최소비용 계획")

    if args.demo:
        run_demo(cli, args.demo)
        return

    cont = True
    while cont:
        cont = cli.step()

if __name__ == "__main__":
    main()

