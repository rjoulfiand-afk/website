<?php

namespace Database\Seeders;

use App\Models\CampusProfile;
use Illuminate\Database\Seeder;
use Illuminate\Support\Str;

class CampusProfileSeeder extends Seeder
{
    public function run(): void
    {
        CampusProfile::updateOrCreate(
            ['slug' => 'default'],
            [
                'id' => (string) Str::uuid(),
                'name' => 'Pedoman Standar Penulisan Karya Ilmiah',
                'version' => '1.0.0',
                'source_document' => 'Draft Standar Format Laporan & Skripsi',
                'guideline_year' => 2024,
                'verified' => false, // verified = false: UI shows warning banner
                'rules_yaml' => null,
                'config' => [
                    'margin_cm' => [
                        'top' => 4.0,
                        'bottom' => 3.0,
                        'left' => 4.0,
                        'right' => 3.0,
                    ],
                    'body_font' => [
                        'name' => 'Times New Roman',
                        'size_pt' => 12.0,
                    ],
                    'heading_font' => [
                        'name' => 'Times New Roman',
                        'size_pt' => 12.0,
                    ],
                    'fake_heading_min_size_pt' => 13.0,
                    'chapter_order' => [
                        'HALAMAN JUDUL',
                        'LEMBAR PERSETUJUAN',
                        'LEMBAR PENGESAHAN',
                        'ABSTRAK',
                        'ABSTRACT',
                        'KATA PENGANTAR',
                        'DAFTAR ISI',
                        'DAFTAR TABEL',
                        'DAFTAR GAMBAR',
                        'BAB I',
                        'BAB II',
                        'BAB III',
                        'BAB IV',
                        'BAB V',
                        'DAFTAR PUSTAKA',
                        'LAMPIRAN',
                    ],
                ],
                'is_active' => true,
            ]
        );
    }
}
