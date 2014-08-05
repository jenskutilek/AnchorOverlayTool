"""
Recompose selected glyphs, using anchor positions as reference for placement.
Also resets the metrics of the composite to those of the base glyph(s).

Jens Kutilek
Version 0.1: 2013-05-28
Version 0.2: 2014-08-05 - Implemented chained accents positioning
"""

def getBaseName(glyphname):
    if "." in glyphname and not(glyphname in [".notdef", ".null"]):
        glyphname = glyphname.split(".", 1)[0]
    return glyphname

def getMatchingAnchorName(name):
    # returns "inverted" anchor name, i.e. with leading underscore added or removed
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
        # TODO: plausibility check if the base glyph really is the first component.
        #print baseGlyphCandidates
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
    print "Repositioning composites in '%s' ..." % glyphname
    basename = getBaseGlyphName(font, glyphname)
    #print "    Base glyph is: %s" % basename
    
    nameWithoutSuffix = getBaseName(glyphname)
    
    # Make a temporary glyph
    glyph = RGlyph()
    glyph.appendGlyph(font[glyphname])
    
    baseGlyph = font[basename]
    
    totalWidth = 0
    clearAnchors(glyph)
    
    for i in range(len(font[glyphname].components)):
        c = font[glyphname].components[i]
        #print "\n  Component: %s" % (c.baseGlyph)
        if nameWithoutSuffix in ignoreAnchorNames or "_" in nameWithoutSuffix:
            # Put glyphs next to each other
            d = (int(round(totalWidth)), 0)
            if c.offset != d:
                print "    Setting component offset to (%i, %i)." % d
                c.offset = d
        
        anchor_found = False    
        for mark_anchor in font[c.baseGlyph].anchors:
            if i == 0:
                #print "  Add anchor from base glyph: '%s'" % mark_anchor.name
                glyph.appendAnchor(mark_anchor.name, mark_anchor.position)

            base_anchor_name = getMatchingAnchorName(mark_anchor.name)
            #print "    Looking for matching anchor for '%s': '%s' ..." % (
            #    mark_anchor.name,
            #    base_anchor_name,
            #)
            
            for anchor in glyph.anchors:
                if anchor.name == base_anchor_name:
                    #print "        Process anchor: '%s'" % anchor
                    d = (anchor.x - mark_anchor.x, anchor.y - mark_anchor.y)
                    glyph.removeAnchor(anchor)
                    #print "Move component %s -> %s" % (c.offset, d)
                    if c.offset != d:
                        c.offset = (int(round(d[0])), int(round(d[1])))
                    for temp_anchor in font[c.baseGlyph].anchors:
                        #print "          Append anchor: '%s'" % (temp_anchor.name)
                        glyph.appendAnchor(temp_anchor.name, (int(round(temp_anchor.x + d[0])), int(round(temp_anchor.y + d[1]))))
                    anchor_found = True
                    #glyph.removeAnchor(anchor)
                    break
                else:
                    pass
                    #print "        Ignore anchor: '%s'" % anchor.name
                    #glyph.removeAnchor(anchor)
            if not anchor_found:
                #print "    No matching anchor found, setting offset to (0, 0)."
                if c.offset != (0, 0):
                    c.offset = (0, 0)
        # Limit component depth for debugging purposes
        #if i == 2:
        #    break
        totalWidth += font[c.baseGlyph].width
        font.update()
    if nameWithoutSuffix in ligatureNames or "_" in nameWithoutSuffix:
        # For ligatures, set width to width of all components combined
        w = totalWidth
    else:
        # set width of glyph from baseglyph
        w = baseGlyph.width
    
    modified = False
    glyph.update()
    #clearAnchors(glyph)
    
    if w != font[glyphname].width:
        print "    Setting width from base glyph: %i -> %i." % (font[glyphname].width, w)
        font[glyphname].width = w
        modified = True
    
    for i in range(len(glyph.components)):
        c_ref = glyph.components[i]
        c_mod = font[glyphname].components[i]
        if c_ref.baseGlyph == c_mod.baseGlyph:
            if c_ref.offset != c_mod.offset:
                print "    Move component '%s': %s -> %s." % (c_mod.baseGlyph, c_ref.offset, c_mod.offset)
                c_ref.offset = c_mod.offset
                modified = True
        else:
            print "    Unexpected ERROR: component order mismatch."
    if modified:
        font[glyphname].update()
        print "... component positions were modified."
    else:
        print "... everything is fine."
    del glyph
        

ligatureNames = ["uniFB00", "fi", "fl", "dcaron", "lcaron", "IJ", "ij", "napostrophe", 'onequarter', 'onehalf', 'threequarters', 'onethird', 'twothirds', 'uni2155', 'uni2156', 'uni2157', 'uni2158', 'uni2159', 'uni215A', 'oneeighth', 'threeeighths', 'fiveeighths', 'seveneighths', 'uni215F', 'uni2150', 'uni2151', 'uni2152', 'uni2189', 'percent', 'perthousand']

ignoreAnchorNames = ["uniFB00", "fi", "fl", "IJ", "ij", "napostrophe", 'onequarter', 'onehalf', 'threequarters', 'onethird', 'twothirds', 'uni2155', 'uni2156', 'uni2157', 'uni2158', 'uni2159', 'uni215A', 'oneeighth', 'threeeighths', 'fiveeighths', 'seveneighths', 'uni215F', 'uni2150', 'uni2151', 'uni2152', 'uni2189', 'percent', 'perthousand']

f = CurrentFont()

for glyphname in f.selection:
    f[glyphname].prepareUndo("Reposition components in /%s" % glyphname)
    repositionComponents(glyphname, f)
    f[glyphname].performUndo()
