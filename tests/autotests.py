import requests
IMAGE_DIR = 'images/'

def test():
    # first upload three images
    image_png = open(IMAGE_DIR+'pngtest.png', 'rb')
    image_jpeg = open(IMAGE_DIR+'jpegtest.png', 'rb')
    image_gif = open(IMAGE_DIR+'figtest.png', 'rb')

    if not perform_upload_and_test(image_png, "pngkey"):
        print("png test failed!")
    if not perform_upload_and_test(image_jpeg, "jpegkey"):
        print("jpeg test failed!")
    if not perform_upload_and_test(image_gif, "gifkey"):
        print("gif test failed!")

    # now retrieve all keys
    keys = ["pngkey", "jpegkey", "gifkey"]
    if not get_all_keys_and_test(keys):
        print("listkey test failed!")
    

def perform_upload_and_test(image, key):
    files = dict("key" = key, "file" = image)
    response = requests.post("127.0.0.1:5000/api/upload", data=files)

    try:
        response_data = response.json()
        if (response_data.get("success") == "true"):
            return True
        else:
            print(response_data)
            return False
    except:
        return False

def get_all_keys_and_test(keys):
    response = requests.post("127.0.0.1:5000/api/list_keys")
    response_data = response.json()

    try:
        if (response_data.get("success") == "true"):
            returned_keys = response_data.get("keys")
            for key in keys:
                if key not in returned_keys:
                    print("key", key, "is not in returned keys")
                    return False
            return True
        else:
            print(response_data)
            return False
    except:
        return False