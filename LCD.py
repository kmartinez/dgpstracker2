import pyb
from lcd160cr import *
from Formats import *

lcd = None


def rgb(r, g, b):
    return LCD160CR.rgb(r, g, b)

def resetPen():
    lcd.set_pos(0, 0)
    lcd.set_font(1, 0)
    lcd.set_scroll(False)
    lcd.set_text_color(lcd.rgb(255, 255, 255), lcd.rgb(0, 0, 0))
    lcd.set_pen(rgb(255, 255, 255), rgb(0, 0, 0))


def initLCD():
    global lcd
    lcd = LCD160CR('X')
    lcd.set_orient(LANDSCAPE_UPSIDEDOWN)
    lcd.set_pen(lcd.rgb(255, 255, 255), lcd.rgb(0, 0, 0))
    lcd.erase()
    resetPen()
    # lcd.save_to_flash()
    # lcd.write("LCD initiated")
    # for i in range(0, 20):
    #     lcd.write(str(i) + "\n")
    return lcd


def writeToScreen(text):
    lcd.write(text)


def writeLine(text):
    lcd.write(text + "\n\r")


def clearScreen():
    lcd.erase()


def changeTextColour(fg, bg=rgb(0, 0, 0)):
    lcd.set_text_color(fg, bg)
    return fg, bg


def changeTextColourRGBNoBG(r, g, b):
    return changeTextColour(rgb(r, g, b), rgb(0, 0, 0))


def changePenColour(line, fill=rgb(0, 0, 0)):
    lcd.set_pen(line, fill)
    return line, fill


def resetPenPos():
    lcd.set_pos(0, 0)


def initLCDAPI(log_freq=0, log_start=0, keep_raw=False, keep_med=False, keep_best=False, baseStation=True, svin_dur=0,
               svin_acc=0, svintoggle=lambda: print(), readCallback=lambda: print()):
    global pages, powered, lcd, svinpage, locpage, forceRead
    forceRead = readCallback
    initLCD()
    # lcd.save_to_flash()
    setupPowerButton()
    pages.append(getSettingsScreen(log_freq, log_start, keep_raw, keep_med, keep_best))
    if baseStation:
        print(baseStation, "==> added")
        pages.append(getSVINSettingsScreen(svin_dur, svin_acc, svintoggle))
        svinpage = len(pages)
        pages.append(getSVINMonitorScreen())

    locpage = len(pages)
    pages.append(getLocMonitorScreen(forceRead))
    checkPower()


pages = []
page = 0
powered = 0
UPDATE_TIME = 1000  # minimum ms before LCD updates on-screen info - is affected by gps timeout
updateIn = 0  # force update on startup


def updateLCD(delay):
    global pages, page, updateIn, UPDATE_TIME, reading
    page_ = pages[page]
    checkPower()
    print("checking lcd update:", page, powered, reading, updateIn)
    if powered == 0 or reading:
        return
    elif updateIn <= 0:
        updateIn = UPDATE_TIME
        resetPen()
        page_.eraseScreen()
        page_.drawWidgets()
    else:
        updateIn -= delay

    touches = page_.getTouches()
    if len(touches) > 0:
        touches[0].callback()


def forceUpdateLCD():
    global updateIn, pages, page
    updateIn = 0 # force update immediately after draw
    page_ = pages[page]
    checkPower()
    if powered == 0 or reading:
        return
    resetPen()
    page_.eraseScreen()
    page_.drawWidgets()


def setupPowerButton():
    b = pyb.Switch()
    b.callback(togglePower)


powerchange = True
def togglePower():
    global powered, powerchange
    print("--------")
    print("POWER UPDATE")
    print(powered, powerchange)
    powered = 1 - powered
    lcd.set_power(powered)
    powerchange = True
    print(powered, powerchange)
    print("--------")

def powerOn():
    global powered, powerchange
    powered = 1
    lcd.set_power(powered)
    powerchange = True

def powerOff():
    global powered, powerchange
    powered = 0
    lcd.set_power(powered)
    powerchange = True

def checkPower():
    global powered, powerchange
    if not powerchange:
        return

    # lcd.set_power(powered)
    if powered == 1:
        lcd.set_orient(LANDSCAPE_UPSIDEDOWN)
        # draw busy page if started during busy period
        if reading:
            makeLCDBusy("getReadings")
        Log.LCDEvent(b'\x20').writeLog()
    else:
        Log.LCDEvent(b'\x21').writeLog()
        # pyb.stop()
    powerchange = False


def drawPage():
    global powered, pages, page
    if powered == 1:
        resetPen()
        pages[page].drawWidgets()


def forceDrawPage(page):
    if powered == 1:
        resetPen()
        clearScreen()
        page.drawWidgets()


def leftPage():
    global pages, page, powered
    print("Changing page - L")
    if len(pages) == 0 or powered == 0:
        print("No pages or unpowered:", len(pages), powered)
        return
    page -= 1
    if page < 0:
        page = len(pages) - 1
    forceUpdateLCD()


def rightPage():
    global pages, page, powered
    print("Changing page - R")
    if len(pages) == 0 or powered == 0:
        print("No pages or unpowered:", len(pages), powered)
        return
    page += 1
    if page >= len(pages):
        page = 0
    forceUpdateLCD()


lbutton, rbutton = (None, None)


def getLRButtons():
    global lbutton, rbutton
    if lbutton is not None and rbutton is not None:
        return lbutton, rbutton

    ltriangle, rtriangle = getLRTriangles()
    rbutton = RectButton(llims=(135, 5), ulims=(155, 25), outlineColour=rgb(48, 48, 48),
                         fillColour=rgb(199, 199, 199),
                         filled=True, detail=[rtriangle], callback=rightPage)
    lbutton = RectButton(llims=(135, 103), ulims=(155, 123), outlineColour=rgb(48, 48, 48),
                         fillColour=rgb(199, 199, 199),
                         filled=True, detail=[ltriangle], callback=leftPage)
    return lbutton, rbutton


def getBusyScreen(operation):
    global lcd
    title = TextLine("WARNING", 19, 10, size=0, font=3)
    line1 = TextLine("Operation", 19, 30, size=0, font=3)
    line2 = TextLine("in", 19, 50, size=0, font=3)
    line3 = TextLine("progress", 19, 70, size=0, font=3)
    operation = TextLine("("+operation+")", 19, 90, size=0, font=3)
    busyscreen = Screen(lcd, widgets=[title, line1, line2, line3, operation])
    return busyscreen


reading = False


def makeLCDBusy(operation="unknown"):
    global reading
    operation = "unknown" if operation is None else operation
    Log.LCDEvent(b'\x22').writeLog()
    reading = True
    forceDrawPage(getBusyScreen(operation))


def makeLCDFree():
    global reading
    Log.LCDEvent(b'\x23').writeLog()
    reading = False
    forceUpdateLCD()


def getLRTriangles():
    rtriangle = bytearray()
    rtriangle.extend(bytes([141, 19]))
    rtriangle.extend(bytes([145, 11]))
    rtriangle.extend(bytes([149, 19]))
    rtriangle.extend(bytes([141, 19]))

    ltriangle = bytearray()
    ltriangle.extend(bytes([141, 109]))
    ltriangle.extend(bytes([145, 117]))
    ltriangle.extend(bytes([149, 109]))
    ltriangle.extend(bytes([141, 109]))
    return ltriangle, rtriangle


def checkTouches():
    global pages, page
    if powered == 1:
        touches = pages[page].getTouches()
        if len(touches) > 0:
            touch = touches[0]
            touch.callback()


def getPrintableDate():
    year, month, day, weekday, hours, minutes, seconds, subseconds = pyb.RTC().datetime()
    return str(day) + "/" + str(month) + "/" + str(year)


def getPrintableTime():
    year, month, day, weekday, hours, minutes, seconds, subseconds = pyb.RTC().datetime()
    return "{0:02d}:{1:02d}:{2:02d}.{3}".format(hours, minutes, seconds, subseconds)


def getSettingsScreen(log_freq, log_start, keep_raw, keep_med, keep_best):
    global lcd
    title = TextLine("SETTINGS", 10, 10, size=0, font=3)
    date_line = TextLine(getPrintableDate(), 10, 25, size=0, font=2, fg=rgb(140,200,255), update=getPrintableDate)
    time_line = TextLine(getPrintableTime(), 10, 33, size=0, font=2, fg=rgb(140,200,255), update=getPrintableTime)
    log_freq_line = TextLine("Log every: " + "{0:.2f}h".format(log_freq / 3600), 10, 46, size=0, font=3)
    log_start_line = TextLine("Log start: " + str(log_start), 10, 58, size=0, font=3)
    keep_raw_line = TextLine("Keep Raw", 10, 70, size=0, font=3,
                             fg=rgb(0 if keep_raw else 255, 255 if keep_raw else 0, 0))
    keep_med_line = TextLine("Keep Median", 10, 82, size=0, font=3,
                             fg=rgb(0 if keep_med else 255, 255 if keep_med else 0, 0))
    keep_best_line = TextLine("Keep Best", 10, 94, size=0, font=3,
                              fg=rgb(0 if keep_best else 255, 255 if keep_best else 0, 0))
    lbutton, rbutton = getLRButtons()
    widgets = [lbutton, rbutton, title, log_freq_line, log_start_line, keep_raw_line, keep_med_line, keep_best_line,
               date_line, time_line]

    if not keep_raw:
        strike2 = Line((8, 75), (112, 75), col=rgb(255, 0, 0))
        widgets.append(strike2)
    if not keep_med:
        strike3 = Line((8, 87), (112, 87), col=rgb(255, 0, 0))
        widgets.append(strike3)
    if not keep_best:
        strike1 = Line((8, 99), (112, 99), col=rgb(255, 0, 0))
        widgets.append(strike1)
    screen = Screen(lcd, widgets=widgets)
    return screen


def getSVINSettingsScreen(svin_dur, svin_acc, svintoggle):
    global lcd
    title = TextLine("SVIN SETTINGS", 10, 10, size=0, font=3)
    duration_line = TextLine("Min. dur.: " + str(svin_dur), 10, 32, size=0, font=3)
    acc_line = TextLine("Min. acc.: " + str(svin_acc), 10, 44, size=0, font=3)
    triggerLine = TextLine("START", 15, 75, size=0, font=3,
                           update=lambda: "START SURVEY" if not surveying else "STOP & SAVE")
    triggerBox = RectButton(llims=(10, 64), ulims=(128, 96), filled=False, outlineColour=rgb(255, 279, 102),
                            callback=svintoggle, detail=[triggerLine])
    lbutton, rbutton = getLRButtons()
    screen = Screen(lcd, widgets=[lbutton, rbutton, title, duration_line, acc_line, triggerBox])
    return screen


monitoring = True


def startMonitoring():
    global monitoring, powered
    monitoring = True and powered == 1  # don't monitor when LCD unpowered


def stopMonitoring():
    global monitoring
    monitoring = False


svindata = None
surveying = False
svinpage = -1
forceRead=lambda :print("No callback to force reading")

def getSVINMonitorScreen():
    global lcd, svindata, surveying
    title = TextLine("SVIN MONITOR", 10, 10, size=0, font=3)
    lbutton, rbutton = getLRButtons()
    if svindata is not None:
        nosvin = False
        x_line = TextLine("", 10, 32, size=0, font=2,
                          update=lambda: "X: {0:.2f}".format(svindata.getXPos()))
        y_line = TextLine("", 10, 44, size=0, font=2,
                          update=lambda: "Y: {0:.2f}".format(svindata.getYPos()))
        z_line = TextLine("", 10, 56, size=0, font=2,
                          update=lambda: "Z: {0:.2f}".format(svindata.getZPos()))
        acc_line = TextLine("", 10, 68, size=0, font=2,
                            update=lambda: "Accuracy: {0:.2f}m".format(svindata.getPAcc()))
        duration_line = TextLine("", 10, 80, size=0, font=2,
                                 update=lambda: "Duration: {0:.0f}s".format(svindata.getDuration()))
        # obs_line = TextLine("Observations: " + str(svindata.getObs()), 10, 95, size=0, font=2,
        #                     update=lambda: "Observations: " + str(svindata.getObs()))
        active_line = TextLine("", 25, 100, size=0, font=3,
                               update=lambda: "Active" if svindata.getActive()!=0 or surveying else "Inactive", fg=rgb(10,255,85) if svindata.getActive()!=0 or surveying else rgb(255,85,10))
        screen = Screen(lcd, widgets=[lbutton, rbutton, title, x_line, y_line, z_line, acc_line, duration_line, active_line])
    else:
        nosvin = True
        warning_line = TextLine("NO DATA", 35, 50, size=0, font=3, fg=rgb(255, 50, 0))
        warning_line2 = TextLine("Go to SVIN", 20, 80, size=0, font=3, fg=rgb(255, 85, 0))
        warning_line3 = TextLine("SETTINGS", 25, 100, size=0, font=3, fg=rgb(255, 85, 0))
        screen = Screen(lcd, widgets=[lbutton, rbutton, title, warning_line, warning_line2, warning_line3])

    return screen

nosvin=True
def updateSVINMonitorData(svinmsg, issurveying):
    global svindata, svinpage, surveying, nosvin
    noPreviousData = svindata is None or nosvin
    surveying = issurveying
    svindata = svinmsg
    svindata = svinmsg
    if noPreviousData:
        remakeScreen(svinpage,
                     getSVINMonitorScreen())  # remakes Screen obj with new data - changes "NO DATA" to monitor


locdata = None
statusdata = None
satellites = 0
locpage = -1


def parseLogs():
    makeLCDBusy("parsing logs")
    Log.unparseLogs()
    makeLCDFree()

noloc=True
def getLocMonitorScreen(readCallback):
    global lcd, locdata, satellites, noloc
    title = TextLine("LOC MONITOR", 10, 10, size=0, font=3)
    lbutton, rbutton = getLRButtons()
    parse_line = TextLine("Parse", 13, 106, size=0, font=2)
    parse_button = RectButton(llims=(10, 98), ulims=(55, 118), filled=False, outlineColour=rgb(255, 279, 102),
                              callback=parseLogs, detail=[parse_line])
    trigger_line = TextLine("Read now", 60, 106, size=0, font=2)
    trigger_button = RectButton(llims=(58, 98), ulims=(128, 118), filled=False, outlineColour=rgb(255, 279, 102),
                                callback=readCallback, detail=[trigger_line])
    if locdata is not None:
        noloc=False
        col = rgb(255, 85, 0) if locdata.invalidFix else rgb(255, 255, 255)
        x_line = TextLine("", 10, 32, size=0, font=2, fg=col,
                          update=lambda: "X: {0:.2f}".format(locdata.getXPos()))
        y_line = TextLine("", 10, 44, size=0, font=2, fg=col,
                          update=lambda: "Y: {0:.2f}".format(locdata.getYPos()))
        z_line = TextLine("", 10, 56, size=0, font=2, fg=col,
                          update=lambda: "Z: {0:.2f}".format(locdata.getZPos()))
        acc_line = TextLine("", 10, 68, size=0, font=2, fg=col,
                            update=lambda: "Acc.: {0:.2f}cm".format(locdata.getPAcc()))
        satellites_line = TextLine("", 10, 80, size=0, font=2, fg=col,
                                   update=lambda: "Satellites: {0:.0f}".format(satellites))
        screen = Screen(lcd,
                        widgets=[lbutton, rbutton, title, x_line, y_line, z_line, acc_line, satellites_line,
                                 parse_button, trigger_button])
    else:
        noloc=True
        warning_line = TextLine("NO DATA", 20, 60, size=0, font=3, fg=rgb(255, 85, 0))
        screen = Screen(lcd, widgets=[lbutton, rbutton, title, warning_line, parse_button])
    return screen


def updateLocMonitorData(locmsg, svs):
    global locdata, locpage, satellites, forceRead, noloc
    noPreviousData = locdata is None or noloc
    satellites = svs
    locdata = locmsg
    if noPreviousData:
        remakeScreen(locpage, getLocMonitorScreen(forceRead))  # remakes Screen obj with new data - changes "NO DATA" to monitor

def updateStatData(statmsg):
    global statusdata
    statusdata = statmsg

def remakeScreen(pageno, newscreen):
    global pages
    pages[pageno] = newscreen


pers_touch = False


class Screen:
    widgets = None
    penFg = None
    penBg = None
    screen = None

    def __init__(self, screen, penFg=rgb(255, 255, 255), penBg=rgb(0, 0, 0), widgets=None):
        if widgets is None:
            widgets = []
        self.screen = screen
        self.penFg = penFg
        self.penBg = penBg
        self.widgets = widgets

    # I'm assuming here that it could be multitouch, although the LCD160CR isn't
    # single on-press response, no persistent touch
    def getTouches(self):
        global pers_touch
        # means if you hold down on the screen it registers as one touch
        touches = []
        for w in self.widgets:
            if w.is_touched():
                touches.append(w)

        # if touched last update and still touched then cancel touch registration
        if pers_touch and len(touches) > 0:
            return []
        else:
            pers_touch = len(touches) > 0
            return touches

        # if touched, return

    def drawWidgets(self):
        lcd.set_pen(self.penFg, self.penBg)
        for w in self.widgets:
            w.draw()

    def eraseScreen(self):
        lcd.set_pen(self.penFg, self.penBg)
        self.screen.erase()


class Widget:
    name = "default widget"
    x_u_lim, y_u_lim, x_l_lim, y_l_lim = 0, 0, 0, 0
    lcd = None

    callback = None

    def __init__(self, llims=(0, 0), ulims=(0, 0), callback=None):
        self.callback = callback
        self.x_l_lim, self.y_l_lim = llims
        self.x_u_lim, self.y_u_lim = ulims

    def draw(self):
        pass

    def is_touched(self):
        return False

    def is_touched_action(self):
        return self.callback

    def toString(self):
        return self.name


class RectButton(Widget):
    filled = False
    outlineCol = None
    fillCol = None

    detail = []

    def __init__(self, llims=(0, 0), ulims=(0, 0), fillColour=rgb(0, 0, 0),
                 outlineColour=rgb(255, 255, 255),
                 filled=False,
                 detail=None, callback=(lambda: print("RectButton pressed"))):

        if detail is None:
            detail = [bytearray()]
        self.detail = detail

        self.fillCol = fillColour
        self.outlineCol = outlineColour
        self.filled = filled
        super(RectButton, self).__init__(llims=llims, ulims=ulims, callback=callback)

        self.name = "RectButton at [" + str((self.x_l_lim, self.y_l_lim)) + ", " + str(
            (self.x_u_lim, self.y_u_lim)) + "]"

    def draw(self):
        lcd.set_pen(self.outlineCol, self.fillCol)
        if self.filled:
            lcd.rect_interior(self.x_l_lim, self.y_l_lim, abs(self.x_u_lim - self.x_l_lim),
                              abs(self.y_u_lim - self.y_l_lim))
        else:
            lcd.rect_outline(self.x_l_lim, self.y_l_lim, abs(self.x_u_lim - self.x_l_lim),
                             abs(self.y_u_lim - self.y_l_lim))

        if self.detail is not None:
            # print(self.detail)
            for shape in self.detail:
                if issubclass(type(shape), Widget):
                    shape.draw()
                else:
                    lcd.poly_line(shape)

    def is_touched(self):
        active, touchx, touchy = lcd.get_touch()
        if active == 1 \
                and self.x_l_lim < touchx < self.x_u_lim \
                and self.y_l_lim < touchy < self.y_u_lim:
            print(self.name, "is touched")
            return True

    def addDetailPoint(self, pointX, pointY):
        self.detail.extend(bytes([pointX, pointY]))


# AAAH lost in hard reset, need to reimplement
class TextLine(Widget):
    fgcol = None
    bgcol = None
    text = None
    xpos = 0
    ypos = 0
    size = 0
    font = 0
    update = None

    def __init__(self, text, xpos, ypos, fg=rgb(255, 255, 255), bg=rgb(0, 0, 0), size=1, font=1, update=None):
        self.xpos = xpos
        self.ypos = ypos
        self.text = text
        self.fgcol = fg
        self.bgcol = bg
        self.font = font
        self.size = size
        self.update = update

    def draw(self):
        if self.update is not None:
            self.updateText(self.update())
        lcd.set_pos(self.xpos, self.ypos)
        lcd.set_font(self.font, self.size)
        lcd.set_text_color(self.fgcol, self.bgcol)
        lcd.write(self.text)

    def updateText(self, updated):
        print("Updating display text to", updated)
        self.text = str(updated)

    def appendText(self, append):
        self.text += str(append)

    def prependText(self, prepend):
        self.text = str(prepend) + self.text


class Line(Widget):
    xStart = 0
    xEnd = 0
    yStart = 0
    yEnd = 0
    col = rgb(0, 0, 0)

    def __init__(self, start, end, col=rgb(255, 255, 255)):
        self.x_l_lim, self.y_l_lim = start
        self.x_u_lim, self.y_u_lim = end
        self.col = col

    def draw(self):
        lcd.set_pen(self.col, rgb(0, 0, 0))
        lcd.line(self.x_u_lim, self.y_u_lim, self.x_l_lim, self.y_l_lim)
