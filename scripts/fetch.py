import json, time, urllib.request, datetime, sys, concurrent.futures as cf

OUT = sys.argv[1]
FROM = int(datetime.datetime(2023, 1, 1).timestamp())
TO = int(time.time())

def get(url, data=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                                 headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def d(ts):
    return datetime.datetime.utcfromtimestamp(ts + 7 * 3600).strftime("%Y-%m-%d")

def vnd(sym):
    j = get(f"https://dchart-api.vndirect.com.vn/dchart/history?resolution=D&symbol={sym}&from={FROM}&to={TO}")
    if j.get("s") != "ok":
        return None
    # stock prices come in thousand VND
    return {d(t): round(c, 2) for t, c in zip(j["t"], j["c"])}

INDEXES = ["VNINDEX", "VN30", "HNX", "VN100"]
ETFS = ["E1VFVN30", "FUEVFVND", "FUESSVFL", "FUEVN100"]
STOCKS = """ACB BCM BID BVH CTG FPT GAS GVR HDB HPG LPB MBB MSN MWG PLX SAB SHB SSB SSI STB TCB TPB VCB VHM VIB VIC VJC VNM VPB VRE
DGC DIG DXG GEX HCM HSG KBC KDH NLG NKG PDR PNJ POW REE VCI VND VHC VIX DCM DPM GMD BSR PVS PVD SHS MSB EIB OCB HAG HDG CTD CII FRT DGW PC1 KDC VGC IDC NVL BMP SZC TCH VTP""".split()
FUNDS = {28: "DCDS", 25: "DCDE", 23: "VESAF", 20: "VEOF", 11: "SSISCA", 32: "VCBF-BCF", 35: "MAGEF"}

def fund(pid):
    j = get("https://api.fmarket.vn/res/product/get-nav-history",
            {"isAllData": 1, "productId": pid, "fromDate": None, "toDate": datetime.date.today().strftime("%Y%m%d")})
    out = {}
    for r in j["data"]:
        if r["navDate"] >= "2023-01-01":
            out[r["navDate"][:10]] = round(r["nav"], 2)
    return out

res = {"index": {}, "etf": {}, "fund": {}, "stock": {}}
with cf.ThreadPoolExecutor(8) as ex:
    jobs = {}
    for s in INDEXES: jobs[ex.submit(vnd, s)] = ("index", s)
    for s in ETFS: jobs[ex.submit(vnd, s)] = ("etf", s)
    for s in STOCKS: jobs[ex.submit(vnd, s)] = ("stock", s)
    for pid, n in FUNDS.items(): jobs[ex.submit(fund, pid)] = ("fund", n)
    for f in cf.as_completed(jobs):
        k, s = jobs[f]
        try:
            v = f.result()
            if v: res[k][s] = v
            else: print("empty", s)
        except Exception as e:
            print("fail", s, e)

# compact: shared date axis, arrays with null gaps
dates = sorted({dt for g in res.values() for ser in g.values() for dt in ser if dt >= "2023-01-01"})
dates = [x for x in dates if x in res["index"]["VNINDEX"]]  # trading days only
compact = {"dates": dates, "asOf": dates[-1]}
for g, sers in res.items():
    compact[g] = {s: [ser.get(dt) for dt in dates] for s, ser in sorted(sers.items())}
json.dump(compact, open(OUT, "w"), separators=(",", ":"))
print(len(dates), dates[0], dates[-1], {g: len(v) for g, v in res.items()})
