import os
import io
import zipfile
import shutil
from PIL import Image
from build_sfo import build_sfo

base_dir = r"d:\fyeshi\project\rohit\vita_port"
src_vpk = os.path.join(base_dir, "vitajs-0.5.1.vpk")
out_vpk = r"d:\fyeshi\project\rohit\FARSverse_Pocket.vpk"
desktop_dir = os.path.expanduser(r"~\Desktop")
desktop_vpk = os.path.join(desktop_dir, "FARSverse_Pocket.vpk")

print("1. Generating custom param.sfo for FARSverse Pocket...")
sfo_data = {
    'APP_VER': (0x0204, '01.00', 8),
    'ATTRIBUTE': (0x0404, 32768, 4),
    'ATTRIBUTE2': (0x0404, 0, 4),
    'ATTRIBUTE_MINOR': (0x0404, 16, 4),
    'BOOT_FILE': (0x0204, '', 32),
    'CATEGORY': (0x0204, 'gd', 4),
    'CONTENT_ID': (0x0204, '', 48),
    'EBOOT_APP_MEMSIZE': (0x0404, 0, 4),
    'EBOOT_ATTRIBUTE': (0x0404, 0, 4),
    'EBOOT_PHY_MEMSIZE': (0x0404, 0, 4),
    'LAREA_TYPE': (0x0404, 0, 4),
    'NP_COMMUNICATION_ID': (0x0204, '', 16),
    'PARENTAL_LEVEL': (0x0404, 0, 4),
    'PSP2_DISP_VER': (0x0204, '00.000', 8),
    'PSP2_SYSTEM_VER': (0x0404, 0, 4),
    'STITLE': (0x0204, 'FARSverse Pocket', 52),
    'TITLE': (0x0204, 'FARSverse Pocket', 128),
    'TITLE_ID': (0x0204, 'FARS00001', 12),
    'VERSION': (0x0204, '01.00', 8),
}
sfo_bytes = build_sfo(sfo_data)
sfo_file = os.path.join(base_dir, "param.sfo")
with open(sfo_file, "wb") as f:
    f.write(sfo_bytes)

def get_compliant_vita_png(file_path, target_size, allow_transparency=True):
    """
    PS Vita / PS TV promoter utility requires LiveArea PNG images to strictly be
    8-bit indexed palette (mode 'P', max 256 colors) with standard PLTE chunks.
    Otherwise VitaShell fails with error 0x8010113D (SCE_PROMOTER_UTIL_ERROR_INVALID_PARAM).
    """
    im = Image.open(file_path)
    if im.size != target_size:
        im = im.resize(target_size, Image.Resampling.LANCZOS)
    if allow_transparency and im.mode == 'RGBA':
        im_p = im.quantize(colors=256)
    else:
        im_p = im.convert('RGB').quantize(colors=256)
    buf = io.BytesIO()
    im_p.save(buf, format='PNG', optimize=True)
    return buf.getvalue()

print("2. Packaging FARSverse_Pocket.vpk with PS Vita/PSTV-compliant assets...")
# Extract eboot.bin and font from base vpk
with zipfile.ZipFile(src_vpk, "r") as z_in:
    eboot_data = z_in.read("eboot.bin")
    font_data = z_in.read("assets/segoeui.ttf")
    dts_data = z_in.read("assets/vitajs.d.ts")

# Read generated/authored files
with open(os.path.join(base_dir, "assets", "main.js"), "rb") as f:
    main_js_data = f.read()

icon_data = get_compliant_vita_png(os.path.join(base_dir, "sce_sys", "icon0.png"), (128, 128), True)
bg_data = get_compliant_vita_png(os.path.join(base_dir, "sce_sys", "livearea", "contents", "bg.png"), (840, 500), False)
startup_data = get_compliant_vita_png(os.path.join(base_dir, "sce_sys", "livearea", "contents", "startup.png"), (280, 158), True)

with open(os.path.join(base_dir, "sce_sys", "livearea", "contents", "template.xml"), "rb") as f:
    template_data = f.read()

# Build VPK archive (ZIP format with standard compression)
with zipfile.ZipFile(out_vpk, "w", zipfile.ZIP_DEFLATED) as z_out:
    z_out.writestr("eboot.bin", eboot_data)
    z_out.writestr("sce_sys/param.sfo", sfo_bytes)
    z_out.writestr("sce_sys/icon0.png", icon_data)
    z_out.writestr("sce_sys/livearea/contents/bg.png", bg_data)
    z_out.writestr("sce_sys/livearea/contents/startup.png", startup_data)
    z_out.writestr("sce_sys/livearea/contents/template.xml", template_data)
    z_out.writestr("assets/main.js", main_js_data)
    z_out.writestr("assets/segoeui.ttf", font_data)
    z_out.writestr("assets/vitajs.d.ts", dts_data)

file_size = os.path.getsize(out_vpk)
print(f"3. VPK Build complete! Output: {out_vpk} ({file_size} bytes)")

# Copy to Desktop for user convenience
try:
    shutil.copy2(out_vpk, desktop_vpk)
    print(f"4. Copied to Desktop: {desktop_vpk}")
except Exception as e:
    print(f"Warning: Could not copy to desktop: {e}")
