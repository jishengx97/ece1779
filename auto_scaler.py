#!venv/bin/python
from sqlalchemy.orm import scoped_session
from common import database, models
from decouple import config
import boto3
import requests
import time
from datetime import datetime,timedelta
from pytz import timezone
import pytz
from flask import  _app_ctx_stack

if __name__ == "__main__":
    database.init_db()
    db_session = scoped_session(database.SessionLocal, scopefunc=_app_ctx_stack.__ident_func__)
    local_session = db_session()

    while True:
        local_session.commit()
        result = local_session.query(models.MemcachePoolResizeConfig).first()
        while result.resize_mode != "Automatic":
            time.sleep(1)
            local_session.commit()
            result = local_session.query(models.MemcachePoolResizeConfig).first()

        # now the automatic scaling option is enabled
        # check miss rate for the past one minute
        print("entering automatic scaling mode")
        cw_client = boto3.client('cloudwatch', 
            aws_access_key_id=config('AWSAccessKeyId'), 
            aws_secret_access_key=config('AWSSecretKey')
        )
        
        eastern = timezone('US/Eastern')
        current_time = datetime.now(eastern)
        metric_namespace = 'ece1779-a2-memcache-stats'
        dimension_name = 'InstanceID'

        metric_name_num_miss = 'num_miss'
        metric_name_num_access = 'num_access'
        metric_name_num_workers = 'num_workers'
        metric_names_need_raw_data = [
            metric_name_num_miss,
            metric_name_num_access,
        ]
        metric_names_need_max = [
            metric_name_num_workers,
        ]
        metric_data_queries = []
        for metric_name in metric_names_need_raw_data:
            metric_data_queries.append(
                {
                    'Id': metric_name,
                    'Expression': "FILL(REMOVE_EMPTY(SEARCH('{" + metric_namespace + "," + dimension_name + "} MetricName=\""+metric_name+"\"', 'Sum', 60)),0)",
                    'ReturnData': True,
                }
            )
        for metric_name in metric_names_need_max:
            metric_data_queries.append(
                {
                    'Id': metric_name,
                    'Expression': "SEARCH('{" + metric_namespace + "," + dimension_name + "} MetricName=\""+metric_name+"\"', 'Maximum', 60)",
                    'ReturnData': False,
                }
            )
        for metric_name in metric_names_need_max:
            metric_data_queries.append(
                {
                    'Id': 'sum_'+metric_name,
                    'Expression': "SUM(FILL(REMOVE_EMPTY("+metric_name+"),0))",
                    'ReturnData': True,
                }
            )

        try:
            response = cw_client.get_metric_data(
                MetricDataQueries=metric_data_queries,
                StartTime=current_time - timedelta(seconds=1*60),
                EndTime=current_time,
                LabelOptions={
                    'Timezone': '-0500'
                },
            )
        except:
            print("No statistics found for memcache. Please check back as memcache populate more statistic entries!")
            continue

        num_workers_values = []
        miss_rate_values = []
        num_miss_result_list = []
        num_access_result_list = []
        results = response['MetricDataResults']
        for result in results:
            if result['Id'] == 'sum_' + metric_name_num_workers:
                num_workers_values = result['Values'][::-1]
            elif result['Id'] == metric_name_num_miss:
                num_miss_result_list.append(result)
                miss_rate_values = [0] * len(result['Timestamps'])
            elif result['Id'] == metric_name_num_access:
                num_access_result_list.append(result)

        for num_miss_item in num_miss_result_list:
            num_miss_label = num_miss_item['Label']
            for num_access_item in num_access_result_list:
                num_access_label = num_access_item['Label']
                if num_miss_label.split()[0] == num_access_label.split()[0]:
                    # print("found", num_miss_label, "is the same as", num_access_label)
                    miss_rate_result = []
                    hit_rate_result = []
                    this_miss_value = num_miss_item['Values'][::-1]
                    this_access_value = num_access_item['Values'][::-1]
                    for miss, access in zip(this_miss_value, this_access_value):
                        if access == 0:
                            miss_rate_result.append(0)
                        else:
                            miss_rate_result.append(miss/access*100)
                    miss_rate_values = [x+y for x, y in zip(miss_rate_values, miss_rate_result)]
        miss_rate_values = [x/y if y != 0 else 0 for x, y in zip(miss_rate_values, num_workers_values)]
        if len(miss_rate_values) != 1:
            print("WARNING! got more than one miss rate for the past minute, len =", len(miss_rate_values))
            continue
        
        local_session.commit()
        result = local_session.query(models.MemcachePoolResizeConfig).first()
        if result.resize_mode != "Automatic":
            # surprise!
            continue
        if miss_rate_values[0] > result.max_missrate_threshold:
            # send expand request to manager
            print("sending expand request to manager")
            r = requests.post("http://127.0.0.1:5000/auto_config/expand", data={'ratio': str(result.expand_ratio) })
        elif miss_rate_values[0] < result.min_missrate_threshold:
            # send shrink request to manager
            print("sending shrink request to manager")
            r = requests.post("http://127.0.0.1:5000/auto_config/shrink", data={'ratio': str(result.shrink_ratio) })

        # wait for the next minute
        time.sleep(60)
