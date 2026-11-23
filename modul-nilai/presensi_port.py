from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Tuple


class PresensiPort(ABC):
    """Port untuk memeriksa persentase kehadiran mahasiswa pada suatu kelas."""

    @abstractmethod
    def get_persentase_kehadiran(self, kelas_id: int, nim: str) -> Decimal:
        raise NotImplementedError

    def memenuhi_syarat_ujian(
        self, kelas_id: int, nim: str, minimal_persen: Decimal = Decimal("75.00")
    ) -> bool:
        return self.get_persentase_kehadiran(kelas_id, nim) >= minimal_persen


class PresensiStub(PresensiPort):
    """Stub presensi untuk pengembangan dan pengujian Minggu 9."""

    def __init__(self, data_presensi: Dict[Tuple[int, str], Decimal] | None = None, default_persen: Decimal = Decimal("100.00")):
        self._data: Dict[Tuple[int, str], Decimal] = data_presensi or {}
        self._default = default_persen

    def set_kehadiran(self, kelas_id: int, nim: str, persen: Decimal) -> None:
        self._data[(kelas_id, nim)] = Decimal(str(persen))

    def get_persentase_kehadiran(self, kelas_id: int, nim: str) -> Decimal:
        return self._data.get((kelas_id, nim), self._default)