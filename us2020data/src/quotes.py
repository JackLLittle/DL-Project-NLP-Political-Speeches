# https://gist.github.com/goodmami/98b0a6e2237ced0025dd
# quote list: https://en.wikipedia.org/wiki/Quotation_mark
QUOTES = (
    '\u0022'  # quotation mark (")
    '\u0027'  # apostrophe (')
    '\u00ab'  # left-pointing double-angle quotation mark
    '\u00bb'  # right-pointing double-angle quotation mark
    '\u2018'  # left single quotation mark
    '\u2019'  # right single quotation mark
    '\u201a'  # single low-9 quotation mark
    '\u201b'  # single high-reversed-9 quotation mark
    '\u201c'  # left double quotation mark
    '\u201d'  # right double quotation mark
    '\u201e'  # double low-9 quotation mark
    '\u201f'  # double high-reversed-9 quotation mark
    '\u2039'  # single left-pointing angle quotation mark
    '\u203a'  # single right-pointing angle quotation mark
    '\u300c'  # left corner bracket
    '\u300d'  # right corner bracket
    '\u300e'  # left white corner bracket
    '\u300f'  # right white corner bracket
    '\u301d'  # reversed double prime quotation mark
    '\u301e'  # double prime quotation mark
    '\u301f'  # low double prime quotation mark
    '\ufe41'  # presentation form for vertical left corner bracket
    '\ufe42'  # presentation form for vertical right corner bracket
    '\ufe43'  # presentation form for vertical left corner white bracket
    '\ufe44'  # presentation form for vertical right corner white bracket
    '\uff02'  # fullwidth quotation mark
    '\uff07'  # fullwidth apostrophe
    '\uff62'  # halfwidth left corner bracket
    '\uff63'  # halfwidth right corner bracket
)
# mapping of {open: close} quotes extracted from
#   https://en.wikipedia.org/wiki/Quotation_mark
# and augmented with other observed patterns
# note: adding grave accent (`) and comma (,) as they've been observed
#       serving as quotes
QUOTEPAIRS = {
    '\u0022': ['\u0022'],  # quotation mark (")
    '\u0027': ['\u0027'],  # apostrophe (')
    '\u002c': ['\u0027', '\u0060'],  # comma/(apostrophe|grave-accent)
    '\u0060': ['\u0027'],  # grave-accent/apostrophe
    '\u00ab': ['\u00bb'],  # left/right-pointing double-angle quotation mark
    '\u00bb': ['\u00ab', '\u00bb'],  # right/(left|right)-pointing double-angle quotation mark
    '\u2018': ['\u2019'],  # left/right single quotation mark
    '\u2019': ['\u2019'],  # right single quotation mark
    '\u201a': ['\u201b', '\u2018', '\u2019'],  # single low-9/(high-reversed-9|left-single|right-single) quotation mark
    '\u201b': ['\u2019'],  # single high-reversed-9/right-single quotation mark
    '\u201c': ['\u201d'],  # left/right double quotation mark
    '\u201d': ['\u201d'],  # right double quotation mark
    '\u201e': ['\u201c', '\u201d'],  # double-low-9/(left-double|right-double) quotation mark
    '\u201f': ['\u201d'],  # double-high-reversed-9/right-double quotation mark
    '\u2039': ['\u203a'],  # single left/right-pointing angle quotation mark
    '\u203a': ['\u2039', '\u203a'],  # single right/(left|right)-pointing angle quotation mark
    '\u300c': ['\u300d'],  # left/right corner bracket
    '\u300e': ['\u300f'],  # left/right white corner bracket
    '\u301d': ['\u301e'],  # reversed/* double prime quotation mark
    '\u301f': ['\u301e'],  # low/* double prime quotation mark
    '\ufe41': ['\ufe42'],  # presentation form for vertical left/right corner bracket
    '\ufe43': ['\ufe44'],  # presentation form for vertical left/right corner white bracket
    '\uff02': ['\uff02'],  # fullwidth quotation mark
    '\uff07': ['\uff07'],  # fullwidth apostrophe
    '\uff62': ['\uff63']  # halfwidth left/right corner bracket
}
OPENQUOTES = ''.join(QUOTEPAIRS.keys())
CLOSEQUOTES = ''.join(q for qs in QUOTEPAIRS.values() for q in qs)
