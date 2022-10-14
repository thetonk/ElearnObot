import os, sqlite3, requests, hashlib,config
from moodleUtils import moodleInterface, Course


moodle = moodleInterface()

if os.path.exists("out.txt"):
    os.remove("out.txt")

fileOut = open("out.txt", "a",encoding="utf-8")

courses = []

for course in moodle.getCourses():
    id = course["id"]
    c = Course(
        fullName=course["fullname"],
        courseID=id,
        summary=course["summary"]
        )
    c.refresh()
    courses.append(c)
    fileOut.write("==============================LESSON {}==================================\n".format(course["fullname"]))
    courseUnits = moodle.getCourseData(courseID=id)
    for unit in courseUnits:
        modules = unit["modules"]
        fileOut.write("|> Unit name: {}\n".format(unit["name"]))
        for module in modules:
            #print(module)
            moduleType = module["modplural"]
            fileOut.write("|\t|> Module name: {}, type: {}\n".format(module["name"], moduleType))
            if moduleType == "Forums":
                pass #forum

            elif moduleType == "Quizzes":
                pass #quiz

            elif moduleType == "Assignments":
                pass #assignment

            elif moduleType == "Workshops":
                pass #assignment

            elif moduleType == "Labels":
                pass #label

            elif moduleType == "Pages":
                pass #label

            if "contents" in module:
                files = module["contents"]
                for file in files:
                    if moduleType == "Pages" or moduleType == "Folders" or moduleType == "Files":
                        fileOut.write("|\t|\t|> --------------------------------------------------------------------------------\n")
                        fileOut.write("|\t|\t|> FILENAME\t" + file["filename"]+"\n|\t|\t|> "+ "FILEURL\t" + file["fileurl"]+"\n")
                    else:
                        fileOut.write("|\t|> --------------------------------------------------------------------------------\n")
                        fileOut.write("|\t|> FILENAME\t" + file["filename"]+"\n|\t|> "+ "FILEURL\t" + file["fileurl"]+"\n")

fileOut.close()
connection = sqlite3.connect("Database/elearnObotdbTest.db")
cursor = connection.cursor()

def generateMD5Hash(fileURL: str):
         return hashlib.md5(requests.get(fileURL, params={"token":config.API_TOKEN}).content).hexdigest() #kinda memory inefficient though

def populateDB():
    for course in courses: #big O goes BRRRRRRRR
        print(course.name)
        cursor.execute("INSERT OR IGNORE INTO Courses(courseID, Fullname, Summary) VALUES (?,?,?)",(
            course.ID, course.name, course.summary,
        ))

        for file in course.files:
            query = '''INSERT OR IGNORE INTO Files(courseID, Filename, Path, Size, TimeModified, MimeType, Author, URL, License, MD5, moduleID) 
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)
                    '''
            cursor.execute(query,(
                (course.ID, file.filename, file.path, file.size, file.timeModified, file.mimeType, file.author, file.URL, file.License,
                generateMD5Hash(file.URL), file.moduleID)
            ))
        
        for quizz in course.quizzes:
            cursor.execute("INSERT OR IGNORE INTO Quizzes(ID, courseID, Name, URL) VALUES (?,?,?,?)",(
                (quizz.ID, course.ID, quizz.name, quizz.URL,)
            ))
        
        for assignment in course.assignments:
            cursor.execute("INSERT OR IGNORE INTO Assignments(ID, courseID, Name, URL, TimeOpened, TimeDue) VALUES (?,?,?,?,?,?)",(
                (assignment.ID, course.ID, assignment.name, assignment.URL, assignment.timeOpened, assignment.timeDue,)
            ))
        
        for page in course.pages:
            cursor.execute("INSERT OR IGNORE INTO Pages(ID, courseID, Name, URL, Description) VALUES (?,?,?,?,?)",(
                (page.ID, course.ID, page.name, page.URL, page.description,)
            ))

        for label in course.labels:
            cursor.execute("INSERT OR IGNORE INTO Labels(courseID, Description) VALUES (?,?)",(
                (course.ID, label.description,)
            ))

        for workshop in course.workshops:
            cursor.execute("INSERT OR IGNORE INTO Workshops(ID, courseID, Name, URL) VALUES (?,?,?,?)",(
                (workshop.ID, course.ID, workshop.name, workshop.URL, )
            ))
        
        for forum in course.forums:
            cursor.execute("INSERT OR IGNORE INTO Forums(ID, courseID, Name, URL) VALUES (?,?,?,?)",(
                (forum.ID, course.ID, forum.name, forum.URL, )
            ))
            for discussion in forum.discussions:
                cursor.execute("INSERT OR IGNORE INTO Discussions(ID, courseID, Name, URL, TimeModified, Message) VALUES (?,?,?,?,?,?)",(
                    (discussion.ID, course.ID, discussion.name, discussion.URL, discussion.timeModified, discussion.message)
                ))
                for attachment in discussion.files:
                    query = '''INSERT OR IGNORE INTO Files(courseID, Filename, Path, Size, TimeModified, MimeType, Author, URL, License, MD5, discussionID) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                            '''
                    cursor.execute(query,(
                        (course.ID, attachment.filename, attachment.path, attachment.size, attachment.timeModified, attachment.mimeType, attachment.author, attachment.URL, attachment.License,
                        generateMD5Hash(attachment.URL), discussion.ID)
                    ))

    connection.commit()
    connection.close()

populateDB()