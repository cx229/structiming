from typing import Optional, Dict, Any, Literal

TimeUnit = Literal["ms", "s", "m", "h"]

_UNSET = object()

# 全局注册表（仍放在 types 层，方便集中管理）
all_stimers: Dict[str, Any] = {}