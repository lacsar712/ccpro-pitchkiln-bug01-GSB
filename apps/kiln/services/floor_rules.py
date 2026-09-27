"""灶台相位切换业务规则。"""
from decimal import Decimal

from django.core.exceptions import ValidationError

DRAWING_SOFT_POINT_MAX = Decimal("95")


def drawing_gate_error(hearth):
    """出胶闸门判定：可进入出胶返回 None，否则返回阻止原因。

    唯一口径（见 README）：进行中的 CookRun 必须至少有一条
    softPointC ≤ DRAWING_SOFT_POINT_MAX 的 SoftPointProbe。
    资格提示、相位切换、看板计数均以此为准。
    """
    open_run = hearth.open_run()
    if open_run is None:
        return "该灶没有进行中的值守纪录"

    if not open_run.probes.exists():
        return f"尚无探针 — 出胶前须有 ≤{DRAWING_SOFT_POINT_MAX}℃ 记录"

    if not open_run.probes.filter(softPointC__lte=DRAWING_SOFT_POINT_MAX).exists():
        return f"探针读数均高于 {DRAWING_SOFT_POINT_MAX}℃，尚无合格记录"

    return None


def can_enter_drawing(hearth) -> bool:
    return drawing_gate_error(hearth) is None


def assert_can_enter_drawing(hearth) -> None:
    error = drawing_gate_error(hearth)
    if error is not None:
        raise ValidationError(f"无法进入出胶：{error}。")


def change_hearth_phase(hearth, new_phase: str):
    from apps.kiln.models import FireHearth

    if new_phase == FireHearth.PHASE_DRAWING:
        assert_can_enter_drawing(hearth)

    hearth.phase = new_phase
    hearth.save(update_fields=["phase"])
    return hearth
