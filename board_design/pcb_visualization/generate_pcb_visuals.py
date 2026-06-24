from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
PCB_TOP = ROOT / "relightx_stm32_node_pcb_top.png"
NETWORK = ROOT / "relightx_five_node_pcb_network.png"
VIEWER = ROOT / "pcb_viewer.html"


W, H = 1800, 1150


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


F_TITLE = font(42, True)
F_H = font(24, True)
F = font(20)
F_SMALL = font(16)
F_TINY = font(13)


COLORS = {
    "bg": (8, 13, 18),
    "board": (16, 105, 61),
    "board_edge": (75, 225, 158),
    "copper": (226, 158, 72),
    "silk": (224, 245, 238),
    "component": (31, 41, 55),
    "component2": (45, 64, 89),
    "connector": (37, 145, 89),
    "power": (236, 105, 80),
    "signal": (70, 190, 255),
    "bus": (220, 180, 70),
    "sensor": (140, 210, 255),
    "warning": (244, 205, 80),
    "white": (238, 248, 255),
    "muted": (148, 163, 184),
    "wireless": (87, 218, 255),
}


def rounded(draw: ImageDraw.ImageDraw, xy, fill, outline=None, width=3, radius=18):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text_center(draw: ImageDraw.ImageDraw, xy, text: str, fnt=F, fill=COLORS["white"]):
    x0, y0, x1, y1 = xy
    bbox = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=4, align="center")
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.multiline_text(((x0 + x1 - tw) / 2, (y0 + y1 - th) / 2), text, font=fnt, fill=fill, spacing=4, align="center")


def label(draw: ImageDraw.ImageDraw, xy, title: str, subtitle: str = "", fill=COLORS["component"], outline=(80, 120, 150)):
    rounded(draw, xy, fill=fill, outline=outline, width=3, radius=14)
    x0, y0, x1, y1 = xy
    draw.text((x0 + 12, y0 + 10), title, font=F_H, fill=COLORS["white"])
    if subtitle:
        draw.multiline_text((x0 + 12, y0 + 42), subtitle, font=F_SMALL, fill=COLORS["silk"], spacing=3)


def pin_row(draw: ImageDraw.ImageDraw, x: int, y: int, count: int, label_text: str, vertical: bool = False):
    for i in range(count):
        px = x if vertical else x + i * 22
        py = y + i * 22 if vertical else y
        draw.ellipse((px, py, px + 12, py + 12), fill=COLORS["copper"], outline=(80, 48, 20), width=1)
    draw.text((x, y + (count * 22 if vertical else 18)), label_text, font=F_TINY, fill=COLORS["silk"])


def trace(draw: ImageDraw.ImageDraw, points, color, width=5):
    draw.line(points, fill=color, width=width, joint="curve")


def draw_pcb_top() -> None:
    img = Image.new("RGB", (W, H), COLORS["bg"])
    draw = ImageDraw.Draw(img)
    draw.text((70, 45), "ReLight-X STM32 Pole Node PCB - Detailed Top View", font=F_TITLE, fill=COLORS["white"])
    draw.text((72, 96), "Research prototype layout view: not fabrication-ready. Use as a KiCad placement/routing guide.", font=F, fill=COLORS["muted"])

    board = (120, 165, 1680, 980)
    rounded(draw, board, fill=COLORS["board"], outline=COLORS["board_edge"], width=6, radius=30)
    draw.text((135, 930), "Board size target: 120 mm x 80 mm | 4-layer recommended: SIGNAL / GND / POWER / SIGNAL", font=F_SMALL, fill=COLORS["silk"])

    # Mounting holes
    for x, y in [(165, 210), (1635, 210), (165, 935), (1635, 935)]:
        draw.ellipse((x - 22, y - 22, x + 22, y + 22), outline=COLORS["silk"], width=4)
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=COLORS["bg"])

    # Major blocks
    label(draw, (245, 245, 560, 505), "STM32 MCU", "STM32G0/G4/H5 class\nTIM PWM\nFDCAN\nUSART/I2C/SPI/ADC\nSWD debug", COLORS["component2"], COLORS["signal"])
    pin_row(draw, 275, 520, 10, "MCU GPIO breakout")

    label(draw, (1120, 235, 1525, 390), "Wireless Module", "Sub-GHz / LoRa / 802.15.4 /\nWi-Fi HaLow / LTE-M module\ncertified module footprint", (20, 70, 86), COLORS["wireless"])
    rounded(draw, (1440, 180, 1650, 225), fill=(28, 58, 63), outline=COLORS["wireless"], width=3, radius=10)
    text_center(draw, (1440, 180, 1650, 225), "ANTENNA KEEPOUT", F_SMALL, COLORS["wireless"])
    trace(draw, [(1320, 235), (1450, 210)], COLORS["wireless"], width=4)

    label(draw, (1180, 455, 1515, 605), "Industrial Buses", "Isolated CAN/CAN FD transceiver\nIsolated RS485 / Modbus RTU\nservice + wired fallback", (46, 42, 30), COLORS["bus"])
    label(draw, (1320, 635, 1615, 785), "J6/J7 BUS", "CANH CANL GND SHIELD\nRS485 A B GND SHIELD", COLORS["connector"], COLORS["bus"])
    pin_row(draw, 1345, 798, 8, "CAN + RS485 terminals")

    label(draw, (1255, 820, 1605, 925), "J2 DIM / DALI", "0-10V DIM OUT + COM\nDALI/D4i future interface", COLORS["connector"], COLORS["warning"])
    pin_row(draw, 1295, 935, 8, "driver terminals")

    label(draw, (665, 695, 1115, 890), "Dimming Analog Stage", "Timer PWM -> RC low-pass\nrail-to-rail op-amp gain 3.03\n0-10V protected output", (33, 52, 41), COLORS["copper"])
    rounded(draw, (700, 800, 815, 850), fill=(110, 80, 38), outline=COLORS["copper"], width=2, radius=8)
    text_center(draw, (700, 800, 815, 850), "RC", F_SMALL)
    rounded(draw, (845, 790, 1035, 860), fill=(38, 43, 54), outline=COLORS["copper"], width=2, radius=8)
    text_center(draw, (845, 790, 1035, 860), "OP-AMP\n0-10V", F_SMALL)

    label(draw, (945, 245, 1110, 390), "SWD", "debug\nprogram", COLORS["connector"], COLORS["signal"])
    pin_row(draw, 980, 405, 5, "SWDIO SWCLK")

    label(draw, (690, 245, 900, 390), "Status / Override", "HEALTH LED\nLINK LED\nTEST input\nFAULT input", (30, 62, 49), COLORS["signal"])

    label(draw, (170, 660, 500, 860), "Power Entry", "J1 12/24V DC\nfuse + reverse protection\nTVS + common-mode filter", (74, 37, 31), COLORS["power"])
    label(draw, (530, 665, 665, 785), "5V Buck", "wide input", (65, 47, 34), COLORS["power"])
    label(draw, (530, 810, 665, 890), "3V3 LDO", "", (45, 56, 48), COLORS["power"])
    pin_row(draw, 195, 875, 4, "VIN GND")

    label(draw, (610, 455, 940, 620), "Sensor I2C", "VEML7700 or BH1750\nBME280\nINA226/INA228", (34, 70, 88), COLORS["sensor"])
    label(draw, (190, 555, 500, 635), "J5 mmWave Radar", "UART/SPI sensor connector", COLORS["connector"], COLORS["sensor"])
    label(draw, (965, 455, 1110, 620), "Temp", "NTC ADC\nDS18B20", (46, 50, 66), COLORS["sensor"])
    pin_row(draw, 640, 630, 8, "I2C + sensors")

    # Traces and buses
    trace(draw, [(500, 735), (535, 735)], COLORS["power"], 8)
    trace(draw, [(655, 725), (760, 725), (760, 505)], COLORS["power"], 5)
    trace(draw, [(655, 850), (720, 850), (720, 505)], COLORS["power"], 5)
    trace(draw, [(560, 350), (690, 350)], COLORS["signal"], 5)
    trace(draw, [(560, 430), (610, 535)], COLORS["sensor"], 5)
    trace(draw, [(560, 470), (500, 595)], COLORS["sensor"], 5)
    trace(draw, [(560, 500), (665, 785)], COLORS["copper"], 5)
    trace(draw, [(1115, 795), (1255, 870)], COLORS["copper"], 5)
    trace(draw, [(1110, 330), (1120, 315)], COLORS["wireless"], 5)
    trace(draw, [(1110, 535), (1180, 535)], COLORS["bus"], 5)
    trace(draw, [(1515, 535), (1320, 710)], COLORS["bus"], 5)

    # Legend
    lx, ly = 125, 1015
    legend = [
        ("POWER", COLORS["power"]),
        ("SENSOR", COLORS["sensor"]),
        ("CAN/RS485", COLORS["bus"]),
        ("WIRELESS", COLORS["wireless"]),
        ("0-10V", COLORS["copper"]),
    ]
    for i, (name, color) in enumerate(legend):
        x = lx + i * 210
        draw.line((x, ly, x + 70, ly), fill=color, width=8)
        draw.text((x + 82, ly - 12), name, font=F_SMALL, fill=COLORS["white"])

    img.save(PCB_TOP)


def draw_network() -> None:
    img = Image.new("RGB", (W, 980), COLORS["bg"])
    draw = ImageDraw.Draw(img)
    draw.text((70, 45), "ReLight-X Five PCB / Five Pole Network", font=F_TITLE, fill=COLORS["white"])
    draw.text((72, 96), "Each pole has one STM32 node PCB, sensor stack, wireless link, RS485/CAN footprints, and one luminaire output.", font=F, fill=COLORS["muted"])

    gateway = (70, 390, 320, 620)
    rounded(draw, gateway, fill=(25, 35, 50), outline=COLORS["wireless"], width=3, radius=14)
    draw.text((86, 405), "PLC / RTU", font=F_H, fill=COLORS["white"])
    draw.text((86, 438), "Gateway", font=F_H, fill=COLORS["white"])
    draw.multiline_text((86, 480), "cabinet controller\nMQTT/SCADA bridge\nwireless concentrator", font=F_SMALL, fill=COLORS["silk"], spacing=4)
    draw.line((315, 420, 420, 345), fill=COLORS["wireless"], width=6)

    for i in range(5):
        x = 430 + i * 260
        y = 330
        label(draw, (x, y, x + 210, y + 230), f"RLX-N{i + 1:02d}", f"STM32 pole node\nmmWave + ALS\nBME280 + temp\ncurrent monitor", COLORS["board"], COLORS["board_edge"])
        draw.rectangle((x + 30, y + 165, x + 180, y + 205), fill=(24, 35, 45), outline=COLORS["copper"], width=2)
        text_center(draw, (x + 30, y + 165, x + 180, y + 205), "0-10V DIM", F_TINY)
        draw.rectangle((x + 55, y - 110, x + 155, y - 35), fill=(55, 58, 62), outline=COLORS["silk"], width=2)
        text_center(draw, (x + 55, y - 110, x + 155, y - 35), f"Light {i + 1}", F_SMALL)
        draw.line((x + 105, y - 35, x + 105, y), fill=COLORS["copper"], width=4)
        draw.ellipse((x + 35, y - 28, x + 175, y + 42), outline=COLORS["warning"], width=4)
        draw.text((x + 14, y + 242), f"Pole {i + 1} / P{i + 1:03d}", font=F_SMALL, fill=COLORS["silk"])

        if i == 0:
            draw.line((320, 505, x, y + 80), fill=COLORS["wireless"], width=5)
        if i < 4:
            draw.line((x + 210, y + 76, x + 260, y + 76), fill=COLORS["wireless"], width=5)

    draw.text((80, 760), "Behavior:", font=F_H, fill=COLORS["white"])
    behaviors = [
        "RLX-N01 detects vehicle entry and pre-lights downstream nodes.",
        "RLX-N02 confirms approach and raises brightness.",
        "RLX-N03 peaks brightness while vehicle passes under pole.",
        "RLX-N04 holds light after pass, then fades to 30%.",
        "RLX-N05 prepares next zone or returns to eco.",
    ]
    for idx, item in enumerate(behaviors):
        draw.text((105, 805 + idx * 30), f"- {item}", font=F, fill=COLORS["silk"])

    img.save(NETWORK)


def write_viewer() -> None:
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>ReLight-X PCB Detail Viewer</title>
  <style>
    body {{ margin: 0; background: #080d12; color: #eaf8ff; font-family: Arial, sans-serif; }}
    main {{ max-width: 1500px; margin: 0 auto; padding: 28px; }}
    h1 {{ margin: 0 0 8px; }}
    p {{ color: #a8c3d8; line-height: 1.55; }}
    img {{ width: 100%; border: 1px solid rgba(125, 211, 252, .28); border-radius: 8px; margin: 18px 0 34px; background: #071018; }}
    code {{ color: #7dd3fc; }}
    .note {{ border-left: 4px solid #22d3ee; padding: 10px 14px; background: rgba(14, 165, 233, .10); }}
  </style>
</head>
<body>
  <main>
    <h1>ReLight-X PCB Detail Viewer</h1>
    <p class="note">These are detailed research/prototype PCB visuals, not fabrication-ready Gerber/KiCad outputs. Use them as a placement, connector, and architecture guide.</p>
    <h2>STM32 Pole Node PCB Top View</h2>
    <p>Shows MCU, wireless module, RS485/CAN, mmWave radar, ambient/environment/temperature/current sensors, power input, 0-10V dimming stage, and DALI/D4i future connector.</p>
    <img src="{PCB_TOP.name}" alt="ReLight-X STM32 node PCB top view" />
    <h2>Five PCB Network</h2>
    <p>Shows five pole-node PCBs connected wirelessly to an industrial PLC/RTU gateway, each with its own luminaire and sensor stack.</p>
    <img src="{NETWORK.name}" alt="ReLight-X five node PCB network" />
    <p>Related files: <code>board_design/bom.csv</code>, <code>board_design/pin_mapping.csv</code>, <code>board_design/five_node_board_map.csv</code>.</p>
  </main>
</body>
</html>
"""
    VIEWER.write_text(html, encoding="utf-8")


def main() -> None:
    draw_pcb_top()
    draw_network()
    write_viewer()
    print(f"Wrote {PCB_TOP}")
    print(f"Wrote {NETWORK}")
    print(f"Wrote {VIEWER}")


if __name__ == "__main__":
    main()
