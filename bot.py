import nextcord, config, sqlite3, math
from json import dumps
from random import randint
#from time import time
from datetime import datetime
from os import path,makedirs
from asyncio import sleep
from nextcord.ext import commands, tasks
from nextcord.ui import Select, Button, button, View
from moodleUtils import *

def filesizeConversion(bytes):
    out = int(bytes)/1024.0
    if out > 1024:
        out = out/1024.0
        return "{}MB".format(round(out, 2))
    return "{}KB".format(round(out, 2))

async def messageSplitter(channel, message: str, itemsCountPerMessage: int, itemType: str, course: Course, itemState: str, embedColor: int):
    items = message.split("\n")
    del items[len(items) - 1] #delete last empty item, since it's useless
    totalMessages = math.ceil(len(items) / float(itemsCountPerMessage))
    for m in range(totalMessages):
        messages = ""
        for message in items[:itemsCountPerMessage]:
            messages += message+"\n"
        embed = nextcord.Embed(title=f"{itemType} list: {m+1}/{totalMessages}", color=embedColor, description=messages)
        embed.set_author(name=f"{itemState} {itemType}s in course: {course.name}", url=course.URL)
        dc_print(f"Sending {itemState} {itemType} in course {course.name} by parts (too many characters for single message!). Progress: {m+1}/{totalMessages}")
        await channel.send(embed=embed)
        del items[:itemsCountPerMessage]

def saveAPIResponse(*,jsonResponse, savePath, course):
    savePath = path.join(savePath,course)
    filename = f"{round(datetime.timestamp(datetime.now()))}.json"
    print(filename)
    if not path.exists(path.join(savePath)):
        makedirs(savePath)
    with open(path.join(savePath,filename), "w") as out:
        out.write(dumps(jsonResponse, indent=5, sort_keys=True))

client = commands.Bot(intents=nextcord.Intents.default())
#client.remove_command("help")

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
        for row in data:
            myoptions.append(nextcord.SelectOption(label=row[0],value=str(row[1])))

        courseSelect = Select(placeholder="Choose a course", min_values=1, max_values=1, options=myoptions)

        async def selectCallback(interaction: nextcord.Interaction):  
            dc_print(f"User {interaction.user} selected course with ID {courseSelect.values[0]} in the Files menu")        
            connector = sqlite3.connect(config.SQLITE_DB_PATH)
            cursor= connector.cursor()
            self.fileData = cursor.execute("SELECT Filename,ID,URL,Size FROM Files WHERE courseID=?", (int(courseSelect.values[0]),)).fetchall()
            connector.close()
            self.totalPages = int(math.ceil(len(self.fileData)/float(config.FILES_PER_PAGE)))
            embed = nextcord.Embed(color=config.FILE_EMBED_COLOR, title=f"**Page {self.currentPage}/{self.totalPages}**")
            for row in self.fileData[:config.FILES_PER_PAGE]:
                embed.add_field(name=row[0],value=f"{filesizeConversion(row[3])} | [Download]({row[2].replace('webservice/', '')})")
            dc_print(f"Responding with {self.totalPages} pages!")
            await interaction.response.edit_message(content="", embed=embed, view=self)

        courseSelect.callback = selectCallback
        self.add_item(courseSelect)
    
    @button(emoji="◀️", style=nextcord.ButtonStyle.blurple)
    async def leftCallback(self, button: Button, interaction: nextcord.Interaction):
        dc_print(f"User {interaction.user} requested prev page in Files")
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
        dc_print(f"User {interaction.user} requested next page in Files")
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
        for row in data:
            myoptions.append(nextcord.SelectOption(label=row[0],value=str(row[1])))

        courseSelect = Select(placeholder="Choose a course", min_values=1, max_values=1, options=myoptions)

        async def selectCallback(interaction: nextcord.Interaction):
            dc_print(f"User {interaction.user} selected course with ID {courseSelect.values[0]} in the Discussions menu") 
        #     if courseSelect.values[0]=="12526":
        #         await interaction.response.send_message("Noice", ephemeral=True) # Τηλεπ 1 much?
            
            connector = sqlite3.connect(config.SQLITE_DB_PATH)
            cursor = connector.cursor()
            self.discussionData = cursor.execute("SELECT Name,ID,URL FROM Discussions WHERE courseID=?", (int(courseSelect.values[0]),)).fetchall()
            connector.close()
            self.totalPages = int(math.ceil(len(self.discussionData)/float(config.DISCUSSIONS_PER_PAGE)))
            embed = nextcord.Embed(color=config.DISCUSSION_EMBED_COLOR, title=f"**Page {self.currentPage}/{self.totalPages}**")
            for row in self.discussionData[:config.DISCUSSIONS_PER_PAGE]:
                embed.add_field(name=row[0],value=f"[Link]({row[2]})")
            dc_print(f"Responding with {self.totalPages} pages!")
            await interaction.response.edit_message(content="", embed=embed, view=self)

        courseSelect.callback = selectCallback
        self.add_item(courseSelect)
    
    @button(emoji="◀️", style=nextcord.ButtonStyle.blurple)
    async def leftCallback(self, button: Button, interaction: nextcord.Interaction):
        dc_print(f"User {interaction.user} requested prev page in Discussions")
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
        dc_print(f"User {interaction.user} requested next page in Discussions")
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
    dc_print(f"Connected as {client.user}, starting Moodle thread")
    check.start()
    mdl_print("Started!")

@client.slash_command(name="files", description="Show courses\' files")
async def fileMenu(interaction):
    dc_print(f"User {interaction.user} used /files command on #{interaction.channel}")
    await interaction.response.send_message("Select a course:", view=filesView(), ephemeral=True)

@client.slash_command(name="discussions", description="Show courses\' discussions")
async def discussionMenu(interaction):
    dc_print(f"User {interaction.user} used /discussions command on #{interaction.channel}")
    await interaction.response.send_message("Select a course:", view=discussionsView(), ephemeral=True)

@tasks.loop(minutes=config.UPDATE_MINUTES)
#sample function for updating database
async def check():
    sleepAmount = randint(0,60)*60
    if sleepAmount > 0:
        await sleep(sleepAmount)
    #print("Initializing refresh...")
    courses= []
    moodle = moodleInterface()
    notificationCh = client.get_channel(config.NOTIFICATION_CHANNEL)
    dc_print(f"Got notification channel #{notificationCh.name}")
    mdl_print("Refreshing courses")
    getCoursesAPIResponse = moodle.getCourses() #we will need this later for debugging ;)
    for course in getCoursesAPIResponse:
        id = course["id"]
        c = Course(
            fullName=course["fullname"],
            courseID=id,
            summary=course["summary"]
        )
        mdl_print(f"Now refreshing course {c.name}")
        c.refresh()
        courses.append(c)

    filesCheckQuery = "SELECT TimeModified,URL FROM Files WHERE Filename = ? AND courseID=? AND moduleID=? AND Path=? AND discussionID IS NULL"
    filesUpdateQuery = '''UPDATE Files SET Path=?, Size=?, TimeModified=?, Author=?, URL=?, License=?, MD5=?
        WHERE Filename=? AND courseID=? AND moduleID=? AND Path=? AND DiscussionID IS NULL'''
    filesDeleteQuery = "DELETE FROM Files WHERE CourseID = ? AND URL = ? AND discussionID IS NULL"

    linksCheckQuery = "SELECT TimeModified,URL FROM Files WHERE Filename = ? AND courseID=? AND moduleID=? AND Path IS NULL AND discussionID IS NULL"
    linksUpdateQuery = '''UPDATE Files SET Path=NULL, Size=?, TimeModified=?, Author=?, URL=?, License=?, MD5=?
        WHERE Filename=? AND courseID=? AND moduleID=? AND Path IS NULL AND DiscussionID IS NULL'''

    filesCheckDiscussionQuery = "SELECT TimeModified,URL FROM Files WHERE Filename = ? AND courseID=? AND Path=? AND discussionID=? AND moduleID IS NULL"
    filesUpdateDiscussionQuery = '''UPDATE Files SET Path=?, Size=?, TimeModified=?, Author=?, URL=?, License=?, MD5=?
    WHERE Filename=? AND courseID=? AND DiscussionID=? AND Path=? AND moduleID IS NULL'''
    filesDeleteDiscussionQuery = "DELETE FROM Files WHERE URL = ? AND ID=?"

    #forumsCheckQuery = "SELECT Name FROM Forums WHERE ID = ?"
    #forumsUpdateQuery = "UPDATE Forums SET Name=? WHERE ID = ?"

    discussionsCheckQuery = "SELECT Name,TimeModified,Message,URL FROM Discussions WHERE ID=?"
    discussionsUpdateQuery = "UPDATE Discussions SET Name=?, TimeModified=?, Message=? WHERE ID = ?"
    discussionsDeleteQuery = "DELETE FROM Discussions WHERE ID = ?"

    pagesCheckQuery = "SELECT Name, Description,URL FROM Pages WHERE ID = ?"
    pagesUpdateQuery = "UPDATE Pages SET Name=?, Description=? WHERE ID = ?"
    pagesDeleteQuery = "DELETE FROM Pages WHERE ID=?"

    assignmentsCheckQuery = "SELECT Name, TimeOpened, TimeDue,URL FROM Assignments WHERE ID=?"
    assignmentsUpdateQuery = "UPDATE Assignments SET Name=?,TimeOpened=?,TimeDue=? WHERE ID=?"
    assignmentsDeleteQuery = "DELETE FROM Assignments WHERE ID=?"

    QuizzesAndWorkshopsCheckQuery = "SELECT Name FROM {} WHERE ID=?"
    QuizzesAndWorkshopsUpdateQuery = "UPDATE {} SET Name=? WHERE ID=?"
    QuizzesAndWorkshopsDeleteQuery = "DELETE FROM {} WHERE ID=?"

    connector = sqlite3.connect(config.SQLITE_DB_PATH)
    cursor = connector.cursor()
    courseCount = cursor.execute("SELECT COUNT(courseID) FROM Courses").fetchone()[0]
    FIRST_RUN = True

    if courseCount > 0:
        mdl_print("Database is not empty!")
        FIRST_RUN = False
    else:
        mdl_print("Database empty! This is the first run!")

    for course in courses:
        # this is spaghetti (I use these for discord)
        filesAdded = ""
        filesChanged = ""
        filesDeleted = ""
        linksAdded = ""
        linksChanged = ""
        linksDeleted = ""
        quizzesAdded = ""
        quizzesChanged = ""
        quizzesDeleted = ""
        assignmentsAdded = ""
        assignmentsChanged = ""
        assignmentsDeleted = ""
        pagesAdded = ""
        pagesChanged = ""
        pagesDeleted = ""
        workshopsAdded = ""
        workshopsChanged = ""
        workshopsDeleted = ""
        forumsDeleted = ""
        discussionsChanged = ""
        discussionsDeleted = ""
        attachmentsAdded = ""
        attachmentsChanged = ""
        attachmentsDeleted = ""

        cursor.execute("INSERT OR IGNORE INTO Courses(courseID, Fullname, Summary) VALUES (?,?,?)",(
            course.ID, course.name, course.summary,
        ))
        for file in course.files:
            if file.path != None and file.URL != None: #if path exists but url is None (probably) is a book
                data = cursor.execute(filesCheckQuery, (file.filename, course.ID, file.moduleID, file.path)).fetchone()
                if data != None:
                    if data[0] != file.timeModified:
                        mdl_print(f"File {file.filename} got updated! URL: {file.URL}")
                        cursor.execute(filesUpdateQuery, (
                                file.path, file.size, file.timeModified,
                                file.author, file.URL, file.License, "",file.filename, course.ID, file.moduleID, file.path)
                            )
                        filesChanged += f"~ [{file.filename}]({file.URL.replace('webservice/', '')}) ({filesizeConversion(file.size)})\n"
                        if config.DOWNLOAD_FILES:
                            dl_print(f"Downloading changed file {file.filename}, {file.size} bytes!")
                            file.download(path.join(config.DOWNLOAD_DIR, course.name))
                else:
                    mdl_print(f"New file! URL: {file.URL}")
                    query = '''INSERT OR IGNORE INTO Files(courseID, Filename, Path, Size, TimeModified, MimeType, Author, URL, License, MD5, moduleID) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                            '''
                    cursor.execute(query,(
                            (course.ID, file.filename, file.path, file.size, file.timeModified, file.mimeType, file.author, file.URL, file.License,
                                "", file.moduleID)
                        ))
                    filesAdded += f"+ [{file.filename}]({file.URL.replace('webservice/', '')}) ({filesizeConversion(file.size)}) by *{file.author}*\n"
                    if config.DOWNLOAD_FILES:
                        dl_print(f"Downloading new file {file.filename}, {file.size} bytes!")
                        file.download(path.join(config.DOWNLOAD_DIR, course.name))
            elif file.path == None and file.URL != None: # if file.path is None, it's a link
                data = cursor.execute(linksCheckQuery, (file.filename, course.ID, file.moduleID)).fetchone()
                if data != None:
                    if data[0] != file.timeModified:
                        mdl_print(f"Link {file.filename} got updated! URL: {file.URL}")
                        cursor.execute(linksUpdateQuery, (
                                file.size, file.timeModified,
                                file.author, file.URL, file.License, "",file.filename, course.ID, file.moduleID)
                            )
                        linksChanged += f"~ [{file.filename}]({file.URL.replace('webservice/', '')})\n"
                else:
                    mdl_print(f"New link! URL: {file.URL}")
                    query = '''INSERT OR IGNORE INTO Files(courseID, Filename, Path, Size, TimeModified, MimeType, Author, URL, License, MD5, moduleID) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                            '''
                    cursor.execute(query,(
                            (course.ID, file.filename, file.path, file.size, file.timeModified, file.mimeType, file.author, file.URL, file.License,
                                "", file.moduleID)
                        ))
                    linksAdded += f"+ [{file.filename}]({file.URL.replace('webservice/', '')})\n"
        # check for deletion (URL-based)
        for localFile in cursor.execute("SELECT URL, Filename, Size, Path FROM Files WHERE courseID=? AND discussionID IS NULL", (course.ID,)).fetchall():
            if localFile[3] != None:
                courseFileURLs = []
                for file in course.files:
                    courseFileURLs.append(file.URL)
                if localFile[0] not in courseFileURLs:
                    mdl_print(f"File {localFile[1]} deleted!")
                    cursor.execute(filesDeleteQuery, (course.ID, localFile[0]))
                    filesDeleted += f"- ~~{localFile[1]}~~ ({filesizeConversion(localFile[2])})\n"
            else: # if None it's a link
                courseFileURLs = []
                for file in course.files:
                    courseFileURLs.append(file.URL)
                if localFile[0] not in courseFileURLs:
                    mdl_print(f"Link {localFile[1]} deleted!")
                    cursor.execute(filesDeleteQuery, (course.ID, localFile[0]))
                    linksDeleted += f"- ~~{localFile[1]}~~\n"
        
        for quiz in course.quizzes:
            data = cursor.execute(QuizzesAndWorkshopsCheckQuery.format("Quizzes"), (quiz.ID,)).fetchone()
            if data != None:
                if data[0] != quiz.name:
                    mdl_print(f"Quiz name changed! URL: {quiz.URL}")
                    cursor.execute(QuizzesAndWorkshopsUpdateQuery.format("Quizzes"), (quiz.name, quiz.ID,))
                    quizzesChanged += f"~ ~~{data[0]}~~[{quiz.name}]({quiz.URL})\n"
            else:
                mdl_print(f"New quiz! URL: {quiz.URL}")
                cursor.execute("INSERT OR IGNORE INTO Quizzes(ID, courseID, Name, URL) VALUES (?,?,?,?)",(
                    (quiz.ID, course.ID, quiz.name, quiz.URL,)
                ))
                quizzesAdded += f"+ [{quiz.name}]({quiz.URL})\n"
        # check for deletion (Quiz ID)
        for localQuiz in cursor.execute("SELECT ID, Name FROM Quizzes WHERE courseID=?", (course.ID,)).fetchall():
            courseQuizIDs = []
            for quiz in course.quizzes:
                courseQuizIDs.append(quiz.ID)
            if localQuiz[0] not in courseQuizIDs:
                mdl_print(f"Quiz {localQuiz[1]} deleted!")
                cursor.execute(QuizzesAndWorkshopsDeleteQuery.format("Quizzes"), (localQuiz[0],))
                quizzesDeleted += f"- ~~{localQuiz[1]}~~\n"
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
                        mdl_print(f"Assignment name changed! New name: {assignment.name}")
                        assignmentsChanged += f"~ ~~{data[0]}~~[{assignment.name}]({assignment.URL})\n"
                    else:
                        assignmentsChanged += f"~ [{assignment.name}]({assignment.URL})\n"
                    if data[1] != assignment.timeOpened:
                        mdl_print(f"Assignment {assignment.name} time opened changed!")
                        assignmentsChanged += f"    *Opened: ~~{str(datetime.fromtimestamp(data[1]))}~~{str(datetime.fromtimestamp(assignment.timeOpened))}*\n"
                    else:
                        assignmentsChanged += f"    *Opened: {str(datetime.fromtimestamp(assignment.timeOpened))}*\n"
                    if data[2] != assignment.timeDue:
                        mdl_print(f"Assignment {assignment.name} time due changed!")
                        assignmentsChanged += f"    *Due: ~~{str(datetime.fromtimestamp(data[2]))}~~{str(datetime.fromtimestamp(assignment.timeDue))}*\n"
                    else:
                        assignmentsChanged += f"    *Due: {str(datetime.fromtimestamp(assignment.timeDue))}*\n"
                cursor.execute(assignmentsUpdateQuery, (assignment.name, assignment.timeOpened,
                    assignment.timeDue, assignment.ID   
                ))

            else:
                mdl_print(f"New assignment! URL: {assignment.URL}")
                cursor.execute("INSERT OR IGNORE INTO Assignments(ID, courseID, Name, URL, TimeOpened, TimeDue) VALUES (?,?,?,?,?,?)",(
                    (assignment.ID, course.ID, assignment.name, assignment.URL, assignment.timeOpened, assignment.timeDue,)
                ))
                assignmentsAdded += f"+ [{assignment.name}]({assignment.URL})\n    *Opened: {str(datetime.fromtimestamp(assignment.timeOpened))}*\n    *Due: {str(datetime.fromtimestamp(assignment.timeDue))}*\n"
        #check for deletion (ID)
        for localAssignment in cursor.execute("SELECT ID, Name FROM Assignments WHERE courseID=?", (course.ID,)).fetchall():
            courseAssignmentIDs = []
            for assignment in course.assignments:
                courseAssignmentIDs.append(assignment.ID)
            if localAssignment[0] not in courseAssignmentIDs:
                mdl_print(f"Assignment {localAssignment[1]} deleted!")
                cursor.execute(assignmentsDeleteQuery, (localAssignment[0],))
                assignmentsDeleted += f"- ~~{localAssignment[1]}~~\n"

        for page in course.pages:
            data = cursor.execute(pagesCheckQuery, (page.ID, )).fetchone()
            if data != None:
                if (data[0] != page.name or data[1] != page.description):
                    if data[0] != page.name:
                        mdl_print(f"Page {data[0]} name changed! New name: {page.name}")
                        pagesChanged += f"~ ~~{data[0]}~~[{page.name}]({page.URL})\n"
                    else:
                        pagesChanged += f"~ [{page.name}]({page.URL})\n"
                    if data[1] != page.description:
                        mdl_print("Page description changed!")
                        pagesChanged += f"    *Page content modified*\n"
                cursor.execute(pagesUpdateQuery, (page.name, page.description, page.ID, ))
            else:
                mdl_print("New page!")
                cursor.execute("INSERT OR IGNORE INTO Pages(ID, courseID, Name, URL, Description) VALUES (?,?,?,?,?)",(
                    (page.ID, course.ID, page.name, page.URL, page.description,)
                ))
                pagesAdded += f"+ [{page.name}]({page.URL})\n"
        # check for deletion (ID)
        for localPage in cursor.execute("SELECT ID, Name FROM Pages WHERE courseID=?", (course.ID,)).fetchall():
            coursePageIDs = []
            for page in course.pages:
                coursePageIDs.append(page.ID)
            if localPage[0] not in coursePageIDs:
                mdl_print(f"Page {localPage[1]} deleted!")
                cursor.execute(pagesDeleteQuery, (localPage[0],))
                pagesDeleted += f"- ~~{localPage[1]}~~\n"

        for workshop in course.workshops:
            data = cursor.execute(QuizzesAndWorkshopsCheckQuery.format("Workshops"), (workshop.ID,)).fetchone()
            if data != None:
                #print(data)
                if data[0] != workshop.name:
                    mdl_print(f"Workshop {data[0]} name changed! New name: {workshop.name}")
                    cursor.execute(QuizzesAndWorkshopsUpdateQuery.format("Workshops"), (workshop.name, workshop.ID,))
                    workshopsChanged += f"~ ~~{data[0]}~~[{workshop.name}]({workshop.URL})\n"
            else:
                mdl_print(f"New workshop: URL: {workshop.URL}")
                cursor.execute("INSERT OR IGNORE INTO Workshops(ID, courseID, Name, URL) VALUES (?,?,?,?)",(
                    (workshop.ID, course.ID, workshop.name, workshop.URL, )
                ))
                workshopsAdded += f"+ [{workshop.name}]({workshop.URL})\n"
        # check for deletion (ID)        
        for localWorkshop in cursor.execute("SELECT ID, Name FROM Workshops WHERE courseID=?", (course.ID,)).fetchall():
            courseWorkshopIDs=[]
            for workshop in course.workshops:
                courseWorkshopIDs.append(workshop.ID)
            if localWorkshop[0] not in courseWorkshopIDs:
                mdl_print(f"Workshop {localWorkshop[1]} deleted!")
                cursor.execute(QuizzesAndWorkshopsDeleteQuery.format("Workshops"),(localWorkshop[0],))
                workshopsDeleted += f"- ~~{localWorkshop[1]}~~\n"
        
        for forum in course.forums:
            cursor.execute("INSERT OR IGNORE INTO Forums(ID, courseID, Name, URL) VALUES (?,?,?,?)",(
                (forum.ID, course.ID, forum.name, forum.URL, )
            )) #we dont care for forum changes, so simply populate the database
            for discussion in forum.discussions:
                data = cursor.execute(discussionsCheckQuery, (discussion.ID,)).fetchone()
                if data != None:
                    if data[1] != discussion.timeModified: #discussion updated! 
                        mdl_print(f"Discussion {discussion.name} update!")
                        if discussion.name != data[0]:
                            mdl_print(f"Discussion {data[0]} name changed! New name: {discussion.name}")
                            discussionsChanged += f"~ ~~{data[0]}~~[{discussion.name}]({discussion.URL})\n"
                        else:
                            discussionsChanged += f"~ [{discussion.name}]({discussion.URL})\n"
                        if discussion.message != data[2]:
                            mdl_print(f"Message update! Old message: {data[2]} New message: {discussion.message} Link: {discussion.URL}")
                            discussionsChanged += f"    *Discussion content modified*\n"
                        cursor.execute(discussionsUpdateQuery,(discussion.name, discussion.timeModified, discussion.message, discussion.ID,))
                
                else: #new discussion
                    mdl_print(f"New discussion! URL: {discussion.URL}")
                    cursor.execute("INSERT OR IGNORE INTO Discussions(ID, courseID, Name, URL, TimeModified, Message, forumID) VALUES (?,?,?,?,?,?,?)",(
                        (discussion.ID, course.ID, discussion.name, discussion.URL, discussion.timeModified, discussion.message, forum.ID)
                    ))
                    if not FIRST_RUN:
                        discussionEmbed = nextcord.Embed(title=discussion.name, url=discussion.URL, color=config.DISCUSSION_EMBED_COLOR, description=discussion.message)
                        if len(discussion.message) > 4096:
                            await messageSplitter(notificationCh, discussion.message, config.DISCUSSION_LINES_PER_EMBED, "Discussion", course, "NEW", config.DISCUSSION_EMBED_COLOR)

                        elif len(discussion.message) > 0 and len(discussion.message) < 4096:
                            discussionEmbed.set_author(name=f"New discussion in forum \'{forum.name}\' of course {course.name}", url=forum.URL)
                            dc_print(f"Sending a new discussion ({discussion.name})!") ## The only call made to Discord from within the loop
                            await notificationCh.send(embed=discussionEmbed)
                for attachment in discussion.files:
                    data = cursor.execute(filesCheckDiscussionQuery, (attachment.filename,course.ID,attachment.path, discussion.ID)).fetchone()
                    if data != None:
                        if data[0] != attachment.timeModified: #file modified
                            mdl_print(f"Discussion attachment modified! New link: {attachment.URL}")
                            cursor.execute(filesUpdateDiscussionQuery, (
                                attachment.path, attachment.size, attachment.timeModified,
                                attachment.author, attachment.URL, attachment.License, "",attachment.filename, course.ID, discussion.ID, attachment.path))
                            attachmentsChanged += f"~ [{attachment.filename}]({attachment.URL.replace('webservice/', '')}) ({filesizeConversion(attachment.size)})\n"
                    
                    else: #new file
                        mdl_print(f"New attachment found! URL: {attachment.URL}")
                        query = '''INSERT OR IGNORE INTO Files(courseID, Filename, Path, Size, TimeModified, MimeType, Author, URL, License, MD5, discussionID) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                                '''
                        cursor.execute(query,(
                            (course.ID, attachment.filename, attachment.path, attachment.size, attachment.timeModified, attachment.mimeType, attachment.author, attachment.URL, attachment.License,
                                "", discussion.ID)
                            ))

                        attachmentsAdded += f"+ [{attachment.filename}]({attachment.URL.replace('webservice/', '')}) ({filesizeConversion(attachment.size)}) by *{attachment.author}* in discussion [{discussion.name}]({discussion.URL})\n"
                #check attachment deletion (by URL)
                for localAttachment in cursor.execute("SELECT URL, Filename FROM Files WHERE courseID=? AND discussionID=?", (course.ID, discussion.ID)).fetchall():
                    discussionFileURLs = []
                    for attachment in discussion.files:
                        discussionFileURLs.append(attachment.URL)
                    if localAttachment[0] not in discussionFileURLs:
                        mdl_print(f"Attachment {localAttachment[1]} from discussion {discussion.name} deleted!")
                        cursor.execute(filesDeleteDiscussionQuery, (localAttachment[0], discussion.ID))
                        attachmentsDeleted += f"- ~~{localAttachment[1]}~~ in discussion [{discussion.name}]({discussion.URL})\n"

            for localDiscussion in cursor.execute("SELECT ID, Name FROM Discussions WHERE forumID=?", (forum.ID,)).fetchall():
                forumDiscussionIDs = []
                for discussion in forum.discussions:
                    forumDiscussionIDs.append(discussion.ID)
                if localDiscussion[0] not in forumDiscussionIDs:
                    mdl_print(f"Discussion {localDiscussion[1]} deleted!")
                    cursor.execute("DELETE FROM Files WHERE discussionID=?", (localDiscussion[0],)) # also delete the files to tidy the DB
                    cursor.execute(discussionsDeleteQuery, (localDiscussion[0],))
                    discussionsDeleted += f"- ~~{localDiscussion[1]}~~\n"
        for localForum in cursor.execute("SELECT ID, Name FROM Forums WHERE courseID=?", (course.ID,)).fetchall():
            courseForumIDs = []
            for forum in course.forums:
                courseForumIDs.append(forum.ID)
            if localForum[0] not in courseForumIDs:
                mdl_print(f"Forum {localForum[1]} deleted, deleting discussions and attachments!")
                for i in cursor.execute("SELECT ID FROM Discussions WHERE forumID=?", (localForum[0],)).fetchall():
                    cursor.execute("DELETE FROM Files WHERE discussionID=?", (i[0],))
                cursor.execute("DELETE FROM Discussions WHERE forumID=?", (localForum[0],))
                cursor.execute("DELETE FROM Forums WHERE ID=?", (localForum[0],))
                forumsDeleted += f"- ~~{localForum[1]}~~\n"

        if not FIRST_RUN:
            if len(filesAdded) > 0 and len(filesAdded) < 4096:
                embed = nextcord.Embed(title="File list:", color=config.FILE_EMBED_COLOR, description=filesAdded)
                embed.set_author(name=f"New files in course: {course.name}", url=course.URL)
                dc_print(f"Sending new files in course {course.name}")
                await notificationCh.send(embed=embed)
            elif len(filesAdded) > 4096:
                await messageSplitter(notificationCh, filesAdded, config.FILES_PER_EMBED, "File", course, "NEW", config.FILE_EMBED_COLOR)

            if len(filesChanged) > 0 and len(filesChanged) < 4096:
                embed = nextcord.Embed(title="File list:", color=config.FILE_EMBED_COLOR, description=filesChanged)
                embed.set_author(name=f"Files changed in course: {course.name}", url=course.URL)
                dc_print(f"Sending changed files in course: {course.name}")
                await notificationCh.send(embed=embed)
            elif len(filesChanged) > 4096:
                await messageSplitter(notificationCh, filesChanged, config.FILES_PER_EMBED, "File", course, "CHANGED", config.FILE_EMBED_COLOR)

            if len(filesDeleted) > 0 and len(filesDeleted) < 4096:
                embed = nextcord.Embed(title="File list:", color=config.FILE_EMBED_COLOR, description=filesDeleted)
                embed.set_author(name=f"Files deleted in course: {course.name}", url=course.URL)
                dc_print(f"Sending deleted files in course: {course.name}")
                await notificationCh.send(embed=embed)
                saveAPIResponse(jsonResponse=moodle.getCourseData(course.ID), savePath=path.join(config.DOWNLOAD_DIR,"API_RESPONSES"), course=course.name)
            elif len(filesDeleted) > 4096:
                await messageSplitter(notificationCh, filesDeleted, config.FILES_PER_EMBED, "File", course, "DELETED", config.FILE_EMBED_COLOR)
                saveAPIResponse(jsonResponse=moodle.getCourseData(course.ID), savePath=path.join(config.DOWNLOAD_DIR,"API_RESPONSES"), course=course.name)

            if len(linksAdded) > 0 and len(linksAdded) < 4096:
                embed = nextcord.Embed(title="Link list:", color=config.LINK_EMBED_COLOR, description=linksAdded)
                embed.set_author(name=f"New links in course: {course.name}", url=course.URL)
                dc_print(f"Sending new links in course {course.name}")
                await notificationCh.send(embed=embed)
            elif len(filesAdded) > 4096:
                await messageSplitter(notificationCh, linksAdded, config.LINKS_PER_EMBED, "Link", course, "NEW", config.LINK_EMBED_COLOR)

            if len(linksChanged) > 0 and len(linksChanged) < 4096:
                embed = nextcord.Embed(title="Link list:", color=config.LINK_EMBED_COLOR, description=linksChanged)
                embed.set_author(name=f"Links changed in course: {course.name}", url=course.URL)
                dc_print(f"Sending changed links in course: {course.name}")
                await notificationCh.send(embed=embed)
            elif len(filesChanged) > 4096:
                await messageSplitter(notificationCh, linksChanged, config.LINKS_PER_EMBED, "Link", course, "CHANGED", config.LINK_EMBED_COLOR)

            if len(linksDeleted) > 0 and len(linksDeleted) < 4096:
                embed = nextcord.Embed(title="Link list:", color=config.LINK_EMBED_COLOR, description=linksDeleted)
                embed.set_author(name=f"Links deleted in course: {course.name}", url=course.URL)
                dc_print(f"Sending deleted links in course: {course.name}")
                await notificationCh.send(embed=embed)
            elif len(filesDeleted) > 4096:
                await messageSplitter(notificationCh, linksDeleted, config.LINKS_PER_EMBED, "Link", course, "DELETED", config.LINK_EMBED_COLOR)

            if len(quizzesAdded) > 0:
                embed = nextcord.Embed(title="Quiz list:", color=config.QUIZ_EMBED_COLOR, description=quizzesAdded)
                embed.set_author(name=f"New quizzes in course: {course.name}", url=course.URL)
                dc_print(f"Sending new quizzes in course {course.name}")
                await notificationCh.send(embed=embed)
            if len(quizzesChanged) > 0:
                embed = nextcord.Embed(title="Quiz list:", color=config.QUIZ_EMBED_COLOR, description=quizzesChanged)
                embed.set_author(name=f"Quizzes changed in course: {course.name}", url=course.URL)
                dc_print(f"Sending changed quizzes in course: {course.name}")
                await notificationCh.send(embed=embed)
            if len(quizzesDeleted) > 0:
                embed = nextcord.Embed(title="Quiz list:", color=config.QUIZ_EMBED_COLOR, description=quizzesDeleted)
                embed.set_author(name=f"Quizzes deleted in course: {course.name}", url=course.URL)
                dc_print(f"Sending deleted quizzes in course: {course.name}")
                await notificationCh.send(embed=embed)

            if len(assignmentsAdded) > 0:
                embed = nextcord.Embed(title="Assignment list:", color=config.ASSIGNMENT_EMBED_COLOR, description=assignmentsAdded)
                embed.set_author(name=f"New assignments in course: {course.name}", url=course.URL)
                dc_print(f"Sending new assignments in course {course.name}")
                await notificationCh.send(embed=embed)
            if len(assignmentsChanged) > 0:
                embed = nextcord.Embed(title="Assignment list:", color=config.ASSIGNMENT_EMBED_COLOR, description=assignmentsChanged)
                embed.set_author(name=f"Assignments changed in course: {course.name}", url=course.URL)
                dc_print(f"Sending changed assignments in course: {course.name}")
                await notificationCh.send(embed=embed)
            if len(assignmentsDeleted) > 0:
                embed = nextcord.Embed(title="Assignment list:", color=config.ASSIGNMENT_EMBED_COLOR, description=assignmentsDeleted)
                embed.set_author(name=f"assignments deleted in course: {course.name}", url=course.URL)
                dc_print(f"Sending deleted assignments in course: {course.name}")
                await notificationCh.send(embed=embed)

            if len(pagesAdded) > 0:
                embed = nextcord.Embed(title="Page list:", color=config.PAGE_EMBED_COLOR, description=pagesAdded)
                embed.set_author(name=f"New pages in course: {course.name}", url=course.URL)
                dc_print(f"Sending new pages in course {course.name}")
                await notificationCh.send(embed=embed)
            if len(pagesChanged) > 0:
                embed = nextcord.Embed(title="Page list:", color=config.PAGE_EMBED_COLOR, description=pagesChanged)
                embed.set_author(name=f"Pages changed in course: {course.name}", url=course.URL)
                dc_print(f"Sending changed pages in course: {course.name}")
                await notificationCh.send(embed=embed)
            if len(pagesDeleted) > 0:
                embed = nextcord.Embed(title="Page list:", color=config.PAGE_EMBED_COLOR, description=pagesDeleted)
                embed.set_author(name=f"Pages deleted in course: {course.name}", url=course.URL)
                dc_print(f"Sending deleted pages in course: {course.name}")
                await notificationCh.send(embed=embed)

            if len(workshopsAdded) > 0:
                embed = nextcord.Embed(title="Workshop list:", color=config.WORKSHOP_EMBED_COLOR, description=workshopsAdded)
                embed.set_author(name=f"New workshops in course: {course.name}", url=course.URL)
                dc_print(f"Sending new workshops in course {course.name}")
                await notificationCh.send(embed=embed)
            if len(workshopsChanged) > 0:
                embed = nextcord.Embed(title="Workshop list:", color=config.WORKSHOP_EMBED_COLOR, description=workshopsChanged)
                embed.set_author(name=f"Workshops changed in course: {course.name}", url=course.URL)
                dc_print(f"Sending changed workshops in course: {course.name}")
                await notificationCh.send(embed=embed)
            if len(workshopsDeleted) > 0:
                embed = nextcord.Embed(title="Workshop list:", color=config.WORKSHOP_EMBED_COLOR, description=workshopsDeleted)
                embed.set_author(name=f"Workshops deleted in course: {course.name}", url=course.URL)
                dc_print(f"Sending deleted workshops in course: {course.name}")
                await notificationCh.send(embed=embed)

            if len(forumsDeleted) > 0:
                embed = nextcord.Embed(title="Forum list:", color=config.FORUM_EMBED_COLOR, description=forumsDeleted)
                embed.set_author(name=f"Forums deleted in course: {course.name}", url=course.URL)
                dc_print(f"Sending deleted forums in course: {course.name}")
                await notificationCh.send(embed=embed)

            if len(discussionsChanged) > 0 and len(discussionsChanged) < 4096:
                embed = nextcord.Embed(title="Discussion list:", color=config.DISCUSSION_EMBED_COLOR, description=discussionsChanged)
                embed.set_author(name=f"Discussions changed in course: {course.name}", url=course.URL)
                dc_print(f"Sending changed discussions in course: {course.name}")
                await notificationCh.send(embed=embed)
            elif len(discussionsChanged) > 4096:
                await messageSplitter(notificationCh, discussionsChanged, config.DISCUSSIONS_PER_EMBED, "Discussions", course, "CHANGED", config.DISCUSSION_EMBED_COLOR)

            if len(discussionsDeleted) > 0 and len(discussionsDeleted) < 4096:
                embed = nextcord.Embed(title="Discussion list:", color=config.DISCUSSION_EMBED_COLOR, description=discussionsDeleted)
                embed.set_author(name=f"Discussions deleted in course: {course.name}", url=course.URL)
                dc_print(f"Sending deleted workshops in course: {course.name}")
                await notificationCh.send(embed=embed)
            elif len(discussionsDeleted) > 4096:
                await messageSplitter(notificationCh, discussionsDeleted, config.DISCUSSIONS_PER_EMBED, "Discussions", course, "DELETED", config.DISCUSSION_EMBED_COLOR)

            if len(attachmentsAdded) > 0 and len(attachmentsAdded) < 4096:
                embed = nextcord.Embed(title="Attachment list:", color=config.ATTACHMENT_EMBED_COLOR, description=attachmentsAdded)
                embed.set_author(name=f"New attachments in course: {course.name}", url=course.URL)
                dc_print(f"Sending new attachments in course {course.name}")
                await notificationCh.send(embed=embed)
            elif len(attachmentsAdded) > 4096:
                await messageSplitter(notificationCh, attachmentsAdded, config.ATTACHMENTS_PER_EMBED, "Attachments", course, "NEW", config.ATTACHMENT_EMBED_COLOR)

            if len(attachmentsChanged) > 0 and len(attachmentsChanged) < 4096:
                embed = nextcord.Embed(title="Attachment list:", color=config.ATTACHMENT_EMBED_COLOR, description=attachmentsChanged)
                embed.set_author(name=f"Attachments changed in course: {course.name}", url=course.URL)
                dc_print(f"Sending changed attachments in course: {course.name}")
                await notificationCh.send(embed=embed)
            elif len(attachmentsChanged) > 4096:
                await messageSplitter(notificationCh, attachmentsChanged, config.ATTACHMENTS_PER_EMBED, "Attachments", course, "CHANGED", config.ATTACHMENT_EMBED_COLOR)

            if len(attachmentsDeleted) > 0 and len(attachmentsDeleted) < 4096:
                embed = nextcord.Embed(title="Attachment list:", color=config.ATTACHMENT_EMBED_COLOR, description=attachmentsDeleted)
                embed.set_author(name=f"Attachments deleted in course: {course.name}", url=course.URL)
                dc_print(f"Sending deleted attachments in course: {course.name}")
                await notificationCh.send(embed=embed)
            elif len(attachmentsDeleted) > 4096:
                await messageSplitter(notificationCh, attachmentsDeleted, config.ATTACHMENTS_PER_EMBED, "Attachments", course, "DELETED", config.ATTACHMENT_EMBED_COLOR)

    FIRST_RUN = False
    connector.commit()
    connector.close()
    mdl_print("Refresh finished!")

def mdl_print(text):
    print(f"{str(datetime.now())} - [MOODLE]  {text}")

def dc_print(text):
    print(f"{str(datetime.now())} - [DISCORD] {text}")

def dl_print(text):
    print(f"{str(datetime.now())} - [DLOADER] {text}")

client.run(config.BOT_TOKEN)
