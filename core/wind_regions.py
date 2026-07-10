from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WindLocationGroup:
    province: str
    area: str
    group: str
    region: str
    note: str


WHOLE_PROVINCE = "ทั้งจังหวัด"
MANUAL_LOCATION = "เลือก Wind group เอง / Manual group selection"


# DPT 1311-50 / 1312-50 province-to-reference-wind-speed group lookup.
# Source data entered from the user-provided DPT province group table.
DPT_WIND_PROVINCE_GROUPS: dict[str, dict[str, object]] = {
    # North
    "กำแพงเพชร": {"region": "ภาคเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "เชียงใหม่": {"region": "ภาคเหนือ", "areas": {WHOLE_PROVINCE: "Group 3"}},
    "เชียงราย": {"region": "ภาคเหนือ", "areas": {WHOLE_PROVINCE: "Group 3"}},
    "ตาก": {"region": "ภาคเหนือ", "areas": {"อำเภออุ้มผาง": "Group 1", "บริเวณอื่น ๆ": "Group 2"}},
    "นครสวรรค์": {"region": "ภาคเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "น่าน": {"region": "ภาคเหนือ", "areas": {WHOLE_PROVINCE: "Group 2"}},
    "พะเยา": {"region": "ภาคเหนือ", "areas": {WHOLE_PROVINCE: "Group 3"}},
    "พิจิตร": {"region": "ภาคเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "พิษณุโลก": {"region": "ภาคเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "เพชรบูรณ์": {"region": "ภาคเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "แพร่": {"region": "ภาคเหนือ", "areas": {WHOLE_PROVINCE: "Group 2"}},
    "แม่ฮ่องสอน": {"region": "ภาคเหนือ", "areas": {WHOLE_PROVINCE: "Group 3"}},
    "ลำปาง": {"region": "ภาคเหนือ", "areas": {WHOLE_PROVINCE: "Group 2"}},
    "ลำพูน": {"region": "ภาคเหนือ", "areas": {WHOLE_PROVINCE: "Group 2"}},
    "สุโขทัย": {"region": "ภาคเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "อุตรดิตถ์": {"region": "ภาคเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "อุทัยธานี": {"region": "ภาคเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},

    # Central
    "กรุงเทพมหานคร": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "กาญจนบุรี": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "ฉะเชิงเทรา": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "ชัยนาท": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "นครนายก": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "นครปฐม": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "นนทบุรี": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "ปราจีนบุรี": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "ปทุมธานี": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "ประจวบคีรีขันธ์": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 4A"}},
    "เพชรบุรี": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 4B"}},
    "ราชบุรี": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "ลพบุรี": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "สระบุรี": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "สิงห์บุรี": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "สุพรรณบุรี": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "สมุทรปราการ": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "สมุทรสงคราม": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "สมุทรสาคร": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "สระแก้ว": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "อยุธยา": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "อ่างทอง": {"region": "ภาคกลาง", "areas": {WHOLE_PROVINCE: "Group 1"}},

    # East
    "จันทบุรี": {"region": "ภาคตะวันออก", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "ชลบุรี": {"region": "ภาคตะวันออก", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "ตราด": {"region": "ภาคตะวันออก", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "ระยอง": {"region": "ภาคตะวันออก", "areas": {WHOLE_PROVINCE: "Group 1"}},

    # Northeast
    "กาฬสินธุ์": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "ขอนแก่น": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "ชัยภูมิ": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "นครพนม": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 2"}},
    "นครราชสีมา": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "บุรีรัมย์": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "มหาสารคาม": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "มุกดาหาร": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 2"}},
    "ยโสธร": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 2"}},
    "ร้อยเอ็ด": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "เลย": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "ศรีสะเกษ": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "สกลนคร": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "สุรินทร์": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "หนองคาย": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 2"}},
    "หนองบัวลำภู": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "อุดรธานี": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 1"}},
    "อำนาจเจริญ": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 2"}},
    "อุบลราชธานี": {"region": "ภาคตะวันออกเฉียงเหนือ", "areas": {WHOLE_PROVINCE: "Group 2"}},

    # South
    "กระบี่": {"region": "ภาคใต้", "areas": {WHOLE_PROVINCE: "Group 4B"}},
    "ชุมพร": {"region": "ภาคใต้", "areas": {WHOLE_PROVINCE: "Group 4A"}},
    "ตรัง": {"region": "ภาคใต้", "areas": {WHOLE_PROVINCE: "Group 4B"}},
    "นครศรีธรรมราช": {
        "region": "ภาคใต้",
        "areas": {
            "อำเภอเมือง, ขนอม, สิชล, ท่าศาลา, ทุ่งใหญ่, พรหมคีรี, ลานสกา, ร่อนพิบูลย์, ปากพนัง, เชียรใหญ่, หัวไทร, ชะอวด": "Group 4A",
            "บริเวณอื่น ๆ": "Group 4B",
        },
    },
    "นราธิวาส": {"region": "ภาคใต้", "areas": {WHOLE_PROVINCE: "Group 4A"}},
    "ปัตตานี": {"region": "ภาคใต้", "areas": {WHOLE_PROVINCE: "Group 4A"}},
    "พังงา": {"region": "ภาคใต้", "areas": {WHOLE_PROVINCE: "Group 4B"}},
    "พัทลุง": {"region": "ภาคใต้", "areas": {WHOLE_PROVINCE: "Group 4A"}},
    "ภูเก็ต": {"region": "ภาคใต้", "areas": {WHOLE_PROVINCE: "Group 4B"}},
    "ยะลา": {"region": "ภาคใต้", "areas": {WHOLE_PROVINCE: "Group 4A"}},
    "ระนอง": {"region": "ภาคใต้", "areas": {WHOLE_PROVINCE: "Group 4B"}},
    "สงขลา": {"region": "ภาคใต้", "areas": {WHOLE_PROVINCE: "Group 4A"}},
    "สตูล": {"region": "ภาคใต้", "areas": {WHOLE_PROVINCE: "Group 4B"}},
    "สุราษฎร์ธานี": {
        "region": "ภาคใต้",
        "areas": {
            "อำเภอเมือง, ท่าชนะ, ไชยา, ท่าฉาง, คีรีรัฐนิคม, พุนพิน, กาญจนดิษฐ์, ดอนสัก, บ้านนาเดิม, บ้านนาสาร, เกาะสมุย, เกาะพะงัน": "Group 4A",
            "บริเวณอื่น ๆ": "Group 4B",
        },
    },
}


def wind_province_options() -> list[str]:
    return list(DPT_WIND_PROVINCE_GROUPS.keys())


def wind_area_options(province: str) -> list[str]:
    data = DPT_WIND_PROVINCE_GROUPS.get(province)
    if not data:
        return [WHOLE_PROVINCE]
    return list(dict(data["areas"]).keys())


def wind_group_from_province_area(province: str, area: str | None = None) -> WindLocationGroup | None:
    data = DPT_WIND_PROVINCE_GROUPS.get(province)
    if not data:
        return None
    areas = dict(data["areas"])
    selected_area = area if area in areas else next(iter(areas))
    group = str(areas[selected_area])
    return WindLocationGroup(
        province=province,
        area=selected_area,
        group=group,
        region=str(data["region"]),
        note="DPT 1311-50 / 1312-50 province group table",
    )
