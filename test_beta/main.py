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
import requests
import json
## target_x = -79.3479061
## target_y = 43.7792657
# target_x = -79.2990569
# target_y = 43.7560562
# source_x = -79.2859861
# source_y = 43.7472545



title = "Map"
BLOCK_SIZE = 0.01

def get_region_id(x,y):
    min_x = -79.3941167
    max_x = -79.2820821
    min_y = 43.7270892
    max_y = 43.807974

    lowest_cap_x = -79.4
    highest_cap_x = -79.28
    lowest_cap_y = 43.72
    highest_cap_y = 43.81
    
    num_x_blocks = round((highest_cap_x - lowest_cap_x)/BLOCK_SIZE)
    num_y_blocks = round((highest_cap_y - lowest_cap_y)/BLOCK_SIZE)

    x_val = math.floor((x - lowest_cap_x) / BLOCK_SIZE)
    y_val = math.floor((y - lowest_cap_y) / BLOCK_SIZE)
    region_id = x_val + y_val * num_x_blocks  
    return region_id

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


    G = osmnx.load_graphml('./base.graphml')
    dynamo_client = boto3.client('dynamodb')
    visited_region = set()
    my_local_graph = {}

    region_id = get_region_id(source_x, source_y)
    response = dynamo_client.query(
        TableName='table_find_nearest_point',
        ExpressionAttributeValues={
            ':v1': {
                'N': str(region_id),
            },
        },
        KeyConditionExpression = "region_id = :v1",
    )

    visited_region.add(region_id)

    for item in response['Items']:
        node_id = int(item['node_id']['N'])
        
        my_local_graph[node_id] = item
        if node_id not in G.nodes:
            G.add_node(node_id, x=float(item['x']['N']) ,y=float(item['y']['N']))

    source_id = osmnx.distance.nearest_nodes(G,source_x,source_y,return_dist=False)

    region_id = get_region_id(target_x, target_y)
    response = dynamo_client.query(
        TableName='table_find_nearest_point',
        ExpressionAttributeValues={
            ':v1': {
                'N': str(region_id),
            },
        },
        KeyConditionExpression = "region_id = :v1",
    )
    visited_region.add(region_id)

    for item in response['Items']:
        node_id = int(item['node_id']['N'])
        
        my_local_graph[node_id] = item
        if node_id not in G.nodes:
            G.add_node(node_id, x=float(item['x']['N']) ,y=float(item['y']['N']))

    target_id = osmnx.distance.nearest_nodes(G,target_x,target_y,return_dist=False)

    edge_table = {}
    path = []
    dote = []
    rank = queue.PriorityQueue()
    visited_node = set()


    visited_node.add(source_id)
    assert source_id in my_local_graph

    for i in range(len(my_local_graph[source_id]["adj_region"]["L"])):
        adj_region_id = int(my_local_graph[source_id]["adj_region"]["L"][i]["N"])
        if not adj_region_id in visited_region:
            response = dynamo_client.query(
                TableName='table_find_nearest_point',
                ExpressionAttributeValues={
                    ':v1': {
                        'N': str(adj_region_id),
                    },
                },
                KeyConditionExpression = "region_id = :v1",
            )
            visited_region.add(adj_region_id)

            for item in response['Items']:
                node_id = int(item['node_id']['N'])

                my_local_graph[node_id] = item
                if node_id not in G.nodes:
                    G.add_node(node_id, x=float(item['x']['N']) ,y=float(item['y']['N']))
        
        length = my_local_graph[source_id]["adj_length"]["L"][i]["N"]
        speed = my_local_graph[source_id]["adj_current_speed"]["L"][i]["N"]
        item_tuple = (source_id, int(my_local_graph[source_id]["adj_list"]["L"][i]["N"]), int(my_local_graph[source_id]["adj_edge_id"]["L"][i]["N"]))
        rank.put((float(length)/float(speed),[item_tuple]))

    while(not rank.empty()):
        toppath = rank.get()
        if(toppath[1][-1][1]==target_id):
            path = toppath[1].copy()
            visited_node.add(toppath[1][-1][1])
            rank = queue.PriorityQueue()
        else:
            next_node_id = toppath[1][-1][1]
            if(not next_node_id in visited_node):
                visited_node.add(next_node_id)
                assert next_node_id in my_local_graph
                for i in range(len(my_local_graph[next_node_id]["adj_region"]["L"])):
                    adj_region_id = int(my_local_graph[next_node_id]["adj_region"]["L"][i]["N"])
                    if not adj_region_id in visited_region:
                        response = dynamo_client.query(
                            TableName='table_find_nearest_point',
                            ExpressionAttributeValues={
                                ':v1': {
                                    'N': str(adj_region_id),
                                },
                            },
                            KeyConditionExpression = "region_id = :v1",
                        )
                        visited_region.add(adj_region_id)

                        for item in response['Items']:
                            node_id = int(item['node_id']['N'])
                            my_local_graph[node_id] = item
                            if node_id not in G.nodes:
                                G.add_node(node_id, x=float(item['x']['N']) ,y=float(item['y']['N']))
                    
                    length = my_local_graph[next_node_id]["adj_length"]["L"][i]["N"]
                    speed = my_local_graph[next_node_id]["adj_current_speed"]["L"][i]["N"]
                    item_tuple = (next_node_id, int(my_local_graph[next_node_id]["adj_list"]["L"][i]["N"]), int(my_local_graph[next_node_id]["adj_edge_id"]["L"][i]["N"]))
                    temppath = toppath[1].copy()
                    temppath.append(item_tuple)
                    rank.put((toppath[0]+float(length)/float(speed),temppath))
    
    pathset = set(path)
    print(pathset)
    pathes = []
    for path in pathset:
        response = dynamo_client.get_item(
            TableName='table_edges',
            Key={
                "src_node_id": {"N": str(path[0])},
                "edge_tuple": {"S":'(' + str(path[0])+', '+str(path[1])+', '+str(path[2])+')' },
            },
        )

        dictionary_list = response["Item"]["geometry"]['L']
        if len(dictionary_list) > 0:
            geometry_tup_list = []
            for dictionary in dictionary_list:
                geometry_tup_list.append(eval(dictionary['S']))
            geometry_linstr = shapely.geometry.linestring.LineString(geometry_tup_list)
            G.add_edge(path[0],path[1],geometry = geometry_linstr)
        else:
            G.add_edge(path[0],path[1])
        
        path_source = path[0]
        path_source_x = float(my_local_graph[path_source]["x"]["N"])
        path_source_y = float(my_local_graph[path_source]["y"]["N"])
        region_id = get_region_id(path_source_x, path_source_y)

        response = dynamo_client.get_item(
            TableName='table_find_nearest_point',
            Key={
                "region_id": {"N": str(region_id)},
                "node_id": {"N": str(path_source) },
            },
            ConsistentRead = True,
        )

        found = False
        for i in range(len(response["Item"]["adj_region"]["L"])):
            if (int(response["Item"]["adj_list"]["L"][i]["N"]) == path[1] and int(response["Item"]["adj_edge_id"]["L"][i]["N"]) == path[2]):
                found = True
                current_speed = float(response["Item"]["adj_current_speed"]["L"][i]["N"])
                newspeed = current_speed
                if current_speed > 5:
                    newspeed = current_speed - 5
                response["Item"]["adj_current_speed"]["L"][i]["N"] = str(newspeed)
                next_response = dynamo_client.put_item(
                    TableName='table_find_nearest_point',
                    Item={
                        "region_id": {"N": str(region_id)},
                        "node_id": {"N": str(path_source)},
                        "x": response["Item"]["x"],
                        "y": response["Item"]["y"],
                        "adj_list": response["Item"]["adj_list"],
                        "adj_edge_id": response["Item"]["adj_edge_id"],
                        "adj_region": response["Item"]["adj_region"],
                        "adj_length": response["Item"]["adj_length"],
                        "adj_speed_limit": response["Item"]["adj_speed_limit"],
                        "adj_current_speed": response["Item"]["adj_current_speed"],
                    },
                )
        assert found
        pathes.append(path[0])
        pathes.append(path[1])
        pathes.append(path[2])
        pathes.append(region_id)
    
    data = {
        "input": "{  \"path\":  "+ json.dumps(pathes) +" }",
        "stateMachineArn": "arn:aws:states:us-east-1:968434901467:stateMachine:MyStateMachine",
    }

    response = requests.post("https://nadcdu8gn4.execute-api.us-east-1.amazonaws.com/prod/execution", data=json.dumps(data))
    
    ns = [50 if i_d == source_id or i_d == target_id else 0 for i_d in G.nodes]
    na = [1 if i_d == source_id or i_d == target_id else 0 for i_d in G.nodes]
    nc = ['#FF7874' if i_d == target_id else '#78DAFF' for i_d in G.nodes]
    el = [4 for u, v, d in G.edges]
    ea = [1 for u, v, d in G.edges]
    ec = ['#78DAFF' for u, v, d in G.edges]
    fig, ax = osmnx.plot_graph(G,figsize=(10,10),bgcolor='w',node_size=ns,node_alpha=na,node_color=nc,edge_linewidth=el,edge_alpha=ea,edge_color=ec,show=False,close=True,filepath=None)
    if os.path.exists('./_path.png'):
        os.remove('./_path.png')
    fig.savefig('./_path.png')
    back = PIL.Image.open('./_back.png')
    testtt = PIL.Image.open('./_path.png')
    back = back.convert("RGBA")
    testtt = testtt.convert("RGBA")
    blended = PIL.Image.blend(back, testtt, alpha=0.3)
    if os.path.exists('./_blended.png'):
        os.remove('./_blended.png')
    blended.save('./_blended.png')
    return render_template("main.html",title = title,error_msg = error_msg,img_file = '_blended.png')

@webapp.route('/<filename>')
def send_img(filename):
    return send_from_directory(os.getcwd()+"/",filename)