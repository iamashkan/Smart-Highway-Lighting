# 3D Board Model

This folder contains simple generated OBJ/MTL models of the ReLight-X Edge Controller Board.

Use cases:

- Import into Blender for presentation renders.
- Import into Unity as a static model if you do not want the procedural model.
- Use as a visual reference for the PCB/enclosure concept.

## Files

- `relightx_edge_controller_board.obj`: one STM32-style edge controller board with wireless, RS485/CAN, sensor, power, and dimming blocks.
- `relightx_five_node_network.obj`: five pole-node boards, five luminaires, sensors, wireless links, and one industrial PLC/RTU gateway.
- `relightx_edge_controller_board.mtl`: shared material library.
- `generate_board_obj.py`: generator script.

Regenerate with:

```bash
python3 board_design/3d_model/generate_board_obj.py
```

The Unity 6 project also includes a procedural 3D board model in:

```text
unity_projects/ReLightX_Unity6/Assets/ReLightX/Scripts/ReLightXBoard3DModel.cs
```

That procedural model is automatically mounted on each highway pole if board visualization is enabled later. The current Unity digital twin intentionally focuses on the road visualization only.
