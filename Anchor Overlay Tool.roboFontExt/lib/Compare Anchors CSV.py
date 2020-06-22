import codecs
from os.path import expanduser, join
from re import compile, search


class AnchorComparison(object):
    def __init__(self, fontlist=[]):
        fonts = []
        for f in fontlist:
            fonts.append((f.info.openTypeOS2WeightClass, f))
        fonts.sort(key=lambda i: i[0])
        self.fonts = [f[1] for f in fonts]

    def get_global_glyph_list(self):
        gl = []
        for f in self.fonts:
            gl.extend(f.glyphOrder)
        return sorted(list(set(gl)))

    def get_global_anchor_list(self, glyph_name):
        al = []
        for f in self.fonts:
            al.extend([a.name for a in f[glyph_name].anchors])
        return sorted(list(set(al)))

    def get_anchors_by_name(self, glyph):
        anchor_names = [a.name for a in glyph.anchors]
        if len(anchor_names) != len(set(anchor_names)):
            print("  WARNING: Duplicate anchor name in %s" % glyph.name)
        return {a.name: (a.x, a.y) for a in glyph.anchors}

    def get_comparison_csv(self):
        csv = 'Glyph;Anchor;'
        for i in range(len(self.fonts)):
            csv += '%s;%s;' % (self.fonts[i].info.familyName, self.fonts[i].info.styleName)
        csv += "\n"
        glyphs = self.get_global_glyph_list()
        for name in glyphs:
            all_anchors = self.get_global_anchor_list(name)
            for anchor in all_anchors:
                csv += '%s;%s;' % (name, anchor)
                for i in range(len(self.fonts)):
                    if name in self.fonts[i]:
                        glyph_anchors = self.get_anchors_by_name(self.fonts[i][name])
                        if anchor in glyph_anchors:
                            pos = self.get_anchors_by_name(self.fonts[i][name])[anchor]
                            csv += '%i;%i;' % (pos[0], pos[1])
                        else:
                            csv += ';;'
                    else:
                        csv += '(no glyph);'
                csv += "\n"
        return csv

    def save_comparison_csv(self, path=None):
        if len(self.fonts) > 0:
            if not path:
                path = join(expanduser("~"), "Documents", "%s_Anchor_Comparison.csv" % self.fonts[0].info.familyName)
            with codecs.open(path, "wb", encoding="utf-8") as csv:
                csv.write(self.get_comparison_csv())
            print("Anchor table written to '%s'." % path)
        else:
            print("There are no open fonts.")

ac = AnchorComparison(AllFonts())
ac.save_comparison_csv()
