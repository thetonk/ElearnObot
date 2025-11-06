import requests, config, os, blake3, tempfile, re, codecs, logging
from bs4 import BeautifulSoup
from utils import loggingUtils, enums

USER_AGENT = "MoodleMobile 4.1.1"
HEADERS = {"User-Agent": USER_AGENT}

def hashInternetData(logger: logging.Logger, url: str, remove_media_nonce=False) -> str:
    tmpfilepath = ""
    chunk_size = 1024**2
    cpus = os.cpu_count()
    if cpus is None:
        cpus = 1
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            tmpfilepath = tmpfile.name
            with requests.get(url, headers=HEADERS, stream=True) as r:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    tmpfile.write(chunk)

        if remove_media_nonce:
            # read and replace file in chunks, for memory efficient processing
            overlap_size = 50 # keep the previous 50 characters of previous chunk for replacement
            regex_pattern = re.compile(r'id=([\'"])id_videojs_[a-f0-9_]+\1')
            buffer = ''
            decoder = codecs.getincrementaldecoder("utf-8")(errors='replace')
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmpfile:
                new_tmpfilepath = tmpfile.name
                try:
                    with open(tmpfilepath, "rb") as f:
                        while True:
                            text = decoder.decode(f.read(chunk_size))
                            if not text:
                                #process the leftover tail as well just in case
                                processed_text = regex_pattern.sub('', buffer)
                                tmpfile.write(processed_text)
                                break
                            text = buffer + text
                            processed_text = regex_pattern.sub('', text[:-overlap_size])
                            tmpfile.write(processed_text)
                            buffer = text[-overlap_size:]
                finally:
                    os.remove(tmpfilepath)
                    tmpfilepath = new_tmpfilepath
            del text, buffer

        hash_function = blake3.blake3(max_threads=cpus)
        with open(tmpfilepath, "rb") as tmpfile:
            for chunk in iter(lambda: tmpfile.read(chunk_size), b''):
                hash_function.update(chunk)
        hexdigest = hash_function.hexdigest()

    except (Exception, KeyboardInterrupt) as e:
        logger.error(e, exc_info=True)
        hexdigest = '#INVALID-HASH#'
    finally:
        if os.path.exists(tmpfilepath):
            os.remove(tmpfilepath)
    return hexdigest


class moodleInterface():

    def __init__(self):
        self.URL = "https://{domain}/webservice/rest/server.php?wstoken={token}&moodlewsrestformat=json".format(domain=config.DOMAIN, token=config.API_TOKEN)

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
        chunk_size = 1024**2
        if not os.path.exists(dest):
            os.makedirs(dest, exist_ok=True)
        filepath = os.path.join(dest, self.filename)
        if os.path.exists(filepath):
            count = 1
            while True:
                filepath = os.path.join(dest, self.filename.replace(".", f"({count})."))
                if not os.path.exists(filepath):
                    break
                count += 1
        with open(filepath, "wb") as file:
            with requests.get(f"{self.URL}&token={config.API_TOKEN}", headers=HEADERS, stream=True) as r:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    file.write(chunk)

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
    def __init__(self, *,  name, pageID, pageURL, hashValue):
        self.name = name
        self.ID = pageID
        self.URL = pageURL
        self.hashValue = hashValue

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
        self._logger = logging.getLogger("ElearnOBot.Course")
        self._logger = loggingUtils.prepare_logger(self._logger)
        self.ID: int = courseID
        self.name: str = fullName
        soup = BeautifulSoup(summary, "html.parser")
        self.summary: str = soup.get_text()
        self.forums: list[Forum] = []
        self.quizzes: list[Quiz] = []
        self.assignments: list[Assignment] = []
        self.files: list[File] = []
        self.workshops: list[Workshop] = []
        self.pages: list[Page] = []
        self.labels: list[Label] = []
        self.URL = f"https://{config.DOMAIN}/course/view.php?id={courseID}"

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
                                    moduleID=-1,
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
                    soup = BeautifulSoup(module["description"], "html.parser")
                    self.labels.append(Label(
                        description = soup.get_text()
                    ))

                elif moduleType == "page":
                    htmlpath = module["contents"][0]["fileurl"]
                    pageHash = hashInternetData(self._logger, htmlpath+"&token={}".format(config.API_TOKEN), True)
                    self.pages.append(Page(
                        name = module["name"],
                        pageID = module["id"],
                        pageURL = htmlpath,
                        hashValue = pageHash
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
