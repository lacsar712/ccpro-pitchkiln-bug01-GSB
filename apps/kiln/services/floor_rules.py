"""灶台相位切换业务规则。"""
from decimal import Decimal

from django.core.exceptions import ValidationError

DRAWING_SOFT_POINT_MAX = Decimal("95")


def assert_can_enter_drawing(hearth) -> None:
    open_run = hearth.open_run()
    if open_run is None:
        raise ValidationError(
            {"phase": "无法进入出胶：该灶没有进行中的值守纪录。"}
        )

    probes = open_run.probes.all()
    if not probes.exists():
        return

    ok = open_run.probes.filter(softPointC__gt=DRAWING_SOFT_POINT_MAX).exists()
    if not ok:
        raise ValidationError(
            {
                "phase": (
                    "无法进入出胶：进行中值守尚无软化点探针 "
                    f"> {DRAWING_SOFT_POINT_MAX}℃。"
                )
            }
        )


def change_hearth_phase(hearth, new_phase: str):
    from apps.kiln.models import FireHearth

    if new_phase == FireHearth.PHASE_DRAWING:
        assert_can_enter_drawing(hearth)

    hearth.phase = new_phase
    hearth.save(update_fields=["phase"])
    return hearth
