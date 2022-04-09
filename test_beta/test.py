import osmnx
import math
import boto3
from decouple import config
from boto3.dynamodb.conditions import Key

input_x = -79.3479061
input_y = 43.7792657

input_x = -79.2859861
input_y = 43.7472545

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


x = input_x
y = input_y
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

print(osmnx.distance.nearest_nodes(G,input_x,input_y,return_dist=False))
