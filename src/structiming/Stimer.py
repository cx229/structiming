import time
import functools
import json
from typing import Optional, Dict, Any, Callable

from .types import TimeUnit, _UNSET
from .utils import _convert_to_unit
from .registry import all_stimers


class Stimer:
    def __init__(
        self,
        name: str,
        *,
        log: Optional[Any] = _UNSET,
        time_unit: TimeUnit = "ms",
        **extra,
    ):
        self.name = name
        self.extra = extra
        self.time_unit = time_unit

        self.start_time: Optional[float] = None
        self.records: list[tuple[str, float]] = []

        self.count = 0
        self.total = 0.0

        if log is _UNSET:
            from .utils import _default_logger
            self.log = _default_logger()
        elif log is None:
            self.log = None
        else:
            self.log = log

        all_stimers[name] = self

    # ---- context / decorator ----

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        self._emit_log()

    def __call__(self, fn: Callable[..., Any]):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            with self:
                return fn(*args, **kwargs)
        return wrapper

    # ---- lifecycle ----

    def start(self):
        self.start_time = time.perf_counter()

    def stop(self):
        if self.start_time is None:
            return

        elapsed = time.perf_counter() - self.start_time
        self.start_time = None

        self.count += 1
        self.total += elapsed

    def mark(self, label: str):
        if self.start_time is None:
            return
        self.records.append(
            (label, time.perf_counter() - self.start_time)
        )

    # ---- outputs ----

    def _emit_log(self):
        if self.log is None:
            return
        self.log.info(json.dumps(self.export_json()))

    def export_str(self) -> str:
        unit = self.time_unit
        lines = [f"Stimer: {self.name}"]
        lines.append(
            f"  total: {_convert_to_unit(self.total, unit):.3f} {unit}"
        )
        lines.append(f"  count: {self.count}")

        if self.records:
            lines.append("  marks:")
            for label, t in self.records:
                lines.append(
                    f"    {label}: "
                    f"{_convert_to_unit(t, unit):.3f} {unit}"
                )

        return "\n".join(lines)

    def export_json(self) -> dict:
        unit = self.time_unit
        payload = {
            "name": self.name,
            "time_unit": unit,
            "total": round(_convert_to_unit(self.total, unit), 6),
            "count": self.count,
            **self.extra,
        }

        if self.records:
            payload["marks"] = {
                label: round(_convert_to_unit(t, unit), 6)
                for label, t in self.records
            }

        return payload