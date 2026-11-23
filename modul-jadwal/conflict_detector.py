from typing import List, Dict, Any

def is_overlap(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
    """Interval setengah terbuka [mulai, selesai): jika end_a == start_b, TIDAK bentrok."""
    return start_a < end_b and start_b < end_a

def detect_naive(schedules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Pendekatan Naif O(N^2): membandingkan setiap pasang jadwal."""
    conflicts = []
    n = len(schedules)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = schedules[i], schedules[j]
            if a["hari"] != b["hari"]:
                continue
            if is_overlap(a["jam_mulai"], a["jam_selesai"], b["jam_mulai"], b["jam_selesai"]):
                reasons = []
                if a["ruangan_id"] == b["ruangan_id"]:
                    reasons.append(f"Ruangan ID {a['ruangan_id']} bentrok")
                if a["dosen_id"] == b["dosen_id"]:
                    reasons.append(f"Dosen ID {a['dosen_id']} bentrok")
                if reasons:
                    pair = tuple(sorted([a["id"], b["id"]]))
                    conflicts.append({
                        "jadwal_1_id": pair[0],
                        "jadwal_2_id": pair[1],
                        "hari": a["hari"],
                        "alasan": " & ".join(reasons)
                    })
    return conflicts

def detect_schedule_conflict(schedules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Algoritma Sweep Line O(N log N):
    Mengurutkan titik waktu mulai (+1) dan selesai (-1) per hari.
    Pada titik waktu yang sama, event END diproses lebih dulu dari START
    sehingga jadwal yang bersambungan (misal 08:00-10:00 dan 10:00-12:00) tidak dianggap bentrok.
    """
    by_day: Dict[str, List[Dict[str, Any]]] = {}
    for s in schedules:
        by_day.setdefault(s["hari"], []).append(s)

    seen_pairs = set()
    conflicts = []

    for hari, day_schedules in by_day.items():
        events = []
        for s in day_schedules:
            # Event type: 0 untuk END (keluar duluan), 1 untuk START (masuk belakangan)
            events.append((s["jam_mulai"], 1, s))
            events.append((s["jam_selesai"], 0, s))

        # Sort berdasarkan waktu, lalu tipe event (0 sebelum 1)
        events.sort(key=lambda x: (x[0], x[1]))

        active: Dict[int, Dict[str, Any]] = {}
        for time_pt, ev_type, sched in events:
            if ev_type == 0:
                active.pop(sched["id"], None)
            else:
                for act_id, act_sched in active.items():
                    reasons = []
                    if sched["ruangan_id"] == act_sched["ruangan_id"]:
                        reasons.append(f"Ruangan ID {sched['ruangan_id']} bentrok")
                    if sched["dosen_id"] == act_sched["dosen_id"]:
                        reasons.append(f"Dosen ID {sched['dosen_id']} bentrok")
                    if reasons:
                        pair = tuple(sorted([sched["id"], act_id]))
                        if pair not in seen_pairs:
                            seen_pairs.add(pair)
                            conflicts.append({
                                "jadwal_1_id": pair[0],
                                "jadwal_2_id": pair[1],
                                "hari": hari,
                                "alasan": " & ".join(reasons)
                            })
                active[sched["id"]] = sched

    return sorted(conflicts, key=lambda c: (c["jadwal_1_id"], c["jadwal_2_id"]))