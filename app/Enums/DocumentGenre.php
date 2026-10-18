<?php

namespace App\Enums;

enum DocumentGenre: string
{
    case AUTO = 'auto';
    case SKRIPSI = 'skripsi';
    case MAKALAH = 'makalah';
    case LAPORAN_MAGANG = 'laporan_magang';
    case PROPOSAL_PENELITIAN = 'proposal_penelitian';
    case CUSTOM = 'custom';

    public function label(): string
    {
        return match ($this) {
            self::AUTO => 'Deteksi Otomatis',
            self::SKRIPSI => 'Skripsi / Tugas Akhir / Tesis',
            self::MAKALAH => 'Makalah / Paper Akademik',
            self::LAPORAN_MAGANG => 'Laporan Magang / PKL',
            self::PROPOSAL_PENELITIAN => 'Proposal Penelitian / Skripsi',
            self::CUSTOM => 'Dokumen Kustom',
        };
    }

    public function description(): string
    {
        return match ($this) {
            self::AUTO => 'Sistem akan mendeteksi tipe naskah berdasarkan susunan bab dan kata kunci secara otomatis.',
            self::SKRIPSI => 'Karya ilmiah monograf formal lengkap 5 bab (Pendahuluan s.d. Penutup).',
            self::MAKALAH => 'Karya tulis ilmiah atau tugas mata kuliah ringkas tanpa penomoran bab formal (BAB I-V).',
            self::LAPORAN_MAGANG => 'Laporan kegiatan praktik kerja lapangan / magang industri (Bab I s.d. Bab IV).',
            self::PROPOSAL_PENELITIAN => 'Rancangan usulan penelitian sebelum riset lapangan (Bab I - III disertai Jadwal).',
            self::CUSTOM => 'Dokumen umum dengan urutan bagian bebas.',
        };
    }
}
