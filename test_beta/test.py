import osmnx
import math
import boto3
from decouple import config
from boto3.dynamodb.conditions import Key
import queue
import shapely
import PIL

target_x = -79.3479061
target_y = 43.7792657
# target_x = -79.2990569
# target_y = 43.7560562
source_x = -79.2859861
source_y = 43.7472545

BLOCK_SIZE = 0.01
G = osmnx.load_graphml('./base.graphml')
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
# print(G.nodes[node_id]["x"], G.nodes[node_id]["y"], region_id)

response = dynamo_client.query(
    TableName='table_find_nearest_point',
    # Key={
    #     "region_id": {"N": str(region_id)},
    # },
    ExpressionAttributeValues={
        ':v1': {
            'N': str(region_id),
        },
    },
    KeyConditionExpression = "region_id = :v1",
    # Key("region_id").eq(str(region_id)),
    # ProjectionExpression = "node_id"
)

for item in response['Items']:
    G.add_node(int(item['node_id']['N']), x=float(item['x']['N']) ,y=float(item['y']['N']))

source_id = osmnx.distance.nearest_nodes(G,source_x,source_y,return_dist=False)

G = osmnx.load_graphml('./base.graphml')

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
    rank.put((float(item['length']['N'])/float(item['speed_kph']['N']),[item_tuple]))

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
                    rank.put((toppath[0]+float(item['length']['N'])/float(item['speed_kph']['N']),temppath)) 

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
ns = [0 for i_d in G.nodes]
na = [0 for i_d in G.nodes]
nc = ['#7D7D7D' for i_d in G.nodes]
el = [4 for u, v, d in G.edges]
ea = [1 for u, v, d in G.edges]
ec = ['#78DAFF' for u, v, d in G.edges]
fig, ax = osmnx.plot_graph(G,figsize=(10,10),bgcolor='w',node_size=ns,node_alpha=na,node_color=nc,edge_linewidth=el,edge_alpha=ea,edge_color=ec,show=False,close=True,filepath=None)
fig.savefig('_testtt.png')
back = PIL.Image.open('_back.png')
testtt = PIL.Image.open('_testtt.png')
back = back.convert("RGBA")
testtt = testtt.convert("RGBA")
blended = PIL.Image.blend(back, testtt, alpha=0.3)
blended.save("blended.png")