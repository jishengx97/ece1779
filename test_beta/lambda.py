import json
import boto3
def lambda_handler(event, context):
    error_msg = ""
    path = []
    print('Receievd event: ' + json.dumps(event,indent=2))
    if 'path' in event and len(event['path']) > 0:
        error_msg = "case1"
        path = event['path']
    elif 'queryStringParameters' in event and 'path' in event ['queryStringParameters']:
        error_msg = "case2"
        path = event['queryStringparameters']['path']
    else:
        error_msg = "case3"
    
    if error_msg == "case1" or error_msg == "case2":
        path3d = [path[i:i+4] for i in range(0, len(path), 4)]
        path_tuples = []
        for path in path3d:
            path_tuples.append(tuple(path))
        dynamo_client = boto3.client('dynamodb')
        for path_tuple in path_tuples:
            response = dynamo_client.get_item(
                TableName='table_find_nearest_point',
                Key={
                    "region_id": {"N": str(path_tuple[3])},
                    "node_id": {"N": str(path_tuple[0]) },
                },
                ConsistentRead = True,
            )
            print(response)
            found = False
            for i in range(len(response["Item"]["adj_region"]["L"])):
                if (int(response["Item"]["adj_list"]["L"][i]["N"]) == path_tuple[1] and int(response["Item"]["adj_edge_id"]["L"][i]["N"]) == path_tuple[2]):
                    found = True
                    current_speed = float(response["Item"]["adj_current_speed"]["L"][i]["N"])
                    speed_limit = float(response["Item"]["adj_speed_limit"]["L"][i]["N"])
                    newspeed = speed_limit
                    if current_speed + 5 <= speed_limit:
                        newspeed = current_speed + 5
                    response["Item"]["adj_current_speed"]["L"][i]["N"] = str(newspeed)
                    next_response = dynamo_client.put_item(
                        TableName='table_find_nearest_point',
                        Item={
                            "region_id": {"N": str(path_tuple[3])},
                            "node_id": {"N": str(path_tuple[0])},
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
                
    return error_msg