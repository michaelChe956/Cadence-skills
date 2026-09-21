"""断言器自测：合法基线必须全绿（正控）；损坏样本必须命中预期红名单（反控），崩溃/缺依赖不算红。"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent


def run_assert(script: str, args: list) -> subprocess.CompletedProcess:
    return subprocess.run(["python3", str(HERE / script)] + args,
                          capture_output=True, text=True)


def main():
    ok = True
    # 正控：fixtures-valid 三件套全绿
    for script, args in [
            ("tier0.py", ["--kb-products", str(HERE / "fixtures-valid"), "--stage", "global-validation"]),
            ("named.py", ["--kb-products", str(HERE / "fixtures-valid"), "--stage", "global-validation", "--variant", "full"]),
            ("negative.py", ["--kb-products", str(HERE / "fixtures-valid")])]:
        p = run_assert(script, args)
        green = p.returncode == 0
        print(f"valid/{script}: {'GREEN(正确)' if green else 'RED(基线树非法!)'}")
        if not green:
            print(p.stdout)
        ok = ok and green
    # 反控：损坏样本命中红名单（断言名精确出现在 FAIL 行）
    cases = [
        ("broken-matrix", "tier0.py", ["--kb-products", "__D__", "--stage", "base-info"], ["矩阵表头六列"]),
        ("broken-graph", "tier0.py", ["--kb-products", "__D__", "--stage", "base-info"], ["图边数==矩阵行数"]),
        ("broken-secret", "negative.py", ["--kb-products", "__D__"], ["反例:无敏感值[Pr0d@A"]),
        ("broken-cap", "negative.py", ["--kb-products", "__D__"], ["反例:空实现不得verified"]),
    ]
    for name, script, args, expect_red in cases:
        p = run_assert(script, [a.replace("__D__", str(HERE / "fixtures-broken" / name)) for a in args])
        out = p.stdout + p.stderr
        hit = p.returncode != 0 and all(any(e in line for line in out.splitlines()) for e in expect_red)
        print(f"broken/{name}: {'RED命中预期断言(正确)' if hit else '未命中预期红名单(断言器问题!)'}")
        if not hit:
            print(out)
        ok = ok and hit
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
