from pathlib import Path


ROOT = Path(__file__).resolve().parent
OBJ = ROOT / "relightx_edge_controller_board.obj"
NETWORK_OBJ = ROOT / "relightx_five_node_network.obj"
MTL = ROOT / "relightx_edge_controller_board.mtl"


MATERIALS = {
    "enclosure": (0.32, 0.34, 0.36),
    "pcb": (0.02, 0.34, 0.16),
    "esp32": (0.04, 0.17, 0.42),
    "terminal": (0.14, 0.58, 0.22),
    "black": (0.03, 0.03, 0.035),
    "copper": (0.92, 0.42, 0.14),
    "warning": (0.90, 0.70, 0.12),
    "cover": (0.70, 0.86, 1.00),
    "pole": (0.38, 0.40, 0.40),
    "light": (1.00, 0.82, 0.42),
    "radar": (0.10, 0.10, 0.12),
    "ambient": (0.80, 0.92, 1.00),
    "wireless": (0.18, 0.72, 1.00),
    "network": (0.18, 0.95, 0.78),
}


def cube_vertices(cx, cy, cz, sx, sy, sz):
    x0, x1 = cx - sx / 2, cx + sx / 2
    y0, y1 = cy - sy / 2, cy + sy / 2
    z0, z1 = cz - sz / 2, cz + sz / 2
    return [
        (x0, y0, z0),
        (x1, y0, z0),
        (x1, y1, z0),
        (x0, y1, z0),
        (x0, y0, z1),
        (x1, y0, z1),
        (x1, y1, z1),
        (x0, y1, z1),
    ]


def add_cube(lines, name, mat, cx, cy, cz, sx, sy, sz, index):
    lines.append(f"o {name}")
    lines.append(f"usemtl {mat}")
    for vertex in cube_vertices(cx, cy, cz, sx, sy, sz):
        lines.append("v {:.4f} {:.4f} {:.4f}".format(*vertex))
    faces = [
        (1, 2, 3, 4),
        (5, 8, 7, 6),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 8, 4),
        (4, 8, 5, 1),
    ]
    for face in faces:
        lines.append("f {} {} {} {}".format(*(index + value - 1 for value in face)))
    return index + 8


def board_parts(prefix, ox, oy, oz, scale=1.0):
    return [
        (f"{prefix}_backplate", "enclosure", ox, oy, oz, 1.95 * scale, 0.10 * scale, 1.28 * scale),
        (f"{prefix}_pcb", "pcb", ox, oy + 0.08 * scale, oz, 1.65 * scale, 0.06 * scale, 1.04 * scale),
        (f"{prefix}_stm32_mcu", "esp32", ox - 0.36 * scale, oy + 0.17 * scale, oz + 0.14 * scale, 0.42 * scale, 0.12 * scale, 0.32 * scale),
        (f"{prefix}_wireless_module", "wireless", ox - 0.74 * scale, oy + 0.17 * scale, oz + 0.14 * scale, 0.18 * scale, 0.10 * scale, 0.34 * scale),
        (f"{prefix}_buck_converter", "black", ox + 0.38 * scale, oy + 0.17 * scale, oz + 0.34 * scale, 0.42 * scale, 0.12 * scale, 0.24 * scale),
        (f"{prefix}_rs485_can_terminal", "terminal", ox + 0.72 * scale, oy + 0.18 * scale, oz + 0.10 * scale, 0.28 * scale, 0.12 * scale, 0.28 * scale),
        (f"{prefix}_dim_terminal", "terminal", ox + 0.72 * scale, oy + 0.18 * scale, oz - 0.30 * scale, 0.28 * scale, 0.12 * scale, 0.26 * scale),
        (f"{prefix}_sensor_header", "black", ox - 0.28 * scale, oy + 0.17 * scale, oz - 0.48 * scale, 0.64 * scale, 0.045 * scale, 0.06 * scale),
        (f"{prefix}_radar_header", "radar", ox - 0.72 * scale, oy + 0.19 * scale, oz - 0.26 * scale, 0.22 * scale, 0.08 * scale, 0.16 * scale),
        (f"{prefix}_ambient_sensor", "ambient", ox + 0.08 * scale, oy + 0.19 * scale, oz - 0.40 * scale, 0.14 * scale, 0.05 * scale, 0.14 * scale),
        (f"{prefix}_bme280_sensor", "warning", ox + 0.28 * scale, oy + 0.19 * scale, oz - 0.40 * scale, 0.14 * scale, 0.05 * scale, 0.14 * scale),
        (f"{prefix}_cover", "cover", ox, oy + 0.30 * scale, oz, 2.04 * scale, 0.07 * scale, 1.36 * scale),
    ]


def write_materials():
    mtl_lines = []
    for name, color in MATERIALS.items():
        mtl_lines.extend(
            [
                f"newmtl {name}",
                "Kd {:.3f} {:.3f} {:.3f}".format(*color),
                "Ka {:.3f} {:.3f} {:.3f}".format(*(c * 0.35 for c in color)),
                "Ks 0.120 0.120 0.120",
                "Ns 24",
                "",
            ]
        )
    MTL.write_text("\n".join(mtl_lines), encoding="utf-8")


def write_single_board():
    lines = ["mtllib relightx_edge_controller_board.mtl"]
    idx = 1
    parts = [
        ("weatherproof_backplate", "enclosure", 0, 0, 0, 1.95, 0.10, 1.28),
        ("green_pcb", "pcb", 0, 0.08, 0, 1.65, 0.06, 1.04),
        ("stm32_edge_mcu", "esp32", -0.43, 0.17, 0.14, 0.50, 0.12, 0.36),
        ("wireless_module", "wireless", -0.76, 0.20, 0.14, 0.16, 0.08, 0.34),
        ("buck_converter", "black", 0.38, 0.17, 0.34, 0.42, 0.12, 0.24),
        ("regulator_3v3", "black", 0.06, 0.17, 0.33, 0.20, 0.09, 0.16),
        ("opamp_0_10v_stage", "black", 0.46, 0.17, -0.06, 0.40, 0.10, 0.20),
        ("rc_filter_a", "copper", 0.16, 0.17, -0.08, 0.17, 0.06, 0.06),
        ("rc_filter_b", "copper", 0.16, 0.17, -0.20, 0.17, 0.06, 0.06),
        ("vin_terminal", "terminal", 0.72, 0.18, 0.08, 0.28, 0.12, 0.14),
        ("dim_a_terminal", "terminal", 0.72, 0.18, -0.18, 0.28, 0.12, 0.14),
        ("dim_b_terminal", "terminal", 0.72, 0.18, -0.42, 0.28, 0.12, 0.14),
        ("rs485_can_terminal", "terminal", -0.42, 0.18, -0.38, 0.42, 0.12, 0.16),
        ("dali_d4i_future", "warning", -0.04, 0.17, -0.36, 0.28, 0.09, 0.18),
        ("radar_uart_header", "radar", -0.74, 0.17, -0.32, 0.32, 0.07, 0.10),
        ("ambient_light_sensor", "ambient", -0.18, 0.19, -0.48, 0.16, 0.05, 0.12),
        ("bme280_sensor", "warning", 0.04, 0.19, -0.48, 0.16, 0.05, 0.12),
        ("current_header", "black", 0.30, 0.17, -0.48, 0.24, 0.045, 0.06),
        ("transparent_cover", "cover", 0, 0.30, 0, 2.04, 0.07, 1.36),
    ]
    for part in parts:
        idx = add_cube(lines, *part, idx)

    OBJ.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_five_node_network():
    lines = ["mtllib relightx_edge_controller_board.mtl"]
    idx = 1
    spacing = 3.15

    for node in range(5):
        x = (node - 2) * spacing
        prefix = f"rlx_n{node + 1:02d}"
        parts = [
            (f"{prefix}_pole", "pole", x, 1.15, -0.95, 0.10, 2.30, 0.10),
            (f"{prefix}_luminaire", "light", x + 0.45, 2.22, -0.95, 0.86, 0.16, 0.30),
            (f"{prefix}_light_pool", "warning", x + 0.46, 0.02, -0.95, 1.38, 0.025, 0.92),
            (f"{prefix}_radar_pod", "radar", x - 0.22, 1.62, -0.78, 0.28, 0.18, 0.18),
            (f"{prefix}_ambient_pod", "ambient", x + 0.22, 1.62, -0.78, 0.18, 0.14, 0.14),
            (f"{prefix}_antenna", "wireless", x - 0.82, 0.76, 0.00, 0.035, 0.74, 0.035),
        ]
        parts.extend(board_parts(prefix, x, 0.26, 0.0, scale=0.55))
        for part in parts:
            idx = add_cube(lines, *part, idx)

        if node < 4:
            link_x = x + spacing / 2
            idx = add_cube(lines, f"wireless_link_{node + 1}_{node + 2}", "network", link_x, 1.06, 0.08, spacing - 0.70, 0.035, 0.035, idx)

    idx = add_cube(lines, "industrial_plc_rtu_gateway", "black", -spacing * 2.75, 0.55, 0.78, 0.80, 0.68, 0.46, idx)
    idx = add_cube(lines, "gateway_wireless_antenna", "wireless", -spacing * 2.75, 1.12, 0.78, 0.04, 0.82, 0.04, idx)
    idx = add_cube(lines, "gateway_to_node_wireless_backhaul", "network", -spacing * 1.95, 1.13, 0.42, spacing * 1.42, 0.035, 0.035, idx)
    NETWORK_OBJ.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    write_materials()
    write_single_board()
    write_five_node_network()
    print(f"Wrote {OBJ}")
    print(f"Wrote {NETWORK_OBJ}")
    print(f"Wrote {MTL}")


if __name__ == "__main__":
    main()
