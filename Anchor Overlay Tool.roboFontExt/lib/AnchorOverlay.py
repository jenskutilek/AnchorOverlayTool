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
# Version 0.8.0: Jens Kutilek 2021-02-03

import vanilla

# from time import time

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
from mojo.roboFont import CurrentFont, CurrentGlyph

from lib.tools.defaults import getDefaultColor
from mojo.UI import UpdateCurrentGlyphView, CurrentGlyphWindow
from mojo.extensions import getExtensionDefault, setExtensionDefault

from extensionID import extensionID
from FontAnchors import FontAnchors


def roundCoordinates(coordinatesTuple):
    return (int(round(coordinatesTuple[0])), int(round(coordinatesTuple[1])))


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
            if minX is None or p.x < minX:
                minX = p.x
            if maxX is None or p.x > maxX:
                maxX = p.x
            if minY is None or p.y < minY:
                minY = p.y
            if maxY is None or p.y > maxY:
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
        UpdateCurrentGlyphView()

    def centerAnchorY(self, sender=None, glyph=None):
        g = CurrentGlyph()
        g.prepareUndo(undoTitle="v-align anchors in /%s" % g.name)
        p = self._getReferencePoint(g)
        for a in g.anchors:
            if a.selected:
                a.y = p[1]
        g.performUndo()
        UpdateCurrentGlyphView()

    def addAnchorAndUpdateList(self, glyph, name, position):
        self.fontAnchors.addAnchor(glyph, name, position, addToGlyph=True)
        self.w.showAnchors.set(self.fontAnchors.getAnchorNames())
        UpdateCurrentGlyphView()

    # Align anchors based on metrics

    def moveAnchorBaseline(self, sender=None, glyph=None):
        g = CurrentGlyph()
        g.prepareUndo(undoTitle="align anchors to baseline in /%s" % g.name)
        for a in g.anchors:
            if a.selected:
                a.y = 0
        g.performUndo()
        UpdateCurrentGlyphView()

    def moveAnchorXheight(self, sender=None, glyph=None):
        g = CurrentGlyph()
        g.prepareUndo(undoTitle="align anchors to x-height in /%s" % g.name)
        y = self.fontAnchors.font.info.xHeight
        for a in g.anchors:
            if a.selected:
                a.y = y
        g.performUndo()
        UpdateCurrentGlyphView()

    def moveAnchorCapheight(self, sender=None, glyph=None):
        g = CurrentGlyph()
        g.prepareUndo(undoTitle="align anchors to cap height in /%s" % g.name)
        y = self.fontAnchors.font.info.capHeight
        for a in g.anchors:
            if a.selected:
                a.y = y
        g.performUndo()
        UpdateCurrentGlyphView()

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
