<?php

namespace Tests\Feature;

use App\Enums\JobStatus;
use App\Enums\Severity;
use App\Livewire\FindingsList;
use App\Livewire\ReportPage;
use App\Livewire\UploadForm;
use App\Models\CampusProfile;
use App\Models\Document;
use App\Models\Finding;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Queue;
use Illuminate\Support\Facades\Storage;
use Livewire\Livewire;
use Tests\TestCase;
use ZipArchive;

class UploadTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        Storage::fake('documents');
    }

    protected function createFakeDocx(string $filename = 'test.docx'): UploadedFile
    {
        $tempPath = tempnam(sys_get_temp_dir(), 'docx_');
        $zip = new ZipArchive();
        $zip->open($tempPath, ZipArchive::CREATE);
        $zip->addFromString('[Content_Types].xml', '<Types></Types>');
        $zip->addFromString('word/document.xml', '<w:document></w:document>');
        $zip->close();

        $content = file_get_contents($tempPath);
        unlink($tempPath);

        return UploadedFile::fake()->createWithContent($filename, $content);
    }

    public function test_home_page_renders_upload_form(): void
    {
        $response = $this->get('/');
        $response->assertStatus(200);
        $response->assertSee('Rapikan');
        $response->assertSee('Periksa Kerapian Naskah');
    }

    public function test_can_upload_valid_docx_and_creates_document(): void
    {
        Queue::fake();

        $profile = CampusProfile::create([
            'slug' => 'test-profile',
            'name' => 'Universitas Uji Coba',
            'version' => '1.0.0',
            'verified' => false,
            'config' => [],
        ]);

        $file = $this->createFakeDocx('skripsi_budi.docx');

        Livewire::test(UploadForm::class)
            ->set('file', $file)
            ->set('campusProfileId', $profile->id)
            ->set('llmConsent', true)
            ->call('processUpload')
            ->assertHasNoErrors()
            ->assertRedirect();

        $this->assertDatabaseHas('documents', [
            'original_filename' => 'skripsi_budi.docx',
            'file_type' => 'docx',
            'llm_consent_given' => true,
        ]);
    }

    public function test_rejects_malicious_exe_renamed_to_docx(): void
    {
        Queue::fake();

        $tempPath = tempnam(sys_get_temp_dir(), 'exe_');
        file_put_contents($tempPath, "MZ\x90\x00\x03\x00\x00\x00\x04\x00");
        $content = file_get_contents($tempPath);
        unlink($tempPath);
        $fakeExe = UploadedFile::fake()->createWithContent('evil.docx', $content);

        Livewire::test(UploadForm::class)
            ->set('file', $fakeExe)
            ->call('processUpload')
            ->assertSee('executable (MZ)');

        $this->assertDatabaseCount('documents', 0);
    }

    public function test_report_page_displays_document_and_warning_for_unverified_profile(): void
    {
        $profile = CampusProfile::create([
            'slug' => 'unverified-campus',
            'name' => 'Kampus Belum Terverifikasi',
            'version' => '1.0.0',
            'verified' => false, // triggers warning
            'config' => [],
        ]);

        $doc = Document::create([
            'original_filename' => 'laporan_magang.docx',
            'file_type' => 'docx',
            'detection_confidence' => 0.99,
            'storage_path' => 'raw/sample.docx',
            'file_hash' => hash('sha256', 'dummy'),
            'file_size_bytes' => 12345,
            'campus_profile_id' => $profile->id,
            'status' => JobStatus::DONE,
        ]);

        Finding::create([
            'document_id' => $doc->id,
            'rule_id' => 'W001',
            'rule_name' => 'Heading Palsu',
            'severity' => Severity::WARNING,
            'location_type' => 'paragraph',
            'location_id' => 'p_0005',
            'location_label' => 'Paragraf p_0005',
            'evidence_current' => ['snippet' => 'BAB I PENDAHULUAN'],
            'suggestion_text' => 'Ganti dengan Heading 1.',
            'auto_fixable' => true,
            'confidence' => 0.9,
            'status' => 'open',
        ]);

        Livewire::test(ReportPage::class, ['id' => $doc->id])
            ->assertSee('laporan_magang.docx')
            ->assertSee('Peringatan: Profil format ini belum diverifikasi')
            ->assertSee('Heading Palsu')
            ->assertSee('p_0005');
    }

    public function test_can_report_false_positive_feedback(): void
    {
        $doc = Document::create([
            'original_filename' => 'skripsi.docx',
            'file_type' => 'docx',
            'detection_confidence' => 0.99,
            'storage_path' => 'raw/sample.docx',
            'file_hash' => hash('sha256', 'dummy'),
            'file_size_bytes' => 12345,
            'status' => JobStatus::DONE,
        ]);

        $finding = Finding::create([
            'document_id' => $doc->id,
            'rule_id' => 'W003',
            'rule_name' => 'Font Mix',
            'severity' => Severity::WARNING,
            'location_type' => 'paragraph',
            'location_id' => 'p_0010',
            'location_label' => 'Paragraf p_0010',
            'evidence_current' => ['snippet' => 'Campuran font'],
            'suggestion_text' => 'Samakan font.',
            'status' => 'open',
        ]);

        Livewire::test(FindingsList::class, ['documentId' => $doc->id])
            ->call('openFeedbackModal', $finding->id)
            ->set('feedbackReason', 'Font sengaja berbeda untuk source code')
            ->call('submitFalsePositive')
            ->assertSee('laporan ketidaktepatan temuan telah disimpan');

        $this->assertDatabaseHas('finding_feedback', [
            'finding_id' => $finding->id,
            'is_false_positive' => true,
            'reason' => 'Font sengaja berbeda untuk source code',
        ]);

        $this->assertEquals('false_positive', $finding->fresh()->status);
    }
}
