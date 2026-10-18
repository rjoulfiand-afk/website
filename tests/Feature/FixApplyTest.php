<?php

namespace Tests\Feature;

use App\Enums\JobStatus;
use App\Enums\Severity;
use App\Livewire\FindingsList;
use App\Livewire\ReportPage;
use App\Models\CampusProfile;
use App\Models\Document;
use App\Models\Finding;
use App\Models\FixLog;
use App\Models\GuideModule;
use App\Services\FixApplier;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Storage;
use Livewire\Livewire;
use Tests\TestCase;

class FixApplyTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        Storage::fake('documents');
    }

    public function test_cannot_overwrite_original_file_invariant(): void
    {
        $doc = Document::create([
            'original_filename' => 'skripsi_bab1.docx',
            'file_type' => 'docx',
            'detection_confidence' => 1.0,
            'storage_path' => 'raw/test_doc.docx',
            'file_hash' => hash('sha256', 'dummy'),
            'file_size_bytes' => 5000,
            'status' => JobStatus::DONE,
        ]);

        $finding = Finding::create([
            'document_id' => $doc->id,
            'rule_id' => 'W001',
            'rule_name' => 'Heading Palsu',
            'severity' => Severity::WARNING,
            'location_type' => 'paragraph',
            'location_id' => 'p_0001',
            'location_label' => 'Paragraf p_0001',
            'evidence_current' => ['snippet' => 'BAB I PENDAHULUAN'],
            'suggestion_text' => 'Gunakan style Heading 1.',
            'auto_fixable' => true,
            'confidence' => 0.95,
            'status' => 'open',
        ]);

        $fixLog = new FixLog([
            'id' => 'fixed-log-uuid-1234',
            'document_id' => $doc->id,
            'finding_id' => $finding->id,
            'fixed_storage_path' => 'fixed/fixed-uuid-1234.docx',
            'change_summary' => [
                'fixes_applied' => 1,
                'details' => [['rule_id' => 'W001', 'status' => 'applied']],
            ],
            'applied_at' => now(),
            'reanalysis_clean' => true,
        ]);
        $fixLog->save();

        $this->assertNotEquals($doc->storage_path, $fixLog->fixed_storage_path);
        $this->assertStringStartsWith('fixed/', $fixLog->fixed_storage_path);
        $this->assertStringStartsWith('raw/', $doc->storage_path);
    }

    public function test_livewire_can_open_guide_module_modal_with_8_sections_and_shows_belum_diverifikasi(): void
    {
        $guide = GuideModule::create([
            'slug' => 'word-heading-style',
            'app_target' => 'Microsoft Word / Google Docs',
            'title' => 'Penerapan Style Heading Resmi',
            'definition' => 'Heading Style adalah format struktural bawaan.',
            'when_to_use' => 'Gunakan setiap kali menuliskan judul bab.',
            'how_to_use' => 'Sorot teks lalu pilih Heading 1.',
            'how_to_remove' => 'Pilih Normal style.',
            'how_to_fix' => 'Klik kanan Heading 1 -> Modify.',
            'common_mistakes' => 'Mengetik dengan Normal lalu menebalkan manual.',
            'example_before' => 'BAB I (Bold manual)',
            'example_after' => 'BAB I (Heading 1)',
            'app_version_verified' => 'Word 365',
            'verified_at' => null, // Belum diverifikasi
            'is_published' => true,
        ]);

        $doc = Document::create([
            'original_filename' => 'skripsi.docx',
            'file_type' => 'docx',
            'detection_confidence' => 1.0,
            'storage_path' => 'raw/doc.docx',
            'file_hash' => hash('sha256', 'dummy'),
            'file_size_bytes' => 5000,
            'status' => JobStatus::DONE,
        ]);

        Finding::create([
            'document_id' => $doc->id,
            'rule_id' => 'W001',
            'rule_name' => 'Heading Palsu',
            'severity' => Severity::WARNING,
            'location_type' => 'paragraph',
            'location_id' => 'p_0001',
            'location_label' => 'Paragraf p_0001',
            'evidence_current' => ['snippet' => 'BAB I PENDAHULUAN'],
            'suggestion_text' => 'Gunakan Heading 1.',
            'auto_fixable' => true,
            'guide_module_slug' => 'word-heading-style',
            'status' => 'open',
        ]);

        Livewire::test(FindingsList::class, ['documentId' => $doc->id])
            ->call('openGuideModal', 'word-heading-style')
            ->assertSee('Penerapan Style Heading Resmi')
            ->assertSee('1. Definisi')
            ->assertSee('Heading Style adalah format struktural bawaan.')
            ->assertSee('2. Kapan Dipakai')
            ->assertSee('3. Cara Pakai (Standar Resmi)')
            ->assertSee('4. Cara Hapus / Batalkan')
            ->assertSee('5. Cara Merapikan / Memperbaiki')
            ->assertSee('6. Kesalahan Umum')
            ->assertSee('7. Contoh Sebelum dan Sesudah')
            ->assertSee('8. Versi Aplikasi dan Terakhir Diverifikasi')
            ->assertSee('Belum diverifikasi');
    }

    public function test_report_page_displays_auto_fix_banner_when_safe_findings_exist(): void
    {
        $doc = Document::create([
            'original_filename' => 'laporan.docx',
            'file_type' => 'docx',
            'detection_confidence' => 1.0,
            'storage_path' => 'raw/laporan.docx',
            'file_hash' => hash('sha256', 'dummy'),
            'file_size_bytes' => 5000,
            'status' => JobStatus::DONE,
        ]);

        Finding::create([
            'document_id' => $doc->id,
            'rule_id' => 'W008',
            'rule_name' => 'Spasi Manual Berulang',
            'severity' => Severity::WARNING,
            'location_type' => 'paragraph',
            'location_id' => 'p_0002',
            'location_label' => 'Paragraf p_0002',
            'evidence_current' => ['snippet' => '[Enter ganda]'],
            'suggestion_text' => 'Gunakan Space After.',
            'auto_fixable' => true,
            'status' => 'open',
        ]);

        Livewire::test(ReportPage::class, ['id' => $doc->id])
            ->assertSee('Perapian Format Otomatis Aman (1 Temuan)')
            ->assertSee('Rapikan Format Sekaligus');
    }

    public function test_report_page_displays_rewrite_proposal_notice_for_b002(): void
    {
        $doc = Document::create([
            'original_filename' => 'naskah.docx',
            'file_type' => 'docx',
            'detection_confidence' => 1.0,
            'storage_path' => 'raw/naskah.docx',
            'file_hash' => hash('sha256', 'dummy'),
            'file_size_bytes' => 5000,
            'status' => JobStatus::DONE,
        ]);

        Finding::create([
            'document_id' => $doc->id,
            'rule_id' => 'B002',
            'rule_name' => 'Pola Kata Tidak Baku',
            'severity' => Severity::WARNING,
            'location_type' => 'paragraph',
            'location_id' => 'p_0005',
            'location_label' => 'Paragraf p_0005',
            'evidence_current' => ['snippet' => 'praktek'],
            'suggestion_text' => 'Ganti dengan praktik.',
            'auto_fixable' => false,
            'status' => 'open',
        ]);

        Livewire::test(ReportPage::class, ['id' => $doc->id])
            ->assertSee('Tersedia 1 Usulan Penulisan Kata Baku (KBBI)')
            ->assertSee('tidak pernah dijalankan secara massal');

        Livewire::test(FindingsList::class, ['documentId' => $doc->id])
            ->assertSee('Usulan Kata Baku (Perlu Persetujuan)')
            ->assertSee('Setujui Usulan Kata');
    }

    public function test_download_fixed_document_sanitizes_filename_and_prevents_traversal(): void
    {
        $storageDir = storage_path('app/documents/fixed');
        if (!is_dir($storageDir)) {
            mkdir($storageDir, 0755, true);
        }

        $dummyFixedFile = $storageDir . DIRECTORY_SEPARATOR . 'test-download-fixed.docx';
        file_put_contents($dummyFixedFile, 'dummy fixed docx binary content');

        // File with potentially dangerous characters in original_filename
        $doc = Document::create([
            'original_filename' => '../../evil<script>:skripsi*final?.docx',
            'file_type' => 'docx',
            'detection_confidence' => 1.0,
            'storage_path' => 'raw/safe.docx',
            'file_hash' => hash('sha256', 'dummy'),
            'file_size_bytes' => 5000,
            'status' => JobStatus::DONE,
        ]);

        $finding = Finding::create([
            'document_id' => $doc->id,
            'rule_id' => 'W001',
            'rule_name' => 'Heading Palsu',
            'severity' => Severity::WARNING,
            'location_type' => 'paragraph',
            'location_id' => 'p_0001',
            'location_label' => 'Paragraf p_0001',
            'evidence_current' => ['snippet' => 'dummy'],
            'suggestion_text' => 'dummy',
            'auto_fixable' => true,
            'confidence' => 0.95,
            'status' => 'fixed',
        ]);

        $fixLog = FixLog::create([
            'document_id' => $doc->id,
            'finding_id' => $finding->id,
            'fixed_storage_path' => 'fixed/test-download-fixed.docx',
            'change_summary' => ['fixes_applied' => 1],
            'applied_at' => now(),
            'reanalysis_clean' => true,
        ]);

        $response = $this->get(route('documents.download-fixed', [$doc->id, $fixLog->id]));
        $response->assertStatus(200);
        // Assert filename was sanitized: slashes, tags, colons, question marks stripped
        $response->assertHeader('content-disposition', 'attachment; filename="[Rapikan] evilscriptskripsifinal.docx"');

        @unlink($dummyFixedFile);
    }

    public function test_report_page_displays_preflight_warning_when_document_has_revisions_or_comments(): void
    {
        $doc = Document::create([
            'original_filename' => 'skripsi_revisi.docx',
            'file_type' => 'docx',
            'detection_confidence' => 1.0,
            'storage_path' => 'raw/skripsi_revisi.docx',
            'file_hash' => hash('sha256', 'dummy'),
            'file_size_bytes' => 5000,
            'status' => JobStatus::DONE,
        ]);

        Finding::create([
            'document_id' => $doc->id,
            'rule_id' => 'PRE_FLIGHT_REVISION',
            'rule_name' => 'Peringatan Dokumen Mengandung Revisi',
            'severity' => Severity::WARNING,
            'location_type' => 'document',
            'location_id' => 'doc_revisions',
            'location_label' => 'Seluruh Dokumen',
            'evidence_current' => ['snippet' => 'Tracked changes aktif'],
            'suggestion_text' => 'Terima atau tolak revisi terlebih dahulu.',
            'auto_fixable' => false,
            'status' => 'open',
        ]);

        Livewire::test(ReportPage::class, ['id' => $doc->id])
            ->assertSee('Peringatan Pre-Flight: Dokumen Mengandung Revisi atau Komentar Aktif')
            ->assertSee('Sangat disarankan untuk menerima atau menolak seluruh revisi');
    }
}
