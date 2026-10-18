<?php

namespace Tests\Feature;

use App\Enums\DocumentGenre;
use App\Enums\FileType;
use App\Enums\JobStatus;
use App\Livewire\ReportPage;
use App\Livewire\UploadForm;
use App\Models\CampusProfile;
use App\Models\Document;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Queue;
use Illuminate\Support\Facades\Storage;
use Livewire\Livewire;
use Tests\TestCase;
use ZipArchive;

class GenreTest extends TestCase
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

    public function test_can_upload_with_specific_genre(): void
    {
        Queue::fake();

        $file = $this->createFakeDocx('proposal_skripsi.docx');

        Livewire::test(UploadForm::class)
            ->set('file', $file)
            ->set('genre', DocumentGenre::PROPOSAL_PENELITIAN->value)
            ->call('processUpload')
            ->assertHasNoErrors();

        $doc = Document::latest()->first();
        $this->assertNotNull($doc);
        $this->assertEquals(DocumentGenre::PROPOSAL_PENELITIAN, $doc->genre);
    }

    public function test_can_upload_with_auto_detect_genre_as_default(): void
    {
        Queue::fake();

        $file = $this->createFakeDocx('makalah_ilmiah.docx');

        Livewire::test(UploadForm::class)
            ->set('file', $file)
            ->call('processUpload')
            ->assertHasNoErrors();

        $doc = Document::latest()->first();
        $this->assertNotNull($doc);
        $this->assertEquals(DocumentGenre::AUTO, $doc->genre);
    }

    public function test_report_page_displays_genre_badge(): void
    {
        $doc = Document::create([
            'original_filename' => 'makalah_etika.docx',
            'file_type' => FileType::DOCX,
            'detection_confidence' => 1.0,
            'storage_path' => 'raw/makalah.docx',
            'file_hash' => hash('sha256', 'dummy'),
            'file_size_bytes' => 1234,
            'genre' => DocumentGenre::MAKALAH,
            'genre_detected' => DocumentGenre::MAKALAH,
            'genre_confidence' => 0.92,
            'genre_markers' => ['Terdeteksi kata kunci Makalah', 'Tidak ada BAB formal'],
            'status' => JobStatus::DONE,
        ]);

        Livewire::test(ReportPage::class, ['id' => $doc->id])
            ->assertStatus(200)
            ->assertSee('Genre: Makalah / Paper Akademik')
            ->assertSee('92%')
            ->assertSee('Terdeteksi kata kunci Makalah');
    }
}
