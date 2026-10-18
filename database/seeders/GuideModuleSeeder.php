<?php

namespace Database\Seeders;

use App\Models\GuideModule;
use Illuminate\Database\Seeder;

class GuideModuleSeeder extends Seeder
{
    public function run(): void
    {
        $modules = [
            [
                'slug' => 'word-heading-style',
                'app_target' => 'Microsoft Word / Google Docs',
                'title' => 'Penerapan Style Heading Resmi (Judul & Subbab)',
                'definition' => 'Heading Style adalah format struktural bawaan Microsoft Word (Heading 1, Heading 2, dst.) yang menandai hierarki bab dan subbab secara semantik, bukan sekadar teks biasa yang ditebalkan dan diperbesar.',
                'when_to_use' => 'Gunakan setiap kali menuliskan judul bab (misal: BAB I PENDAHULUAN) dan subbab (misal: 1.1 Latar Belakang). Ini wajib agar Daftar Isi dan panel navigasi dokumen dapat berfungsi otomatis.',
                'how_to_use' => "1. Sorot teks judul bab atau subbab.\n2. Pada pita menu 'Home' (Beranda), buka galeri 'Styles'.\n3. Klik 'Heading 1' untuk judul bab utama, atau 'Heading 2' untuk subbab level 2.",
                'how_to_remove' => "Sorot teks, lalu pada galeri 'Styles' pilih style 'Normal'. Format teks akan kembali menjadi paragraf standar.",
                'how_to_fix' => "1. Klik kanan pada 'Heading 1' di galeri Styles -> pilih 'Modify' (Ubah).\n2. Atur font ke 'Times New Roman', ukuran 12pt atau 14pt tebal, warna Hitam otomatis.\n3. Jangan menebalkan atau mengubah ukuran font secara manual per paragraf; biarkan style yang mengaturnya.",
                'common_mistakes' => "Mengetik judul bab dengan style 'Normal' lalu menekan tombol Ctrl+B (Tebal) dan menaikkan font ke 14pt secara manual. Dokumen terlihat seperti judul tetapi tidak terdeteksi oleh mesin Daftar Isi otomatis Word.",
                'example_before' => "Style: Normal | Font: 14pt Bold manual\nBAB I PENDAHULUAN",
                'example_after' => "Style: Heading 1 (Word Native) | Font: Sesuai Style Panduan\nBAB I PENDAHULUAN",
                'app_version_verified' => 'Microsoft 365 Word / Word 2021',
                'verified_at' => null, // Wajib null sampai diverifikasi langsung oleh user di Word
                'is_published' => true,
            ],
            [
                'slug' => 'word-toc',
                'app_target' => 'Microsoft Word / Google Docs',
                'title' => 'Pembuatan & Pembaruan Daftar Isi Otomatis',
                'definition' => 'Daftar Isi Otomatis (Table of Contents / TOC) adalah bidang khusus (field code) yang secara dinamis memindai seluruh dokumen untuk mengumpulkan judul berkategori Heading beserta nomor halamannya.',
                'when_to_use' => 'Gunakan pada halaman Daftar Isi setelah halaman Pengesahan/Abstrak. Jangan pernah membuat daftar isi dengan mengetik judul dan titik-titik manual.',
                'how_to_use' => "1. Letakkan kursor di halaman kosong Daftar Isi.\n2. Buka tab 'References' (Referensi) -> klik 'Table of Contents'.\n3. Pilih 'Automatic Table 1' atau 'Automatic Table 2'.",
                'how_to_remove' => "Buka tab 'References' -> klik 'Table of Contents' -> pilih 'Remove Table of Contents' di bagian paling bawah.",
                'how_to_fix' => "Bila ada perubahan halaman atau penambahan subbab:\n1. Klik kanan pada area Daftar Isi -> pilih 'Update Field' (Perbarui Bidang).\n2. Pilih 'Update entire table' (Perbarui seluruh tabel) lalu klik OK.",
                'common_mistakes' => "Mengetik judul bab lalu menekan tombol titik (.) berkali-kali sampai ujung kanan halaman lalu mengetik nomor halaman manual. Saat naskah bergeser, titik-titik akan berantakan dan nomor halaman menjadi salah.",
                'example_before' => "BAB I PENDAHULUAN............................................... 1\n1.1 Latar Belakang........................................ 1 (diketik manual)",
                'example_after' => "{TOC \\o \"1-3\" \\h \\z \\u} (Bidang Otomatis Word yang tersinkronisasi)",
                'app_version_verified' => 'Microsoft 365 Word / Word 2021',
                'verified_at' => null, // Wajib null sampai diverifikasi langsung oleh user di Word
                'is_published' => true,
            ],
            [
                'slug' => 'word-table-format',
                'app_target' => 'Microsoft Word / Google Docs',
                'title' => 'Format Tabel Standar Akademik & Header Berulang',
                'definition' => 'Format tabel akademik mensyaratkan baris judul tabel (header row) ditebalkan dan ditandai dengan opsi Repeat as Header Row (w:tblHeader) sehingga otomatis muncul kembali jika tabel terpotong ke halaman berikutnya.',
                'when_to_use' => 'Gunakan pada semua tabel data dalam naskah laporan atau skripsi, terutama tabel yang memiliki lebih dari 3 baris data atau berpotensi melompati batas halaman.',
                'how_to_use' => "1. Klik baris pertama (baris judul/header) pada tabel.\n2. Buka tab 'Layout' (Tata Letak Tabel) pada pita menu atas.\n3. Klik tombol 'Repeat Header Rows' (Ulangi Baris Header).",
                'how_to_remove' => "Klik baris pertama tabel -> pada tab 'Layout', nonaktifkan tombol 'Repeat Header Rows'.",
                'how_to_fix' => "1. Pastikan teks pada baris header ditebalkan (Bold) dan rata tengah/kiri konsisten.\n2. Klik kanan tabel -> 'Table Properties' -> tab 'Row' -> centang 'Repeat as header row at the top of each page'.",
                'common_mistakes' => "Membuat tabel panjang yang terpotong ke halaman berikutnya tanpa menyertakan baris judul di halaman kedua, atau menyalin ulang baris judul secara manual sebagai baris data biasa di halaman berikutnya.",
                'example_before' => "Tabel terpotong ke halaman 2 langsung menampilkan angka tanpa judul kolom.",
                'example_after' => "Baris header 'No | Variabel | Nilai | Keterangan' otomatis berulang di bagian atas halaman 2.",
                'app_version_verified' => 'Microsoft 365 Word / Word 2021',
                'verified_at' => null, // Wajib null sampai diverifikasi langsung oleh user di Word
                'is_published' => true,
            ],
            [
                'slug' => 'word-spacing',
                'app_target' => 'Microsoft Word / Google Docs',
                'title' => 'Pengaturan Jarak Spasi Antar Paragraf & Baris',
                'definition' => 'Pengaturan spasi standar dilakukan melalui atribut Paragraf (Before/After Spacing dan Line Spacing), bukan dengan menekan tombol Enter (paragraf kosong) berulang kali untuk memberi jarak.',
                'when_to_use' => 'Gunakan untuk mengatur jarak antara judul bab dengan subbab, atau antar paragraf dalam satu bab.',
                'how_to_use' => "1. Sorot paragraf yang ingin diatur jaraknya.\n2. Pada tab 'Home', klik ikon peluncur dialog 'Paragraph' (tanda panah kecil di pojok kanan bawah grup Paragraf).\n3. Di bagian 'Spacing', atur 'Before' (Sebelum) dan 'After' (Sesudah) misalnya 6pt atau 12pt, serta 'Line spacing' ke 1.5 baris.",
                'how_to_remove' => "Atur nilai Spacing 'Before' dan 'After' kembali ke 0pt.",
                'how_to_fix' => "Hapus semua baris kosong yang dihasilkan dari penekanan Enter berulang kali. Atur jarak vertikal dengan properti 'Space After' pada paragraf sebelum, atau 'Space Before' pada paragraf sesudahnya.",
                'common_mistakes' => "Menekan Enter 3 sampai 5 kali untuk menurunkan judul bab atau memisahkan paragraf. Saat dokumen dibuka di komputer lain dengan printer driver berbeda, jarak akan bergeser dan merusak tata letak.",
                'example_before' => "Paragraf 1.\n[Enter]\n[Enter]\n[Enter]\nParagraf 2.",
                'example_after' => "Paragraf 1 (dengan atribut Space After = 12pt, tanpa paragraf kosong tambahan).\nParagraf 2.",
                'app_version_verified' => 'Microsoft 365 Word / Word 2021',
                'verified_at' => null, // Wajib null sampai diverifikasi langsung oleh user di Word
                'is_published' => true,
            ],
            [
                'slug' => 'word-bahasa-indonesia',
                'app_target' => 'Microsoft Word / Bahasa & Tipografi',
                'title' => 'Kaidah Kata Baku KBBI & Kebersihan Tipografi',
                'definition' => 'Penulisan karya ilmiah wajib mematuhi ragam bahasa formal baku sesuai KBBI daring (Badan Pengembangan dan Pembinaan Bahasa, Kemendikbudristek) dan Pedoman Umum Ejaan Bahasa Indonesia (EYD V), termasuk menghindari spasi ganda.',
                'when_to_use' => 'Diterapkan pada seluruh isi teks naskah laporan, pembatasan masalah, hingga bagian kesimpulan.',
                'how_to_use' => "1. Gunakan rujukan resmi KBBI daring (kbbi.kemdikbud.go.id).\n2. Gunakan fitur 'Find and Replace' (Ctrl+H) untuk menormalkan spasi ganda menjadi spasi tunggal.",
                'how_to_remove' => "Tidak ada; kebersihan tipografi dan kebakuan kata adalah syarat mutlak karya ilmiah.",
                'how_to_fix' => "Ganti kata tidak baku dengan bentuk baku berimbuhan yang tepat sesuai entri resmi KBBI daring:\n- 'praktek' -> 'praktik'\n- 'analisa' -> 'analisis'\n- 'merubah' -> 'mengubah'\n- 'dirubah' -> 'diubah'\n- 'kualitas' bukan 'kwalitas'\n- 'jadwal' bukan 'jadual'",
                'common_mistakes' => "1. Mengetik spasi ganda setelah tanda titik atau di antara kata.\n2. Menggunakan bentuk turunan yang salah (misal: 'merubah' yang berasal dari kata dasar 'ubah' seharusnya 'mengubah').\n3. Tertukar antara awalan 'di-' dengan kata depan 'di'.",
                'example_before' => "Praktek  analisa data dilakukan untuk merubah paradigma.",
                'example_after' => "Praktik analisis data dilakukan untuk mengubah paradigma.",
                'app_version_verified' => 'KBBI daring (Badan Pengembangan dan Pembinaan Bahasa)',
                'verified_at' => null, // Wajib null sampai diverifikasi langsung oleh user di Word
                'is_published' => true,
            ],
        ];

        foreach ($modules as $m) {
            GuideModule::updateOrCreate(
                ['slug' => $m['slug']],
                $m
            );
        }
    }
}
