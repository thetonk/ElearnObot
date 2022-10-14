import nextcord, config, sqlite3, math
from random import randint
from time import time
from asyncio import sleep
from nextcord.ext import commands, tasks
from nextcord.ui import Select, Button, button, View
from moodleUtils import *


client = commands.Bot(command_prefix=";", intents=nextcord.Intents.default())
client.remove_command("help")

class myView(View):

    def __init__(self):
        self.timeout = None
        super().__init__()
        myoptions = []
        self.discussionData = []
        self.currentPage = 1
        connector = sqlite3.connect("Database/test.db")
        cursor= connector.cursor()
        data = cursor.execute("SELECT Fullname, courseID FROM Courses").fetchall()
        connector.close()
        self.totalPages = 0
        for row in data:
            myoptions.append(nextcord.SelectOption(label=row[0],value=str(row[1])))

        courseSelect = Select(placeholder="Choose a course", min_values=1, max_values=1, options=myoptions)

        async def selectCallback(interaction: nextcord.Interaction):
            if courseSelect.values[0]=="12526":
                await interaction.response.send_message("Noice", ephemeral=True)
            
            connector = sqlite3.connect("Database/test.db")
            cursor= connector.cursor()
            self.discussionData = cursor.execute("SELECT Name,ID,URL FROM Discussions WHERE courseID=?", (int(courseSelect.values[0]),)).fetchall()
            connector.close()
            self.totalPages = int(math.ceil(len(self.discussionData)/15.0))
            embed = nextcord.Embed(color=0x3a34eb)
            for row in self.discussionData[:15]:
                embed.add_field(name=row[0],value=f"[link]({row[2]})")
            await interaction.message.edit(f"Page: {self.currentPage}/{self.totalPages}", embed=embed, view=self)

        courseSelect.callback = selectCallback
        self.add_item(courseSelect)
    
    @button(emoji="◀️", style=nextcord.ButtonStyle.blurple)
    async def leftCallback(self, button: Button, interaction: nextcord.Interaction):
        if self.currentPage > 1:
            self.currentPage -= 1
            embed = nextcord.Embed(color=0x3a34eb)
            if self.currentPage == self.totalPages:
                for row in self.discussionData[(self.totalPages-1)*15:]:
                    print(row)
                    embed.add_field(name=row[0],value=f"[link]({row[2]})")
            else:
                for row in self.discussionData[(self.currentPage-1)*15 : self.currentPage*15]:
                    print(row)
                    embed.add_field(name=row[0],value=f"[link]({row[2]})")
            await interaction.message.edit(f"Page: {self.currentPage}/{self.totalPages}", embed=embed, view=self)
        else:
            return

    @button(emoji="▶️", style=nextcord.ButtonStyle.blurple)
    async def rightCallback(self, button: Button, interaction: nextcord.Interaction):
        if self.currentPage < self.totalPages:
            self.currentPage += 1
            embed = nextcord.Embed(color=0x3a34eb)
            if self.currentPage == self.totalPages:
                for row in self.discussionData[(self.totalPages-1)*15:]:
                    print(row)
                    embed.add_field(name=row[0],value=f"[link]({row[2]})")
                button.disabled = True
            else:
                for row in self.discussionData[(self.currentPage-1)*15 : self.currentPage*15]:
                    print(row)
                    embed.add_field(name=row[0],value=f"[link]({row[2]})")
            await interaction.message.edit(f"Page: {self.currentPage}/{self.totalPages}", embed=embed, view=self)
        else:
            return

@client.event
async def on_ready():
    print("Ive been attached as '%s'" % client.user)

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    await client.process_commands(message)

@client.command()
async def menu(ctx):
    await ctx.channel.send("Hi", view=myView())


@tasks.loop(minutes=90)
#sample function for updating database
async def check():
    print("refreshing courses...")
    #sleepAmount = randint(0,60)*60
    #if sleepAmount > 0:
        #await sleep(sleepAmount)
    print("Initializing refresh...")
    courses= []
    moodle = moodleInterface()
    for course in moodle.getCourses():
        id = course["id"]
        c = Course(
            fullName=course["fullname"],
            courseID=id,
            summary=course["summary"]
        )
        c.refresh()
        courses.append(c)

    filesCheckQuery = "SELECT TimeModified,URL FROM Files WHERE Filename = ? AND courseID=? AND moduleID=? AND Path=? AND discussionID IS NULL"
    filesUpdateQuery = '''UPDATE Files SET Path=?, Size=?, TimeModified=?, Author=?, URL=?, License=?, MD5=?
        WHERE Filename=? AND courseID=? AND moduleID=? AND Path=? AND DiscussionID IS NULL'''

    filesCheckDiscussionQuery = "SELECT TimeModified,URL FROM Files WHERE Filename = ? AND courseID=? AND Path=? AND discussionID=? AND moduleID IS NULL"
    filesUpdateDiscussionQuery = '''UPDATE Files SET Path=?, Size=?, TimeModified=?, Author=?, URL=?, License=?, MD5=?
    WHERE Filename=? AND courseID=? AND DiscussionID=? AND Path=? AND moduleID IS NULL'''

    #forumsCheckQuery = "SELECT Name FROM Forums WHERE ID = ?"
    #forumsUpdateQuery = "UPDATE Forums SET Name=? WHERE ID = ?"

    discussionsCheckQuery = "SELECT Name,TimeModified,Message,URL FROM Discussions WHERE ID=?"
    discussionsUpdateQuery = "UPDATE Discussions SET Name=?, TimeModified=?, Message=? WHERE ID = ?"

    pagesCheckQuery = "SELECT Name, Description,URL FROM Pages WHERE ID = ?"
    pagesUpdateQuery = "UPDATE Pages SET Name=?, Description=? WHERE ID = ?"

    assignmentsCheckQuery = "SELECT Name, TimeOpened, TimeDue,URL FROM Assignments WHERE ID=?"
    assignmentsUpdateQuery = "UPDATE Assignments SET Name=?,TimeOpened=?,TimeDue=? WHERE ID=?"

    QuizzesAndWorkshopsCheckQuery = "SELECT Name FROM {} WHERE ID=?"
    QuizzesAndWorkshopsUpdateQuery = "UPDATE {} SET Name=? WHERE ID=?"

    connector = sqlite3.connect("Database/test.db")
    cursor = connector.cursor()
    for course in courses:
        cursor.execute("INSERT OR IGNORE INTO Courses(courseID, Fullname, Summary) VALUES (?,?,?)",(
            course.ID, course.name, course.summary,
        ))
        for file in course.files:
            data = cursor.execute(filesCheckQuery, (file.filename, course.ID, file.moduleID, file.path)).fetchone()
            if data != None:
                if data[0] != file.timeModified:
                    print(f"File {file.filename} got updated! URL: {file.URL}")
                    cursor.execute(filesUpdateQuery, (
                            file.path, file.size, file.timeModified,
                            file.author, file.URL, file.License, "",file.filename, course.ID, file.moduleID, file.path)
                        )
            else:
                print(f"New file! URL: {file.URL}")
                query = '''INSERT OR IGNORE INTO Files(courseID, Filename, Path, Size, TimeModified, MimeType, Author, URL, License, MD5, moduleID) 
                            VALUES (?,?,?,?,?,?,?,?,?,?,?)
                        '''
                cursor.execute(query,(
                        (course.ID, file.filename, file.path, file.size, file.timeModified, file.mimeType, file.author, file.URL, file.License,
                            "", file.moduleID)
                    ))
        
        for quizz in course.quizzes:
            data = cursor.execute(QuizzesAndWorkshopsCheckQuery.format("Quizzes"), (quizz.ID,)).fetchone()
            if data != None:
                if data[0] != quizz.name:
                    print(f"Quizz name changed! URL: {quizz.URL}")
                    cursor.execute(QuizzesAndWorkshopsUpdateQuery.format("Quizzes"), (quizz.name, quizz.ID,))
            else:
                print(f"New quizz! URL: {quizz.URL}")
                cursor.execute("INSERT OR IGNORE INTO Quizzes(ID, courseID, Name, URL) VALUES (?,?,?,?)",(
                    (quizz.ID, course.ID, quizz.name, quizz.URL,)
                ))

        for label in course.labels:
            cursor.execute("INSERT OR IGNORE INTO Labels(courseID, Description) VALUES (?,?)",(
                (course.ID, label.description,)
            ))

        for assignment in course.assignments:
            data = cursor.execute(assignmentsCheckQuery, (assignment.ID,)).fetchone()
            if data != None:
                if data[0] != assignment.name:
                    print("Assignment name changed!")
                if data[1] != assignment.timeOpened:
                    print("Assignment time opened changed!")
                if data[2] != assignment.timeDue:
                    print("Assignment time due changed!")
                cursor.execute(assignmentsUpdateQuery, (assignment.name, assignment.timeOpened,
                    assignment.timeDue, assignment.ID   
                ))

            else:
                cursor.execute("INSERT OR IGNORE INTO Assignments(ID, courseID, Name, URL, TimeOpened, TimeDue) VALUES (?,?,?,?,?,?)",(
                    (assignment.ID, course.ID, assignment.name, assignment.URL, assignment.timeOpened, assignment.timeDue,)
                ))
        
        for page in course.pages:
            data = cursor.execute(pagesCheckQuery, (page.ID, )).fetchone()
            #print(data)
            if data != None:
                if data[0] != page.name:
                    print("Page name changed!")
                if data[1] != page.description:
                    print("Page description changed!")
                cursor.execute(pagesUpdateQuery, (page.name, page.description, page.ID, ))
            else:
                cursor.execute("INSERT OR IGNORE INTO Pages(ID, courseID, Name, URL, Description) VALUES (?,?,?,?,?)",(
                    (page.ID, course.ID, page.name, page.URL, page.description,)
                ))

        for workshop in course.workshops:
            data = cursor.execute(QuizzesAndWorkshopsCheckQuery.format("Workshops"), (workshop.ID,)).fetchone()
            if data != None:
                #print(data)
                if data[0] != workshop.name:
                    print("Workshop name changed! ")
                    cursor.execute(QuizzesAndWorkshopsUpdateQuery.format("Workshops"), (workshop.name, workshop.ID,))
            else:
                print(f"New workshop: URL: {workshop.URL}")
                cursor.execute("INSERT OR IGNORE INTO Workshops(ID, courseID, Name, URL) VALUES (?,?,?,?)",(
                    (workshop.ID, course.ID, workshop.name, workshop.URL, )
                ))
        
        for forum in course.forums:
            cursor.execute("INSERT OR IGNORE INTO Forums(ID, courseID, Name, URL) VALUES (?,?,?,?)",(
                (forum.ID, course.ID, forum.name, forum.URL, )
            )) #we dont care for forum changes, so simply populate the database
            for discussion in forum.discussions:
                data = cursor.execute(discussionsCheckQuery, (discussion.ID,)).fetchone()
                if data != None:
                    if data[1] != discussion.timeModified: #discussion updated!
                        print("Discussion update!")
                        if discussion.message != data[2]:
                            print(f"Message update!\n Old message: {data[2]}\nNew message: {discussion.message}\nLink: {discussion.URL}")
                        cursor.execute(discussionsUpdateQuery,(discussion.name, discussion.timeModified, discussion.message, discussion.ID,))
                
                else: #new discussion
                    print(f"New discussion! URL: {discussion.URL}")
                    cursor.execute("INSERT OR IGNORE INTO Discussions(ID, courseID, Name, URL, TimeModified, Message) VALUES (?,?,?,?,?,?)",(
                        (discussion.ID, course.ID, discussion.name, discussion.URL, discussion.timeModified, discussion.message)
                    ))
                
                for attachment in discussion.files:
                    data = cursor.execute(filesCheckDiscussionQuery, (attachment.filename,course.ID,attachment.path, discussion.ID)).fetchone()
                    if data != None:
                        if data[0] != attachment.timeModified: #file modified
                            print(f"Discussion attachment modified! New link: {attachment.URL}")
                            cursor.execute(filesUpdateDiscussionQuery, (
                                attachment.path, attachment.size, attachment.timeModified,
                                attachment.author, attachment.URL, attachment.License, "",attachment.filename, course.ID, discussion.ID, attachment.path))
                    
                    else: #new file
                        print(f"New attachment found! URL: {attachment.URL}")
                        query = '''INSERT OR IGNORE INTO Files(courseID, Filename, Path, Size, TimeModified, MimeType, Author, URL, License, MD5, discussionID) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                                '''
                        cursor.execute(query,(
                            (course.ID, attachment.filename, attachment.path, attachment.size, attachment.timeModified, attachment.mimeType, attachment.author, attachment.URL, attachment.License,
                                "", discussion.ID)
                            ))

    connector.commit()
    connector.close()
    print("Update finished!")

check.start()
client.run(config.BOT_TOKEN)