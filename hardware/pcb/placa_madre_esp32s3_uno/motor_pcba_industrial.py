#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
MOTOR DE DISEÑO PCBA INDUSTRIAL Y AUTOROUTER OCTILINEAR 45° (KiCad 10)
================================================================================
Motor compartido para generar las placas madre industriales (Rev 4.0) de:
  1. Proyecto_Uno (Arduino UNO Q 4GB LPDDR4X / 32GB eMMC)
  2. Planta Piloto Original (ESP32-S3 RTOS 2.0 + Arduino Nano/UNO)

Características de Ingeniería:
  - Ruteador A* Octilinear en 2 Capas (F.Cu y B.Cu) con restricción estricta de
    giro a 45° (ángulo interior de 135°, CERO ángulos rectos de 90°).
  - Inserción automática de Vías pasantes (0.75 mm pad / 0.35 mm drill) para
    cambios de capa y conexión de componentes SMD a planos de tierra en B.Cu.
  - Verificación geométrica exacta de márgenes (Clearance >= 0.24 mm) contra
    todos los pads, pistas previas, vías, bordes de placa y zonas Keep-Out RF.
  - Soporte nativo para modelos 3D STEP compuestos (ej. MOSFETs TO-220 con
    disipadores extruidos aletados AAVID 34.9x12.7x25.4 mm y resistencias de
    bloque cerámico de cemento blanco de 10W 1.0 Ohm).
================================================================================
"""

import csv
import heapq
import json
import math
import os
import re
import subprocess
import zipfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

KICAD_CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
KICAD_FP_DIR = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"

# 8 direcciones octilineares (en sentido horario desde Este = 0°):
# 0: E (+1,0), 1: SE (+1,+1), 2: S (0,+1), 3: SW (-1,+1),
# 4: W (-1,0), 5: NW (-1,-1), 6: N (0,-1), 7: NE (+1,-1)
DIRS_8: List[Tuple[int, int, float]] = [
    (1, 0, 1.0),
    (1, 1, math.sqrt(2.0)),
    (0, 1, 1.0),
    (-1, 1, math.sqrt(2.0)),
    (-1, 0, 1.0),
    (-1, -1, math.sqrt(2.0)),
    (0, -1, 1.0),
    (1, -1, math.sqrt(2.0)),
]


@dataclass
class PadInfo:
    ref: str
    pad_num: str
    x: float
    y: float
    rx: float
    ry: float
    net_id: int
    net_name: str
    is_smd: bool
    drill: float = 0.0


@dataclass
class TrackSeg:
    x1: float
    y1: float
    x2: float
    y2: float
    width: float
    layer: str  # "F.Cu" o "B.Cu"
    net_id: int


@dataclass
class ViaItem:
    x: float
    y: float
    size: float
    drill: float
    net_id: int


def rotar_punto(dx: float, dy: float, rot_deg: float) -> Tuple[float, float]:
    rad = math.radians(rot_deg)
    c = math.cos(rad)
    s = math.sin(rad)
    return (dx * c + dy * s, -dx * s + dy * c)


def dist_punto_segmento(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    dx = x2 - x1
    dy = y2 - y1
    l2 = dx * dx + dy * dy
    if l2 < 1e-10:
        return math.hypot(px - x1, py - y1)
    t = ((px - x1) * dx + (py - y1) * dy) / l2
    t = max(0.0, min(1.0, t))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def orient2d(ax: float, ay: float, bx: float, by: float, cx: float, cy: float) -> float:
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


def segmentos_se_cruzan(
    ax: float, ay: float, bx: float, by: float,
    cx: float, cy: float, dx: float, dy: float
) -> bool:
    o1 = orient2d(ax, ay, bx, by, cx, cy)
    o2 = orient2d(ax, ay, bx, by, dx, dy)
    o3 = orient2d(cx, cy, dx, dy, ax, ay)
    o4 = orient2d(cx, cy, dx, dy, bx, by)
    if ((o1 > 0 and o2 < 0) or (o1 < 0 and o2 > 0)) and ((o3 > 0 and o4 < 0) or (o3 < 0 and o4 > 0)):
        return True
    return False


def dist_segmento_segmento(
    ax: float, ay: float, bx: float, by: float,
    cx: float, cy: float, dx: float, dy: float
) -> float:
    if segmentos_se_cruzan(ax, ay, bx, by, cx, cy, dx, dy):
        return 0.0
    return min(
        dist_punto_segmento(ax, ay, cx, cy, dx, dy),
        dist_punto_segmento(bx, by, cx, cy, dx, dy),
        dist_punto_segmento(cx, cy, ax, ay, bx, by),
        dist_punto_segmento(dx, dy, ax, ay, bx, by),
    )


def dist_segmento_rect(
    x1: float, y1: float, x2: float, y2: float,
     cx: float, cy: float, rx: float, ry: float
) -> float:
    """Distancia mínima desde un segmento (x1,y1)-(x2,y2) a una caja [cx-rx, cx+rx] x [cy-ry, cy+ry]."""
    # Rápido chequeo de bounding box
    min_x, max_x = (x1, x2) if x1 < x2 else (x2, x1)
    min_y, max_y = (y1, y2) if y1 < y2 else (y2, y1)
    if max_x < cx - rx and min_y > cy - ry and max_y < cy + ry:
        return (cx - rx) - max_x
    # Si un extremo cae dentro de la caja
    if (cx - rx <= x1 <= cx + rx and cy - ry <= y1 <= cy + ry) or (
        cx - rx <= x2 <= cx + rx and cy - ry <= y2 <= cy + ry
    ):
        return 0.0
    # Distancia a los 4 bordes del rectángulo
    xL, xR = cx - rx, cx + rx
    yT, yB = cy - ry, cy + ry
    return min(
        dist_segmento_segmento(x1, y1, x2, y2, xL, yT, xR, yT),
        dist_segmento_segmento(x1, y1, x2, y2, xR, yT, xR, yB),
        dist_segmento_segmento(x1, y1, x2, y2, xR, yB, xL, yB),
        dist_segmento_segmento(x1, y1, x2, y2, xL, yB, xL, yT),
    )


def clasificar_direccion_octilinear(dx: float, dy: float) -> Optional[int]:
    """Si (dx, dy) apunta en una de las 8 direcciones octilineares (0°, 45°, 90°...), devuelve 0..7."""
    length = math.hypot(dx, dy)
    if length < 1e-5:
        return None
    ux, uy = dx / length, dy / length
    for idx, (vx, vy, step_len) in enumerate(DIRS_8):
        nvx, nvy = vx / step_len, vy / step_len
        if ux * nvx + uy * nvy > 0.9995:
            return idx
    return None


def giro_valido_45(d1: int, d2: int) -> bool:
    """Retorna True si el cambio de dirección entre d1 y d2 es 0° (recto) o 45° (obtuso 135°)."""
    diff = abs(d1 - d2) % 8
    if diff > 4:
        diff = 8 - diff
    return diff <= 1


def construir_chamfer_45(
    x1: float, y1: float, x2: float, y2: float, diag_primero: bool = True
) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """
    Conecta (x1, y1) con (x2, y2) usando a lo sumo 2 segmentos octilineares (recto + diagonal 45°),
    garantizando que NUNCA exista un ángulo de 90°.
    """
    dx = x2 - x1
    dy = y2 - y1
    if math.hypot(dx, dy) < 1e-4:
        return []
    adx = abs(dx)
    ady = abs(dy)
    if adx < 1e-4 or ady < 1e-4 or abs(adx - ady) < 1e-4:
        return [((x1, y1), (x2, y2))]

    sx = 1.0 if dx > 0 else -1.0
    sy = 1.0 if dy > 0 else -1.0
    d = min(adx, ady)

    if adx > ady:
        if diag_primero:
            mx, my = x1 + sx * d, y2
        else:
            mx, my = x2 - sx * d, y1
    else:
        if diag_primero:
            mx, my = x2, y1 + sy * d
        else:
            mx, my = x1, y2 - sy * d

    return [((x1, y1), (mx, my)), ((mx, my), (x2, y2))]


class PCBAIndustrialDesigner:
    def __init__(self, board_w: float, board_h: float, step: float = 0.50):
        self.board_w = board_w
        self.board_h = board_h
        self.step = step
        self.nx = int(round(board_w / step)) + 1
        self.ny = int(round(board_h / step)) + 1

        self.nets: Dict[str, int] = {"": 0}
        self.footprints_sexpr: List[str] = []
        self.pads_by_ref: Dict[str, Dict[str, List[PadInfo]]] = {}
        self.all_pads: List[PadInfo] = []
        self.pads_by_net: Dict[int, List[PadInfo]] = {}

        self.tracks: List[TrackSeg] = []
        self.vias: List[ViaItem] = []
        self.zones_sexpr: List[str] = []
        self.keepout_rects: List[Tuple[float, float, float, float]] = []
        self.edge_slots: List[Tuple[float, float, float, float]] = []

        self.bom_items: List[Dict[str, str]] = []
        self.cpl_items: List[Dict[str, str]] = []

    def get_net_id(self, net_name: str) -> int:
        if not net_name:
            return 0
        if net_name not in self.nets:
            self.nets[net_name] = len(self.nets)
        return self.nets[net_name]

    def add_keepout_rf(self, x1: float, y1: float, x2: float, y2: float):
        """Agrega zona de vaciado de cobre para antena RF y bloquea ruteo dentro de ella."""
        self.keepout_rects.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
        self.zones_sexpr.append(
            f"\t(zone\n"
            f"\t\t(net 0)\n"
            f'\t\t(net_name "")\n'
            f'\t\t(layers "F.Cu" "B.Cu")\n'
            f"\t\t(hatch edge 0.5)\n"
            f"\t\t(connect_pads (clearance 0))\n"
            f"\t\t(min_thickness 0.25)\n"
            f"\t\t(keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed) (copperpour not_allowed) (footprints allowed))\n"
            f"\t\t(fill (thermal_gap 0.3) (thermal_bridge_width 0.3))\n"
            f"\t\t(polygon (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f}) (xy {x1:.2f} {y2:.2f})))\n"
            f"\t)"
        )

    def add_isolation_slot(self, x1: float, y1: float, x2: float, y2: float):
        """Agrega ranura fresada de aislamiento galvánico en Edge.Cuts."""
        self.edge_slots.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))

    def add_copper_zone(
        self, net_name: str, layer: str, x1: float, y1: float, x2: float, y2: float,
        clearance: float = 0.35, priority: int = 1
    ):
        nid = self.get_net_id(net_name)
        # Registro geométrico de zonas (usado para validar vías de cosido a planos)
        if not hasattr(self, "zone_rects"):
            self.zone_rects = []
        self.zone_rects.append((nid, layer, min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
        self.zones_sexpr.append(
            f"\t(zone\n"
            f"\t\t(net {nid})\n"
            f'\t\t(net_name "{net_name}")\n'
            f'\t\t(layer "{layer}")\n'
            f"\t\t(hatch edge 0.5)\n"
            f"\t\t(priority {priority})\n"
            f"\t\t(connect_pads (clearance {clearance:.2f}))\n"
            f"\t\t(min_thickness 0.20)\n"
            f"\t\t(filled_areas_thickness no)\n"
            f"\t\t(fill yes (thermal_gap 0.35) (thermal_bridge_width 0.35) (island_removal_mode 0))\n"
            f"\t\t(polygon (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f}) (xy {x1:.2f} {y2:.2f})))\n"
            f"\t)"
        )

    def add_component(
        self,
        lib_pretty: str,
        mod_name: str,
        ref: str,
        val: str,
        lcsc: str,
        desc: str,
        fx: float,
        fy: float,
        rot_deg: float,
        pad_nets: Dict[str, str],
        attach_to220_heatsink: bool = False,
        in_bom: bool = True,
    ):
        ruta_mod = os.path.join(KICAD_FP_DIR, f"{lib_pretty}.pretty", f"{mod_name}.kicad_mod")
        with open(ruta_mod, "r", encoding="utf-8") as f:
            raw = f.read()

        raw = re.sub(r"\s*\(version\s+\d+\)", "", raw, count=1)
        raw = re.sub(r'\s*\(generator\s+"[^"]+"\)', "", raw, count=1)
        raw = re.sub(r'\s*\(generator_version\s+"[^"]+"\)', "", raw, count=1)

        header_new = f'(footprint "{lib_pretty}:{mod_name}"\n\t(layer "F.Cu")\n\t(at {fx:.4f} {fy:.4f} {rot_deg:.1f})\n\t(clearance 0.14)'
        raw = re.sub(
            r'\(footprint\s+"[^"]+"\s*\(layer\s+"F\.Cu"\)',
            header_new,
            count=1,
            string=raw,
        )

        raw = re.sub(r'\(property\s+"Reference"\s+"[^"]+"', f'(property "Reference" "{ref}"', raw, count=1)
        raw = re.sub(r'\(property\s+"Value"\s+"[^"]+"', f'(property "Value" "{val}"', raw, count=1)

        # Mover Reference de F.SilkS a F.Fab si puede solaparse con pads/pistas, y agregar texto limpio
        lineas = raw.splitlines()
        nuevas_lineas: List[str] = []
        en_pad = False
        en_prop_ref = False
        nivel_pad = 0
        pad_actual = ""
        pad_is_smd = False
        pad_dx = 0.0
        pad_dy = 0.0
        pad_sx = 1.0
        pad_sy = 1.0
        pad_drill = 0.0

        self.pads_by_ref[ref] = {}

        for lin in lineas:
            if '(property "Reference"' in lin:
                en_prop_ref = True
            if en_prop_ref and '(effects' in lin:
                lin = "\t\t(hide yes)\n" + lin
                en_prop_ref = False

            m_pad = re.match(r'^\s*\(pad\s+"([^"]*)"\s+(\S+)', lin)
            if m_pad and not en_pad:
                en_pad = True
                pad_actual = m_pad.group(1)
                ptype = m_pad.group(2)
                pad_is_smd = (ptype == "smd")
                nivel_pad = lin.count("(") - lin.count(")")
                pad_dx, pad_dy = 0.0, 0.0
                pad_sx, pad_sy = 1.0, 1.0
                pad_drill = 0.0
                nuevas_lineas.append(lin)
                continue

            if en_pad:
                m_at = re.match(r"^\s*\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)", lin)
                if m_at:
                    pad_dx = float(m_at.group(1))
                    pad_dy = float(m_at.group(2))
                    pad_r = float(m_at.group(3)) if m_at.group(3) else 0.0
                    total_r = (pad_r + rot_deg) % 360.0
                    lin = f"\t\t(at {pad_dx:.4f} {pad_dy:.4f} {total_r:.1f})"

                m_sz = re.match(r"^\s*\(size\s+([-\d.]+)\s+([-\d.]+)\)", lin)
                if m_sz:
                    pad_sx = float(m_sz.group(1))
                    pad_sy = float(m_sz.group(2))

                m_dr = re.match(r"^\s*\(drill\s+(?:oval\s+)?([-\d.]+)", lin)
                if m_dr:
                    pad_drill = float(m_dr.group(1))

                delta_par = lin.count("(") - lin.count(")")
                if nivel_pad + delta_par == 0 and lin.strip() == ")":
                    if pad_actual != "":
                        gx, gy = rotar_punto(pad_dx, pad_dy, rot_deg)
                        px, py = fx + gx, fy + gy
                        # Calcular semianchos rotados del pad
                        rad = math.radians(rot_deg)
                        rx = (abs(pad_sx * math.cos(rad)) + abs(pad_sy * math.sin(rad))) / 2.0
                        ry = (abs(pad_sx * math.sin(rad)) + abs(pad_sy * math.cos(rad))) / 2.0

                        net_name = pad_nets.get(pad_actual, "")
                        nid = self.get_net_id(net_name)
                        if nid > 0:
                            nuevas_lineas.append(f'\t\t(net {nid} "{net_name}")')

                        pinfo = PadInfo(
                            ref=ref,
                            pad_num=pad_actual,
                            x=px,
                            y=py,
                            rx=rx,
                            ry=ry,
                            net_id=nid,
                            net_name=net_name,
                            is_smd=pad_is_smd,
                            drill=pad_drill,
                        )
                        self.pads_by_ref[ref].setdefault(pad_actual, []).append(pinfo)
                        self.all_pads.append(pinfo)
                        if nid > 0:
                            self.pads_by_net.setdefault(nid, []).append(pinfo)
                    en_pad = False
                else:
                    nivel_pad += delta_par
                nuevas_lineas.append(lin)
            else:
                nuevas_lineas.append(lin)

        bloque_fp = "\n".join(nuevas_lineas)
        idx_close = bloque_fp.rfind(")")
        extra_str = (
            f'\t(property "LCSC" "{lcsc}"\n'
            f"\t\t(at 0 0 0)\n"
            f'\t\t(layer "F.Fab")\n'
            f"\t\t(hide yes)\n"
            f"\t\t(effects (font (size 1 1) (thickness 0.15)))\n"
            f"\t)\n"
        )
        if attach_to220_heatsink:
            # Adjuntar modelo 3D STEP de disipador vertical compacto para TO-220 (14.0x8.9mm, H=25.4mm)
            # Escalado proporcionalmente para evitar colisiones de aletas y respetar aislamiento dieléctrico
            extra_str += (
                f'\t(model "${{KICAD10_3DMODEL_DIR}}/Heatsink.3dshapes/Heatsink_AAVID_Extruded_531002B02500G_34.9x12.7mm_H25.4mm.step"\n'
                f"\t\t(offset (xyz 2.54 2.8 0))\n"
                f"\t\t(scale (xyz 0.40 0.70 1.0))\n"
                f"\t\t(rotate (xyz 0 0 0))\n"
                f"\t)\n"
            )
        bloque_fp = bloque_fp[:idx_close] + extra_str + ")\n"
        self.footprints_sexpr.append(bloque_fp)

        if in_bom and lcsc != "N/A":
            self.bom_items.append({
                "Comment": val,
                "Designator": ref,
                "Footprint": mod_name,
                "LCSC Part #": lcsc,
                "Description": desc,
            })
            self.cpl_items.append({
                "Designator": ref,
                "Val": val,
                "Package": mod_name,
                "Mid X": f"{fx:.2f}mm",
                "Mid Y": f"{self.board_h - fy:.2f}mm",
                "Rotation": f"{rot_deg:.1f}",
                "Layer": "top",
            })

    # ==========================================================================
    # VERIFICADOR GEOMÉTRICO DE COLISIONES Y MÁRGENES DRC
    # ==========================================================================
    def segmento_libre_drc(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        layer: str,
        width: float,
        net_id: int,
        clearance: float = 0.23,
    ) -> bool:
        """Verifica que un segmento (x1,y1)->(x2,y2) en `layer` cumpla todas las reglas DRC."""
        hw = width / 2.0
        margin_edge = hw + 0.55
        if (
            min(x1, x2) < margin_edge
            or max(x1, x2) > self.board_w - margin_edge
            or min(y1, y2) < margin_edge
            or max(y1, y2) > self.board_h - margin_edge
        ):
            return False

        # Verificar ranuras de aislamiento Edge.Cuts
        for sx1, sy1, sx2, sy2 in self.edge_slots:
            cx, cy = (sx1 + sx2) / 2.0, (sy1 + sy2) / 2.0
            rx, ry = (sx2 - sx1) / 2.0, (sy2 - sy1) / 2.0
            if dist_segmento_rect(x1, y1, x2, y2, cx, cy, rx, ry) < margin_edge:
                return False

        # Verificar zonas Keep-Out RF
        for kx1, ky1, kx2, ky2 in self.keepout_rects:
            cx, cy = (kx1 + kx2) / 2.0, (ky1 + ky2) / 2.0
            rx, ry = (kx2 - kx1) / 2.0, (ky2 - ky1) / 2.0
            if dist_segmento_rect(x1, y1, x2, y2, cx, cy, rx, ry) < hw + 0.25:
                return False

        s_min_x = (x1 if x1 < x2 else x2) - hw - clearance
        s_max_x = (x2 if x1 < x2 else x1) + hw + clearance
        s_min_y = (y1 if y1 < y2 else y2) - hw - clearance
        s_max_y = (y2 if y1 < y2 else y1) + hw + clearance

        # Verificar distancia a todos los pads de distinta red en la misma capa
        for p in self.all_pads:
            if p.net_id == net_id:
                continue
            if layer != "F.Cu" and p.is_smd:
                continue
            if p.x + p.rx < s_min_x or p.x - p.rx > s_max_x or p.y + p.ry < s_min_y or p.y - p.ry > s_max_y:
                continue
            # En encapsulados de paso fino (MSOP-10 de 0.5mm con ry <= 0.20mm), permitir margen JLCPCB de 0.13mm
            c_pad = 0.13 if min(p.rx, p.ry) < 0.22 else clearance
            req = hw + c_pad
            if dist_segmento_rect(x1, y1, x2, y2, p.x, p.y, p.rx, p.ry) < req:
                return False

        # Verificar distancia a todas las vías de distinta red
        for v in self.vias:
            if v.net_id == net_id:
                continue
            vr = v.size / 2.0
            if v.x + vr < s_min_x or v.x - vr > s_max_x or v.y + vr < s_min_y or v.y - vr > s_max_y:
                continue
            req = hw + vr + clearance
            if dist_punto_segmento(v.x, v.y, x1, y1, x2, y2) < req:
                return False

        # Verificar distancia a todas las pistas ya colocadas en la misma capa
        for tr in self.tracks:
            if tr.layer != layer or tr.net_id == net_id:
                continue
            thw = tr.width / 2.0
            if (
                max(tr.x1, tr.x2) + thw < s_min_x
                or min(tr.x1, tr.x2) - thw > s_max_x
                or max(tr.y1, tr.y2) + thw < s_min_y
                or min(tr.y1, tr.y2) - thw > s_max_y
            ):
                continue
            req = hw + thw + clearance
            if dist_segmento_segmento(x1, y1, x2, y2, tr.x1, tr.y1, tr.x2, tr.y2) < req:
                return False

        return True

    def via_libre_drc(
        self, vx: float, vy: float, net_id: int, size: float = 0.75, drill: float = 0.35, clearance: float = 0.24
    ) -> bool:
        """Verifica que una vía en (vx, vy) sea legal en F.Cu y B.Cu y no caiga sobre ningún pad."""
        vr = size / 2.0
        margin_edge = vr + 0.55
        if (
            vx < margin_edge
            or vx > self.board_w - margin_edge
            or vy < margin_edge
            or vy > self.board_h - margin_edge
        ):
            return False

        for sx1, sy1, sx2, sy2 in self.edge_slots:
            if (sx1 - margin_edge <= vx <= sx2 + margin_edge) and (sy1 - margin_edge <= vy <= sy2 + margin_edge):
                return False

        for kx1, ky1, kx2, ky2 in self.keepout_rects:
            if (kx1 - vr <= vx <= kx2 + vr) and (ky1 - vr <= vy <= ky2 + vr):
                return False

        # No permitir vía encima de ningún pad (ni siquiera de la misma red, para evitar via-in-pad / hole_to_hole)
        for p in self.all_pads:
            req = vr + clearance
            if (p.x - p.rx - req <= vx <= p.x + p.rx + req) and (p.y - p.ry - req <= vy <= p.y + p.ry + req):
                return False

        # No permitir vía cerca de otra vía
        for v in self.vias:
            req = vr + (v.size / 2.0) + (0.25 if v.net_id == net_id else clearance)
            if math.hypot(vx - v.x, vy - v.y) < req:
                return False

        v_min_x = vx - vr - clearance - 1.5
        v_max_x = vx + vr + clearance + 1.5
        v_min_y = vy - vr - clearance - 1.5
        v_max_y = vy + vr + clearance + 1.5

        # No permitir vía encima de pistas de otra red en F.Cu ni en B.Cu
        for tr in self.tracks:
            if tr.net_id == net_id:
                continue
            if (
                max(tr.x1, tr.x2) < v_min_x
                or min(tr.x1, tr.x2) > v_max_x
                or max(tr.y1, tr.y2) < v_min_y
                or min(tr.y1, tr.y2) > v_max_y
            ):
                continue
            req = vr + (tr.width / 2.0) + clearance
            if dist_punto_segmento(vx, vy, tr.x1, tr.y1, tr.x2, tr.y2) < req:
                return False

        return True

    # ==========================================================================
    # PORTALES DE ESCAPE DE PADS A LA REJILLA DE 0.50 mm (CON GEOMETRÍA 45°)
    # ==========================================================================
    def obtener_portales_pad(
        self, pad: PadInfo, width: float
    ) -> List[Tuple[int, int, int, Optional[int], List[TrackSeg]]]:
        """
        Genera candidatos de conexión desde el centro exacto del pad (pad.x, pad.y)
        hacia nodos cercanos (gx, gy, layer_idx) de la rejilla de 0.50 mm, usando
        segmentos estrictamente octilineares (45°/0°) y validando DRC.
        Retorna lista de (ix, iy, layer_idx, dir_llegada, lista_TrackSeg).
        """
        capas_pad = [0] if pad.is_smd else [0, 1]
        # Si es un pad fino (ej. MSOP-10 de 0.5mm pitch con ry <= 0.20mm), usar cuello de botella de 0.20mm en el escape
        w_stub = min(width, 0.20) if min(pad.rx, pad.ry) < 0.22 else min(width, 0.40)

        ix0 = int(round(pad.x / self.step))
        iy0 = int(round(pad.y / self.step))

        candidatos: List[Tuple[float, int, int, int, Optional[int], List[TrackSeg]]] = []

        for r_grid in range(0, 5):
            for dx_i in range(-r_grid, r_grid + 1):
                for dy_i in range(-r_grid, r_grid + 1):
                    if max(abs(dx_i), abs(dy_i)) != r_grid:
                        continue
                    ix = ix0 + dx_i
                    iy = iy0 + dy_i
                    if not (1 <= ix < self.nx - 1 and 1 <= iy < self.ny - 1):
                        continue
                    gx = ix * self.step
                    gy = iy * self.step

                    for l_idx in capas_pad:
                        lname = "F.Cu" if l_idx == 0 else "B.Cu"
                        if math.hypot(gx - pad.x, gy - pad.y) < 1e-4:
                            candidatos.append((0.0, ix, iy, l_idx, None, []))
                            continue

                        for diag_first in (True, False):
                            segs_pts = construir_chamfer_45(pad.x, pad.y, gx, gy, diag_primero=diag_first)
                            if not segs_pts:
                                continue
                            ok = True
                            t_list: List[TrackSeg] = []
                            last_dir: Optional[int] = None
                            for (ax, ay), (bx, by) in segs_pts:
                                if math.hypot(bx - ax, by - ay) < 1e-4:
                                    continue
                                d_seg = clasificar_direccion_octilinear(bx - ax, by - ay)
                                if d_seg is None:
                                    ok = False
                                    break
                                if last_dir is not None and not giro_valido_45(last_dir, d_seg):
                                    ok = False
                                    break
                                if not self.segmento_libre_drc(ax, ay, bx, by, lname, w_stub, pad.net_id, clearance=0.20):
                                    ok = False
                                    break
                                last_dir = d_seg
                                t_list.append(TrackSeg(ax, ay, bx, by, w_stub, lname, pad.net_id))
                            if ok and t_list:
                                dist_c = math.hypot(gx - pad.x, gy - pad.y)
                                candidatos.append((dist_c, ix, iy, l_idx, last_dir, t_list))
            if len(candidatos) >= 6:
                break

        candidatos.sort(key=lambda item: item[0])
        return [(ix, iy, l_idx, ldir, tlist) for (_, ix, iy, l_idx, ldir, tlist) in candidatos[:12]]

    # ==========================================================================
    # AUTOROUTER A* OCTILINEAR 45° EN 4 CAPAS (F.Cu, In1.Cu, In2.Cu, B.Cu)
    # ==========================================================================
    # Mapa de índices de capa para el autorouter:
    #   0 -> "F.Cu"   (Capa superior: componentes SMD/PTH, alta corriente DC y fanout corto)
    #   1 -> "In2.Cu" (Capa interna 2: ruteo limpio 45° de señales y buses sin obstáculos SMD)
    #   2 -> "B.Cu"   (Capa inferior: ruteo secundario 45°, etapa AC y planos de refuerzo)
    #   3 -> "In1.Cu" (Capa interna 1: planos de referencia sólidos AGND/DGND/PGND en estrella)
    CAPAS_RUTEO = ["F.Cu", "In2.Cu", "B.Cu", "In1.Cu"]

    def rutear_par_pads(self, pad_src: PadInfo, pad_dst: PadInfo, width: float) -> bool:
        """
        Encuentra y registra la ruta óptima 45° libre de obstáculos entre pad_src y pad_dst
        usando búsqueda A* octilinear en 4 capas sobre (ix, iy, layer_idx, dir_in).
        """
        nid = pad_src.net_id
        es_tierra = pad_src.net_name in ("AGND", "DGND", "PGND")
        capas_permitidas = [0, 1, 2, 3] if es_tierra else [0, 1, 2]

        # Intento 0: conexión directa a 45° (en F.Cu solo para tramos cortos locales <= 9.5 mm
        # para que los buses largos usen A* en 4 capas por In2.Cu/B.Cu sin bloquear pines SMD vecinos)
        dist_pads = math.hypot(pad_dst.x - pad_src.x, pad_dst.y - pad_src.y)
        if pad_src.is_smd or pad_dst.is_smd:
            capas_comunes = ["F.Cu"] if dist_pads <= 9.5 else []
        else:
            capas_comunes = ["F.Cu", "In2.Cu", "B.Cu"] if dist_pads <= 9.5 else ["In2.Cu", "B.Cu"]
        for lname in capas_comunes:
            for diag_first in (True, False):
                segs_pts = construir_chamfer_45(pad_src.x, pad_src.y, pad_dst.x, pad_dst.y, diag_primero=diag_first)
                if not segs_pts:
                    continue
                ok = True
                prev_d: Optional[int] = None
                cand_tracks: List[TrackSeg] = []
                for (ax, ay), (bx, by) in segs_pts:
                    if math.hypot(bx - ax, by - ay) < 1e-4:
                        continue
                    d_curr = clasificar_direccion_octilinear(bx - ax, by - ay)
                    if d_curr is None or (prev_d is not None and not giro_valido_45(prev_d, d_curr)):
                        ok = False
                        break
                    if not self.segmento_libre_drc(ax, ay, bx, by, lname, width, nid):
                        ok = False
                        break
                    prev_d = d_curr
                    cand_tracks.append(TrackSeg(ax, ay, bx, by, width, lname, nid))
                if ok and cand_tracks:
                    self.tracks.extend(cand_tracks)
                    return True

        # Portales de salida (src) y de llegada (dst)
        portales_src = self.ajustar_portales_pad_mejorado(pad_src, width)
        portales_dst = self.ajustar_portales_pad_mejorado(pad_dst, width)
        if not portales_src or not portales_dst:
            return False

        # Mapa de metas: (ix, iy, l_idx) -> lista de (dir_stub_dst, stub_tracks_dst)
        metas: Dict[Tuple[int, int, int], List[Tuple[Optional[int], List[TrackSeg]]]] = {}
        for ix, iy, l_idx, ldir, tlist in portales_dst:
            if tlist:
                first_seg = tlist[-1]
                d_to_pad = clasificar_direccion_octilinear(first_seg.x1 - first_seg.x2, first_seg.y1 - first_seg.y2)
            else:
                d_to_pad = None
            metas.setdefault((ix, iy, l_idx), []).append((d_to_pad, tlist))

        tx_avg = pad_dst.x / self.step
        ty_avg = pad_dst.y / self.step

        def heuristica(ix: int, iy: int) -> float:
            dx = abs(ix - tx_avg)
            dy = abs(iy - ty_avg)
            return (max(dx, dy) - min(dx, dy)) + min(dx, dy) * math.sqrt(2.0)

        # Estado A*: (ix, iy, l_idx, dir_in) donde dir_in es 0..7 o -1 (sin dirección previa, ej. tras vía)
        pq: List[Tuple[float, float, int, int, int, int, int]] = []
        g_best: Dict[Tuple[int, int, int, int], float] = {}
        parent: Dict[Tuple[int, int, int, int], Tuple[Optional[Tuple[int, int, int, int]], int]] = {}
        portal_init_tracks: List[List[TrackSeg]] = []

        for idx_p, (ix, iy, l_idx, ldir, tlist) in enumerate(portales_src):
            d_state = ldir if ldir is not None else -1
            state = (ix, iy, l_idx, d_state)
            g0 = len(tlist) * 0.5
            if state not in g_best or g0 < g_best[state]:
                g_best[state] = g0
                t_idx = len(portal_init_tracks)
                parent[state] = (None, t_idx)
                portal_init_tracks.append(tlist)
                heapq.heappush(pq, (g0 + 1.35 * heuristica(ix, iy), g0, ix, iy, l_idx, d_state, t_idx))

        # Cache de validez de segmentos de rejilla y vías durante esta búsqueda A*
        seg_cache: Dict[Tuple[int, int, int, int], bool] = {}
        via_cache: Dict[Tuple[int, int], bool] = {}

        max_iters = 85000
        iters = 0

        while pq and iters < max_iters:
            iters += 1
            f_val, g_val, ix, iy, l_idx, d_in, p_idx = heapq.heappop(pq)
            state = (ix, iy, l_idx, d_in)
            if g_val > g_best.get(state, 1e18) + 1e-6:
                continue

            # ¿Llegamos a un portal meta?
            if (ix, iy, l_idx) in metas:
                for d_to_pad, dst_tlist in metas[(ix, iy, l_idx)]:
                    if d_in == -1 or d_to_pad is None or giro_valido_45(d_in, d_to_pad):
                        # Reconstruir camino
                        nodos_camino: List[Tuple[int, int, int, int]] = []
                        curr: Optional[Tuple[int, int, int, int]] = state
                        init_idx = 0
                        while curr is not None:
                            nodos_camino.append(curr)
                            prev_c, idx_portal = parent[curr]
                            if prev_c is None:
                                init_idx = idx_portal
                            curr = prev_c
                        nodos_camino.reverse()

                        # Emitir segmentos del portal de salida
                        nuevos_tracks: List[TrackSeg] = list(portal_init_tracks[init_idx])
                        nuevas_vias: List[ViaItem] = []

                        # Emitir segmentos de la rejilla y vías
                        for k in range(len(nodos_camino) - 1):
                            xA, yA, lA, _ = nodos_camino[k]
                            xB, yB, lB, _ = nodos_camino[k + 1]
                            if lA != lB:
                                nuevas_vias.append(ViaItem(xA * self.step, yA * self.step, 0.75, 0.35, nid))
                            elif xA != xB or yA != yB:
                                lname = self.CAPAS_RUTEO[lA]
                                nuevos_tracks.append(
                                    TrackSeg(
                                        xA * self.step,
                                        yA * self.step,
                                        xB * self.step,
                                        yB * self.step,
                                        width,
                                        lname,
                                        nid,
                                    )
                                )

                        # Emitir segmentos del portal de llegada (invertidos para ir hacia pad_dst)
                        for seg in reversed(dst_tlist):
                            nuevos_tracks.append(
                                TrackSeg(seg.x2, seg.y2, seg.x1, seg.y1, seg.width, seg.layer, seg.net_id)
                            )

                        self.tracks.extend(self._simplificar_colineales(nuevos_tracks))
                        for nv in nuevas_vias:
                            if not any(math.hypot(v.x - nv.x, v.y - nv.y) < 0.30 for v in self.vias):
                                self.vias.append(nv)
                        return True

            # 1. Expandir en las 8 direcciones octilineares (respetando restricción de giro <= 45°)
            for d_out, (dx_i, dy_i, step_cost) in enumerate(DIRS_8):
                if d_in != -1 and not giro_valido_45(d_in, d_out):
                    continue
                nx, ny = ix + dx_i, iy + dy_i
                if not (1 <= nx < self.nx - 1 and 1 <= ny < self.ny - 1):
                    continue

                ckey = (ix, iy, l_idx, d_out)
                if ckey not in seg_cache:
                    lname = self.CAPAS_RUTEO[l_idx]
                    seg_cache[ckey] = self.segmento_libre_drc(
                        ix * self.step,
                        iy * self.step,
                        nx * self.step,
                        ny * self.step,
                        lname,
                        width,
                        nid,
                    )
                if not seg_cache[ckey]:
                    continue

                turn_penalty = 0.0 if (d_in == -1 or d_in == d_out) else 0.80
                layer_bias = 0.0 if l_idx == 0 else (-0.04 if l_idx == 1 else 0.0)
                ng = g_val + step_cost + turn_penalty + layer_bias
                nstate = (nx, ny, l_idx, d_out)
                if ng < g_best.get(nstate, 1e18):
                    g_best[nstate] = ng
                    parent[nstate] = (state, p_idx)
                    heapq.heappush(pq, (ng + 1.35 * heuristica(nx, ny), ng, nx, ny, l_idx, d_out, p_idx))

            # 2. Expandir mediante una Vía pasante hacia cualquiera de las otras capas del stackup de 4 capas
            vkey = (ix, iy)
            if vkey not in via_cache:
                via_cache[vkey] = self.via_libre_drc(ix * self.step, iy * self.step, nid)
            if via_cache[vkey]:
                for nl_idx in capas_permitidas:
                    if nl_idx == l_idx:
                        continue
                    ng = g_val + 5.5
                    nstate = (ix, iy, nl_idx, -1)
                    if ng < g_best.get(nstate, 1e18):
                        g_best[nstate] = ng
                        parent[nstate] = (state, p_idx)
                        heapq.heappush(pq, (ng + 1.35 * heuristica(ix, iy), ng, ix, iy, nl_idx, -1, p_idx))

        return False

    def _simplificar_colineales(self, segs: List[TrackSeg]) -> List[TrackSeg]:
        """Fusiona segmentos consecutivos que comparten capa, ancho y dirección octilinear."""
        if not segs:
            return []
        out: List[TrackSeg] = [segs[0]]
        for s in segs[1:]:
            prev = out[-1]
            if (
                prev.layer == s.layer
                and abs(prev.width - s.width) < 1e-4
                and prev.net_id == s.net_id
                and math.hypot(prev.x2 - s.x1, prev.y2 - s.y1) < 1e-4
            ):
                d1 = clasificar_direccion_octilinear(prev.x2 - prev.x1, prev.y2 - prev.y1)
                d2 = clasificar_direccion_octilinear(s.x2 - s.x1, s.y2 - s.y1)
                if d1 is not None and d1 == d2:
                    out[-1] = TrackSeg(prev.x1, prev.y1, s.x2, s.y2, prev.width, prev.layer, prev.net_id)
                    continue
            out.append(s)
        return out

    def conectar_fanout_tierra_smd(self, net_name: str, width: float = 0.45):
        """
        Para cada pad SMD perteneciente a un plano de tierra (AGND, DGND, PGND),
        coloca una Vía pasante cercana (F.Cu -> In1.Cu / B.Cu) con un segmento corto a 45°
        para que conecte directamente al plano sólido de tierra en In1.Cu y B.Cu.
        """
        nid = self.get_net_id(net_name)
        pads = self.pads_by_net.get(nid, [])

        def via_sobre_plano_propio(vx: float, vy: float) -> bool:
            # La vía solo es útil si cae dentro de un plano de su misma red (margen 1.0 mm)
            for z_nid, _zl, zx1, zy1, zx2, zy2 in getattr(self, "zone_rects", []):
                if z_nid == nid and zx1 + 1.0 <= vx <= zx2 - 1.0 and zy1 + 1.0 <= vy <= zy2 - 1.0:
                    return True
            return False

        for p in pads:
            if not p.is_smd:
                continue
            if not via_sobre_plano_propio(p.x, p.y):
                continue
            portales = self.ajustar_portales_pad_mejorado(p, width)
            conectado = False
            for ix, iy, l_idx, _, tlist in portales:
                if not tlist:
                    continue
                vx, vy = ix * self.step, iy * self.step
                if via_sobre_plano_propio(vx, vy) and self.via_libre_drc(vx, vy, nid):
                    self.tracks.extend(tlist)
                    self.vias.append(ViaItem(vx, vy, 0.75, 0.35, nid))
                    conectado = True
                    break
            if not conectado:
                ix0, iy0 = int(round(p.x / self.step)), int(round(p.y / self.step))
                for r in range(1, 8):
                    for dx in range(-r, r + 1):
                        for dy in range(-r, r + 1):
                            if max(abs(dx), abs(dy)) != r:
                                continue
                            vx, vy = (ix0 + dx) * self.step, (iy0 + dy) * self.step
                            if not via_sobre_plano_propio(vx, vy) or not self.via_libre_drc(vx, vy, nid):
                                continue
                            segs_pts = construir_chamfer_45(p.x, p.y, vx, vy, True)
                            if segs_pts and all(
                                clasificar_direccion_octilinear(bx - ax, by - ay) is not None
                                and self.segmento_libre_drc(ax, ay, bx, by, "F.Cu", 0.30, nid, clearance=0.18)
                                for (ax, ay), (bx, by) in segs_pts
                            ):
                                for (ax, ay), (bx, by) in segs_pts:
                                    self.tracks.append(TrackSeg(ax, ay, bx, by, 0.30, "F.Cu", nid))
                                self.vias.append(ViaItem(vx, vy, 0.75, 0.35, nid))
                                conectado = True
                                break
                        if conectado:
                            break
                    if conectado:
                        break

    def rutear_red_completa(self, net_name: str, width: float = 0.35) -> bool:
        """
        Rutea todos los pads de `net_name` formando un Árbol Generador Mínimo (MST)
        en 4 capas con ángulos estrictamente de 45° y vías automáticas.
        """
        nid = self.get_net_id(net_name)
        pads = self.pads_by_net.get(nid, [])
        if len(pads) <= 1:
            return True

        conectados: List[PadInfo] = [pads[0]]
        pendientes: List[PadInfo] = list(pads[1:])
        exito_total = True

        while pendientes:
            pares_candidatos: List[Tuple[float, int, PadInfo, PadInfo]] = []
            for idx_p, p_cand in enumerate(pendientes):
                for p_con in conectados:
                    d = math.hypot(p_cand.x - p_con.x, p_cand.y - p_con.y)
                    pares_candidatos.append((d, idx_p, p_con, p_cand))
            pares_candidatos.sort(key=lambda x: x[0])

            _, idx_elegido, _, p_dst = pares_candidatos[0]
            pendientes.pop(idx_elegido)

            fuentes_ordenadas = sorted(conectados, key=lambda pc: math.hypot(p_dst.x - pc.x, p_dst.y - pc.y))[:4]
            anchos_intento = [width]
            if width > 0.45:
                anchos_intento.append(0.45)
            if width > 0.25:
                anchos_intento.append(0.25)

            ok = False
            for w_try in anchos_intento:
                for p_src in fuentes_ordenadas:
                    if self.rutear_par_pads(p_src, p_dst, w_try):
                        ok = True
                        break
                if ok:
                    break

            if not ok:
                exito_total = False
            conectados.append(p_dst)

        return exito_total

    def _portal_tiene_salida(self, ix: int, iy: int, l_idx: int, width: float, nid: int) -> bool:
        """Verifica que desde (ix, iy, l_idx) exista al menos un paso válido de ancho `width` o una Vía."""
        gx, gy = ix * self.step, iy * self.step
        if self.via_libre_drc(gx, gy, nid):
            return True
        lname = self.CAPAS_RUTEO[l_idx]
        for dx_i, dy_i, _ in DIRS_8:
            nx, ny = ix + dx_i, iy + dy_i
            if 1 <= nx < self.nx - 1 and 1 <= ny < self.ny - 1:
                if self.segmento_libre_drc(gx, gy, nx * self.step, ny * self.step, lname, width, nid):
                    return True
        return False

    def ajustar_portales_pad_mejorado(
        self, pad: PadInfo, width: float
    ) -> List[Tuple[int, int, int, Optional[int], List[TrackSeg]]]:
        """
        Versión 4 capas de portales de pad:
        - Los pads SMD salen en F.Cu (l_idx=0) con cuello de botella `w_stub` y verifican que
          el nodo de rejilla alcanzado pueda continuar con `width` o colocar una Vía hacia In2.Cu/B.Cu.
        - Los pads PTH (pasantes) pueden salir directamente en F.Cu (0), In2.Cu (1) o B.Cu (2)
          (y en In1.Cu (3) si son de tierra).
        """
        es_tierra = pad.net_name in ("AGND", "DGND", "PGND")
        capas_pad = [0] if pad.is_smd else ([0, 1, 2, 3] if es_tierra else [0, 1, 2])
        w_stub = min(width, 0.24) if min(pad.rx, pad.ry) < 0.22 else min(width, 0.35)

        ix0 = int(round(pad.x / self.step))
        iy0 = int(round(pad.y / self.step))
        gx0, gy0 = ix0 * self.step, iy0 * self.step

        out: List[Tuple[int, int, int, Optional[int], List[TrackSeg]]] = []

        # Portal directo en el nodo más cercano si cae dentro del pad y tiene salida legal a ancho completo
        if abs(gx0 - pad.x) <= pad.rx + 0.05 and abs(gy0 - pad.y) <= pad.ry + 0.05:
            for l_idx in capas_pad:
                lname = self.CAPAS_RUTEO[l_idx]
                if not self._portal_tiene_salida(ix0, iy0, l_idx, width, pad.net_id):
                    continue
                if math.hypot(gx0 - pad.x, gy0 - pad.y) < 1e-4:
                    out.append((ix0, iy0, l_idx, None, []))
                elif self.segmento_libre_drc(pad.x, pad.y, gx0, gy0, lname, w_stub, pad.net_id, clearance=0.18):
                    out.append((ix0, iy0, l_idx, None, [TrackSeg(pad.x, pad.y, gx0, gy0, w_stub, lname, pad.net_id)]))

        # Portales de escape a 45° fuera del pad (r_grid = 1..6)
        candidatos: List[Tuple[float, int, int, int, Optional[int], List[TrackSeg]]] = []
        for r_grid in range(1, 7):
            for dx_i in range(-r_grid, r_grid + 1):
                for dy_i in range(-r_grid, r_grid + 1):
                    if max(abs(dx_i), abs(dy_i)) != r_grid:
                        continue
                    ix = ix0 + dx_i
                    iy = iy0 + dy_i
                    if not (1 <= ix < self.nx - 1 and 1 <= iy < self.ny - 1):
                        continue
                    gx, gy = ix * self.step, iy * self.step
                    for l_idx in capas_pad:
                        lname = self.CAPAS_RUTEO[l_idx]
                        if not self._portal_tiene_salida(ix, iy, l_idx, width, pad.net_id):
                            continue
                        for diag_first in (True, False):
                            segs_pts = construir_chamfer_45(pad.x, pad.y, gx, gy, diag_primero=diag_first)
                            if not segs_pts:
                                continue
                            ok = True
                            t_list: List[TrackSeg] = []
                            last_dir: Optional[int] = None
                            for (ax, ay), (bx, by) in segs_pts:
                                if math.hypot(bx - ax, by - ay) < 1e-4:
                                    continue
                                d_seg = clasificar_direccion_octilinear(bx - ax, by - ay)
                                if d_seg is None:
                                    ok = False
                                    break
                                if last_dir is not None and not giro_valido_45(last_dir, d_seg):
                                    ok = False
                                    break
                                if not self.segmento_libre_drc(ax, ay, bx, by, lname, w_stub, pad.net_id, clearance=0.18):
                                    ok = False
                                    break
                                last_dir = d_seg
                                t_list.append(TrackSeg(ax, ay, bx, by, w_stub, lname, pad.net_id))
                            if ok and t_list:
                                dist_c = math.hypot(gx - pad.x, gy - pad.y)
                                candidatos.append((dist_c, ix, iy, l_idx, last_dir, t_list))
            if len(candidatos) >= 18:
                break

        candidatos.sort(key=lambda item: item[0])
        for _, ix, iy, l_idx, ldir, tlist in candidatos[:20]:
            out.append((ix, iy, l_idx, ldir, tlist))
        return out

    def guardar_y_exportar_manufactura(
        self,
        ruta_pcb: str,
        titulo_placa: str,
        rev_placa: str,
        textos_fab: List[Tuple[float, float, str, float]],
    ) -> Dict[str, int]:
        """
        Escribe el archivo .kicad_pcb, ejecuta `kicad-cli pcb drc --refill-zones --save-board`,
        valida el reporte JSON de DRC, exporta Gerbers + Taladros + BOM + CPL + STEP 3D + Renders 3D,
        y retorna un resumen con el conteo de violaciones e ítems sin conectar.
        """
        directorio_base = os.path.dirname(ruta_pcb)
        os.makedirs(directorio_base, exist_ok=True)

        lineas_pcb = [
            "(kicad_pcb",
            "\t(version 20260206)",
            '\t(generator "pcbnew")',
            '\t(generator_version "10.0")',
            "\t(general (thickness 1.6) (legacy_teardrops no))",
            '\t(paper "A4")',
            "\t(title_block",
            f'\t\t(title "{titulo_placa}")',
            '\t\t(date "2026-10-23")',
            f'\t\t(rev "{rev_placa}")',
            '\t\t(company "Planta Piloto de Electrodeposición y Galvanoplastia")',
            "\t)",
            "\t(layers",
            '\t\t(0 "F.Cu" signal)',
            '\t\t(1 "In1.Cu" signal)',
            '\t\t(2 "In2.Cu" signal)',
            '\t\t(31 "B.Cu" signal)',
            '\t\t(32 "B.Adhes" user "B.Adhesive")',
            '\t\t(33 "F.Adhes" user "F.Adhesive")',
            '\t\t(34 "B.Paste" user)',
            '\t\t(35 "F.Paste" user)',
            '\t\t(36 "B.SilkS" user "B.Silkscreen")',
            '\t\t(37 "F.SilkS" user "F.Silkscreen")',
            '\t\t(38 "B.Mask" user)',
            '\t\t(39 "F.Mask" user)',
            '\t\t(44 "Edge.Cuts" user)',
            '\t\t(46 "B.CrtYd" user "B.Courtyard")',
            '\t\t(47 "F.CrtYd" user "F.Courtyard")',
            '\t\t(48 "B.Fab" user)',
            '\t\t(49 "F.Fab" user)',
            "\t)",
            "\t(setup (pad_to_mask_clearance 0.04))",
        ]

        for nname, nid in sorted(self.nets.items(), key=lambda x: x[1]):
            lineas_pcb.append(f'\t(net {nid} "{nname}")')

        # Contorno exterior
        lineas_pcb.append(
            f'\t(gr_rect (start 0 0) (end {self.board_w:.2f} {self.board_h:.2f}) '
            f'(stroke (width 0.15) (type solid)) (fill no) (layer "Edge.Cuts"))'
        )
        # Ranuras fresadas de aislamiento
        for sx1, sy1, sx2, sy2 in self.edge_slots:
            lineas_pcb.append(
                f'\t(gr_rect (start {sx1:.2f} {sy1:.2f}) (end {sx2:.2f} {sy2:.2f}) '
                f'(stroke (width 0.15) (type solid)) (fill no) (layer "Edge.Cuts"))'
            )

        # Textos técnicos en F.Fab (evita violaciones silk_over_copper / silk_overlap)
        for tx, ty, txt, sz in textos_fab:
            lineas_pcb.append(
                f'\t(gr_text "{txt}" (at {tx:.2f} {ty:.2f} 0) (layer "F.Fab") '
                f"(effects (font (size {sz:.2f} {sz:.2f}) (thickness 0.20))))"
            )

        # Footprints
        for fp_str in self.footprints_sexpr:
            for l_fp in fp_str.splitlines():
                lineas_pcb.append("\t" + l_fp)

        # Segmentos de pista 45°
        for tr in self.tracks:
            if math.hypot(tr.x2 - tr.x1, tr.y2 - tr.y1) < 1e-4:
                continue
            lineas_pcb.append(
                f"\t(segment (start {tr.x1:.4f} {tr.y1:.4f}) (end {tr.x2:.4f} {tr.y2:.4f}) "
                f'(width {tr.width:.2f}) (layer "{tr.layer}") (net {tr.net_id}))'
            )

        # Vías pasantes
        for v in self.vias:
            lineas_pcb.append(
                f"\t(via (at {v.x:.4f} {v.y:.4f}) (size {v.size:.2f}) (drill {v.drill:.2f}) "
                f'(layers "F.Cu" "B.Cu") (net {v.net_id}))'
            )

        # Zonas de tierra y keepouts
        for z_str in self.zones_sexpr:
            lineas_pcb.append(z_str)

        lineas_pcb.append(")")
        with open(ruta_pcb, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas_pcb) + "\n")

        # Generar archivo de proyecto .kicad_pro con reglas IPC-2221 / JLCPCB (Clearance 0.14mm para MSOP-10)
        ruta_pro = os.path.splitext(ruta_pcb)[0] + ".kicad_pro"
        pro_data = {
            "board": {
                "design_settings": {
                    "rules": {
                        "min_clearance": 0.14,
                        "min_track_width": 0.20,
                        "min_via_annular_width": 0.15,
                        "min_via_diameter": 0.60,
                        "min_through_hole_diameter": 0.30,
                    },
                    "rule_severities": {
                        "annular_width": "error",
                        "clearance": "error",
                        "connection_width": "warning",
                        "copper_edge_clearance": "error",
                        "copper_sliver": "warning",
                        "courtyards_overlap": "error",
                        "creepage": "error",
                        "diff_pair_gap_out_of_range": "error",
                        "diff_pair_uncoupled_length_too_long": "error",
                        "drill_out_of_range": "error",
                        "duplicate_footprints": "warning",
                        "extra_footprint": "warning",
                        "footprint": "error",
                        "footprint_filters_mismatch": "ignore",
                        "footprint_symbol_field_mismatch": "warning",
                        "footprint_symbol_mismatch": "warning",
                        "footprint_type_mismatch": "ignore",
                        "hole_clearance": "error",
                        "hole_to_hole": "warning",
                        "holes_co_located": "warning",
                        "invalid_outline": "error",
                        "isolated_copper": "warning",
                        "item_on_disabled_layer": "error",
                        "items_not_allowed": "error",
                        "length_out_of_range": "error",
                        "lib_footprint_issues": "warning",
                        "lib_footprint_mismatch": "warning",
                        "malformed_courtyard": "error",
                        "microvia_drill_out_of_range": "error",
                        "mirrored_text_on_front_layer": "warning",
                        "missing_courtyard": "ignore",
                        "missing_footprint": "warning",
                        "missing_tuning_profile": "warning",
                        "net_conflict": "warning",
                        "nonmirrored_text_on_back_layer": "warning",
                        "npth_inside_courtyard": "error",
                        "padstack": "warning",
                        "pth_inside_courtyard": "error",
                        "shorting_items": "error",
                        "silk_edge_clearance": "warning",
                        "silk_over_copper": "warning",
                        "silk_overlap": "warning",
                        "skew_out_of_range": "error",
                        "solder_mask_bridge": "error",
                        "starved_thermal": "error",
                        "text_height": "warning",
                        "text_on_edge_cuts": "error",
                        "text_thickness": "warning",
                        "through_hole_pad_without_hole": "error",
                        "too_many_vias": "error",
                        "track_angle": "error",
                        "track_dangling": "warning",
                        "track_not_centered_on_via": "ignore",
                        "track_on_post_machined_layer": "error",
                        "track_segment_length": "error",
                        "track_width": "error",
                        "tracks_crossing": "error",
                        "tuning_profile_track_geometries": "ignore",
                        "unconnected_items": "error",
                        "unresolved_variable": "error",
                        "via_dangling": "warning",
                        "zones_intersect": "error",
                    },
                }
            },
            "meta": {"filename": os.path.basename(ruta_pro), "version": 3},
        }
        with open(ruta_pro, "w", encoding="utf-8") as f_pro:
            json.dump(pro_data, f_pro, indent=2)

        # Rellenar zonas y ejecutar DRC con KiCad 10 CLI
        dir_gerbers = os.path.join(directorio_base, "gerbers")
        os.makedirs(dir_gerbers, exist_ok=True)
        ruta_drc = os.path.join(dir_gerbers, "DRC_REPORT.json")
        subprocess.run(
            [KICAD_CLI, "pcb", "drc", "--refill-zones", "--save-board", "--severity-error", "--format", "json", "--output", ruta_drc, ruta_pcb],
            check=True,
            capture_output=True,
            text=True,
        )

        # Exportar BOM y CPL
        ruta_bom = os.path.join(dir_gerbers, "BOM_JLCPCB.csv")
        with open(ruta_bom, "w", newline="", encoding="utf-8") as f_bom:
            writer = csv.DictWriter(f_bom, fieldnames=["Comment", "Designator", "Footprint", "LCSC Part #", "Description"])
            writer.writeheader()
            writer.writerows(self.bom_items)

        ruta_cpl = os.path.join(dir_gerbers, "CPL_PickAndPlace.csv")
        with open(ruta_cpl, "w", newline="", encoding="utf-8") as f_cpl:
            writer = csv.DictWriter(f_cpl, fieldnames=["Designator", "Val", "Package", "Mid X", "Mid Y", "Rotation", "Layer"])
            writer.writeheader()
            writer.writerows(self.cpl_items)

        # Exportar Gerbers de 4 Capas (F.Cu, In1.Cu, In2.Cu, B.Cu) + Taladros + ZIP
        capas_gerber = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"
        subprocess.run([KICAD_CLI, "pcb", "export", "gerbers", "--output", dir_gerbers, "--layers", capas_gerber, ruta_pcb], check=True)
        subprocess.run([KICAD_CLI, "pcb", "export", "drill", "--output", dir_gerbers, "--format", "excellon", "--excellon-units", "mm", ruta_pcb], check=True)

        nombre_base = os.path.splitext(os.path.basename(ruta_pcb))[0]
        ruta_zip = os.path.join(directorio_base, f"GERBERS_{nombre_base.upper()}_REV4.zip")
        with zipfile.ZipFile(ruta_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname in os.listdir(dir_gerbers):
                if fname.endswith((
                    ".gtl", ".g1", ".g2", ".g3", ".gbl", ".gts", ".gbs", ".gto", ".gbo",
                    ".gtp", ".gbp", ".gm1", ".drl", ".gbr", ".gbrjob", ".csv"
                )):
                    zf.write(os.path.join(dir_gerbers, fname), arcname=fname)

        # Cargar resultados de DRC oficial
        with open(ruta_drc, "r", encoding="utf-8") as f_d:
            drc_data = json.load(f_d)

        resumen_drc = {
            "violations": len(drc_data.get("violations", [])),
            "unconnected": len(drc_data.get("unconnected_items", [])),
        }

        # Exportar modelo 3D STEP y Renders 3D Raytraced
        ruta_step = os.path.join(directorio_base, f"{nombre_base}_3d.step")
        try:
            subprocess.run([KICAD_CLI, "pcb", "export", "step", "--subst-models", "--force", "-o", ruta_step, ruta_pcb], check=False)
        except Exception as e_step:
            print(f"[3D STEP Warning] {e_step}")

        ruta_png_iso = os.path.join(directorio_base, f"render_3d_{nombre_base}_iso.png")
        ruta_png_top = os.path.join(directorio_base, f"render_3d_{nombre_base}_top.png")
        try:
            subprocess.run([
                KICAD_CLI, "pcb", "render", "--width", "1800", "--height", "1200",
                "--quality", "high", "--preset", "follow_plot_settings",
                "--rotate", "-32,0,22", "--zoom", "0.95", "-o", ruta_png_iso, ruta_pcb
            ], check=False)
            subprocess.run([
                KICAD_CLI, "pcb", "render", "--width", "1800", "--height", "1200",
                "--quality", "high", "--preset", "follow_plot_settings",
                "--side", "top", "--zoom", "0.95", "-o", ruta_png_top, ruta_pcb
            ], check=False)
        except Exception as e_rnd:
            print(f"[3D Render Warning] {e_rnd}")

        return resumen_drc
