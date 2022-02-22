from flask import render_template, url_for, request, json
from frontendapp import webapp
import matplotlib
from common import models
from datetime import datetime
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator
import matplotlib.pyplot as plt
import base64
import math
stats_title = "Memcache Statistics"

@webapp.route('/show_stats',methods=['GET', 'POST'])
def show_stats():
    print("before_stats_query")
    local_session = webapp.db_session()
    num_stats_entries = local_session.query(models.MemcacheStats).count()

    if (num_stats_entries == 0):
        return render_template("pages/show_stats/show_stats_form.html", title = stats_title, error_msg = "No stats available yet!")
    # Either get all entries from the database, or get entries for the last 10 minutes,
    # which is 60 / 5 * 10 = 120 entries
    num_entried_needed = min(num_stats_entries, 120)
    results = local_session.query(models.MemcacheStats).order_by(models.MemcacheStats.id.desc()).limit(num_entried_needed).all()
    # results = statements.statement.execute().fetchall()
    
    # Reverse to get sequence in time
    results = results[::-1]
    # local_session.remove()

    # prepare data to generate figures
    num_items = []
    total_size = []
    num_requests_served = 0
    num_reads_served = 0
    num_reads_missed = 0
    stats_timestamp = []
    for item in results:
        num_items.append(item.num_items)
        total_size.append(item.total_size * 1024)
        num_requests_served += item.num_requests_served
        num_reads_served += item.num_reads_served
        num_reads_missed += item.num_reads_missed
        stats_timestamp.append(item.stats_timestamp.strftime("%X"))
    
    print("after_stats_query")
    local_session.rollback()
    # print (num_items)
    # print (total_size)
    # print (num_requests_served)
    # print (miss_rate)
    # print (hit_rate)
    # print (stats_timestamp)
    
    # num_items_img = get_html_decoded_figure(
    #     stats_timestamp, 
    #     num_items, 
    #     'Number of Items in Memcache', # title
    #     'Time (Eastern)', # xlabel
    #     'Items' # ylabel
    # )

    # total_size_img = get_html_decoded_figure(
    #     stats_timestamp, 
    #     total_size, 
    #     'Total Size of Items in Memcache', # title
    #     'Time (Eastern)', # xlabel
    #     'Byte(s)' # ylabel
    # )

    # num_requests_served_img = get_html_decoded_figure(
    #     stats_timestamp, 
    #     num_requests_served, 
    #     'Number of Requests Served by Memcache', # title
    #     'Time (Eastern)', # xlabel
    #     'Requests' # ylabel
    # )

    # miss_rate_img = get_html_decoded_figure(
    #     stats_timestamp, 
    #     miss_rate, 
    #     'Missrate', # title
    #     'Time (Eastern)', # xlabel
    #     'Percentages' # ylabel
    # )

    # hit_rate_img = get_html_decoded_figure(
    #     stats_timestamp, 
    #     hit_rate, 
    #     'Hitrate', # title
    #     'Time (Eastern)', # xlabel
    #     'Percentages' # ylabel
    # )

    y_axes = [num_items, total_size]
    titles = ['Number of Items in Memcache','Total Size of Items in Memcache']
    xlabels = ['Time (Eastern)', 'Time (Eastern)']
    ylabels = ['Items',  'KiloByte(s)']

    img_all_in_one = get_html_decoded_figure_all_in_one(stats_timestamp, y_axes, titles, xlabels, ylabels)

    # return render_template("pages/show_stats/show_stats_form.html", title = stats_title, error_msg = None, 
    #     num_items_img=num_items_img, total_size_img=total_size_img, num_requests_served_img=num_requests_served_img,
    #     miss_rate_img=miss_rate_img, hit_rate_img=hit_rate_img)
    if num_reads_served == 0:
        hit_rate = 0
        miss_rate = 0
    else:
        hit_rate = (num_reads_served - num_reads_missed) / num_reads_served * 100
        miss_rate = num_reads_missed / num_reads_served * 100
    return render_template("pages/show_stats/show_stats_form.html", title = stats_title, start_time = stats_timestamp[0],
        end_time = stats_timestamp[-1], num_requests_served = str(num_requests_served), 
        hit_rate = str(hit_rate) + "%",
        miss_rate = str(miss_rate) + "%",
        img=img_all_in_one)

def get_html_decoded_figure(x_axis, y_axis, title, xlabel, ylabel):
    output = io.BytesIO()

    num_items_figure = Figure()
    axis = num_items_figure.add_subplot(1, 1, 1)
    num_items_plot = axis.plot(x_axis, y_axis)
    axis.set_ylim(bottom=0)
    axis.set_title(title)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)

    # don't need to show so many ticks, set max number of ticks to 6
    n_bins = 6
    every_nth = max(1, math.ceil(len(x_axis)/6))
    axis.xaxis.set_major_locator(MultipleLocator(every_nth))
    axis.xaxis.set_minor_locator(MultipleLocator(1))
    # for n, label in enumerate(axis.xaxis.get_ticklabels()):
    #     if n % every_nth != 0:
    #         label.set_visible(False)

    num_items_figure.savefig(output, format='png')
    output.seek(0)
    figdata_png = base64.b64encode(output.getvalue())
    return figdata_png.decode('utf8')

def get_html_decoded_figure_all_in_one(x_axis, y_axes, titles, xlabels, ylabels):
    assert len(y_axes) == len(titles) and len(y_axes) == len(xlabels) and len(y_axes) == len(ylabels), "Length should be identical!"
    output = io.BytesIO()

    num_items_figure = plt.figure(figsize=(8, 6*len(y_axes)))
    for i in range(len(y_axes)):
        y_axis = y_axes[i]
        title = titles[i]
        xlabel = xlabels[i]
        ylabel = ylabels[i]

        axis = num_items_figure.add_subplot(len(y_axes), 1, i+1)
        num_items_plot = axis.plot(x_axis, y_axis)
        axis.set_ylim(bottom=0)
        axis.set_title(title)
        axis.set_xlabel(xlabel)
        axis.set_ylabel(ylabel)

        # don't need to show so many ticks, set max number of ticks to 6
        n_bins = 6
        every_nth = max(1, math.ceil(len(x_axis)/6))
        axis.xaxis.set_major_locator(MultipleLocator(every_nth))
        axis.xaxis.set_minor_locator(MultipleLocator(1))
    # for n, label in enumerate(axis.xaxis.get_ticklabels()):
    #     if n % every_nth != 0:
    #         label.set_visible(False)

    num_items_figure.savefig(output, format='png',bbox_inches='tight')
    output.seek(0)
    figdata_png = base64.b64encode(output.getvalue())
    decoded = figdata_png.decode('utf8')
    plt.close(num_items_figure)
    return decoded