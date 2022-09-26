import requests, config


GET_FILES_URL = "https://{domain}/webservice/rest/server.php?wstoken={token}&wsfunction=core_course_get_contents&courseid={courseid}&moodlewsrestformat=json"
GET_COURSES_URL = "https://{domain}/webservice/rest/server.php?wstoken={token}&wsfunction=core_enrol_get_users_courses&userid={userid}&moodlewsrestformat=json"

r = requests.get(GET_COURSES_URL.format(domain=config.DOMAIN,token=config.API_TOKEN, userid=config.USERID))
courses = r.json()

for course in courses:
    id = course["id"]
    courseUnits = requests.get(GET_FILES_URL.format(domain=config.DOMAIN, token=config.API_TOKEN, courseid=id)).json()
    for unit in courseUnits:
        modules = unit["modules"]
        for module in modules:
            #print(module)
            if "contents" in module:
                files = module["contents"]
                for file in files:
                    #print("========================================================================================")
                    #print("FILENAME\t" + file["filename"]+"\n"+ "FILEURL\t" + file["fileurl"]+"\n")
                    with open("out.txt", "a", encoding="utf-8") as txtfile:
                        txtfile.write("========================================================================================\n")
                        txtfile.write("FILENAME\t" + file["filename"]+"\n"+ "FILEURL\t" + file["fileurl"]+"\n")