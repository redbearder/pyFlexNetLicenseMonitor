import yaml
import time
from fastapi import FastAPI
from prometheus_client import start_http_server
from lib import *


interval = 30
licenses = []
debug = 0
with open('config.yaml') as f:
    config_str: str = f.read()
    config = yaml.load(config_str, Loader=yaml.FullLoader)
    interval = config['interval']
    licenses = config['license']
    debug = config['debug']


app = FastAPI(debug=debug)


# Using multiprocess collector for registry
def make_metrics_app():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return make_asgi_app(registry=registry)


feature_active_count_gauge = Gauge('feature_active_count', 'lmutil lmstat -i feature list as gauge, export count',
                                       ['vendor_name', 'server', 'feature', 'version', 'pn'])
feature_expires_gauge = Gauge('feature_expires', 'lmutil lmstat -i feature list as gauge, export expire ts',
              ['vendor_name', 'server', 'feature', 'version', 'vendor', 'pn'])
feature_inuse_count_gauge = Gauge('feature_inuse_count',
                                  'lmutil lmstat -a feature stat list as gauge, export inuse count',
              ['vendor_name', 'server', 'feature', 'pn'])
feature_queue_count_gauge = Gauge('feature_queue_count',
                                  'lmutil lmstat -a feature stat list as gauge, export queue count',
              ['vendor_name', 'server', 'feature', 'pn'])
feature_inuse_startts_gauge = Gauge('feature_inuse_startts',
                                    'lmutil lmstat -a feature stat list as gauge, export inuse startts',
              ['vendor_name', 'server', 'feature', 'username', 'jobhost', 'feature_version', 'pn'])
feature_inuse_count_peruser_counter = Counter('feature_inuse_count_peruser',
                                              'lmutil lmstat -a feature stat list as gauge, export inuse count peruser',
              ['vendor_name', 'server', 'feature', 'username', 'pn'])


def export_main():
    feature_active_count_gauge.clear()
    feature_expires_gauge.clear()
    feature_inuse_count_gauge.clear()
    feature_queue_count_gauge.clear()
    feature_inuse_startts_gauge.clear()
    feature_inuse_count_peruser_counter.clear()
    for lic in licenses:
        try:
            lines = read_lic_file(lic['licensefilepath'],
                                  debug=debug)
            feature_pn_map = get_feature_pn_map(lines)

            feature_list = get_feature_list(
                lmutil_path=lic['lmutilpath'],
                license_path=lic['licensepath'],
                debug=debug
            )
            format_feature_list = get_format_feature_list(feature_list)
            export_vendor_feature_count(feature_active_count_gauge, format_feature_list, lic['name']
                                        , lic['licensepath'], feature_pn_map)
            export_vendor_feature_expires(feature_expires_gauge, format_feature_list, lic['name'], lic['licensepath'],
                                          feature_pn_map)

            stat_list = get_stat_list(
                lmutil_path=lic['lmutilpath'],
                license_path=lic['licensepath'],
                debug=debug
            )
            format_stat_list = get_format_stat_list(stat_list)
            export_vendor_feature_inuse_count(feature_inuse_count_gauge, format_stat_list, lic['name'],
                                              lic['licensepath'], feature_pn_map)
            export_vendor_feature_queue_count(feature_queue_count_gauge, format_stat_list, lic['name'],
                                              lic['licensepath'], feature_pn_map)
            export_vendor_feature_inuse_startts(feature_inuse_startts_gauge, format_stat_list, lic['name'],
                                                lic['licensepath'], feature_pn_map)
            export_vendor_feature_inuse_count_peruser(feature_inuse_count_peruser_counter, format_stat_list,
                                                      lic['name'], lic['licensepath'], feature_pn_map)
        except Exception as e:
            print(lic)
            print(e)


# metrics_app = make_asgi_app()
# app.mount("/metrics", metrics_app)


start_http_server(27777)

while True:
    export_main()
    time.sleep(interval)
