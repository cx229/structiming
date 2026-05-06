import time
import functools
import logging
import json
from typing import Callable, Any, Optional, Dict, List

from .types import TimeUnit, _UNSET
from .utils import _convert_to_unit
from .registry import all_stimers


class StimerLoop:
    """
    StimerLoop 用于统计「同一段逻辑被执行 N 次的耗时分布」。
    """

    def __init__(
        self,
        name: str,
        *,
        number: int,
        func: Optional[Callable[..., Any]] = None,
        log: Optional[logging.Logger] = _UNSET,
        time_unit: TimeUnit = "ms",
        **extra,
    ):
        if number <= 0:
            raise ValueError("number must be > 0")

        self.name = name
        self.number = number
        self.func = func
        self.extra = extra
        self.time_unit = time_unit

        # ---- runtime state ----
        self.samples: List[float] = []
        self.mark_samples: Dict[str, List[float]] = {}
        self._iter_start: Optional[float] = None
        self._inside_context: bool = False

        # ---- logging ----
        if log is _UNSET:
            from .utils import _default_logger
            self.log = _default_logger()
        elif log is None:
            self.log = None
        else:
            self.log = log

        all_stimers[name] = self

    # =================================
    # Context management
    # =================================

    def __enter__(self):
        if self._inside_context:
            raise RuntimeError("StimerLoop already entered")

        self._inside_context = True

        self.samples.clear()
        self.mark_samples.clear()
        return self

    def __exit__(self, exc_type, exc, tb):
        self._inside_context = False
        self._emit_log()

    # =================================
    # Core iteration API
    # =================================

    def iter(self):
        """
        Usage:
            with loop:
                for _ in loop.iter():
                    work()
                    loop.mark(...)
        """
        if not self._inside_context:
            raise RuntimeError(
                "StimerLoop.iter() must be used inside 'with'"
            )
        
        for _ in range(self.number):
            self._iter_start = time.perf_counter()
            yield
            elapsed = time.perf_counter() - self._iter_start
            self.samples.append(elapsed)

    # =================================
    # Execution APIs
    # =================================

    def run(self, *args, **kwargs):
        if self.func is None:
            raise RuntimeError("StimerLoop.func is None")
        res=None
        self._inside_context = True
        self.samples.clear()
        self.mark_samples.clear()
        for _ in self.iter():
            res=self.func(*args, **kwargs)
        self._inside_context = False
        return res # 返回最后一次的返回值

    def __call__(self, fn: Callable[..., Any]):
        self.func = fn

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            res=None
            with self:
                for _ in self.iter():
                    res=self.func(*args, **kwargs)
                return res # 返回最后一次的返回值

        return wrapper

    # =================================
    # Mark API
    # =================================

    def mark(self, label: str):
        if not self._inside_context:
            raise RuntimeError(
                "StimerLoop.mark() must be used inside 'with'"
            )
        if self._iter_start is None:
            return

        now = time.perf_counter()
        self.mark_samples.setdefault(label, []).append(
            now - self._iter_start
        )

    # =================================
    # Outputs
    # =================================

    def export_json(self) -> dict:
        unit = self.time_unit
        payload = {
            "name": self.name,
            "time_unit": unit,
            "number": self.number,
            **self.extra,
        }

        if not self.samples:
            return payload

        payload.update(
            {
                "total": round(
                    _convert_to_unit(sum(self.samples), unit),
                    6,
                ),
                "min": round(
                    _convert_to_unit(min(self.samples), unit),
                    6,
                ),
                "max": round(
                    _convert_to_unit(max(self.samples), unit),
                    6,
                ),
                "mean": round(
                    _convert_to_unit(
                        sum(self.samples) / len(self.samples),
                        unit,
                    ),
                    6,
                ),
            }
        )

        if self.mark_samples:
            payload["marks"] = {
                label: {
                    "mean": round(
                        _convert_to_unit(
                            sum(ts) / len(ts),
                            unit,
                        ),
                        6,
                    ),
                    "min": round(
                        _convert_to_unit(min(ts), unit),
                        6,
                    ),
                    "max": round(
                        _convert_to_unit(max(ts), unit),
                        6,
                    ),
                }
                for label, ts in self.mark_samples.items()
            }

        return payload

    def export_str(self) -> str:
        unit = self.time_unit
        lines = [f"StimerLoop: {self.name}"]

        if self.samples:
            lines.append(
                f"  total: "
                f"{_convert_to_unit(sum(self.samples), unit):.3f} {unit}"
            )
            lines.append(
                f"  mean: "
                f"{_convert_to_unit(sum(self.samples)/len(self.samples), unit):.3f} {unit}"
            )
            lines.append(
                f"  min: "
                f"{_convert_to_unit(min(self.samples), unit):.3f} {unit}"
            )
            lines.append(
                f"  max: "
                f"{_convert_to_unit(max(self.samples), unit):.3f} {unit}"
            )

        if self.mark_samples:
            lines.append("  marks:")
            for label, ts in self.mark_samples.items():
                lines.append(
                    f"    {label}: "
                    f"mean={_convert_to_unit(sum(ts)/len(ts), unit):.3f}, "
                    f"min={_convert_to_unit(min(ts), unit):.3f}, "
                    f"max={_convert_to_unit(max(ts), unit):.3f} {unit}"
                )

        return "\n".join(lines)

    # =================================
    # Logging
    # =================================

    def _emit_log(self):
        if self.log is None:
            return
        self.log.info(json.dumps(self.export_json()))