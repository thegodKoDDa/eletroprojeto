"""Reviewed NBR5410:2004/VC2008 §9.1.2.1, fig18 and §9.1.4.3.1.

Only a shower without tray/recess/clear enclosure, one continuous level floor,
no intervening partitions. Component bounding envelopes, not center points.
No volume0, product approval, circuit association or final compliance claim.
"""

from decimal import Decimal as D
from decimal import localcontext

REFERENCE = "NBR5410:2004/VC2008 §9.1.2.1, figura18 (pp.170–172); §9.1.4.3.1–3 (p.174)."
URLS = [
    "https://www.abntcatalogo.com.br/",
    "https://professor.pucgoias.edu.br/SiteDocente/admin/arquivosUpload/18451/material/nbr_5410.pdf",
]
LIMITATIONS = [
    "Somente chuveiro sem piso-boxe/rebaixo/delimitação clara, piso único no mesmo nível, sem paredes/divisórias entre o chuveiro e os componentes. Não abrange banheira ou cabine pré-fabricada.",
    "Informar envelope externo completo de cada componente e coordenadas em metros no mesmo referencial; z=0 no piso de banho. Fronteiras pertencem ao volume mais restritivo.",
    "Este estudo localiza volumes e impede tomada/interruptor comum nos volumes1/2. Não aprova componentes, IP, classes, SELV, DR, equipotencialização, circuitos, percurso ou instalação. Exceções exigem análise própria.",
]


def calculate_bathroom_geometry(project):
    output = []
    with localcontext() as context:
        context.prec = 40
        for room in project.get("environments", []):
            geometry = room.get("bathroom_geometry")
            if geometry is None:
                continue
            pending = []
            if room.get("type") != "bathroom":
                pending.append(
                    "O ambiente precisa estar classificado como banheiro para este estudo."
                )
            if not geometry.get("scope_confirmed"):
                pending.append(
                    "Confirme chuveiro sem piso-boxe/rebaixo/delimitação, piso único no mesmo nível e ausência de paredes/divisórias intermediárias. Outros arranjos exigem modelo próprio."
                )
            if any(
                geometry.get(key) is None
                for key in ("shower_x_m", "shower_y_m", "measurement_source")
            ):
                pending.append("Informe posição da saída do chuveiro e fonte das medidas.")
            if not geometry.get("points"):
                pending.append("Cadastre os envelopes dos componentes a estudar.")
            points = []
            for point in geometry.get("points", []):
                row = dict(
                    point_id=point["id"],
                    name=point["name"],
                    status="pending",
                    volume=None,
                    nearest_horizontal_distance_m=None,
                    ordinary_socket_or_switch_forbidden=None,
                    pending_checks=[],
                )
                bounds = [
                    point.get(key)
                    for key in ("x_min_m", "x_max_m", "y_min_m", "y_max_m", "z_min_m", "z_max_m")
                ]
                if any(value is None for value in bounds):
                    row["pending_checks"].append(
                        "Informe as seis coordenadas do envelope externo do componente, em metros."
                    )
                else:
                    x0, x1, y0, y1, z0, z1 = map(lambda v: D(str(v)), bounds)
                    if x0 > x1 or y0 > y1 or z0 > z1:
                        row["status"] = "invalid"
                        row["pending_checks"].append(
                            "Cada coordenada mínima deve ser menor ou igual à máxima."
                        )
                    elif not pending:
                        sx, sy = D(str(geometry["shower_x_m"])), D(str(geometry["shower_y_m"]))
                        dx = max(x0 - sx, sx - x1, D(0))
                        dy = max(y0 - sy, sy - y1, D(0))
                        distance2 = dx * dx + dy * dy
                        volume = (
                            "1"
                            if distance2 <= D(".36") and z0 <= D("2.25")
                            else "2"
                            if distance2 <= D("1.44") and z0 <= D(3)
                            else "3"
                            if distance2 <= D("12.96") and z0 <= D("2.25")
                            else "outside"
                        )
                        forbidden = volume in {"1", "2"} and point.get("kind") in {
                            "socket",
                            "switch",
                        }
                        row.update(
                            volume=volume,
                            nearest_horizontal_distance_m=distance2.sqrt(),
                            ordinary_socket_or_switch_forbidden=forbidden,
                            status="invalid" if forbidden else "estimated",
                        )
                        row["pending_checks"].append(
                            "Tomada/interruptor comum vedado neste volume (§9.1.4.3.1); reposicionar ou submeter exceção específica à análise técnica."
                            if forbidden
                            else "Conferir IP, classe, proteção contra choque, DR/SELV/separação, equipotencialização e condições do produto; volume isolado não autoriza instalação."
                        )
                if pending:
                    row["pending_checks"] = pending + row["pending_checks"]
                points.append(row)
            status = (
                "invalid"
                if any(p["status"] == "invalid" for p in points)
                else "pending"
                if pending or any(p["status"] == "pending" for p in points)
                else "estimated"
            )
            output.append(
                dict(
                    environment_id=str(room["id"]),
                    name=room["name"],
                    status=status,
                    points=points,
                    pending_checks=pending,
                    reference=REFERENCE,
                    reference_urls=URLS,
                    limitations=LIMITATIONS,
                )
            )
    return output
