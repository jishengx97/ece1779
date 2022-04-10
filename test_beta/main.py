from flask import Flask
webapp = Flask(__name__)
from flask import render_template, url_for, request, send_from_directory
# from test_beta import webapp
from flask import json
import osmnx
import math
import boto3
from decouple import config
from boto3.dynamodb.conditions import Key
import queue
import shapely
import PIL
import os
## target_x = -79.3479061
## target_y = 43.7792657
# target_x = -79.2990569
# target_y = 43.7560562
# source_x = -79.2859861
# source_y = 43.7472545



title = "Map"

@webapp.route('/',methods=['GET'])
def main():
    return render_template("main.html",title = title, error_msg = None,img_file = "_back.png")


@webapp.route('/',methods=['POST'])
def key_save():
    error_msg = None

    source_x = request.form.get("source_x")
    source_y = request.form.get("source_y")
    target_x = request.form.get("target_x")
    target_y = request.form.get("target_y")
    if source_x == "":
        error_msg = "Missing Departure Longitude"
        return render_template("main.html",title = title,error_msg = error_msg,img_file = "_back.png")
    try:
        source_x = float(source_x)
    except ValueError:
        error_msg = "Departure Longitude is not a float"
        return render_template("main.html",title = title,error_msg = error_msg,img_file = "_back.png")
    if not -79.3941167 <= source_x <= -79.2820821:
        error_msg = "Departure Longitude out of range Now we only support -79.3941167 <= Longitude <= -79.2820821"
        return render_template("main.html",title = title,error_msg = error_msg,img_file = "_back.png")


    if source_y == "":
        error_msg = "Missing Departure Latitude"
        return render_template("main.html",title = title,error_msg = error_msg,img_file = "_back.png")
    try:
        source_y = float(source_y)
    except ValueError:
        error_msg = "Departure Latitude is not a float"
        return render_template("main.html",title = title,error_msg = error_msg,img_file = "_back.png")   
    if not 43.7270892 <= source_y <= 43.807974:
        error_msg = "Departure Latitude out of range Now we only support 43.7270892 <= Latitude <= 43.807974"
        return render_template("main.html",title = title,error_msg = error_msg,img_file = "_back.png")


    if target_x == "":
        error_msg = "Missing Destination Longitude"
        return render_template("main.html",title = title,error_msg = error_msg,img_file = "_back.png")
    try:
        target_x = float(target_x)
    except ValueError:
        error_msg = "Destination Longitude is not a float"
        return render_template("main.html",title = title,error_msg = error_msg,img_file = "_back.png") 
    if not -79.3941167 <= target_x <= -79.2820821:
        error_msg = "Destination Longitude out of range Now we only support -79.3941167 <= Longitude <= -79.2820821"
        return render_template("main.html",title = title,error_msg = error_msg,img_file = "_back.png")


    if target_y == "":
        error_msg = "Missing Destination Latitude"
        return render_template("main.html",title = title,error_msg = error_msg,img_file = "_back.png")
    try:
        target_y = float(target_y)
    except ValueError:
        error_msg = "Destination Latitude is not a float"
        return render_template("main.html",title = title,error_msg = error_msg,img_file = "_back.png")
    if not 43.7270892 <= target_y <= 43.807974:
        error_msg = "Destination Latitude out of range Now we only support 43.7270892 <= Latitude <= 43.807974"
        return render_template("main.html",title = title,error_msg = error_msg,img_file = "_back.png")

    BLOCK_SIZE = 0.01
    G = osmnx.load_graphml('./test_beta/base.graphml')
    dynamo_client = boto3.client('dynamodb', 
        aws_access_key_id=config('AWSAccessKeyId'), 
        aws_secret_access_key=config('AWSSecretKey')
    )

    min_x = -79.3941167
    max_x = -79.2820821
    min_y = 43.7270892
    max_y = 43.807974

    lowest_cap_x = -79.4
    highest_cap_x = -79.28
    lowest_cap_y = 43.72
    highest_cap_y = 43.81

    # set 0.01*0.01 blocks
    num_x_blocks = 12
    num_y_blocks = 9


    x = source_x
    y = source_y
    x_val = math.floor((x - lowest_cap_x) / BLOCK_SIZE)
    y_val = math.floor((y - lowest_cap_y) / BLOCK_SIZE)

    region_id = x_val + y_val * num_x_blocks  
    response = dynamo_client.query(
        TableName='table_find_nearest_point',
        ExpressionAttributeValues={
            ':v1': {
                'N': str(region_id),
            },
        },
        KeyConditionExpression = "region_id = :v1",
    )

    for item in response['Items']:
        G.add_node(int(item['node_id']['N']), x=float(item['x']['N']) ,y=float(item['y']['N']))

    source_id = osmnx.distance.nearest_nodes(G,source_x,source_y,return_dist=False)

    G = osmnx.load_graphml('./test_beta/base.graphml')

    x = target_x
    y = target_y
    x_val = math.floor((x - lowest_cap_x) / BLOCK_SIZE)
    y_val = math.floor((y - lowest_cap_y) / BLOCK_SIZE)

    region_id = x_val + y_val * num_x_blocks

    response = dynamo_client.query(
        TableName='table_find_nearest_point',
        ExpressionAttributeValues={
            ':v1': {
                'N': str(region_id),
            },
        },
        KeyConditionExpression = "region_id = :v1",
    )

    for item in response['Items']:
        G.add_node(int(item['node_id']['N']), x=float(item['x']['N']) ,y=float(item['y']['N']))

    target_id = osmnx.distance.nearest_nodes(G,target_x,target_y,return_dist=False)

    G = osmnx.load_graphml('./test_beta/base.graphml')

    edge_table = {}
    path = []
    dote = []
    rank = queue.PriorityQueue()
    visited_node = set()

    response = dynamo_client.query(
        TableName='table_edges',
        ExpressionAttributeValues={
            ':v1': {
                'N': str(source_id),
            },
        },
        KeyConditionExpression = "src_node_id = :v1",
    )

    visited_node.add(source_id)
    for item in response['Items']:
        item_tuple = eval(item['edge_tuple']['S'])
        edge_table[item_tuple] = item
        rank.put((float(item['length']['N'])/float(item['current_speed']['N']),[item_tuple]))

    while(not rank.empty()):
        toppath = rank.get()
        if(toppath[1][-1][1]==target_id):
            path = toppath[1].copy()
            visited_node.add(toppath[1][-1][1])
            rank = queue.PriorityQueue()
        else:
            if(not toppath[1][-1][1] in visited_node):
                visited_node.add(toppath[1][-1][1])
                response = dynamo_client.query(
                    TableName='table_edges',
                    ExpressionAttributeValues={
                        ':v1': {
                            'N': str(toppath[1][-1][1]),
                        },
                    },
                    KeyConditionExpression = "src_node_id = :v1",
                )
                if response['Count']!=0:
                    for item in response['Items']:
                        item_tuple = eval(item['edge_tuple']['S'])
                        edge_table[item_tuple] = item
                        temppath = toppath[1].copy()
                        temppath.append(item_tuple)
                        rank.put((toppath[0]+float(item['length']['N'])/float(item['current_speed']['N']),temppath)) 

    pathset = set(path)
    for path in pathset:
        dote.append(path[0])
        dote.append(path[1])
    doteset = set(dote)
    for dote in doteset:
        response = dynamo_client.get_item(
            TableName='table_node',
            Key={
                "node_id": {"N": str(dote)},
            },
        )
        G.add_node(dote, x=float(response['Item']['x']['N']) ,y=float(response['Item']['y']['N']))

    for path in pathset:
        dictionary_list = edge_table[path]['geometry']['L']
        if len(dictionary_list) > 0:
            geometry_tup_list = []
            for dictionary in dictionary_list:
                geometry_tup_list.append(eval(dictionary['S']))
            geometry_linstr = shapely.geometry.linestring.LineString(geometry_tup_list)
            G.add_edge(path[0],path[1],geometry = geometry_linstr)
        else:
            G.add_edge(path[0],path[1])
    ns = [50 if i_d == source_id or i_d == target_id else 0 for i_d in G.nodes]
    na = [1 if i_d == source_id or i_d == target_id else 0 for i_d in G.nodes]
    nc = ['#FF7874' if i_d == target_id else '#78DAFF' for i_d in G.nodes]
    el = [4 for u, v, d in G.edges]
    ea = [1 for u, v, d in G.edges]
    ec = ['#78DAFF' for u, v, d in G.edges]
    fig, ax = osmnx.plot_graph(G,figsize=(10,10),bgcolor='w',node_size=ns,node_alpha=na,node_color=nc,edge_linewidth=el,edge_alpha=ea,edge_color=ec,show=False,close=True,filepath=None)
    if os.path.exists('./test_beta/_path.png'):
        os.remove('./test_beta/_path.png')
    fig.savefig('./test_beta/_path.png')
    back = PIL.Image.open('./test_beta/_back.png')
    testtt = PIL.Image.open('./test_beta/_path.png')
    back = back.convert("RGBA")
    testtt = testtt.convert("RGBA")
    blended = PIL.Image.blend(back, testtt, alpha=0.3)
    if os.path.exists('./test_beta/_blended.png'):
        os.remove('./test_beta/_blended.png')
    blended.save('./test_beta/_blended.png')
    return render_template("main.html",title = title,error_msg = error_msg,img_file = '_blended.png')

@webapp.route('/<filename>')
def send_img(filename):
    return send_from_directory(os.getcwd()+"/test_beta/",filename)