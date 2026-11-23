from abc import ABC, abstractmethod

class BaseValidator(ABC):
    def __init__(self):
        self._next_validator = None

    def set_next(self, validator):
        self._next_validator = validator
        return validator

    @abstractmethod
    def validate(self, context: dict) -> list[str]:
        if self._next_validator:
            return self._next_validator.validate(context)
        return []

# Validator 1: Cek Duplikasi Mata Kuliah
class DuplicateCourseValidator(BaseValidator):
    def validate(self, context: dict) -> list[str]:
        errors = []
        existing_codes = [d.kode_mk for d in context["existing_details"]]
        new_code = context["new_course"]["kode_mk"]
        if new_code in existing_codes:
            errors.append(f"Mata kuliah {new_code} sudah ada di dalam KRS.")
        return errors + super().validate(context)

# Validator 2: Cek Batas Maksimal SKS (24 SKS)
class MaxSKSValidator(BaseValidator):
    def validate(self, context: dict) -> list[str]:
        errors = []
        current_sks = sum(d.sks for d in context["existing_details"])
        new_sks = context["new_course"]["sks"]
        max_sks = context.get("max_sks", 24)

        if current_sks + new_sks > max_sks:
            errors.append(f"Total SKS ({current_sks + new_sks}) melebihi batas maksimal ({max_sks} SKS).")
        return errors + super().validate(context)

# Validator 3: Cek Bentrok Jadwal (Irisan Interval)
class ScheduleConflictValidator(BaseValidator):
    def validate(self, context: dict) -> list[str]:
        errors = []
        new_c = context["new_course"]
        for d in context["existing_details"]:
            if d.hari.lower() == new_c["hari"].lower():
                # Irisan interval: start_A < end_B AND start_B < end_A
                if new_c["jam_mulai"] < d.jam_selesai and d.jam_mulai < new_c["jam_selesai"]:
                    errors.append(f"Jadwal bentrok dengan {d.kode_mk} ({d.nama_mk}) pada hari {d.hari}.")
        return errors + super().validate(context)

# Validator 4: Cek Prasyarat Mata Kuliah
class PrerequisiteValidator(BaseValidator):
    def validate(self, context: dict) -> list[str]:
        errors = []
        repo = context["repo"]
        unmet = repo.get_unmet_prerequisites(context["nim"], context["new_course"]["kode_mk"])
        for req in unmet:
            errors.append(
                f"Prasyarat {req['kode_mk_syarat']} (minimal nilai {req['min_huruf']}) belum terpenuhi."
            )
        return errors + super().validate(context)

def build_chain() -> BaseValidator:
    v1 = DuplicateCourseValidator()
    v2 = MaxSKSValidator()
    v3 = ScheduleConflictValidator()
    v4 = PrerequisiteValidator()

    # Urutan rantai: dari validasi memori tercepat ke query database
    v1.set_next(v2).set_next(v3).set_next(v4)
    return v1