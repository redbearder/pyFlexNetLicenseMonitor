from datetime import datetime
import subprocess
from dateutil.relativedelta import relativedelta
from prometheus_client import CollectorRegistry, multiprocess, make_asgi_app, \
    Counter, Histogram, Gauge, Summary


def get_feature_list(lmutil_path: str, license_path: str, debug=0) -> list:
    if debug:
        f = subprocess.run(['cat', 'featurelist.txt'], capture_output=True, text=True)
    else:
        f = subprocess.run([lmutil_path, 'lmstat', '-c', license_path, '-i'], capture_output=True, text=True)
    feature_list = f.stdout.split('\n')
    for idx, feature in enumerate(feature_list):
        if '_____' in feature:
            return feature_list[idx + 1:]


def get_format_feature_list(feature_list: list):
    feature_obj_list = []
    for feature in feature_list:
        idx = feature.find('\n')
        if idx > 0:
            feature = feature[:idx]

        feature_item_list = []
        for item in feature.split(' '):
            if '' != item:
                feature_item_list.append(item)
        if len(feature_item_list) > 0:
            feature_obj = {
                "feature": feature_item_list[0],
                "version": feature_item_list[1],
                "count": feature_item_list[2],
                "vendor": feature_item_list[3],
                "expires": '31-dec-2099' if 'permanent' in feature_item_list[4] else feature_item_list[4]
            }
            feature_obj_list.append(feature_obj)
    return feature_obj_list


def get_stat_list(lmutil_path: str, license_path: str, debug=0) -> list:
    if debug:
        f = subprocess.run(['cat', 'statlist.txt'], capture_output=True, text=True)
    else:
        f = subprocess.run([lmutil_path, 'lmstat', '-c', license_path, '-a'], capture_output=True, text=True)
    stat_list = f.stdout.split('\n')
    for idx, stat in enumerate(stat_list):
        if 'Users of' in stat:
            return stat_list[idx:]


def get_format_stat_list(stat_list: list):
    total_stat_list = []
    last_stat = ''
    last_stat_use_list = []
    last_stat_queue_list = []
    for idx, stat in enumerate(stat_list):
        try:
            if 'Users of' in stat:
                if last_stat != '':
                    last_stat_feature_name = last_stat.split(':')[0].replace('Users of ', '')
                    total_stat_list.append({
                        "feature_name": last_stat_feature_name,
                        "feature_user_list": last_stat_use_list,
                        "feature_queue_list": last_stat_queue_list
                    })

                last_stat = stat
                last_stat_use_list = []
                last_stat_queue_list = []
            else:
                if stat.startswith(' '*4):
                    if stat.endswith('\n'):
                        stat = stat[4:-1]
                    else:
                        stat = stat[4:]
                    if 'queued for' not in stat:
                        stat_use_block_list = stat.split(',')
                        stat_use_list0 = stat_use_block_list[0].split(' ')
                        stat_use_list1 = stat_use_block_list[1].split(' ')
                        start_day = stat_use_list1[3]
                        start_time = stat_use_list1[4]
                        start_year = datetime.now().strftime('%Y')
                        start_dt = datetime.strptime(f'{start_year}/{start_day} {start_time}', '%Y/%m/%d %H:%M')
                        if start_dt > datetime.now():
                            start_dt = start_dt - relativedelta(years=1)
                        stat_use_obj = {
                            "username": stat_use_list0[0],
                            "jobhost": stat_use_list0[1],
                            "feature_version": stat_use_list0[-3][1:-1],
                            "start_ts": start_dt.timestamp()
                        }
                        last_stat_use_list.append(stat_use_obj)
                    else:
                        stat_use_block_list = stat.split(' queued for ')
                        stat_use_list0 = stat_use_block_list[0].split(' ')
                        stat_use_list1 = stat_use_block_list[1].split(' ')
                        stat_queue_obj = {
                            "username": stat_use_list0[0],
                            "jobhost": stat_use_list0[1],
                            "feature_version": stat_use_list0[-3][1:-1],
                            "count": int(stat_use_list1[0])
                        }
                        last_stat_queue_list.append(stat_queue_obj)

            if idx == len(stat_list) - 1:
                if 'Users of' in stat:
                    last_stat_feature_name = last_stat.split(':')[0].replace('Users of ', '')
                    total_stat_list.append({
                        "feature_name": last_stat_feature_name,
                        "feature_user_list": last_stat_use_list,
                        "feature_queue_list": last_stat_queue_list
                    })
                else:
                    if stat.startswith(' ' * 4):
                        if stat.endswith('\n'):
                            stat = stat[4:-1]
                        else:
                            stat = stat[4:]
                        if 'queued for' not in stat:
                            stat_use_block_list = stat.split(',')
                            stat_use_list0 = stat_use_block_list[0].split(' ')
                            stat_use_list1 = stat_use_block_list[1].split(' ')
                            start_day = stat_use_list1[3]
                            start_time = stat_use_list1[4]
                            start_year = datetime.now().strftime('%Y')
                            start_dt = datetime.strptime(f'{start_year}/{start_day} {start_time}', '%Y/%m/%d %H:%M')
                            if start_dt > datetime.now():
                                start_dt = start_dt - relativedelta(years=1)
                            stat_use_obj = {
                                "username": stat_use_list0[0],
                                "jobhost": stat_use_list0[1],
                                "feature_version": stat_use_list0[-3][1:-1],
                                "start_ts": start_dt.timestamp()
                            }
                            last_stat_use_list.append(stat_use_obj)
                        else:
                            stat_use_block_list = stat.split(' queued for ')
                            stat_use_list0 = stat_use_block_list[0].split(' ')
                            stat_use_list1 = stat_use_block_list[1].split(' ')
                            stat_queue_obj = {
                                "username": stat_use_list0[0],
                                "jobhost": stat_use_list0[1],
                                "feature_version": stat_use_list0[-3][1:-1],
                                "count": int(stat_use_list1[0])
                            }
                            last_stat_queue_list.append(stat_queue_obj)

                    last_stat_feature_name = last_stat.split(':')[0].replace('Users of ', '')
                    total_stat_list.append({
                        "feature_name": last_stat_feature_name,
                        "feature_user_list": last_stat_use_list,
                        "feature_queue_list": last_stat_queue_list
                    })
        except Exception as e:
            print(f'last_stat is {last_stat}')
            print('get_format_stat_list exception ' + str(e))
            continue

    return total_stat_list


def export_vendor_feature_count(feature_active_count_gauge: Gauge, format_feature_list: list, vendor_name: str,
                                server: str, feature_pn_map:dict):
    for f in format_feature_list:
        pn = "NONE"
        if f['feature'] in feature_pn_map:
            pn = feature_pn_map[f['feature']]
        expires = f['expires'][:3] + f['expires'][3].upper() + f['expires'][4:]
        expire_date = datetime.strptime(expires, '%d-%b-%Y')
        if expire_date > datetime.now():
            feature_active_count_gauge.labels(vendor_name, server, f['feature'], f['version'], pn)\
                .set(f['count'])


def export_vendor_feature_expires(feature_expires_gauge: Gauge, format_feature_list: list, vendor_name: str,
                                  server: str, feature_pn_map:dict):
    for f in format_feature_list:
        pn = "NONE"
        if f['feature'] in feature_pn_map:
            pn = feature_pn_map[f['feature']]
        expires = f['expires'][:3] + f['expires'][3].upper() + f['expires'][4:]
        expire_date = datetime.strptime(expires, '%d-%b-%Y')
        feature_expires_gauge.labels(vendor_name, server, f['feature'], f['version'], f['vendor'], pn)\
            .set(expire_date.timestamp())


def export_vendor_feature_inuse_count(feature_inuse_count_gauge: Gauge, format_stat_list: list, vendor_name: str,
                                      server: str, feature_pn_map:dict):
    for f in format_stat_list:
        pn = "NONE"
        if f['feature_name'] in feature_pn_map:
            pn = feature_pn_map[f['feature_name']]
        feature_inuse_count_gauge.labels(vendor_name, server, f['feature_name'], pn).set(len(f['feature_user_list']))


def export_vendor_feature_queue_count(feature_queue_count_gauge: Gauge, format_stat_list: list, vendor_name: str,
                                      server: str, feature_pn_map:dict):
    for f in format_stat_list:
        count = 0
        pn = "NONE"
        if f['feature_name'] in feature_pn_map:
            pn = feature_pn_map[f['feature_name']]
        for queue in f['feature_queue_list']:
            count += queue['count']
        feature_queue_count_gauge.labels(vendor_name, server, f['feature_name'], pn).set(count)


def export_vendor_feature_inuse_startts(feature_inuse_startts_gauge: Gauge, format_stat_list: list, vendor_name: str,
                                        server: str, feature_pn_map:dict):
    for f in format_stat_list:
        pn = "NONE"
        if f['feature_name'] in feature_pn_map:
            pn = feature_pn_map[f['feature_name']]
        for user in f['feature_user_list']:
            feature_inuse_startts_gauge.labels(vendor_name, server, f['feature_name'], user['username'],
                                               user['jobhost'],user['feature_version'], pn).set(user['start_ts'])


def export_vendor_feature_inuse_count_peruser(feature_inuse_count_peruser_counter: Counter, format_stat_list: list,
                                              vendor_name: str, server: str, feature_pn_map:dict):
    for f in format_stat_list:
        pn = "NONE"
        if f['feature_name'] in feature_pn_map:
            pn = feature_pn_map[f['feature_name']]
        for user in f['feature_user_list']:
            feature_inuse_count_peruser_counter.labels(vendor_name, server, f['feature_name'], user['username'],
                                                       pn)\
                .inc()


# add function to map feature and product id
def read_lic_file(file_path:str, debug=0) -> list:
    if debug:
        with open("snpslmd.txt", "r") as f:
            lines = f.readlines()
            return lines
    else:
        with open(file_path, "r") as f:
            lines = f.readlines()
            return lines

def get_synopsys_feature_pn_map(lic_lines) -> dict:
    d = {}
    feature_name = None
    for line in lic_lines:
        if line.startswith("INCREMENT"):
            line_col = line.split(" ")
            feature_name = line_col[1]
        else:
            if "SN=TK" in line:
                line_col = line.split(":")
                if line_col[1] != "0":
                    d[feature_name] = line_col[1]

    return d


def get_cadence_feature_pn_map(lic_lines) -> dict:
    d = {}
    product_id = None
    for line in lic_lines:
        if line.startswith("# Product Id"):
            line_col = line.split(":")
            line_col1 = line_col[1].split(",")
            product_id = line_col1[0].strip()
        else:
            if "Feature:" in line:
                line_col = line.split(":")
                line_col1 = line_col[1].split("[")
                feature_name = line_col1[0].strip()
                d[feature_name] = product_id
    return d

def get_feature_pn_map(lic_lines: list) -> dict:
    for line in lic_lines:
        if "SYNOPSYS" in line:
            return get_synopsys_feature_pn_map(lic_lines)

    return get_cadence_feature_pn_map(lic_lines)
