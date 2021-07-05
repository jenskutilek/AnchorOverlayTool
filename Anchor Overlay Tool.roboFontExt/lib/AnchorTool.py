from os.path import join, dirname, isfile

from AppKit import NSBezierPath, NSImage

from fontTools.misc.arrayTools import pointInRect

from lib.tools import bezierTools  # for single point click selection
from lib.tools.defaults import getDefaultColor
from mojo.events import BaseEventTool
from mojo.roboFont import CurrentGlyph

from AnchorOverlay import AnchorOverlay


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

    def shouldShowMarqueRect(self):
        return True

    def shouldShowSelection(self):
        return True

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
        # self.drawBackgroundSelection(scale)
