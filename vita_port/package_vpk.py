import os
import zipfile
import shutil
from build_sfo import build_sfo

base_dir = r"d:\fyeshi\project\rohit\vita_port"
src_vpk = os.path.join(base_dir, "vitajs-0.5.1.vpk")
out_vpk = r"d:\fyeshi\project\rohit\FARSverse_Pocket.vpk"

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

print("2. Packaging FARSverse_Pocket.vpk...")
# Extract eboot.bin and font from base vpk
with zipfile.ZipFile(src_vpk, "r") as z_in:
    eboot_data = z_in.read("eboot.bin")
    font_data = z_in.read("assets/segoeui.ttf")
    dts_data = z_in.read("assets/vitajs.d.ts")

# Read generated/authored files
with open(os.path.join(base_dir, "assets", "main.js"), "rb") as f:
    main_js_data = f.read()

with open(os.path.join(base_dir, "sce_sys", "icon0.png"), "rb") as f:
    icon_data = f.read()

with open(os.path.join(base_dir, "sce_sys", "livearea", "contents", "bg.png"), "rb") as f:
    bg_data = f.read()

with open(os.path.join(base_dir, "sce_sys", "livearea", "contents", "startup.png"), "rb") as f:
    startup_data = f.read()

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
