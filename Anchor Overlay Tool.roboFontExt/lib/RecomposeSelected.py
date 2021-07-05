from __future__ import division, print_function

"""
Recompose selected glyphs, using anchor positions as reference for placement.
Also resets the metrics of the composite to those of the base glyph(s).

Jens Kutilek
Version 0.1: 2013-05-28
Version 0.2: 2014-08-05 - Implemented chained accents positioning
Version 0.3: 2014-11-22 - Bug fixes for ligatures
Version 0.4: 2016-02-03 - Support kerning when positioning ligature-style components
"""

from operator import attrgetter
from re import compile


class jkKernInfo(object):
    def __init__(self, font):
        self.font = font
        self.group_name_pattern = compile("^@MMK_*")
        self.group_name_l_pattern = compile("^@MMK_L_*")
        self.group_name_r_pattern = compile("^@MMK_R_*")
        self._analyze_kerning()

    def is_kerning_group(self, name, side=None):
        # Test if supplied name is a kerning group name
        if side is None:
            return self.group_name_pattern.search(name)
        elif side == "l":
            return self.group_name_l_pattern.search(name)
        elif side == "r":
            return self.group_name_r_pattern.search(name)
        return False

    def _analyze_kerning(self):
        self.kerning = self.font.kerning
        self.group_info = {
            "l": {},
            "r": {},
        }
        for group_name, group_content in self.font.groups.items():
            if self.is_kerning_group(group_name, "l"):
                for glyph_name in group_content:
                    self.group_info["l"][glyph_name] = group_name
            if self.is_kerning_group(group_name, "r"):
                for glyph_name in group_content:
                    self.group_info["r"][glyph_name] = group_name

    def get_group_for_glyph(self, glyph_name, side):
        group_name = self.group_info[side].get(glyph_name, None)
        return group_name

    def getKernValue(self, left, right):
        left_group = self.get_group_for_glyph(left, "l")
        right_group = self.get_group_for_glyph(right, "r")
        pair_value = self.kerning.get((left, right), None)
        if pair_value is not None:
            return pair_value
        lg_value = self.kerning.get((left_group, right), None)
        if lg_value is not None:
            return lg_value
        rg_value = self.kerning.get((left, right_group), None)
        if rg_value is not None:
            return rg_value
        group_value = self.kerning.get((left_group, right_group), None)
        if group_value is None:
            group_value = 0
        return group_value


def getBaseName(glyphname):
    if "." in glyphname and not (glyphname in [".notdef", ".null"]):
        glyphname = glyphname.split(".", 1)[0]
    return glyphname


def getMatchingAnchorName(name):
    # returns "inverted" anchor name, i.e. with leading underscore added or
    # removed
    if name[0] == "_":
        return name[1:]
    else:
        return "_" + name


def getBaseGlyphName(font, name):
    g = font[name]
    baseGlyphCandidates = []
    for c in g.components:
        baseGlyphCandidates.append(c.baseGlyph)
    numCandidates = len(baseGlyphCandidates)
    if numCandidates == 0:
        return name
    elif numCandidates == 1:
        return baseGlyphCandidates[0]
    else:
        # TODO: plausibility check if the base glyph really is the first
        # component.
        # print(baseGlyphCandidates)
        return baseGlyphCandidates[0]


def clearAnchors(glyph):
    for a in glyph.anchors:
        glyph.removeAnchor(a)


def deleteAnchor(glyph, name, position):
    for a in glyph.anchors:
        if a.name == name and a.position == position:
            glyph.removeAnchor(a)
            break


def repositionComponents(glyphname, font):
    print("Repositioning composites in '%s' ..." % glyphname)
    basename = getBaseGlyphName(font, glyphname)
    # print("    Base glyph is: %s" % basename)

    nameWithoutSuffix = getBaseName(glyphname)

    anchor_map = {}

    baseGlyph = font[basename]

    totalWidth = 0

    modified = False
    prevComponentName = None
    kerning = 0
    is_liga = False

    for i, c in enumerate(font[glyphname].components):
        c = font[glyphname].components[i]
        print(f"\n  Component: {c.baseGlyph}")
        if (
            nameWithoutSuffix in ignoreAnchorNames
            or "_" in nameWithoutSuffix
            and not nameWithoutSuffix.endswith("comb")
        ):
            # Handle as ligature resp. ignore anchors
            is_liga = True
            if prevComponentName is not None:
                kerning = kern_info.getKernValue(
                    prevComponentName, c.baseGlyph
                )
                print(
                    "Kerning /%s/%s = %s"
                    % (prevComponentName, c.baseGlyph, kerning)
                )
                if kerning is None:
                    kerning = 0
            # Put glyphs next to each other
            d = (int(round(totalWidth + kerning)), 0)
            if c.offset != d:
                modified = True
                font[glyphname].prepareUndo(
                    f"Reposition components in /{glyphname}"
                )
                print("    Setting component offset to (%i, %i)." % d)
                c.offset = d
        else:
            # Handle as mark positioning
            anchor_found = False
            for mark_anchor in sorted(
                font[c.baseGlyph].anchors, key=attrgetter("name")
            ):
                # print(f"  Mark anchor: {mark_anchor}")
                if i == 0:
                    if mark_anchor.name.startswith("_"):
                        continue
                    # print(
                    #     "  Add anchor from base glyph: '%s'" % mark_anchor.name
                    # )
                    anchor_map[mark_anchor.name] = mark_anchor.position

                base_anchor_name = getMatchingAnchorName(mark_anchor.name)
                # print(
                #     "    Looking for matching anchor for '%s': '%s' ..."
                #     % (
                #         mark_anchor.name,
                #         base_anchor_name,
                #     )
                # )

                for name in sorted(anchor_map.keys(), reverse=True):
                    pos = anchor_map.get(name, (0, 0))
                    if name == base_anchor_name:
                        x, y = pos
                        d = (
                            x - mark_anchor.x,
                            y - mark_anchor.y,
                        )
                        if c.offset != d:
                            modified = True
                            font[glyphname].prepareUndo(
                                f"Reposition components in /{glyphname}"
                            )
                            print(f"  Moving component {c.offset} -> {d}")
                            c.offset = (int(round(d[0])), int(round(d[1])))

                        for temp_anchor in sorted(
                            font[c.baseGlyph].anchors,
                            key=attrgetter("name"),
                            reverse=True,
                        ):
                            if temp_anchor.name.startswith("_"):
                                break

                            anchor_map[temp_anchor.name] = (
                                temp_anchor.x + d[0],
                                temp_anchor.y + d[1],
                            )
                        anchor_found = True
                        break

                if anchor_found:
                    break
                else:
                    print(
                        "    No matching anchor found, "
                        "setting offset to (0, 0)."
                    )
                    if c.offset != (0, 0):
                        c.offset = (0, 0)

        totalWidth += font[c.baseGlyph].width + kerning
        font.changed()
        prevComponentName = c.baseGlyph

    if is_liga or nameWithoutSuffix in ligatureNames:
        # For ligatures, set width to width of all components combined
        w = totalWidth
    else:
        # set width of glyph from baseglyph
        w = baseGlyph.width

    if w != font[glyphname].width:
        print(
            "    Setting width from base glyph: %i -> %i."
            % (font[glyphname].width, w)
        )
        if not modified:
            font[glyphname].prepareUndo(
                "Reposition components in /%s" % glyphname
            )
        font[glyphname].width = w

    if modified:
        font[glyphname].performUndo()
        font[glyphname].changed()
        print("... component positions were modified.")
    else:
        print("... everything is fine.")


ligatureNames = [
    "uniFB00",
    "fi",
    "fl",
    "uniFB01",
    "uniFB02",
    "uniFB03",
    "uniFB04",
    "uniFB05",
    "uniFB06",
    "dcaron",
    "lcaron",
    "IJ",
    "ij",
    "napostrophe",
    "onequarter",
    "onehalf",
    "threequarters",
    "onethird",
    "twothirds",
    "uni2155",
    "uni2156",
    "uni2157",
    "uni2158",
    "uni2159",
    "uni215A",
    "oneeighth",
    "threeeighths",
    "fiveeighths",
    "seveneighths",
    "uni215F",
    "uni2150",
    "uni2151",
    "uni2152",
    "uni2189",
    "percent",
    "perthousand",
    "germandbls",
    "uni01C4",
    "uni01C5",
    "uni01C6",
    "uni01C7",
    "uni01C8",
    "uni01C9",
    "uni01CA",
    "uni01CB",
    "uni01CC",
]

ignoreAnchorNames = [
    "uniFB00",
    "fi",
    "fl",
    "uniFB01",
    "uniFB02",
    "uniFB03",
    "uniFB04",
    "uniFB05",
    "uniFB06",
    "IJ",
    "ij",
    "napostrophe",
    "onequarter",
    "onehalf",
    "threequarters",
    "onethird",
    "twothirds",
    "uni2155",
    "uni2156",
    "uni2157",
    "uni2158",
    "uni2159",
    "uni215A",
    "oneeighth",
    "threeeighths",
    "fiveeighths",
    "seveneighths",
    "uni215F",
    "uni2150",
    "uni2151",
    "uni2152",
    "uni2189",
    "percent",
    "perthousand",
    "uni01C4",
    "uni01C5",
    "uni01C6",
    "uni01C7",
    "uni01C8",
    "uni01C9",
    "uni01CA",
    "uni01CB",
    "uni01CC",
]

f = CurrentFont()

glyphs = []

if CurrentGlyph() is not None:
    glyphs = [CurrentGlyph().name]
elif f.selection:
    glyphs = f.selection

kern_info = jkKernInfo(f)

for glyphname in glyphs:
    result = repositionComponents(glyphname, f)
