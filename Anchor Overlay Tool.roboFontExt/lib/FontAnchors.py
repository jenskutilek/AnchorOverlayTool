from mojo.extensions import getExtensionDefault
from extensionID import extensionID


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
