"""
Recompose selected glyphs, using anchor positions as reference for placement.
Also resets the metrics of the composite to those of the base glyph(s).

Jens Kutilek, 2013-05-28
"""


def getMatchingAnchorName(name):
    # returns "inverted" anchor name, i.e. with leading underscore added or removed
    if name[0] == "_":
        return name[1:]
    else:
        return "_" + name


def getBaseName(glyphname):
    if "." in glyphname and not(glyphname in [".notdef", ".null"]):
        glyphname = glyphname.split(".", 1)[0]
    return glyphname


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
        # TODO: plausibility check if the base glyph really is the first component.
        #print baseGlyphCandidates
        return baseGlyphCandidates[0]


f = CurrentFont()

ligatureNames = ["fi", "fl", "dcaron", "lcaron", "IJ", "ij", "napostrophe", 'onequarter', 'onehalf', 'threequarters', 'onethird', 'twothirds', 'uni2155', 'uni2156', 'uni2157', 'uni2158', 'uni2159', 'uni215A', 'oneeighth', 'threeeighths', 'fiveeighths', 'seveneighths', 'uni215F', 'uni2150', 'uni2151', 'uni2152', 'uni2189', 'percent', 'perthousand']
ignoreAnchorNames = ["fi", "fl", "IJ", "ij", "napostrophe", 'onequarter', 'onehalf', 'threequarters', 'onethird', 'twothirds', 'uni2155', 'uni2156', 'uni2157', 'uni2158', 'uni2159', 'uni215A', 'oneeighth', 'threeeighths', 'fiveeighths', 'seveneighths', 'uni215F', 'uni2150', 'uni2151', 'uni2152', 'uni2189', 'percent', 'perthousand']

for glyphname in f.selection:
    isLigature = getBaseName(glyphname) in ligatureNames
    print "Recomposing '%s' ..." % glyphname
    f[glyphname].prepareUndo("Recompose /%s" % glyphname)
    if isLigature:
        print "    Is a ligature."
    basename = getBaseGlyphName(f, glyphname)
    print "    Base glyph is: %s" % basename
    baseGlyph = f[basename]
    totalWidth = 0
    for c in f[glyphname].components:
        if c.baseGlyph == basename:
            if c.offset != (0, 0):
                print "    Setting offset of base glyph to 0."
                c.offset = (0, 0)
        else:
            if getBaseName(glyphname) in ignoreAnchorNames:
                # Put glyphs next to each other
                d = (int(round(totalWidth)), 0)
                if c.offset != d:
                    print "    Setting component offset to (%i, %i)." % d
                    c.offset = d
            else:
                # TODO: If more than one mark glyph, second one must
                # attach to offset of base + first mark etc.
                for a in f[c.baseGlyph].anchors:
                    myMarkAnchor = getMatchingAnchorName(a.name)
                    #print "    Looking for anchor '%s' in component ..." % myMarkAnchor
                    anchorFound = False
                    for a2 in baseGlyph.anchors:
                        if a2.name == myMarkAnchor:
                            #print "      ... found."
                            d = (a2.x - a.x, a2.y - a.y)
                            if c.offset != d:
                                print "    Setting component offset to (%i, %i)." % d
                                c.offset = d
                            anchorFound = True
                            break
                    if not anchorFound:
                        print "      WARNING: anchor '%s' not found in component." % myMarkAnchor
        totalWidth += f[c.baseGlyph].width
        f.update()
    if isLigature:
        # set width to width of all components combined
        w = totalWidth
    else:
        # set width of glyph from baseglyph
        w = baseGlyph.width
    if w != f[glyphname].width:
        print "    Setting width from base glyphs: %i -> %i" % (f[glyphname].width, w)
        f[glyphname].width = w
    f[glyphname].performUndo()
    
