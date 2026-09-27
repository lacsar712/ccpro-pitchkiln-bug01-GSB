"""灶台相位切换业务规则。"""
from decimal import Decimal

from django.core.exceptions import ValidationError

DRAWING_SOFT_POINT_MAX = Decimal("95")


def drawing_eligibility(hearth):
    """出胶资格唯一判定来源。

    规则：进行中的值守至少有一条软化点探针 ≤ 95℃。
    返回 (是否合格, 说明)。抽屉资格提示、改相位闸门、
    探针登记后的提示都必须以本函数的结论为准。
    """
    open_run = hearth.open_run()
    if open_run is None:
        return False, "该灶没有进行中的值守"

    probes = open_run.probes.all()
    if not probes.exists():
        return False, f"尚无探针 — 出胶前须有 ≤{DRAWING_SOFT_POINT_MAX}℃ 记录"
    if not probes.filter(softPointC__lte=DRAWING_SOFT_POINT_MAX).exists():
        return False, f"已有探针全部高于 {DRAWING_SOFT_POINT_MAX}℃，未达出胶资格"
    return True, f"已有 ≤{DRAWING_SOFT_POINT_MAX}℃ 探针记录"


def assert_can_enter_drawing(hearth) -> None:
    ok, reason = drawing_eligibility(hearth)
    if not ok:
        raise ValidationError(f"无法进入出胶：{reason}")


def change_hearth_phase(hearth, new_phase: str):
    from apps.kiln.models import FireHearth

    if new_phase == FireHearth.PHASE_DRAWING:
        assert_can_enter_drawing(hearth)

    hearth.phase = new_phase
    hearth.save(update_fields=["phase"])
    return hearth
