import os
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
for course in courses:
    print(course.name)
    for file in course.files:
        print(file.URL)
