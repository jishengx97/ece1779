import requests
import hashlib
import time
IMAGE_DIR = 'images/'

def test():
    # cycle for 's' is 4 %4 is 0
    # cycle for 'a' is 1 %4 is 1
    # cycle for 'e' is 2 %4 is 2
    # cycle for 'b' is 15 %4 is 3
    image_jpeg = open(IMAGE_DIR+'jpegtest.jpeg', 'rb')
    keys = ['s', 'a', 'e', 'b']
    for key in keys:
        value = {"key":key}
        response = requests.post("http://127.0.0.1:5000/api/upload", data=value,files={"file":image_jpeg})

        try:
            response_data = response.json()
            if (response_data.get("success") == "true"):
                print("uploaded key", key)
            else:
                print("failed to upload key", key)
        except:
            print("failed to upload key", key)

    count = 0
    while True:
        for key in keys:
            response = requests.post("http://127.0.0.1:5000/api/key/"+key)
            count += 1
            try:
                response_data = response.json()
                if (response_data.get("success") == "true"):
                    print("round", count, "succeeded")
                else:
                    print("get image not success, response=", response)
            except:
                print("get image failed for unknown reaseon, response=", response)

            time.sleep(2)


def main():
    test()

if __name__ == "__main__":
    main()