"""src/metrics/quality_s"""

WEIGHTS = {
    "conformity": 0.40,
    "completeness": 0.25,
    "uniqueness": 0.20,
    "schema_stability": 0.15,
}

MANDATORY_NULL_FACTOR = 2.0
OPTIONAL_NULL_MAX_PENALTY =  50.0

DUPLICATE_FACTOR = 20.0

_STABILITY = {None: 100.0, "NON_BREAKING": 70.0, "BREAKING": 0.0}

def _dim(value, detail):
    return {"value": None if value is None else round(value,1), "detail": detail}

def _conformity(val_result, cast_report):
    if val_result.status == "DLQ":
        return _dim(0.0, "tabela em quarentena (breaking change)")
    if not cast_report:
        return _dim(None, "sem relatorio de cast (tabela nao promovida)")

    broken = [c for c, s in cast_report.items() if not s.get("cast_ok", True)]
    if broken:
        worst = max(cast_report[c].get("fail_pct", 0) for c in broken)
        return _dim(0.0, "tipo divergente do Manifest em {} ({:.1f}% de falha)".format(
            ", ".join(sorted(broken)), worst))

    avg_fail = sum(s.get("fail_pct", 0) for s in cast_report.values()) / len(cast_report)
    return _dim(max(0.0, 100.0 - avg_fail), "{} colunas conformes, {:.2f}% de falha media de cast".format(len(cast_report), avg_fail))

def _completeness(val_result, profiler_payload, contract):
    mandatory = val_result.null_violations or {}
    mandatory_pct = sum(mandatory.values()) / len(mandatory) if mandatory else 0.0

    cols = (profiler_payload or {}).get("columns", {}) or {}
    optional_ratio = 0.0
    tolerance = None
    if contract is not None and cols:
        required = set(getattr(contract, "get_non_nullable", lambda: [])())
        optional = {c: v.get("null_pct", 0) for c, v in cols.items() if c not in required}
        tolerance = getattr(getattr(contract, "tolerance", None), "max_null_pct", None)
        if optional and tolerance :
            avg_opt = sum(optional.values()) / len(optional)
            optional_ratio = min(1.0, avg_opt / tolerance)
    value = 100.0 - MANDATORY_NULL_FACTOR * mandatory_pct - OPTIONAL_NULL_MAX_PENALTY * optional_ratio
    if cols:
        opt_detail = "anulaveis a {:.0f}% da tolerancia{}".format(
            optional_ratio *100,
              " ({}%)".format(tolerance) if tolerance else " (nao declarado)")
    else:
        opt_detail = "colunas anulaveis nao avaliadas (sem profiling)"
    return _dim(max(0.0, value), "nulos em obrigatorias: {:.2f}% | {}".format(mandatory_pct, opt_detail))

def _uniqueness(val_result, contract):
    pks = getattr(contract, "get_primary_keys", lambda: [])() if contract else []
    if not pks:
        return _dim(None, "contrato sem primary_key declarada")
    if getattr(getattr(contract, "tolerance", None), "allow_duplicates", False):
        return _dim(100.0, "duplicatas permitidas pelo contrato")
    total = val_result.rows_total or 1
    dup_pct = val_result.duplicate_count / total * 100
    return _dim(max(0.0, 100.0 - DUPLICATE_FACTOR * dup_pct), 
                "{} duplicatas na PK {} ({:.2f}%)".format(val_result.duplicate_count, pks, dup_pct))

def _schema_stability(val_result):
    value = _STABILITY.get(val_result.evolution_type, 50.0)
    return _dim(value, "evolucao: {}".format(val_result.evolution_type or "nenhuma"))

def compute(val_result, profiler_payload, contract=None, cast_report=None) -> dict:
    dims={
        "conformity"            : _conformity(val_result, cast_report),
        "completeness"          :_completeness(val_result, profiler_payload, contract),
        "uniqueness"            :_uniqueness(val_result, contract),
        "schema_stability"      :_schema_stability(val_result),
    }
    for name, d in dims.items():
        d["weight"] = WEIGHTS[name]

    measured = {n: d for n, d in dims.items() if d["value"] is not None}
    total_weight = sum(d["weight"] for d in measured.values())
    score = (sum(d["value"] * d["weight"] for d in measured.values()) / total_weight
             if total_weight else 0.0)
    return {"score" : round(min(score, 100.0), 1), "dimensions": dims}