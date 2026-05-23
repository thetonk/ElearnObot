import math
import nextcord
import utils.loggingUtils as logutils
import utils.moodleUtils as mdlutils

def filesizeConversion(bytes):
    out = int(bytes)/1024.0
    if out > 1024:
        out = out/1024.0
        return "{}MiB".format(round(out, 2))
    return "{}kiB".format(round(out, 2))

async def messageSplitter(appLogger: logutils.ApplicationLogger, channel, message: str,
                          itemsCountPerMessage: int, itemType: str, course: mdlutils.Course, itemState: str, embedColor: int):
    items = message.split("\n")
    del items[len(items) - 1] #delete last empty item, since it's useless
    totalMessages = math.ceil(len(items) / float(itemsCountPerMessage))
    for m in range(totalMessages):
        messages = ""
        for message in items[:itemsCountPerMessage]:
            messages += message+"\n"
        embed = nextcord.Embed(title=f"{itemType} list: {m+1}/{totalMessages}", color=embedColor, description=messages)
        embed.set_author(name=f"{itemState} {itemType} in course: {course.name}", url=course.URL)
        appLogger.dc_print(f"Sending {itemState} {itemType} in course {course.name} by parts (too many characters for single message!). Progress: {m+1}/{totalMessages}")
        await channel.send(embed=embed)
        del items[:itemsCountPerMessage]

def textClipper(text: str, char_limit: int) -> str:
    if len(text) > char_limit:
        return text[:char_limit-3] + "..."
    elif len(text) == 0:
        return "Empty"
    else:
        return text
