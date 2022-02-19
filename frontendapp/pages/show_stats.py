from flask import render_template, url_for, request, json
from frontendapp import webapp
import matplotlib
from common import models
from datetime import datetime
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import base64

@webapp.route('/show_stats',methods=['GET'])
def show_stats():
    num_stats_entries = webapp.db_session.query(models.MemcacheStats).count()

    if (num_stats_entries == 0):
        return render_template("pages/show_stats/show_stats_form.html", title = "STATS", error_msg = None)
    # Either get all entries from the database, or get entries for the last 10 minutes,
    # which is 60 / 5 * 10 = 120 entries
    num_entried_needed = min(num_stats_entries, 120)
    results = webapp.db_session.query(models.MemcacheStats).order_by(models.MemcacheStats.id.desc()).limit(num_entried_needed)
    # Reverse to get sequence in time
    results = results[::-1]

    # prepare data to generate figures
    num_items = []
    total_size = []
    num_requests_served = []
    miss_rate = []
    hit_rate = []
    stats_timestamp = []
    for item in results:
        num_items.append(item.num_items)
        total_size.append(item.total_size)
        num_requests_served.append(item.num_requests_served)
        miss_rate.append(item.miss_rate)
        hit_rate.append(item.hit_rate)
        stats_timestamp.append(item.stats_timestamp.strftime("%X"))
    print (num_items)
    print (total_size)
    print (num_requests_served)
    print (miss_rate)
    print (hit_rate)
    print (stats_timestamp)
    
    num_items_img = get_html_decoded_figure(
        stats_timestamp, 
        num_items, 
        'Number of Items in Memcache', # title
        'Time (Eastern)', # xlabel
        'Items' # ylabel
    )

    return render_template("pages/show_stats/show_stats_form.html", title = "STATS", error_msg = None, img=num_items_img)

def get_html_decoded_figure(x_axis, y_axis, title, xlabel, ylabel):
    output = io.BytesIO()

    num_items_figure = Figure()
    axis = num_items_figure.add_subplot(1, 1, 1)
    num_items_plot = axis.plot(x_axis, y_axis)
    axis.set_ylim(bottom=0)
    axis.set_title(title)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)

    # don't need to show so many ticks
    every_nth = 2
    for n, label in enumerate(axis.xaxis.get_ticklabels()):
        if n % every_nth != 0:
            label.set_visible(False)

    num_items_figure.savefig(output, format='png')
    output.seek(0)
    figdata_png = base64.b64encode(output.getvalue())
    return figdata_png.decode('utf8')