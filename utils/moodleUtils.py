import requests, config, os
from bs4 import BeautifulSoup

USER_AGENT = "MoodleMobile 4.1.1"
HEADERS = {"User-Agent": USER_AGENT}

class moodleInterface():

    def __init__(self):
        self.URL = "https://{domain}/webservice/rest/server.php?wstoken={token}&moodlewsrestformat=json".format(domain=config.DOMAIN, token=config.API_TOKEN)

    # def generateMD5Hash(self, *,fileURL: str):
    #     return hashlib.md5(requests.get(fileURL).content).hexdigest() #kinda memory inefficient though

    def getCourses(self):
        parameters = {"wsfunction": "core_enrol_get_users_courses", "userid": config.USERID}
        r  = requests.get(self.URL, params=parameters, headers=HEADERS).json()
        return r

    def getCourseData(self, *, courseID: int):
        parameters = {"wsfunction": "core_course_get_contents", "courseid" : courseID}
        r = requests.get(self.URL, params=parameters, headers=HEADERS).json()
        return r
    
    def getForums(self, *, courseIDs: list):
        parameters = {"wsfunction": "mod_forum_get_forums_by_courses"}
        for i in range(len(courseIDs)):
            parameters["courseids[{}]".format(i)] = courseIDs[i]
        r = requests.get(self.URL, params=parameters, headers=HEADERS).json()
        return r
    
    def getForumDiscussions(self, *, forumID: int):
        parameters = {"wsfunction": "mod_forum_get_forum_discussions", "forumid": forumID}
        r = requests.get(self.URL, params=parameters, headers=HEADERS).json()
        return r

    def getQuizzes(self, *, courseIDs: list):
        parameters = {"wsfunction": "mod_quiz_get_quizzes_by_courses"}
        for i in range(len(courseIDs)):
            parameters["courseids[{}]".format(i)] = courseIDs[i]

        r = requests.get(self.URL, params=parameters, headers=HEADERS).json()
        return r

    def getAssignments(self, *, courseIDs: list):
        parameters = {"wsfunction" : "mod_assign_get_assignments"}
        for i in range(len(courseIDs)):
            parameters["courseids[{}]".format(i)] = courseIDs[i]

        r = requests.get(self.URL, params=parameters, headers=HEADERS).json()
        return r


class File:
    def __init__(self, *, name, path,size, timeModified, mimeType,author, fileURL, License, moduleID):
        self.filename = name
        self.path = path
        self.size = size
        self.mimeType = mimeType
        self.author = author
        self.URL = fileURL
        self.timeModified = timeModified
        self.License = License
        self.moduleID = moduleID
    
    def download(self, downloadPath):
        dest = os.path.join(downloadPath, self.path[1:])
        if not os.path.exists(dest):
            os.makedirs(dest, exist_ok=True)
        r = requests.get(f"{self.URL}&token={config.API_TOKEN}",headers=HEADERS).content
        if os.path.exists(os.path.join(dest, self.filename)):
            count = 1
            while True:
                if not os.path.exists(os.path.join(dest, self.filename.replace(".", f"({count})."))):
                    with open(os.path.join(dest, self.filename.replace(".", f"({count}).")), "wb") as f:
                        f.write(r)
                        f.flush()
                        f.close()
                    break
                count += 1
        else:
            with open(os.path.join(dest, self.filename), "wb") as f:
                f.write(r)
                f.flush()
                f.close()            

class Discussion:
    def __init__(self,*, name, discussionID, forumID, message, timeModified,files):
        self.name = name
        self.ID = discussionID
        self.forumID = forumID
        self.URL = "https://{}/mod/forum/discuss.php?d={}".format(config.DOMAIN, discussionID)
        self.message = message
        self.timeModified = timeModified
        self.files=files

class Page:
    def __init__(self, *,  name, pageID, pageURL, description):
        self.name = name
        self.ID = pageID
        self.URL = pageURL
        self.description = description

class Label:
        def __init__(self, *, description):
            self.description = description

class Forum:
    def __init__(self, *, name, forumID, forumURL, discussionList):
        self.name = name
        self.ID = forumID
        self.URL = forumURL
        self.discussions = discussionList

class Assignment:
    def __init__(self,*, name, assignmentID,assignmentURL, timeOpened, timeDue):
        self.ID = assignmentID
        self.name = name
        self.URL = assignmentURL
        self.timeOpened = timeOpened
        self.timeDue = timeDue

class Quiz:
    def __init__(self,*,name, quizID, quizURL):
        self.name = name
        self.ID = quizID
        self.URL = quizURL

class Workshop:
    def __init__(self,*,name, workshopID, workshopURL):
        self.name = name
        self.ID = workshopID
        self.URL = workshopURL

class Course:

    def __init__(self, *,fullName,courseID,summary):
        self.ID = courseID
        self.name = fullName
        soup = BeautifulSoup(summary, "html.parser")
        self.summary = soup.get_text()
        self.forums = []
        self.quizzes = []
        self.assignments = []
        self.files = []
        self.workshops = []
        self.pages = []
        self.labels = []
        self.URL = f"https://{config.DOMAIN}/course/view.php?id={courseID}"
        #self.refresh()

    def refresh(self):
        moodle = moodleInterface()
        for unit in moodle.getCourseData(courseID=self.ID):
            modules = unit["modules"]
            for module in modules:
                moduleType = module["modname"]
                if moduleType == "forum":
                    forumID = module["instance"]
                    discussions = []
                    for discussion in moodle.getForumDiscussions(forumID=forumID)["discussions"]:
                        attachments = []
                        if "attachments" in  discussion:
                            for attachment in discussion["attachments"]:
                                attachments.append(File(
                                    name=attachment["filename"],
                                    path=attachment["filepath"],
                                    timeModified=attachment["timemodified"],
                                    size=attachment["filesize"],
                                    fileURL=attachment["fileurl"],
                                    mimeType=attachment["mimetype"],
                                    author=discussion["usermodifiedfullname"],
                                    License="",
                                    moduleID=-1
                                ))
                        soup = BeautifulSoup(discussion["message"], "html.parser")
                        discussions.append(Discussion(
                            name=discussion["name"],
                            discussionID=discussion["discussion"],
                            forumID=forumID,
                            message=soup.get_text(),
                            timeModified=discussion["modified"],
                            files=attachments
                        ))

                    self.forums.append(Forum(
                    name=module["name"],
                    forumID=forumID,
                    forumURL=module["url"],
                    discussionList=discussions
                    ))


                elif moduleType == "quiz":
                    self.quizzes.append(Quiz(
                        name=module["name"],
                        quizID=module["id"],
                        quizURL=module["url"]
                    ))

                elif moduleType == "assign":
                    self.assignments.append(Assignment(
                        name = module["name"],
                        assignmentID = module["id"],
                        assignmentURL = module["url"],
                        timeOpened = module["dates"][0]["timestamp"] if "dates" in module and len(module["dates"]) == 2 else 0,
                        timeDue = module["dates"][1]["timestamp"] if "dates" in module and len(module["dates"]) == 2 else 0
                    ))
                elif moduleType == "workshop":
                    self.workshops.append(Workshop(
                        name = module["name"],
                        workshopID = module["id"],
                        workshopURL = module["url"]
                    ))

                elif moduleType == "label":
                    soup = BeautifulSoup(module["description"],"html.parser")
                    self.labels.append(Label(
                        description = soup.get_text()
                    ))

                elif moduleType == "page":

                    #NOTE: pages always have one index.html file which is their text content.
                    
                    htmlpath = module["contents"][0]["fileurl"] 
                    html = requests.get(htmlpath+"&token={}".format(config.API_TOKEN),headers=HEADERS).content
                    soup = BeautifulSoup(html, "html.parser")
                    self.pages.append(Page(
                        name = module["name"],
                        pageID = module["id"],
                        pageURL = module["url"],
                        description=soup.get_text()
                    ))

                if "contents" in module and moduleType != "page" and moduleType != "book":
                    files = module["contents"]
                    for file in files:
                        self.files.append(File(
                            name=file["filename"],
                            path=file["filepath"],
                            fileURL=file["fileurl"],
                            timeModified=file["timemodified"],
                            mimeType= file["mimetype"] if "mimetype" in file else "",
                            size=file["filesize"],
                            author=file["author"],
                            License=file["license"],
                            moduleID=module["id"]
                         ))
