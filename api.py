"""
Optional FastAPI backend for programmatic integration (MVP).

Endpoints:
- POST /profile
- POST /suggestions
- POST /clean
- POST /charts/hist
- POST /charts/corr

Security: Bearer token or JWT; roles via X-Role header (admin/editor/viewer).
Audit: logs to logs/audit.log and optional SQLite store.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from utils.data_analyzer import DataAnalyzer
from utils.data_cleaner import DataCleaner
from utils.db_io import read_from_database
from utils.audit import write_audit

try:
    import jwt  # PyJWT
except Exception:
    jwt = None

# Optional DB persistence for audit
try:
    from utils.audit_store import write_audit_db
except Exception:
    def write_audit_db(*args, **kwargs):
        return None

API_TOKEN = os.getenv("DATA_CLEANER_API_TOKEN", "")
JWT_SECRET = os.getenv("DATA_CLEANER_JWT_SECRET", "")
JWT_ALG = os.getenv("DATA_CLEANER_JWT_ALG", "HS256")

app = FastAPI(title="AI Data Cleaning Assistant API", version="0.2.0")

# CORS
origins = os.getenv("DATA_CLEANER_CORS_ORIGINS", "http://localhost, http://localhost:5173, http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


def _verify_jwt(authorization: Optional[str]) -> Optional[Dict[str, Any]]:
    if not JWT_SECRET or jwt is None:
        return None
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return claims
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid JWT: {e}")


def require_auth(authorization: Optional[str] = Header(None)):
    # Prefer JWT if configured
    if JWT_SECRET and jwt is not None:
        _ = _verify_jwt(authorization)
        return True
    # Fallback to static token
    if API_TOKEN:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Unauthorized")
        token = authorization.split(" ", 1)[1]
        if token != API_TOKEN:
            raise HTTPException(status_code=403, detail="Forbidden")
    return True


def audit_log(user_role: str, action: str, details: Dict[str, Any]):
    write_audit(user_role, action, details)
    try:
        write_audit_db(user_role, action, details)
    except Exception:
        pass


def _load_dataframe(
    file: Optional[UploadFile],
    connection_url: Optional[str],
    table: Optional[str],
    query: Optional[str],
) -> pd.DataFrame:
    if file is not None:
        if file.filename.endswith(".csv"):
            return pd.read_csv(file.file)
        elif file.filename.endswith((".xlsx", ".xls")):
            return pd.read_excel(file.file)
        elif file.filename.endswith(".json"):
            return pd.read_json(file.file)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
    if connection_url:
        return read_from_database(connection_url, table=table, query=query)
    raise HTTPException(status_code=400, detail="Provide a file or database connection")


@app.post("/profile")
async def profile(
    auth=Depends(require_auth),
    role: str = Header("viewer", alias="X-Role"),
    file: Optional[UploadFile] = File(None),
    connection_url: Optional[str] = Form(None),
    table: Optional[str] = Form(None),
    query: Optional[str] = Form(None),
):
    df = _load_dataframe(file, connection_url, table, query)
    analyzer = DataAnalyzer(df)
    profile_json = {
        "shape": list(df.shape),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "missing_total": int(df.isnull().sum().sum()),
        "duplicates": int(df.duplicated().sum()),
        "cardinality": {c: int(df[c].nunique()) for c in df.columns},
        "quality_score": analyzer.get_data_quality_score(),
    }
    audit_log(role, "profile", {"cols": df.shape[1], "rows": df.shape[0]})
    return JSONResponse(profile_json)


@app.post("/suggestions")
async def suggestions(
    auth=Depends(require_auth),
    role: str = Header("viewer", alias="X-Role"),
    file: Optional[UploadFile] = File(None),
    connection_url: Optional[str] = Form(None),
    table: Optional[str] = Form(None),
    query: Optional[str] = Form(None),
):
    df = _load_dataframe(file, connection_url, table, query)
    analyzer = DataAnalyzer(df)
    sugs = analyzer.generate_suggestions()
    audit_log(role, "suggestions", {"count": len(sugs)})
    return JSONResponse(sugs)


@app.post("/clean")
async def clean(
    auth=Depends(require_auth),
    role: str = Header("editor", alias="X-Role"),
    file: Optional[UploadFile] = File(None),
    connection_url: Optional[str] = Form(None),
    table: Optional[str] = Form(None),
    query: Optional[str] = Form(None),
):
    df = _load_dataframe(file, connection_url, table, query)
    analyzer = DataAnalyzer(df)
    sugs = analyzer.generate_suggestions()
    cleaner = DataCleaner(df)
    for key, suggestion in sugs.items():
        t = suggestion.get("type")
        col = suggestion.get("column")
        if t == "missing_numeric":
            cleaner.fill_missing_numeric(col)
        elif t == "missing_categorical":
            cleaner.fill_missing_categorical(col)
        elif t == "duplicates":
            cleaner.remove_duplicates()
        elif t == "outliers":
            cleaner.remove_outliers(col)
        elif t == "data_type":
            cleaner.convert_data_type(col)
        elif t == "whitespace":
            cleaner.trim_whitespace([col])
        elif t == "text_case":
            cleaner.standardize_text_case([col])
        elif t == "datetime_parse":
            cleaner.parse_datetime(col)
        elif t == "constant_column":
            cleaner.remove_columns([col])
        elif t == "boolean_text":
            cleaner.convert_boolean_text(col)
        elif t == "percentage_string":
            cleaner.convert_percentage_strings(col)
    audit_log(role, "clean", {"ops": len(cleaner.get_cleaning_log())})
    cleaned = cleaner.get_cleaned_data()
    return JSONResponse({
        "rows": int(cleaned.shape[0]),
        "cols": int(cleaned.shape[1]),
        "log": cleaner.get_cleaning_log(),
        "head": cleaned.head(10).to_dict(orient="records"),
    })


@app.post("/charts/hist")
async def charts_hist(
    auth=Depends(require_auth),
    role: str = Header("viewer", alias="X-Role"),
    file: Optional[UploadFile] = File(None),
    connection_url: Optional[str] = Form(None),
    table: Optional[str] = Form(None),
    query: Optional[str] = Form(None),
    columns: Optional[str] = Form(None),  # comma-separated
    bins: int = Form(30),
):
    df = _load_dataframe(file, connection_url, table, query)
    cols = [c.strip() for c in (columns.split(",") if columns else df.select_dtypes(include=["number"]).columns.tolist()) if c.strip() in df.columns]
    result: Dict[str, Any] = {}
    for c in cols:
        try:
            s = pd.to_numeric(df[c], errors='coerce').dropna()
            if s.empty:
                continue
            counts, edges = pd.np.histogram(s, bins=bins)  # pandas bundles numpy
            result[c] = {"counts": counts.tolist(), "bin_edges": edges.tolist()}
        except Exception:
            continue
    audit_log(role, "charts_hist", {"cols": len(result)})
    return JSONResponse(result)


@app.post("/charts/corr")
async def charts_corr(
    auth=Depends(require_auth),
    role: str = Header("viewer", alias="X-Role"),
    file: Optional[UploadFile] = File(None),
    connection_url: Optional[str] = Form(None),
    table: Optional[str] = Form(None),
    query: Optional[str] = Form(None),
):
    df = _load_dataframe(file, connection_url, table, query)
    num = df.select_dtypes(include=['number'])
    if num.shape[1] < 2:
        return JSONResponse({"columns": num.columns.tolist(), "matrix": []})
    corr = num.corr(numeric_only=True)
    audit_log(role, "charts_corr", {"cols": int(num.shape[1])})
    return JSONResponse({"columns": corr.columns.tolist(), "matrix": corr.values.tolist()})
