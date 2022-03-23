from flask import render_template, url_for, request, json
from managerapp import webapp
import matplotlib
from datetime import datetime,timedelta
from pytz import timezone
import pytz
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator
import matplotlib.pyplot as plt
import base64
import math
import boto3
from botocore.exceptions import ClientError
from decouple import config
import re
from auto_config import is_float
stats_title = "Memcache Statistics"

def utc_to_local(utc_dt):
    eastern = timezone('US/Eastern')
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(eastern)
    if is_float(utc_dt):
        print("is float!")
    return local_dt

@webapp.route('/show_stats',methods=['GET', 'POST'])
def show_stats():
    print("before_stats_query")

    cw_client = boto3.client('cloudwatch', 
        aws_access_key_id=config('AWSAccessKeyId'), 
        aws_secret_access_key=config('AWSSecretKey')
    )
    eastern = timezone('US/Eastern')
    current_time = datetime.now(eastern)
    if is_float(current_time):
        print("is float!")
    metric_namespace = 'ece1779-a2-memcache-stats'
    dimension_name = 'InstanceID'

    metric_name_num_miss = 'num_miss'
    metric_name_num_access = 'num_access'
    metric_name_num_request = 'num_request'
    metric_name_num_item = 'num_item'
    metric_name_current_size = 'current_size'
    metric_name_num_workers = 'num_workers'
    metric_names_need_raw_data = [
        metric_name_num_miss,
        metric_name_num_access,
    ]
    metric_names_need_sum = [
        metric_name_num_request,
    ]

    metric_names_need_avg = [
        metric_name_current_size,
    ]

    metric_names_need_max = [
        metric_name_num_item,
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
    for metric_name in metric_names_need_sum:
        metric_data_queries.append(
            {
                'Id': metric_name,
                'Expression': "SEARCH('{" + metric_namespace + "," + dimension_name + "} MetricName=\""+metric_name+"\"', 'Sum', 60)",
                'ReturnData': False,
            }
        )
    for metric_name in metric_names_need_avg:
        metric_data_queries.append(
            {
                'Id': metric_name,
                'Expression': "SEARCH('{" + metric_namespace + "," + dimension_name + "} MetricName=\""+metric_name+"\"', 'Average', 60)",
                'ReturnData': False,
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

    for metric_name in metric_names_need_sum:
        metric_data_queries.append(
            {
                'Id': 'sum_'+metric_name,
                'Expression': "SUM(FILL(REMOVE_EMPTY("+metric_name+"),0))",
                'ReturnData': True,
            }
        )
    for metric_name in metric_names_need_avg:
        metric_data_queries.append(
            {
                'Id': 'sum_'+metric_name,
                'Expression': "SUM(FILL(REMOVE_EMPTY("+metric_name+"),0))",
                'ReturnData': True,
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
    
    # print("getting data")
    try:
        response = cw_client.get_metric_data(
            MetricDataQueries=metric_data_queries,
            StartTime=current_time - timedelta(seconds=30*60),
            EndTime=current_time,
            LabelOptions={
                'Timezone': '-0500'
            },
        )
    except:
        error_msg = "No statistics found for memcache. Please check back as memcache populate more statistic entries!"
        return render_template("pages/show_stats/show_stats.html", title = stats_title, error_msg=error_msg)

    # print (response)

    num_item_values = []
    num_item_timestamp = []
    current_size_values = []
    current_size_timestamp = []
    num_workers_values = []
    num_workers_timestamp = []
    num_request_values = []
    num_request_timestamp = []

    miss_rate_values = []
    miss_rate_timestamp = []
    hit_rate_values = []
    hit_rate_timestamp = []

    num_miss_result_list = []
    num_access_result_list = []
    results = response['MetricDataResults']
    for result in results:
        if result['Id'] == 'sum_' + metric_name_num_item:
            num_item_values = result['Values'][::-1]
            num_item_timestamp = result['Timestamps'][::-1]
        elif result['Id'] == 'sum_' + metric_name_current_size:
            current_size_values = result['Values'][::-1]
            current_size_timestamp = result['Timestamps'][::-1]
        elif result['Id'] == 'sum_' + metric_name_num_workers:
            num_workers_values = result['Values'][::-1]
            num_workers_timestamp = result['Timestamps'][::-1]
        elif result['Id'] == 'sum_' + metric_name_num_request:
            num_request_values = result['Values'][::-1]
            num_request_timestamp = result['Timestamps'][::-1]
        elif result['Id'] == metric_name_num_miss:
            num_miss_result_list.append(result)
            miss_rate_timestamp = result['Timestamps'][::-1]
            miss_rate_values = [0] * len(miss_rate_timestamp)
        elif result['Id'] == metric_name_num_access:
            num_access_result_list.append(result)
            hit_rate_timestamp = result['Timestamps'][::-1]
            hit_rate_values = [0] * len(hit_rate_timestamp)

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
                        hit_rate_result.append(0)
                    else:
                        miss_rate_result.append(miss/access*100)
                        hit_rate_result.append((access-miss)/access*100)
                # print("miss_rate_values", miss_rate_values)
                # print("hit_rate_values", hit_rate_values)
                
                miss_rate_values = [x+y for x, y in zip(miss_rate_values, miss_rate_result)]
                hit_rate_values = [x+y for x, y in zip(hit_rate_values, hit_rate_result)]
    miss_rate_values = [x/y if y != 0 else 0 for x, y in zip(miss_rate_values, num_workers_values)]
    hit_rate_values = [x/y if y != 0 else 0 for x, y in zip(hit_rate_values, num_workers_values)]
        
    # print("num_workers_values", num_workers_values)
    # print("miss_rate_values", miss_rate_values)
    # print("hit_rate_values", hit_rate_values)
    # print("num_item_values", num_item_values)
    # print("current_size_values", current_size_values)
    # print("num_request_values", num_request_values)
    plot_worker_result = []
    for x,y in zip(num_workers_values, num_workers_timestamp):
        y = utc_to_local(y)
        plot_worker_result.append([y.timestamp()*1000, x])
    plot_miss_rate_result = []
    for x,y in zip(miss_rate_values, num_workers_timestamp):
        y = utc_to_local(y)
        plot_miss_rate_result.append([y.timestamp()*1000, x])
    plot_hit_rate_result = []
    for x,y in zip(hit_rate_values, num_workers_timestamp):
        y = utc_to_local(y)
        plot_hit_rate_result.append([y.timestamp()*1000, x])
    plot_num_items_result = []
    for x,y in zip(num_item_values, num_workers_timestamp):
        y = utc_to_local(y)
        plot_num_items_result.append([y.timestamp()*1000, x])
    plot_total_size_result = []
    for x,y in zip(current_size_values, num_workers_timestamp):
        y = utc_to_local(y)
        # get size in kb
        plot_total_size_result.append([y.timestamp()*1000, x/1024])
    plot_num_requests_result = []
    for x,y in zip(num_request_values, num_workers_timestamp):
        y = utc_to_local(y)
        plot_num_requests_result.append([y.timestamp()*1000, x])
    return render_template("pages/show_stats/show_stats.html", title = stats_title, start_time = str(utc_to_local(miss_rate_timestamp[0]).strftime("%X")),
        end_time = str(utc_to_local(miss_rate_timestamp[-1]).strftime("%X")), workers = plot_worker_result, miss_rate = plot_miss_rate_result, 
        hit_rate = plot_hit_rate_result, num_items = plot_num_items_result, 
        total_size = plot_total_size_result, num_requests = plot_num_requests_result, )