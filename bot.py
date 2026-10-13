import nextcord, sqlite3, math, logging, sys, socket, os, argparse
import random
from datetime import datetime
from asyncio import sleep
from nextcord.ext import commands, tasks, application_checks
from nextcord.ui import Select, Button, button, View
from utils import moodleUtils as mdlutils
from utils.loggingUtils import prepare_logger, ApplicationLogger
from utils.formattingUtils import messageSplitter, filesizeConversion, textClipper
from utils.config import Config

parser = argparse.ArgumentParser(add_help=True)
parser.add_argument("-c", "--config-file", type=str, help="Path to bot configuration file", default="config.cfg")
args = parser.parse_args()
config_file = args.config_file

config = Config(config_file)
config.load()
client = commands.Bot(intents=nextcord.Intents.default())
logger = logging.getLogger("ElearnOBot")
logger = prepare_logger(logger)
appLogger = ApplicationLogger(logger)
sendInvalidTokenMessage = True

if not os.path.exists(config.SQLITE_DB_PATH):
    parents , f = os.path.split(config.SQLITE_DB_PATH)
    if len(parents) > 0:
        os.makedirs(parents, exist_ok=True)
    logger.info("Creating database and tables...")
    with open("Database/tables.sql", "r") as sql:
        script = sql.read()
        connector = sqlite3.connect(config.SQLITE_DB_PATH)
        cursor = connector.cursor()
        cursor.executescript(script)
        connector.commit()
        connector.close()
    logger.info("Database creation was successful!")
else:
    logger.info("Database file found! Skipping database and table creation!")

if config.DOWNLOAD_FILES and not os.path.isdir(config.DOWNLOAD_DIR):
    logger.info(f"{config.DOWNLOAD_DIR} does not exist! Creating the directory!")
    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)

try:
    socket.gethostbyname(config.DOMAIN)
except socket.gaierror:
    logger.critical(f"Cannot resolve {config.DOMAIN}! Please ensure it's a valid server name and your internet connection! Exiting!")
    sys.exit(1)


class filesView(View):

    def __init__(self):
        self.timeout = None
        super().__init__()
        myoptions = []
        self.discussionData = []
        self.currentPage = 1
        connector = sqlite3.connect(config.SQLITE_DB_PATH)
        cursor = connector.cursor()
        data = cursor.execute("SELECT Fullname, courseID FROM Courses").fetchall()
        connector.close()
        self.totalPages = 0
        for courseName, courseID in data:
            courseName = textClipper(courseName, 100)
            myoptions.append(nextcord.SelectOption(label=courseName, value=str(courseID)))

        # Discord allows us to send up to 25 options, so we must limit them to 25 and warn user
        courseSelect = Select(placeholder="Choose a course", min_values=1, max_values=1, options=myoptions[:25])
        warn_user = True if len(myoptions) > 25 else False
        self.fileData: list[str]

        async def selectCallback(interaction: nextcord.Interaction):  
            appLogger.dc_print(f"User {interaction.user} selected course with ID {courseSelect.values[0]} in the Files menu")        
            connector = sqlite3.connect(config.SQLITE_DB_PATH)
            cursor= connector.cursor()
            self.fileData = cursor.execute("SELECT Filename,ID,URL,Size FROM Files WHERE courseID=?", (int(courseSelect.values[0]),)).fetchall()
            connector.close()
            self.totalPages = int(math.ceil(len(self.fileData)/float(config.FILES_PER_PAGE)))
            embed = nextcord.Embed(color=config.FILE_EMBED_COLOR, title=f"**Page {self.currentPage}/{self.totalPages}**")
            for row in self.fileData[:config.FILES_PER_PAGE]:
                embed.add_field(name=row[0],value=f"{filesizeConversion(row[3])} | [Download]({row[2].replace('webservice/', '')})")
            appLogger.dc_print(f"Responding with {self.totalPages} pages!")
            message = "Warning! You are registered to more than 25 courses. You can select from max 25 courses" if warn_user else ""
            await interaction.response.edit_message(content=message, embed=embed, view=self)

        courseSelect.callback = selectCallback
        self.add_item(courseSelect)
    
    @button(emoji="◀️", style=nextcord.ButtonStyle.blurple)
    async def leftCallback(self, button: Button, interaction: nextcord.Interaction):
        appLogger.dc_print(f"User {interaction.user} requested prev page in Files")
        if self.currentPage > 1:
            self.currentPage -= 1
            embed = nextcord.Embed(color=config.FILE_EMBED_COLOR, title=f"**Page {self.currentPage}/{self.totalPages}**")
            if self.currentPage == self.totalPages:
                for row in self.fileData[(self.totalPages-1)*config.FILES_PER_PAGE:]:
                    embed.add_field(name=row[0],value=f"{filesizeConversion(row[3])} | [Download]({row[2].replace('webservice/', '')})")
            else:
                for row in self.fileData[(self.currentPage-1)*config.FILES_PER_PAGE : self.currentPage*config.FILES_PER_PAGE]:
                    embed.add_field(name=row[0],value=f"{filesizeConversion(row[3])} | [Download]({row[2].replace('webservice/', '')})")
            await interaction.response.edit_message(content="", embed=embed, view=self)
        else:
            return

    @button(emoji="▶️", style=nextcord.ButtonStyle.blurple)
    async def rightCallback(self, button: Button, interaction: nextcord.Interaction):
        appLogger.dc_print(f"User {interaction.user} requested next page in Files")
        if self.currentPage < self.totalPages:
            self.currentPage += 1
            embed = nextcord.Embed(color=config.FILE_EMBED_COLOR, title=f"**Page {self.currentPage}/{self.totalPages}**")
            if self.currentPage == self.totalPages:
                for row in self.fileData[(self.totalPages-1)*config.FILES_PER_PAGE:]:
                    embed.add_field(name=row[0],value=f"{filesizeConversion(row[3])} | [Download]({row[2].replace('webservice/', '')})")
            else:
                for row in self.fileData[(self.currentPage-1)*config.FILES_PER_PAGE : self.currentPage*config.FILES_PER_PAGE]:
                    embed.add_field(name=row[0],value=f"{filesizeConversion(row[3])} | [Download]({row[2].replace('webservice/', '')})")
            await interaction.response.edit_message(content="", embed=embed, view=self)
        else:
            return

class discussionsView(View):

    def __init__(self):
        self.timeout = None
        super().__init__()
        myoptions = []
        self.discussionData = []
        self.currentPage = 1
        connector = sqlite3.connect(config.SQLITE_DB_PATH)
        cursor = connector.cursor()
        data = cursor.execute("SELECT Fullname, courseID FROM Courses").fetchall()
        connector.close()
        self.totalPages = 0
        for courseName, courseID in data:
            courseName = textClipper(courseName, 100)
            myoptions.append(nextcord.SelectOption(label=courseName, value=str(courseID)))

        # Discord allows us to send up to 25 options, so we must limit them to 25 and warn user
        courseSelect = Select(placeholder="Choose a course", min_values=1, max_values=1, options=myoptions[:25])
        warn_user = True if len(myoptions) > 25 else False

        async def selectCallback(interaction: nextcord.Interaction):
            appLogger.dc_print(f"User {interaction.user} selected course with ID {courseSelect.values[0]} in the Discussions menu")
            connector = sqlite3.connect(config.SQLITE_DB_PATH)
            cursor = connector.cursor()
            self.discussionData = cursor.execute("SELECT Name,ID,URL FROM Discussions WHERE courseID=?", (int(courseSelect.values[0]),)).fetchall()
            connector.close()
            self.totalPages = int(math.ceil(len(self.discussionData)/float(config.DISCUSSIONS_PER_PAGE)))
            embed = nextcord.Embed(color=config.DISCUSSION_EMBED_COLOR, title=f"**Page {self.currentPage}/{self.totalPages}**")
            for row in self.discussionData[:config.DISCUSSIONS_PER_PAGE]:
                embed.add_field(name=row[0],value=f"[Link]({row[2]})")
            appLogger.dc_print(f"Responding with {self.totalPages} pages!")
            message = "Warning! You are registered to more than 25 courses. You can select from max 25 courses" if warn_user else ""
            await interaction.response.edit_message(content=message, embed=embed, view=self)

        courseSelect.callback = selectCallback
        self.add_item(courseSelect)
    
    @button(emoji="◀️", style=nextcord.ButtonStyle.blurple)
    async def leftCallback(self, button: Button, interaction: nextcord.Interaction):
        appLogger.dc_print(f"User {interaction.user} requested prev page in Discussions")
        if self.currentPage > 1:
            self.currentPage -= 1
            embed = nextcord.Embed(color=config.DISCUSSION_EMBED_COLOR, title=f"**Page {self.currentPage}/{self.totalPages}**")
            if self.currentPage == self.totalPages:
                for row in self.discussionData[(self.totalPages-1)*config.DISCUSSIONS_PER_PAGE:]:
                    embed.add_field(name=row[0],value=f"[Link]({row[2]})")
            else:
                for row in self.discussionData[(self.currentPage-1)*config.DISCUSSIONS_PER_PAGE : self.currentPage*config.DISCUSSIONS_PER_PAGE]:
                    embed.add_field(name=row[0],value=f"[Link]({row[2]})")
            await interaction.response.edit_message(content="", embed=embed, view=self)
        else:
            return

    @button(emoji="▶️", style=nextcord.ButtonStyle.blurple)
    async def rightCallback(self, button: Button, interaction: nextcord.Interaction):
        appLogger.dc_print(f"User {interaction.user} requested next page in Discussions")
        if self.currentPage < self.totalPages:
            self.currentPage += 1
            embed = nextcord.Embed(color=config.DISCUSSION_EMBED_COLOR, title=f"**Page {self.currentPage}/{self.totalPages}**")
            if self.currentPage == self.totalPages:
                for row in self.discussionData[(self.totalPages-1)*config.DISCUSSIONS_PER_PAGE:]:
                    embed.add_field(name=row[0],value=f"[Link]({row[2]})")
            else:
                for row in self.discussionData[(self.currentPage-1)*config.DISCUSSIONS_PER_PAGE : self.currentPage*config.DISCUSSIONS_PER_PAGE]:
                    embed.add_field(name=row[0],value=f"[Link]({row[2]})")
            await interaction.response.edit_message(content="", embed=embed, view=self)
        else:
            return


@client.event
async def on_ready():
    appLogger.dc_print(f"Connected as {client.user}, bot ready!")

@client.slash_command(name="files", description="Show courses\' files")
async def fileMenu(interaction: nextcord.Interaction):
    appLogger.dc_print(f"User {interaction.user} used /files command on #{interaction.channel}")
    connector = sqlite3.connect(config.SQLITE_DB_PATH)
    cursor = connector.cursor()
    n_courses = int(cursor.execute("SELECT COUNT(courseID) FROM Courses").fetchone()[0])
    connector.close()
    if n_courses > 0:
        await interaction.response.send_message("Select a course:", view=filesView(), ephemeral=True)
    else:
        error_message = "No courses found! Please make sure that youre enrolled in courses and bot synchronization is finished!"
        await interaction.response.send_message(error_message, ephemeral=True)

@client.slash_command(name="discussions", description="Show courses\' discussions")
async def discussionMenu(interaction: nextcord.Interaction):
    appLogger.dc_print(f"User {interaction.user} used /discussions command on #{interaction.channel}")
    connector = sqlite3.connect(config.SQLITE_DB_PATH)
    cursor = connector.cursor()
    n_courses = int(cursor.execute("SELECT COUNT(courseID) FROM Courses").fetchone()[0])
    if n_courses > 0:
        await interaction.response.send_message("Select a course:", view=discussionsView(), ephemeral=True)
    else:
        error_message = "No courses found! Please make sure that youre enrolled in courses and bot synchronization is finished!"
        await interaction.response.send_message(error_message, ephemeral=True)

@client.slash_command(name="updatetoken", description="Update ElearnOBot\'s API token by QR code!")
@application_checks.has_guild_permissions(administrator=True)
async def updateMoodleToken(interaction: nextcord.Interaction, qr_url: str = nextcord.SlashOption(name="qr_code_url", description="URL provided from your personal QR code")):
    qr_data = mdlutils.parse_qr_url(qr_url)
    if qr_data.success:
        config.API_TOKEN = str(qr_data.api_token)
        config.USERID = str(qr_data.user_id)
        config.save()
        message = f"Success! Your new Moodle API token is `{qr_data.api_token}` and user ID is `{qr_data.user_id}`"
        appLogger.mdl_print(message)
        await client.change_presence(status=nextcord.Status.online)
        await interaction.response.send_message(message, ephemeral=True)
    else:
        message = f"Failed to update Moodle API token! Reason: {qr_data.error_message}"
        appLogger.mdl_print(message, error=True)
        await client.change_presence(status=nextcord.Status.dnd)
        await interaction.response.send_message(message, ephemeral=True)

@updateMoodleToken.error
async def on_updateMoodleToken_error(interaction: nextcord.Interaction, error):
    if isinstance(error, application_checks.ApplicationMissingPermissions):
        await interaction.response.send_message("Only administrators are allowed to run this command!", ephemeral=True)


@tasks.loop(minutes=config.UPDATE_MINUTES)
async def check():
    if config.RANDOMIZE_UPDATE_INTERVAL:
        sleepAmount = random.randint(0,30)*60
        await sleep(sleepAmount)
    courses = []
    moodle = mdlutils.moodleInterface(config.DOMAIN, config.API_TOKEN, config.USERID)
    notificationCh = client.get_channel(config.NOTIFICATION_CHANNEL)
    appLogger.dc_print(f"Got notification channel #{notificationCh.name}")
    appLogger.mdl_print("Refreshing courses")
    getCoursesAPIResponse = moodle.getCourses() #we will need this later for debugging ;)
    try:
        courseIDs = [int(course["id"]) for course in getCoursesAPIResponse]
    except TypeError:
        if "errorcode" in getCoursesAPIResponse and getCoursesAPIResponse["errorcode"] == "invalidtoken":
            message = "The Moodle API token has expired! Please renew it!"
            embed = nextcord.Embed(title="Moodle: Invalid token", description=message, color=config.INVALID_TOKEN_EMBED_COLOR)
            await client.change_presence(status=nextcord.Status.dnd, activity=nextcord.activity.Game(message))
            global sendInvalidTokenMessage
            if sendInvalidTokenMessage:
                await notificationCh.send(embed=embed)
                sendInvalidTokenMessage = False
        appLogger.mdl_print(getCoursesAPIResponse, True)
        return

    #get all assignment details in a single call
    assignments = moodle.getAssignments(courseIDs=courseIDs)
    if not "exception" in assignments:
        coursesAssignmentDetails = moodle.getAssignments(courseIDs=courseIDs)["courses"]
    else:
        coursesAssignmentDetails = []
        message = assignments["message"]
        appLogger.mdl_print(f"Could not fetch assignments! Reason: {message}", True)
    for courseIndex,course in enumerate(getCoursesAPIResponse):
        id = course["id"]
        c = mdlutils.Course(
            mdl_domain=config.DOMAIN,
            mdl_token=config.API_TOKEN,
            mdl_userid=config.USERID,
            fullName=course["fullname"],
            courseID=id,
            summary=course["summary"]
        )
        appLogger.mdl_print(f"Now refreshing course {c.name}")
        c.refresh()
        courses.append(c)
        #update time opened and time modified times for assignments
        for assignmentIndex,assignment in enumerate(coursesAssignmentDetails[courseIndex]["assignments"]):
            c.assignments[assignmentIndex].timeOpened = assignment["allowsubmissionsfromdate"]
            c.assignments[assignmentIndex].timeDue = assignment["duedate"]


    filesCheckQuery = "SELECT TimeModified,URL FROM Files WHERE Filename = ? AND courseID=? AND moduleID=? AND Path=? AND discussionID IS NULL"
    filesUpdateQuery = '''UPDATE Files SET Path=?, Size=?, TimeModified=?, Author=?, URL=?, License=?
        WHERE Filename=? AND courseID=? AND moduleID=? AND Path=? AND DiscussionID IS NULL'''
    filesDeleteQuery = "DELETE FROM Files WHERE courseID = ? AND URL = ? AND DiscussionID IS NULL"

    linksCheckQuery = "SELECT TimeModified,URL FROM Files WHERE Filename = ? AND courseID=? AND moduleID=? AND Path IS NULL AND DiscussionID IS NULL"
    linksUpdateQuery = '''UPDATE Files SET Path=NULL, Size=?, TimeModified=?, Author=?, URL=?, License=?
        WHERE Filename=? AND courseID=? AND moduleID=? AND Path IS NULL AND DiscussionID IS NULL'''

    filesCheckDiscussionQuery = "SELECT TimeModified,URL FROM Files WHERE Filename = ? AND courseID=? AND Path=? AND DiscussionID=? AND moduleID IS NULL"
    filesUpdateDiscussionQuery = '''UPDATE Files SET Path=?, Size=?, TimeModified=?, Author=?, URL=?, License=?
    WHERE Filename=? AND courseID=? AND DiscussionID=? AND Path=? AND moduleID IS NULL'''
    filesDeleteDiscussionQuery = "DELETE FROM Files WHERE URL = ? AND courseID=? AND moduleID IS NULL"

    #forumsCheckQuery = "SELECT Name FROM Forums WHERE ID = ?"
    #forumsUpdateQuery = "UPDATE Forums SET Name=? WHERE ID = ?"

    discussionsCheckQuery = "SELECT Name,TimeModified,Message,URL FROM Discussions WHERE ID=?"
    discussionsUpdateQuery = "UPDATE Discussions SET Name=?, TimeModified=?, Message=? WHERE ID = ?"
    discussionsDeleteQuery = "DELETE FROM Discussions WHERE ID = ?"

    pagesCheckQuery = "SELECT Name, HashValue, URL FROM Pages WHERE ID = ?"
    pagesUpdateQuery = "UPDATE Pages SET Name=?, HashValue=? WHERE ID = ?"
    pagesDeleteQuery = "DELETE FROM Pages WHERE ID=?"

    assignmentsCheckQuery = "SELECT Name, TimeOpened, TimeDue,URL FROM Assignments WHERE ID=?"
    assignmentsUpdateQuery = "UPDATE Assignments SET Name=?,TimeOpened=?,TimeDue=? WHERE ID=?"
    assignmentsDeleteQuery = "DELETE FROM Assignments WHERE ID=?"

    QuizzesAndWorkshopsCheckQuery = "SELECT Name FROM {} WHERE ID=?"
    QuizzesAndWorkshopsUpdateQuery = "UPDATE {} SET Name=? WHERE ID=?"
    QuizzesAndWorkshopsDeleteQuery = "DELETE FROM {} WHERE ID=?"

    connector = sqlite3.connect(config.SQLITE_DB_PATH)
    cursor = connector.cursor()

    #enable foreign key actions, sqlite disables them by default
    cursor.execute("PRAGMA foreign_keys = ON")

    courseCount = int(cursor.execute("SELECT COUNT(courseID) FROM Courses").fetchone()[0])
    FIRST_RUN = True

    if courseCount > 0:
        appLogger.mdl_print("Database is not empty!")
        FIRST_RUN = False
    else:
        appLogger.mdl_print("Database empty! This is the first run!")

    for course in courses:
        # new spaghetti
        courseItems = ["Files", "Links", "Quizzes", "Assignments", "Pages","Workshops", "Forums", "Discussions", "Attachments"]
        changeLog = {}
        for item in courseItems:
            changeLog[item] = {"NEW": "", "CHANGED": "", "DELETED": ""}
        cursor.execute("INSERT OR IGNORE INTO Courses(courseID, Fullname, Summary) VALUES (?,?,?)",(
            course.ID, course.name, course.summary,
        ))
        for file in course.files:
            if file.path != None and file.URL != None: #if path exists but url is None (probably) is a book
                data = cursor.execute(filesCheckQuery, (file.filename, course.ID, file.moduleID, file.path)).fetchone()
                if data != None:
                    if data[0] != file.timeModified:
                        appLogger.mdl_print(f"File {file.filename} got updated! URL: {file.URL}")
                        cursor.execute(filesUpdateQuery, (
                                file.path, file.size, file.timeModified,
                                file.author, file.URL, file.License, file.filename, course.ID, file.moduleID, file.path)
                            )
                        changeLog["Files"]["CHANGED"] += f"~ [{file.filename}]({file.URL.replace('webservice/', '')}) ({filesizeConversion(file.size)})\n"
                        if config.DOWNLOAD_FILES:
                            appLogger.dl_print(f"Downloading changed file {file.filename}, {file.size} bytes!")
                            file.download(os.path.join(config.DOWNLOAD_DIR, course.name))
                else:
                    appLogger.mdl_print(f"New file! URL: {file.URL}")
                    query = '''INSERT OR IGNORE INTO Files(courseID, Filename, Path, Size, TimeModified, MimeType, Author, URL, License, moduleID) 
                                VALUES (?,?,?,?,?,?,?,?,?,?)
                            '''
                    cursor.execute(query,(
                            (course.ID, file.filename, file.path, file.size, file.timeModified, file.mimeType, file.author, file.URL, file.License,
                                file.moduleID)
                        ))
                    changeLog["Files"]["NEW"] += f"+ [{file.filename}]({file.URL.replace('webservice/', '')}) ({filesizeConversion(file.size)}) by *{file.author}*\n"
                    if config.DOWNLOAD_FILES:
                        appLogger.dl_print(f"Downloading new file {file.filename}, {file.size} bytes!")
                        file.download(os.path.join(config.DOWNLOAD_DIR, course.name))
            elif file.path == None and file.URL != None: # if file.path is None, it's a link
                data = cursor.execute(linksCheckQuery, (file.filename, course.ID, file.moduleID)).fetchone()
                if data != None:
                    if data[0] != file.timeModified:
                        appLogger.mdl_print(f"Link {file.filename} got updated! URL: {file.URL}")
                        cursor.execute(linksUpdateQuery, (
                                file.size, file.timeModified,
                                file.author, file.URL, file.License, file.filename, course.ID, file.moduleID)
                            )
                        changeLog["Links"]["CHANGED"] += f"~ [{file.filename}]({file.URL.replace('webservice/', '')})\n"
                else:
                    appLogger.mdl_print(f"New link! URL: {file.URL}")
                    query = '''INSERT OR IGNORE INTO Files(courseID, Filename, Path, Size, TimeModified, MimeType, Author, URL, License, moduleID) 
                                VALUES (?,?,?,?,?,?,?,?,?,?)
                            '''
                    cursor.execute(query,(
                            (course.ID, file.filename, file.path, file.size, file.timeModified, file.mimeType, file.author, file.URL, file.License,
                                file.moduleID)
                        ))
                    changeLog["Links"]["NEW"] += f"+ [{file.filename}]({file.URL.replace('webservice/', '')})\n"
        # check for deletion (URL-based)
        for localFile in cursor.execute("SELECT URL, Filename, Size, Path FROM Files WHERE courseID=? AND DiscussionID IS NULL", (course.ID,)).fetchall():
            if localFile[3] != None:
                courseFileURLs = []
                for file in course.files:
                    courseFileURLs.append(file.URL)
                if localFile[0] not in courseFileURLs:
                    appLogger.mdl_print(f"File {localFile[1]} deleted!")
                    cursor.execute(filesDeleteQuery, (course.ID, localFile[0]))
                    changeLog["Files"]["DELETED"] += f"- ~~{localFile[1]}~~ ({filesizeConversion(localFile[2])})\n"
            else: # if None it's a link
                courseFileURLs = []
                for file in course.files:
                    courseFileURLs.append(file.URL)
                if localFile[0] not in courseFileURLs:
                    appLogger.mdl_print(f"Link {localFile[1]} deleted!")
                    cursor.execute(filesDeleteQuery, (course.ID, localFile[0]))
                    changeLog["Links"]["DELETED"] += f"- ~~{localFile[1]}~~\n"

        for quiz in course.quizzes:
            data = cursor.execute(QuizzesAndWorkshopsCheckQuery.format("Quizzes"), (quiz.ID,)).fetchone()
            if data != None:
                if data[0] != quiz.name:
                    appLogger.mdl_print(f"Quiz name changed! URL: {quiz.URL}")
                    cursor.execute(QuizzesAndWorkshopsUpdateQuery.format("Quizzes"), (quiz.name, quiz.ID,))
                    changeLog["Quizzes"]["CHANGED"] += f"~ ~~{data[0]}~~[{quiz.name}]({quiz.URL})\n"
            else:
                appLogger.mdl_print(f"New quiz! URL: {quiz.URL}")
                cursor.execute("INSERT OR IGNORE INTO Quizzes(ID, courseID, Name, URL) VALUES (?,?,?,?)",(
                    (quiz.ID, course.ID, quiz.name, quiz.URL,)
                ))
                changeLog["Quizzes"]["NEW"] += f"+ [{quiz.name}]({quiz.URL})\n"
        # check for deletion (Quiz ID)
        for localQuiz in cursor.execute("SELECT ID, Name FROM Quizzes WHERE courseID=?", (course.ID,)).fetchall():
            courseQuizIDs = []
            for quiz in course.quizzes:
                courseQuizIDs.append(quiz.ID)
            if localQuiz[0] not in courseQuizIDs:
                appLogger.mdl_print(f"Quiz {localQuiz[1]} deleted!")
                cursor.execute(QuizzesAndWorkshopsDeleteQuery.format("Quizzes"), (localQuiz[0],))
                changeLog["Quizzes"]["DELETED"] += f"- ~~{localQuiz[1]}~~\n"
        # this fills up the Labels table, and we don't really need labels anyway

        # for label in course.labels:
        #     cursor.execute("INSERT INTO Labels(courseID, Description) VALUES (?,?)",(
        #         (course.ID, label.description,)
        #     )) 

        for assignment in course.assignments:
            data = cursor.execute(assignmentsCheckQuery, (assignment.ID,)).fetchone()
            if data != None:
                if (data[0] != assignment.name or  data[1] != assignment.timeOpened or data[2] != assignment.timeDue):
                    if data[0] != assignment.name:
                        appLogger.mdl_print(f"Assignment name changed! New name: {assignment.name}")
                        changeLog["Assignments"]["CHANGED"] += f"~ ~~{data[0]}~~[{assignment.name}]({assignment.URL})\n"
                    else:
                        changeLog["Assignments"]["CHANGED"] += f"~ [{assignment.name}]({assignment.URL})\n"
                    if data[1] != assignment.timeOpened:
                        appLogger.mdl_print(f"Assignment {assignment.name} time opened changed!")
                        changeLog["Assignments"]["CHANGED"] += f"    *Opened: ~~{str(datetime.fromtimestamp(data[1]))}~~{str(datetime.fromtimestamp(assignment.timeOpened))}*\n"
                    else:
                        changeLog["Assignments"]["CHANGED"] += f"    *Opened: {str(datetime.fromtimestamp(assignment.timeOpened))}*\n"
                    if data[2] != assignment.timeDue:
                        changeLog["Assignments"]["CHANGED"] += f"    *Due: ~~{str(datetime.fromtimestamp(data[2]))}~~{str(datetime.fromtimestamp(assignment.timeDue))}*\n"
                        appLogger.mdl_print(f"Assignment {assignment.name} time due changed!")
                    else:
                        changeLog["Assignments"]["CHANGED"] += f"    *Due: {str(datetime.fromtimestamp(assignment.timeDue))}*\n"
                cursor.execute(assignmentsUpdateQuery, (assignment.name, assignment.timeOpened,
                    assignment.timeDue, assignment.ID   
                ))

            else:
                appLogger.mdl_print(f"New assignment! URL: {assignment.URL}")
                cursor.execute("INSERT OR IGNORE INTO Assignments(ID, courseID, Name, URL, TimeOpened, TimeDue) VALUES (?,?,?,?,?,?)",(
                    (assignment.ID, course.ID, assignment.name, assignment.URL, assignment.timeOpened, assignment.timeDue,)
                ))
                changeLog["Assignments"]["NEW"] += f"+ [{assignment.name}]({assignment.URL})\n    *Opened: {str(datetime.fromtimestamp(assignment.timeOpened))}*\n    *Due: {str(datetime.fromtimestamp(assignment.timeDue))}*\n"
        #check for deletion (ID)
        for localAssignment in cursor.execute("SELECT ID, Name FROM Assignments WHERE courseID=?", (course.ID,)).fetchall():
            courseAssignmentIDs = []
            for assignment in course.assignments:
                courseAssignmentIDs.append(assignment.ID)
            if localAssignment[0] not in courseAssignmentIDs:
                appLogger.mdl_print(f"Assignment {localAssignment[1]} deleted!")
                cursor.execute(assignmentsDeleteQuery, (localAssignment[0],))
                changeLog["Assignments"]["DELETED"] += f"- ~~{localAssignment[1]}~~\n"

        for page in course.pages:
            data = cursor.execute(pagesCheckQuery, (page.ID, )).fetchone()
            if data != None:
                is_legacy_hash = len(str(data[1])) == 64 and all(c in "0123456789abcdefABCDEF" for c in str(data[1]))
                if is_legacy_hash:
                    # Legacy 64-char BLAKE3 hash: quietly update database to new timestamp without emitting false alerts
                    cursor.execute(pagesUpdateQuery, (page.name, page.hashValue, page.ID, ))
                elif (data[0] != page.name or data[1] != page.hashValue):
                    if data[0] != page.name:
                        appLogger.mdl_print(f"Page {data[0]} name changed! New name: {page.name}")
                        changeLog["Pages"]["CHANGED"] += f"~ ~~{data[0]}~~[{page.name}]({page.URL})\n"
                    else:
                        changeLog["Pages"]["CHANGED"] += f"~ [{page.name}]({page.URL})\n"
                    if data[1] != page.hashValue:
                        appLogger.mdl_print(f"Page content changed!")
                        changeLog["Pages"]["CHANGED"] += f"    *Page content modified*\n"
                    cursor.execute(pagesUpdateQuery, (page.name, page.hashValue, page.ID, ))
            else:
                appLogger.mdl_print("New page!")
                cursor.execute("INSERT OR IGNORE INTO Pages(ID, courseID, Name, URL, HashValue) VALUES (?,?,?,?,?)",(
                    (page.ID, course.ID, page.name, page.URL, page.hashValue,)
                ))
                changeLog["Pages"]["NEW"] += f"+ [{page.name}]({page.URL})\n"
        # check for deletion (ID)
        for localPage in cursor.execute("SELECT ID, Name FROM Pages WHERE courseID=?", (course.ID,)).fetchall():
            coursePageIDs = []
            for page in course.pages:
                coursePageIDs.append(page.ID)
            if localPage[0] not in coursePageIDs:
                appLogger.mdl_print(f"Page {localPage[1]} deleted!")
                cursor.execute(pagesDeleteQuery, (localPage[0],))
                changeLog["Pages"]["DELETED"] += f"- ~~{localPage[1]}~~\n"

        for workshop in course.workshops:
            data = cursor.execute(QuizzesAndWorkshopsCheckQuery.format("Workshops"), (workshop.ID,)).fetchone()
            if data != None:
                #print(data)
                if data[0] != workshop.name:
                    appLogger.mdl_print(f"Workshop {data[0]} name changed! New name: {workshop.name}")
                    cursor.execute(QuizzesAndWorkshopsUpdateQuery.format("Workshops"), (workshop.name, workshop.ID,))
                    changeLog["Workshops"]["CHANGED"] += f"~ ~~{data[0]}~~[{workshop.name}]({workshop.URL})\n"
            else:
                appLogger.mdl_print(f"New workshop: URL: {workshop.URL}")
                cursor.execute("INSERT OR IGNORE INTO Workshops(ID, courseID, Name, URL) VALUES (?,?,?,?)",(
                    (workshop.ID, course.ID, workshop.name, workshop.URL, )
                ))
                changeLog["Workshops"]["NEW"] += f"+ [{workshop.name}]({workshop.URL})\n"
        # check for deletion (ID)
        for localWorkshop in cursor.execute("SELECT ID, Name FROM Workshops WHERE courseID=?", (course.ID,)).fetchall():
            courseWorkshopIDs=[]
            for workshop in course.workshops:
                courseWorkshopIDs.append(workshop.ID)
            if localWorkshop[0] not in courseWorkshopIDs:
                appLogger.mdl_print(f"Workshop {localWorkshop[1]} deleted!")
                cursor.execute(QuizzesAndWorkshopsDeleteQuery.format("Workshops"),(localWorkshop[0],))
                changeLog["Workshops"]["DELETED"] += f"- ~~{localWorkshop[1]}~~\n"

        for forum in course.forums:
            cursor.execute("INSERT OR IGNORE INTO Forums(ID, courseID, Name, URL) VALUES (?,?,?,?)",(
                (forum.ID, course.ID, forum.name, forum.URL, )
            )) #we dont care for forum changes, so simply populate the database
            for discussion in forum.discussions:
                data = cursor.execute(discussionsCheckQuery, (discussion.ID,)).fetchone()
                if data != None:
                    if data[1] != discussion.timeModified: #discussion updated! 
                        appLogger.mdl_print(f"Discussion {discussion.name} update!")
                        if discussion.name != data[0]:
                            appLogger.mdl_print(f"Discussion {data[0]} name changed! New name: {discussion.name}")
                            changeLog["Discussions"]["CHANGED"] += f"~ ~~{data[0]}~~[{discussion.name}]({discussion.URL})\n"
                        else:
                            changeLog["Discussions"]["CHANGED"] += f"~ [{discussion.name}]({discussion.URL})\n"
                        if discussion.message != data[2]:
                            appLogger.mdl_print(f"Message update! Old message: {data[2]} New message: {discussion.message} Link: {discussion.URL}")
                            changeLog["Discussions"]["CHANGED"] += f"    *Discussion content modified*\n"
                        cursor.execute(discussionsUpdateQuery,(discussion.name, discussion.timeModified, discussion.message, discussion.ID,))
                
                else: #new discussion
                    appLogger.mdl_print(f"New discussion! URL: {discussion.URL}")
                    cursor.execute("INSERT OR IGNORE INTO Discussions(ID, courseID, Name, URL, TimeModified, Message, forumID) VALUES (?,?,?,?,?,?,?)",(
                        (discussion.ID, course.ID, discussion.name, discussion.URL, discussion.timeModified, discussion.message, forum.ID)
                    ))
                    if not FIRST_RUN:
                        discussionEmbed = nextcord.Embed(title=discussion.name, url=discussion.URL, color=config.DISCUSSION_EMBED_COLOR, description=discussion.message)
                        if len(discussion.message) > 4096:
                            await messageSplitter(appLogger, notificationCh, discussion.message, config.DISCUSSION_LINES_PER_EMBED, "Discussion", course, "NEW", config.DISCUSSION_EMBED_COLOR)

                        elif len(discussion.message) > 0 and len(discussion.message) < 4096:
                            discussionEmbed.set_author(name=f"New discussion in forum \'{forum.name}\' of course {course.name}", url=forum.URL)
                            appLogger.dc_print(f"Sending a new discussion ({discussion.name})!") ## The only call made to Discord from within the loop
                            await notificationCh.send(embed=discussionEmbed)
                for attachment in discussion.files:
                    data = cursor.execute(filesCheckDiscussionQuery, (attachment.filename,course.ID,attachment.path, discussion.ID)).fetchone()
                    if data != None:
                        if data[0] != attachment.timeModified: #file modified
                            appLogger.mdl_print(f"Discussion attachment modified! New link: {attachment.URL}")
                            cursor.execute(filesUpdateDiscussionQuery, (
                                attachment.path, attachment.size, attachment.timeModified,
                                attachment.author, attachment.URL, attachment.License, attachment.filename, course.ID, discussion.ID, attachment.path))
                            changeLog["Attachments"]["CHANGED"] += f"~ [{attachment.filename}]({attachment.URL.replace('webservice/', '')}) ({filesizeConversion(attachment.size)})\n"

                    else: #new file
                        appLogger.mdl_print(f"New attachment found! URL: {attachment.URL}")
                        query = '''INSERT OR IGNORE INTO Files(courseID, Filename, Path, Size, TimeModified, MimeType, Author, URL, License, DiscussionID)
                                VALUES (?,?,?,?,?,?,?,?,?,?)
                                '''
                        cursor.execute(query,(
                            (course.ID, attachment.filename, attachment.path, attachment.size, attachment.timeModified, attachment.mimeType, attachment.author, attachment.URL, attachment.License,
                                discussion.ID)
                            ))

                        changeLog["Attachments"]["NEW"] += f"+ [{attachment.filename}]({attachment.URL.replace('webservice/', '')}) ({filesizeConversion(attachment.size)}) by *{attachment.author}* in discussion [{discussion.name}]({discussion.URL})\n"
                #check attachment deletion (by URL)
                for localAttachment in cursor.execute("SELECT URL, Filename FROM Files WHERE courseID=? AND DiscussionID=?", (course.ID, discussion.ID)).fetchall():
                    discussionFileURLs = []
                    for attachment in discussion.files:
                        discussionFileURLs.append(attachment.URL)
                    if localAttachment[0] not in discussionFileURLs:
                        appLogger.mdl_print(f"Attachment {localAttachment[1]} from discussion {discussion.name} deleted!")
                        cursor.execute(filesDeleteDiscussionQuery, (localAttachment[0], course.ID))
                        changeLog["Attachments"]["DELETED"] += f"- ~~{localAttachment[1]}~~ in discussion [{discussion.name}]({discussion.URL})\n"

            for localDiscussion in cursor.execute("SELECT ID, Name FROM Discussions WHERE forumID=?", (forum.ID,)).fetchall():
                forumDiscussionIDs = []
                for discussion in forum.discussions:
                    forumDiscussionIDs.append(discussion.ID)
                if localDiscussion[0] not in forumDiscussionIDs:
                    appLogger.mdl_print(f"Discussion {localDiscussion[1]} deleted!")
                    cursor.execute("DELETE FROM Files WHERE DiscussionID=?", (localDiscussion[0],)) # also delete the files to tidy the DB
                    cursor.execute(discussionsDeleteQuery, (localDiscussion[0],))
                    changeLog["Discussions"]["DELETED"] += f"- ~~{localDiscussion[1]}~~\n"
        for localForum in cursor.execute("SELECT ID, Name FROM Forums WHERE courseID=?", (course.ID,)).fetchall():
            courseForumIDs = []
            for forum in course.forums:
                courseForumIDs.append(forum.ID)
            if localForum[0] not in courseForumIDs:
                appLogger.mdl_print(f"Forum {localForum[1]} deleted, deleting discussions and attachments!")
                for i in cursor.execute("SELECT ID FROM Discussions WHERE forumID=?", (localForum[0],)).fetchall():
                    cursor.execute("DELETE FROM Files WHERE DiscussionID=?", (i[0],))
                cursor.execute("DELETE FROM Discussions WHERE forumID=?", (localForum[0],))
                cursor.execute("DELETE FROM Forums WHERE ID=?", (localForum[0],))
                changeLog["Forums"]["DELETED"] += f"- ~~{localForum[1]}~~\n"

        if not FIRST_RUN:
            for courseItem in changeLog:
                for state in changeLog[courseItem]:
                    message = changeLog[courseItem][state]
                    embedAuthor = f"{state} {courseItem} in course: {course.name}"
                    if len(message) > 0 and len(message) < 4096:
                        embed = nextcord.Embed(title=f"{courseItem} list:", color=config.FILE_EMBED_COLOR, description=message)
                        embed.set_author(name=embedAuthor, url=course.URL)
                        appLogger.dc_print(f"Sending {state.lower()} {courseItem.lower()} in course {course.name}")
                        await notificationCh.send(embed=embed)
                    elif len(message) > 4096:
                        await messageSplitter(appLogger, notificationCh, message, config.FILES_PER_EMBED, courseItem.lower(), course, state, config.FILE_EMBED_COLOR)

        connector.commit()

    # Delete older courses that user is not currently enrolled in
    if courseIDs:
        course_delete_query = "DELETE FROM Courses WHERE courseID NOT IN ({})".format(", ".join("?" * len(courseIDs)))
        cursor.execute(course_delete_query, tuple(courseIDs))
        connector.commit()
    FIRST_RUN = False
    connector.close()
    appLogger.mdl_print("Refresh finished!")

@check.before_loop
async def before_mdl_check():
    appLogger.mdl_print("Waiting for discord client to get ready...")
    await client.wait_until_ready()

check.start()
client.run(config.BOT_TOKEN)
