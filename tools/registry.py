import ast, operator, datetime, csv, os, requests


def calculator(expr, **kw):
    """Safe calculator: only numbers and + - * / ** are allowed."""
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg}

    def ev(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            return ops[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in ops:
            return ops[type(node.op)](ev(node.operand))
        raise ValueError("not allowed")

    try:
        return str(ev(ast.parse(expr.strip(), mode="eval").body))
    except Exception:
        return "calculator error: send a plain arithmetic expression like 12*45.5"


def current_date(arg="", **kw):
    return datetime.date.today().strftime("%A, %d %B %Y")


def csv_lookup(query, docs_folder="docs", **kw):
    """Return CSV rows that contain every word of the query."""
    words = query.lower().split()
    found = []
    for fname in os.listdir(docs_folder):
        if fname.lower().endswith(".csv"):
            with open(os.path.join(docs_folder, fname), encoding="utf-8", errors="ignore") as f:
                for row in csv.DictReader(f):
                    line = ", ".join(f"{k}: {v}" for k, v in row.items())
                    if all(w in line.lower() for w in words):
                        found.append(f"[{fname}] {line}")
    return "\n".join(found[:5]) if found else "no matching rows"


def weather(city, **kw):
    """Free open-meteo API, no key needed."""
    try:
        g = requests.get("https://geocoding-api.open-meteo.com/v1/search",
                         params={"name": city, "count": 1}, timeout=15).json()
        loc = g["results"][0]
        w = requests.get("https://api.open-meteo.com/v1/forecast",
                         params={"latitude": loc["latitude"], "longitude": loc["longitude"],
                                 "current_weather": True}, timeout=15).json()["current_weather"]
        return f"{loc['name']}: {w['temperature']} C, wind {w['windspeed']} km/h"
    except Exception as e:
        return f"weather error: {e}"


TOOLS = {
    "calculator": {"fn": calculator,
                   "description": "does arithmetic, such as totals, prices times quantity, percentages",
                   "needs_words": []},
    "current_date": {"fn": current_date,
                     "description": "returns today's date, for questions about deadlines or notice periods",
                     "needs_words": []},
    "csv_lookup": {"fn": csv_lookup,
                   "description": "looks up rows in a CSV table such as a catalogue or price list",
                   "needs_words": ["csv", "catalogue", "catalog", "price list", "inventory",
                                   "stock", "spare", "parts", "table"]},
    "weather": {"fn": weather,
                "description": "current weather of a city",
                "needs_words": ["weather", "temperature", "forecast", "climate", "rain"]},
}