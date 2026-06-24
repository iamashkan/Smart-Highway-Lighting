# PCB Visualization

This folder contains detailed visual inspection files for the ReLight-X board design.

## Open These Files

- `pcb_viewer.html`: browser viewer for the PCB and five-board network.
- `relightx_stm32_node_pcb_top.png`: detailed top-view PCB placement/routing concept.
- `relightx_five_node_pcb_network.png`: five-board network overview.

## Regenerate

```bash
python3 board_design/pcb_visualization/generate_pcb_visuals.py
```

## Important

These images are detailed concept drawings, not fabrication-ready PCB files. For manufacturing, create a real KiCad schematic and PCB from:

- `board_design/implementation/five_node_network_architecture.md`
- `board_design/implementation/pcb_layout_guide.md`
- `board_design/bom.csv`
- `board_design/pin_mapping.csv`
- `board_design/kicad_placeholders/SCHEMATIC_NOTES.md`
