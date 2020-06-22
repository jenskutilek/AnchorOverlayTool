from __future__ import division, print_function

# Anchor Overlay
# An extension for the RoboFont editor
# Requires RoboFont 3
# Version 0.1 by Jens Kutilek 2013-01-04
# Version 0.2 by Jens Kutilek 2013-12-05
# Version 0.4 by Jens Kutilek 2014-02-13
# Version 0.4 by Jens Kutilek 2014-02-13
# Version 0.5.2: Jens Kutilek 2016-01-17
# Version 0.6.0: Jens Kutilek 2018-01-10
# Version 0.7.0: Jens Kutilek 2020-06-22

import vanilla

# from time import time

from AppKit import NSBezierPath

from defconAppKit.windows.baseWindow import BaseWindowController

from mojo.events import addObserver, removeObserver
from mojo.drawingTools import (
    drawGlyph,
    fill,
    restore,
    save,
    strokeWidth,
    translate,
)
from lib.tools import bezierTools  # for single point click selection
from lib.tools.defaults import (
    getDefaultColor,
)  # for using user-defined colours
from mojo.UI import UpdateCurrentGlyphView, CurrentGlyphWindow
from mojo.extensions import getExtensionDefault, setExtensionDefault

from extensionID import extensionID


def roundCoordinates(coordinatesTuple):
    return (int(round(coordinatesTuple[0])), int(round(coordinatesTuple[1])))


class FontAnchors(object):

    anchorNames = []
    anchorGlyphs = {}
    anchorPositions = {}
    invisibleAnchors = []
    invisibleGlyphs = []
    invisibleMarks = []

    hideLists = {
        "anchor": invisibleAnchors,
        "glyph": invisibleGlyphs,
        "mark": invisibleMarks,
    }

    def __init__(self, font):
        self.font = font
        self._readFromFont(self.font)
        self.hideLists = getExtensionDefault(
            "%s.%s" % (extensionID, "hide"), self.hideLists
        )

    def _readFromFont(self, font):
        self.anchorNames = []
        self.anchorGlyphs = {}
        self.anchorPositions = {}

        if font is not None:
            for g in font:
                if len(g.anchors) > 0:
                    for a in g.anchors:
                        self.addAnchor(g, a.name, (a.x, a.y))
            # for a in sorted(self.anchorBaseMap.keys()):
            #    self.anchorNames.append({"Show": True, "Name": a})
            # print("\nanchorGlyphs:", self.anchorGlyphs)
            # print("\nanchorPositions:", self.anchorPositions)
            # print()

    def getVisibility(self, kind, name, includeMatching=True):
        hideList = self.hideLists[kind]
        if not (
            name in hideList
            or (
                includeMatching
                and self.getMatchingAnchorName(name) in hideList
            )
        ):
            return True
        return False

    def setVisibility(self, kind, name, isVisible=True, includeMatching=True):
        hideList = self.hideLists[kind]
        if isVisible:
            if name in hideList:
                hideList.remove(name)
                if includeMatching:
                    hideList.remove(self.getMatchingAnchorName(name))
        else:
            if not (name in hideList):
                hideList.append(name)
                if includeMatching:
                    hideList.append(self.getMatchingAnchorName(name))

    def addAnchor(self, glyph, name, position, addToGlyph=False):
        if len(name) == 0:
            print(
                "WARNING: anchor with empty name at (%i, %i) in glyph '%s', ignored."
                % (position[0], position[1], glyph.name)
            )
        else:
            if (glyph.name, name) in self.anchorPositions.keys():
                print(
                    "WARNING: Duplicate anchor name '%s' requested in glyph '%s' when trying to add anchor. Ignored."
                    % (name, glyph.name)
                )
            else:
                self.anchorPositions[(glyph.name, name)] = position
                if name in self.anchorGlyphs.keys():
                    self.anchorGlyphs[name] += [glyph.name]
                else:
                    self.anchorGlyphs[name] = [glyph.name]
                if addToGlyph:
                    glyph.appendAnchor(name, position)

    def moveAnchor(self, name, newPosition):
        # happens automatically - why?
        # probably only for current glyph, not "inverted" view
        pass

    def renameAnchor(self, name):
        pass

    def deleteAnchor(self, name):
        pass

    def getMatchingAnchorName(self, name):
        # returns "inverted" anchor name, i.e. with leading underscore added or
        # removed
        if name[0] == "_":
            return name[1:]
        else:
            return "_" + name

    def getAnchorNames(self):
        # TODO: anchorNames should not be constructed each time this method is
        # called.
        # Better to build it once and modify it together with other anchor
        # modifications
        anchorNames = []
        for a in sorted(self.anchorGlyphs.keys()):
            if len(a) > 0:
                if a[0] != "_":
                    anchorNames.append(
                        {
                            "Show": self.getVisibility("anchor", a, False),
                            "Name": a,
                        }
                    )
        return anchorNames

    def getAnchoredGlyphNames(self, anchorName):
        # print("Looking up anchored glyphs for", anchorName)
        targetAnchorName = self.getMatchingAnchorName(anchorName)
        if targetAnchorName in self.anchorGlyphs.keys():
            return self.anchorGlyphs[targetAnchorName]
        return []

    def getAnchoredGlyphNamesForList(self, anchorNames, marks=False):
        anchoredGlyphs = []
        for an in anchorNames:
            if marks:
                an = self.getMatchingAnchorName(an)
            if an in self.anchorGlyphs.keys():
                anchoredGlyphs += self.anchorGlyphs[an]
        result = []
        # print("anchoredGlyphs:", anchoredGlyphs)
        for g in sorted(set(anchoredGlyphs)):
            if marks:
                result.append(
                    {"Show": self.getVisibility("mark", g, False), "Name": g}
                )
            else:
                result.append(
                    {"Show": self.getVisibility("glyph", g, False), "Name": g}
                )
        return result

    def selectGlyphsWithAnchorName(self, anchorName):
        self.font.selection = self.getAnchoredGlyphNames(
            self.getMatchingAnchorName(anchorName)
        )
        # self.font.update()


class AnchorOverlay(BaseWindowController):
    def __init__(self):
        self.fontAnchors = FontAnchors(CurrentFont())
        self.showPreview = getExtensionDefault(
            "%s.%s" % (extensionID, "preview"), True
        )
        nscolor = getDefaultColor("glyphViewPreviewFillColor")
        self.preview_color = (
            nscolor.redComponent(),
            nscolor.greenComponent(),
            nscolor.blueComponent(),
            nscolor.alphaComponent(),
        )

        columnDescriptions = [
            {"title": "Show", "cell": vanilla.CheckBoxListCell(), "width": 35},
            {"title": "Name", "typingSensitive": True, "editable": False},
        ]

        self.w = vanilla.FloatingWindow(
            (170, 490), "Anchor Overlay", closable=False
        )

        y = 10
        self.w.showAnchors_label = vanilla.TextBox(
            (10, y, -10, 20), "Show anchors:", sizeStyle="small"
        )
        y += 25
        self.w.showAnchors = vanilla.List(
            (10, y, -10, 150),
            self.fontAnchors.getAnchorNames(),
            columnDescriptions=columnDescriptions,
            drawFocusRing=True,
            editCallback=self.updateAnchorVisibility,
            doubleClickCallback=self.selectGlyphsWithAnchorName,
            selectionCallback=self.updateAnchoredGlyphsList,
        )
        y += 160
        self.w.markAnchors_label = vanilla.TextBox(
            (10, y, 150, 20), "Show mark glyphs:", sizeStyle="small"
        )
        y += 25
        self.w.markAnchors = vanilla.List(
            (10, y, 150, 180),
            [],  # self.fontAnchors.anchorGlyphs.keys(),
            columnDescriptions=columnDescriptions,
            editCallback=self.updateMarkVisibility,
            doubleClickCallback=self.gotoGlyph,
            allowsMultipleSelection=False,
            allowsEmptySelection=False,
        )
        y += 188
        # self.w.drawPreview = vanilla.CheckBox((10, y, -10, -10), "Show in preview mode",
        #    callback=self.setShowPreview,
        #    value=self.showPreview,
        #    sizeStyle="small"
        # )

        # self.w.displayAnchors = vanilla.CheckBox((10, y+25, -10, -10), "Show anchors",
        #    callback=self.setShowAnchors,
        #    value=getGlyphViewDisplaySettings()["Anchors"],
        #    sizeStyle="small"
        # )

        y += 2
        self.w.alignAnchors_label = vanilla.TextBox(
            (10, y, -10, -10), "Align selected anchors:", sizeStyle="small"
        )

        y += 21
        self.w.centerXButton = vanilla.Button(
            (10, y, 72, 25),
            "Points X",
            callback=self.centerAnchorX,
            sizeStyle="small",
        )
        self.w.centerYButton = vanilla.Button(
            (88, y, 72, 25),
            "Points Y",
            callback=self.centerAnchorY,
            sizeStyle="small",
        )

        y += 26
        self.w.baselineButton = vanilla.Button(
            (10, y, 46, 25),
            "base",
            callback=self.moveAnchorBaseline,
            sizeStyle="small",
        )
        self.w.xheightButton = vanilla.Button(
            (62, y, 46, 25),
            "x",
            callback=self.moveAnchorXheight,
            sizeStyle="small",
        )
        self.w.capheightButton = vanilla.Button(
            (114, y, 46, 25),
            "cap",
            callback=self.moveAnchorCapheight,
            sizeStyle="small",
        )

        self.setUpBaseWindowBehavior()
        self.addObservers()

        self.w.showAnchors.setSelection([])
        self.w.open()

    # Observers

    def addObservers(self):
        addObserver(self, "glyphChanged", "draw")
        addObserver(self, "glyphChangedPreview", "drawPreview")
        addObserver(self, "glyphChanged", "drawInactive")

    def removeObservers(self):
        removeObserver(self, "draw")
        removeObserver(self, "drawPreview")
        removeObserver(self, "drawInactive")

    # Callbacks

    def updateAnchorVisibility(self, sender=None, glyph=None):
        for anchor in sender.get():
            # self.fontAnchors.setAnchorVisibility(anchor["Name"], anchor["Show"])
            self.fontAnchors.setVisibility(
                "anchor", anchor["Name"], anchor["Show"]
            )
        UpdateCurrentGlyphView()

    def updateGlyphVisibility(self, sender=None, glyph=None):
        for g in sender.get():
            self.fontAnchors.setVisibility(
                "glyph", g["Name"], g["Show"], False
            )
        UpdateCurrentGlyphView()

    def updateMarkVisibility(self, sender=None, glyph=None):
        for g in sender.get():
            self.fontAnchors.setVisibility("mark", g["Name"], g["Show"], False)
        UpdateCurrentGlyphView()

    def updateAnchoredGlyphsList(self, sender=None, glyph=None):
        selectedAnchorNames = []
        for i in sender.getSelection():
            selectedAnchorNames.append(
                self.fontAnchors.getAnchorNames()[i]["Name"]
            )
        self.w.markAnchors.set(
            self.fontAnchors.getAnchoredGlyphNamesForList(
                selectedAnchorNames, marks=True
            )
        )

    def gotoGlyph(self, sender=None, glyph=None):
        newGlyphName = sender.get()[sender.getSelection()[0]]["Name"]
        # print("Goto Glyph:", newGlyphName)
        CurrentGlyphWindow().setGlyphByName(newGlyphName)

    def selectGlyphsWithAnchorName(self, sender=None):
        anchorName = sender.get()[sender.getSelection()[0]]["Name"]
        self.fontAnchors.selectGlyphsWithAnchorName(anchorName)

    # def setShowPreview(self, sender=None, glyph=None):
    #    self.showPreview = sender.get()

    # def setShowAnchors(self, sender=None, glyph=None):
    #    showAnchors = sender.get()
    #    setGlyphViewDisplaySettings({"Anchors": showAnchors})

    # Drawing helpers

    def setStroke(self, value=0.5):
        strokeWidth(value)

    def setFill(self, rgba=(0.2, 0, 0.2, 0.2)):
        r, g, b, a = rgba
        fill(r, g, b, a)

    # Stuff for anchor alignment buttons

    def _getBBox(self, pointList):
        minX = None
        maxX = None
        minY = None
        maxY = None
        for p in pointList:
            if p.x < minX or minX is None:
                minX = p.x
            if p.x > maxX or maxX is None:
                maxX = p.x
            if p.y < minY or minY is None:
                minY = p.y
            if p.y > maxY or maxY is None:
                maxY = p.y
        return ((minX, minY), (maxX, maxY))

    def _getReferencePoint(self, glyph):
        # calculate a reference point for anchor adjustments
        if len(glyph.selection) == 0:
            # no points selected, place anchor at glyph width or cap height
            # center
            # TODO: x-height for lowercase?
            # print("Ref: metrics")
            return roundCoordinates(
                (glyph.width / 2, self.fontAnchors.font.info.capHeight / 2)
            )
        elif len(glyph.selection) == 1:
            # one point is selected, return same
            # print("Ref: point")
            return roundCoordinates(
                (glyph.selection[0].x, glyph.selection[0].y)
            )
        else:
            # more points are selected, find min/max and return center.
            # print("Ref: bbox")
            ((minX, minY), (maxX, maxY)) = self._getBBox(glyph.selection)
            return roundCoordinates(((minX + maxX) / 2, (minY + maxY) / 2))

    # Align anchors based on selection

    def centerAnchorX(self, sender=None, glyph=None):
        g = CurrentGlyph()
        g.prepareUndo(undoTitle="h-align anchors in /%s" % g.name)
        p = self._getReferencePoint(g)
        for a in g.anchors:
            if a.selected:
                a.x = p[0]
        g.performUndo()

    def centerAnchorY(self, sender=None, glyph=None):
        g = CurrentGlyph()
        g.prepareUndo(undoTitle="v-align anchors in /%s" % g.name)
        p = self._getReferencePoint(g)
        for a in g.anchors:
            if a.selected:
                a.y = p[1]
        g.performUndo()

    def addAnchorAndUpdateList(self, glyph, name, position):
        self.fontAnchors.addAnchor(glyph, name, position, addToGlyph=True)
        self.w.showAnchors.set(self.fontAnchors.getAnchorNames())

    # Align anchors based on metrics

    def moveAnchorBaseline(self, sender=None, glyph=None):
        g = CurrentGlyph()
        g.prepareUndo(undoTitle="align anchors to baseline in /%s" % g.name)
        for a in g.anchors:
            if a.selected:
                a.y = 0
        g.performUndo()

    def moveAnchorXheight(self, sender=None, glyph=None):
        g = CurrentGlyph()
        g.prepareUndo(undoTitle="align anchors to x-height in /%s" % g.name)
        y = self.fontAnchors.font.info.xHeight
        for a in g.anchors:
            if a.selected:
                a.y = y
        g.performUndo()

    def moveAnchorCapheight(self, sender=None, glyph=None):
        g = CurrentGlyph()
        g.prepareUndo(undoTitle="align anchors to cap height in /%s" % g.name)
        y = self.fontAnchors.font.info.capHeight
        for a in g.anchors:
            if a.selected:
                a.y = y
        g.performUndo()

    def glyphChanged(self, info):
        # print("  * glyphChanged")
        g = info["glyph"]
        if g is not None:
            if len(g.anchors) > 0:
                self.drawAnchoredGlyphs(g)

    def glyphChangedPreview(self, info):
        # print("  * glyphChangedPreview")
        g = info["glyph"]
        if (g is not None) and self.showPreview:
            if len(g.anchors) > 0:
                self.drawAnchoredGlyphs(g, preview=True)

    def drawAnchoredGlyphs(self, glyph, preview=False):
        self.setStroke(0)
        if preview:
            self.setFill(self.preview_color)
        else:
            self.setFill()

        # start = time()

        dbx = 0
        dby = 0

        for a in glyph.anchors:
            anchor_name = a.name
            # print("     %s" % anchor_name)
            if self.fontAnchors.getVisibility("anchor", anchor_name):
                glyphsToDraw = self.fontAnchors.getAnchoredGlyphNames(
                    anchor_name
                )
                # get translation for base anchor
                dbx = a.x
                dby = a.y
                save()
                for gn in glyphsToDraw:
                    if (
                        anchor_name[0] != "_"
                        and self.fontAnchors.getVisibility("mark", gn, False)
                    ) or (
                        anchor_name[0] == "_"
                        and self.fontAnchors.getVisibility("glyph", gn, False)
                    ):
                        # get translation for current mark anchor
                        dmx, dmy = self.fontAnchors.anchorPositions[
                            gn,
                            self.fontAnchors.getMatchingAnchorName(
                                anchor_name
                            ),
                        ]
                        x = dbx - dmx
                        y = dby - dmy
                        translate(x, y)
                        drawGlyph(self.fontAnchors.font[gn])
                        dbx = dmx
                        dby = dmy
                restore()

        # stop = time()
        # print("     Draw: %0.1f ms" % (1000 * (stop - start)))

    def windowCloseCallback(self, sender):
        self.removeObservers()
        setExtensionDefault(
            "%s.%s" % (extensionID, "hide"), self.fontAnchors.hideLists
        )
        setExtensionDefault(
            "%s.%s" % (extensionID, "preview"), self.showPreview
        )
        super(AnchorOverlay, self).windowCloseCallback(sender)
        UpdateCurrentGlyphView()


from AppKit import NSImage
from os.path import join, dirname, isfile
from fontTools.misc.arrayTools import pointInRect
from mojo.events import BaseEventTool, installTool


iconpath = join(dirname(__file__), "toolbarToolsAnchor.pdf")

if isfile(iconpath):
    toolbarIcon = NSImage.alloc().initByReferencingFile_(iconpath)
else:
    toolbarIcon = None
    print("Warning: Toolbar icon not found: <%s>" % iconpath)


class AnchorTool(BaseEventTool):
    def setup(self):
        self.pStart = None
        self.pEnd = None
        self._selectedMouseDownPoint = None

    def getToolbarIcon(self):
        return toolbarIcon

    def getToolbarTip(self):
        return "Anchor Tool"

    def becomeActive(self):
        # print("becomeActive")
        self.anchorOverlayUI = AnchorOverlay()

    def becomeInactive(self):
        # print("becomeInactive")
        self.anchorOverlayUI.windowCloseCallback(None)
        self.anchorOverlayUI.w.close()

    def keyDown(self, event):
        # align via key commands
        c = event.characters()
        if c == "X":
            self.anchorOverlayUI.centerAnchorX()
        elif c == "Y":
            self.anchorOverlayUI.centerAnchorY()
        # move anchors with arrow keys
        # default increment is 10 units, hold down shift for 5, option for 1
        # (like in Metrics Machine)
        if self.shiftDown:
            inc = 5
        elif self.optionDown:
            inc = 1
        else:
            inc = 10
        if self.arrowKeysDown["up"]:
            d = (0, inc)
        elif self.arrowKeysDown["down"]:
            d = (0, -inc)
        elif self.arrowKeysDown["left"]:
            d = (-inc, 0)
        elif self.arrowKeysDown["right"]:
            d = (inc, 0)
        else:
            d = (0, 0)
        if d != (0, 0):
            # d = roundCoordinates(d)
            g = CurrentGlyph()
            g.prepareUndo(undoTitle="Move anchors in /%s" % g.name)
            for a in g.anchors:
                if a.selected:
                    a.x = int(round(a.x)) + d[0]
                    a.y = int(round(a.y)) + d[1]
            g.performUndo()

    def _guessAnchorName(self, glyph, p):
        if p.x <= glyph.width // 3:
            horizontal = "Left"
        elif p.x >= glyph.width * 2 // 3:
            horizontal = "Right"
        else:
            horizontal = ""
        if p.y <= glyph.box[2] // 3:
            vertical = "bottom"
        elif p.y >= glyph.box[2] * 2 // 3:
            vertical = "top"
        else:
            vertical = "center"
        name = vertical + horizontal
        if (
            glyph.name,
            name,
        ) in self.anchorOverlayUI.fontAnchors.anchorPositions.keys():
            name += "Attach"
        return name

    def _newAnchor(self, p):
        # Add an anchor at position p
        g = CurrentGlyph()
        newAnchorName = self._guessAnchorName(g, p)
        g.prepareUndo(
            undoTitle="Add anchor %s to /%s" % (newAnchorName, g.name)
        )
        self.anchorOverlayUI.addAnchorAndUpdateList(
            g, newAnchorName, (p.x, p.y)
        )
        g.performUndo()

    def _normalizeBox(self, p0, p1):
        # normalize selection rectangle so it is always positive
        return (
            min(p0.x, p1.x),
            min(p0.y, p1.y),
            max(p0.x, p1.x),
            max(p0.y, p1.y),
        )

    def _getSelectedPoints(self):
        if self.pStart and self.pEnd:
            box = self._normalizeBox(self.pStart, self.pEnd)
            for contour in self._glyph:
                for p in contour.onCurvePoints:
                    if pointInRect((p.x, p.y), box):
                        self.selection.addPoint(
                            p, self.shiftDown, contour=contour
                        )
                        self._selectedMouseDownPoint = (p.x, p.y)
            for anchor in self._glyph.anchors:
                if pointInRect((anchor.x, anchor.y), box):
                    self.selection.addAnchor(anchor, self.shiftDown)
                    self._selectedMouseDownPoint = (anchor.x, anchor.y)

    def mouseDown(self, point, clickCount):
        if not (self.shiftDown):
            self.selection.resetSelection()
        if clickCount > 1:
            self._newAnchor(point)
        else:
            self.pStart = point
            self.pEnd = None
            s = self._view.getGlyphViewOnCurvePointsSize(minSize=7)
            for contour in self._glyph:
                for p in contour.onCurvePoints:
                    if bezierTools.distanceFromPointToPoint(p, point) < s:
                        self.selection.addPoint(
                            p, self.shiftDown, contour=contour
                        )
                        self._selectedMouseDownPoint = (p.x, p.y)
                        return
            for anchor in self._glyph.anchors:
                if bezierTools.distanceFromPointToPoint(anchor, point) < s:
                    self.selection.addAnchor(anchor, self.shiftDown)
                    self._selectedMouseDownPoint = (anchor.x, anchor.y)
                    return

    def mouseUp(self, point):
        self.pEnd = point
        self._getSelectedPoints()
        self.pStart = None
        self.pEnd = None
        self._selectedMouseDownPoint = None

    def mouseDragged(self, point, delta):
        self.pEnd = point
        # self._getSelectedPoints()

    def draw(self, scale):
        if self.isDragging() and self.pStart and self.pEnd:
            r = self.getMarqueRect()
            if r:
                color = getDefaultColor("glyphViewSelectionMarqueColor")
                color.set()
                path = NSBezierPath.bezierPathWithRect_(r)
                path.fill()
            return
        self.drawSelection(scale)


installTool(AnchorTool())
# print("Anchor Tool installed in tool bar.")
