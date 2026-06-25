def patch_pywaffle():
    """
    Patch PyWaffle to use TTF webfonts instead of OTF on Windows.
    Required because Matplotlib cannot render Font Awesome OTF files
    correctly on Windows. Run once per virtual environment, then
    restart the kernel.
    """
    import os, sys, pywaffle

    # Check platform
    if sys.platform != "win32":
        print("Not Windows — no patch needed.")
        return

    venv = sys.prefix
    webfonts = os.path.join(
        venv,
        r"Lib\site-packages\fontawesomefree\static\fontawesomefree\webfonts"
    )

    solid   = os.path.join(webfonts, "fa-solid-900.ttf")
    regular = os.path.join(webfonts, "fa-regular-400.ttf")
    brands  = os.path.join(webfonts, "fa-brands-400.ttf")

    # Verify files exist
    missing = [p for p in [solid, regular, brands] if not os.path.exists(p)]
    if missing:
        print("Missing font files — is fontawesomefree installed?")
        for p in missing:
            print(" ", p)
        return

    handler_path = os.path.join(
        os.path.dirname(pywaffle.__file__), "fontawesome_handler.py"
    )

    # Check if patch already applied
    if os.path.exists(handler_path):
        with open(handler_path) as f:
            existing = f.read()
        if solid in existing:
            print("Patch already applied — no changes made.")
            return

    new_content = f"""import pathlib
import matplotlib.font_manager as fm
from matplotlib.legend_handler import HandlerBase
from matplotlib.text import Text

fontawesome_files = {{
    "solid":   pathlib.Path(r"{solid}"),
    "regular": pathlib.Path(r"{regular}"),
    "brands":  pathlib.Path(r"{brands}"),
}}

class TextLegendBase:
    def __init__(self, text, color, **kwargs):
        self.text = text
        self.color = color
        self.kwargs = kwargs

def LegendClassFactory(name, BaseClass=TextLegendBase):
    def __init__(self, text, color, **kwargs):
        BaseClass.__init__(self, text=text, color=color, **kwargs)
    return type(name, (BaseClass,), {{"__init__": __init__}})

legend_style_class_mapping = {{
    "solid":   LegendClassFactory("SolidTextLegend"),
    "regular": LegendClassFactory("RegularTextLegend"),
    "brands":  LegendClassFactory("BrandsTextLegend"),
}}

class TextLegendHandler(HandlerBase):
    def __init__(self, font_file):
        super().__init__()
        self.font_file = font_file

    def create_artists(self, legend, orig_handle, xdescent, ydescent,
                       width, height, fontsize, trans):
        x = xdescent + width / 2.0
        y = ydescent + height / 2.0
        kwargs = {{
            "horizontalalignment": "center",
            "verticalalignment": "center",
            "color": orig_handle.color,
            "fontproperties": fm.FontProperties(fname=self.font_file, size=fontsize),
        }}
        kwargs.update(orig_handle.kwargs)
        return [Text(x, y, orig_handle.text, **kwargs)]

legend_handler_style_mapping = {{
    v: TextLegendHandler(font_file=fontawesome_files[k])
    for k, v in legend_style_class_mapping.items()
}}
"""

    with open(handler_path, "w") as f:
        f.write(new_content)

    print("Patch applied successfully.")                                # ← inside function
    print("Please restart the kernel before using PyWaffle icons.")    # ← inside function


# Run once
patch_pywaffle()
