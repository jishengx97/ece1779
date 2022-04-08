import osmnx
import math
import boto3
from decouple import config

BLOCK_SIZE = 0.01

def main():
    G = osmnx.load_graphml('./graph.graphml')
    dynamo_client = boto3.client('dynamodb', 
        aws_access_key_id=config('AWSAccessKeyId'), 
        aws_secret_access_key=config('AWSSecretKey')
    )

    min_x = 180
    max_x = -180
    min_y = 180
    max_y = -180
    for node_id in G.nodes:
        # print(node_id)
        # print(G.nodes[node_id])
        # print(G.nodes[node_id]["x"], G.nodes[node_id]["y"])
        if(G.nodes[node_id]["x"] < min_x):
            min_x = G.nodes[node_id]["x"]
        if(G.nodes[node_id]["x"] > max_x):
            max_x = G.nodes[node_id]["x"]

        if(G.nodes[node_id]["y"] < min_y):
            min_y = G.nodes[node_id]["y"]
        if(G.nodes[node_id]["y"] > max_y):
            max_y = G.nodes[node_id]["y"]
    print(min_x, min_y, max_x, max_y)

    lowest_cap_x = math.floor(min_x * 100) / 100
    highest_cap_x = math.ceil(max_x * 100) / 100

    lowest_cap_y = math.floor(min_y * 100) / 100
    highest_cap_y = math.ceil(max_y * 100) / 100

    print(lowest_cap_x, lowest_cap_y, highest_cap_x, highest_cap_y)

    # set 0.01*0.01 blocks
    num_x_blocks = round((highest_cap_x - lowest_cap_x)/BLOCK_SIZE)
    num_y_blocks = round((highest_cap_y - lowest_cap_y)/BLOCK_SIZE)

    print(num_x_blocks, num_y_blocks) 

    list_region = []
    for _ in range(num_x_blocks * num_y_blocks):
        list_region.append(0)

    for node_id in G.nodes:
        x = G.nodes[node_id]["x"]
        y = G.nodes[node_id]["y"]

        x_val = math.floor((x - lowest_cap_x) / BLOCK_SIZE)
        y_val = math.floor((y - lowest_cap_y) / BLOCK_SIZE)

        region_id = x_val + y_val * num_x_blocks
        print(G.nodes[node_id]["x"], G.nodes[node_id]["y"], region_id)

        list_region[region_id] += 1
        response = dynamo_client.put_item(
            TableName='table_find_nearest_point',
            Item={
                "region_id": {"N": str(region_id)},
                "node_id": {"N": str(node_id)},
                "x": {"N": str(x)},
                "y": {"N": str(y)},
            },
        )
    
    for i in range(num_x_blocks * num_y_blocks):
        print("region id", i, "has", list_region[i], "nodes")


if __name__ == "__main__":
    main()