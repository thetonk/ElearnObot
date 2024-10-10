from requests import post
import config
from urllib.parse import urlparse, parse_qs

headers = {"User-Agent":"MoodleMobile 420.69"} # the server checks if we are the moodle app

qrURL = input("Give the QR URL: ")
query = urlparse(qrURL).query
data_dict = parse_qs(query)
print(f"QR token: {data_dict['qrlogin'][0]}, User ID: {data_dict['userid'][0]}")
responseJson = post(f"https://{config.DOMAIN}/lib/ajax/service.php?info=tool_mobile_get_tokens_for_qr_login&lang=en_us", headers=headers, json=[{"index":0,"methodname":"tool_mobile_get_tokens_for_qr_login","args":{"qrloginkey":data_dict["qrlogin"][0],"userid":int(data_dict["userid"][0])}}]).json()
if(responseJson[0]['error']):
    print(f"Got error {responseJson[0]}")
    print("The QR code may have expired.")
    print("You also need to make sure that you run this script from the same IP you used to get the QR.")
else:
    print("Success!")
    print(f"Token (use this for the bot): {responseJson[0]['token']}")
    print(f"privateToken: {responseJson[0]['privatetoken']}")