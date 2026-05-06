

# structiming

> **结构化、可预测的 Python 计时与性能观测工具**

- ✅ 零依赖
- ✅ JSON / 字符串双输出
- ✅ 单次计时 / 循环统计
- ✅ logging 完全可控

---

## 一、核心概念（非常重要）

### ✅ Stimer

> **观测「单次 / 少量执行」**

- 累计总耗时
- 记录执行次数
- 支持中途 mark

### ✅ StimerLoop

> **观测「同一逻辑被执行 N 次的耗时分布」**

- 总耗时 / 均值 / 最小 / 最大
- 对每个 mark 也做统计分析
- 三种等价用法

---

## 二、Stimer 用法

### ✅ 1️⃣ with 语句（推荐）
执行后默认立即输出（可修改log参数）

```python
with Stimer("train", epoch=1) as t:
    t.mark("start")
    work()
    t.mark("done")
    work()
```

---

### ✅ 2️⃣ 装饰器
执行后默认立即输出（可修改log参数）

```python
@Stimer("train", epoch=1)
def train():
    t = all_stimers["train"]
    work()
    t.mark("half")
    work()
```

---

### ✅ 3️⃣ 手动 start / stop
执行后不立即输出

```python
t = Stimer("train", epoch=1)
t.start()
work()
t.mark("done")
work()
t.stop()
```

---

### ✅ 输出示例（JSON）

```json
{
  "name": "train",
  "time_unit": "ms",
  "total": 1234.567,
  "count": 1,
  "marks": {
    "start": 12.345,
    "done": 678.901
  },
  "epoch": 1
}
```

---

## 三、StimerLoop 用法（✅ 三种等价）

> **StimerLoop 只有一种生命周期模型：**
>
> ```text
> with StimerLoop(...):
>     for _ in loop.iter():
>         ...
> ```
>
> 三种用法只是不同入口。

---

### ✅ 用法一（推荐）
执行后默认立即输出（可修改log参数）

```python
with StimerLoop("train", number=5) as loop:
    for _ in loop.iter():
        work()
        loop.mark("epoch_end")
```

---

### ✅ 用法二：装饰器
执行后默认立即输出（可修改log参数）

```python
@StimerLoop("train", number=5)
def train():
    t = all_stimers["train"]
    work()
    t.mark("epoch_end")
```

---

### ✅ 用法三：func + run
不能mark，只能统计耗时
执行后不立即输出

```python
loop = StimerLoop("train", number=5, func=work)
loop.run()
```

✅ 三种方式统计结果基本一致

---

### ✅ 输出示例（JSON）

```json
{
  "name": "train",
  "time_unit": "ms",
  "number": 5,
  "total": 5432.100,
  "min": 1023.456,
  "max": 1123.789,
  "mean": 1086.420,
  "marks": {
    "epoch_end": {
      "mean": 512.345,
      "min": 498.123,
      "max": 534.678
    },
    "epoch_end2": {
      "mean": 987.654,
      "min": 965.432,
      "max": 1001.234
    }
  }
}
```

---

## 四、logging 行为说明（✅ 非常重要）

| log 参数 | 行为 |
|--------|------|
| `None` | ✅ 完全不输出 |
| 未传 | ✅ 输出到控制台（structiming） |
| logging.Logger | ✅ 输出到你指定的 logger |

```python
Stimer("train", log=None)     # 静默
Stimer("train")               # 控制台
Stimer("train", log=mylogger)
```

---

## 五、all_stimers（全局访问）

```python
t = all_stimers["train"]
print(t.export_json())
print(t.export_str())
```
