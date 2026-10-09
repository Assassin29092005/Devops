"""Lab 06: Grafana HTTP API helper (stdlib only).

    python grafana_api.py datasource   # add the Prometheus data source (used after the pipeline re-created Grafana)
    python grafana_api.py dashboard    # create/overwrite the "Delivery Monitoring" dashboard from the JSON file
Credentials come from the environment (GF_USER, default "admin", and GF_PASSWORD) so they are not stored here.
"""
import base64, json, os, sys, urllib.request

GRAFANA = "http://localhost:3000"
HERE = os.path.dirname(os.path.abspath(__file__))
AUTH = base64.b64encode(f"{os.environ.get('GF_USER', 'admin')}:{os.environ['GF_PASSWORD']}".encode()).decode()


def call(method, path, body=None):
    req = urllib.request.Request(GRAFANA + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


if sys.argv[1] == "datasource":
    res = call("POST", "/api/datasources", {"name": "prometheus", "type": "prometheus", "access": "proxy",
                                            "url": "http://host.docker.internal:9090", "isDefault": True})
    print(res["message"], "-", res["datasource"]["name"], res["datasource"]["url"])
    print("health:", call("GET", f"/api/datasources/uid/{res['datasource']['uid']}/health")["message"])
elif sys.argv[1] == "dashboard":
    dash = json.load(open(os.path.join(HERE, "grafana-dashboard-delivery-monitoring.json")))
    res = call("POST", "/api/dashboards/db", {"dashboard": dash, "overwrite": True, "folderUid": ""})
    print(res["status"], "-", dash["title"], "uid", res["uid"], "version", res["version"], "url", res["url"])
    for p in call("GET", f"/api/dashboards/uid/{res['uid']}")["dashboard"]["panels"]:
        print(f"  {p['title']:<40} {p['targets'][0]['expr']}")
