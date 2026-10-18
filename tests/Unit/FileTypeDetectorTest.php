<?php

namespace Tests\Unit;

use App\Enums\FileType;
use App\Services\FileTypeDetector;
use Exception;
use Tests\TestCase;
use ZipArchive;

class FileTypeDetectorTest extends TestCase
{
    protected FileTypeDetector $detector;
    protected string $tmpDir;

    protected function setUp(): void
    {
        parent::setUp();
        $this->detector = new FileTypeDetector();
        $this->tmpDir = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'rapikan_test_' . uniqid();
        mkdir($this->tmpDir, 0777, true);
    }

    protected function tearDown(): void
    {
        // Cleanup temp dir
        if (is_dir($this->tmpDir)) {
            $files = glob($this->tmpDir . '/*');
            foreach ($files as $file) {
                if (is_file($file)) unlink($file);
            }
            rmdir($this->tmpDir);
        }
        parent::tearDown();
    }

    public function test_detects_pdf_by_magic_bytes(): void
    {
        $path = $this->tmpDir . '/test.pdf';
        file_put_contents($path, "%PDF-1.4\n%Test pdf content");

        $result = $this->detector->detect($path);
        $this->assertEquals(FileType::PDF, $result['file_type']);
        $this->assertEquals(1.0, $result['confidence']);
    }

    public function test_rejects_executable_renamed_to_docx(): void
    {
        $path = $this->tmpDir . '/malicious.docx';
        file_put_contents($path, "MZ\x90\x00\x03\x00\x00\x00\x04\x00");

        $this->expectException(Exception::class);
        $this->expectExceptionMessage('executable (MZ)');
        $this->detector->detect($path);
    }

    public function test_detects_docx_by_internal_word_structure(): void
    {
        $path = $this->tmpDir . '/sample.docx';
        $zip = new ZipArchive();
        $zip->open($path, ZipArchive::CREATE);
        $zip->addFromString('[Content_Types].xml', '<Types></Types>');
        $zip->addFromString('word/document.xml', '<w:document></w:document>');
        $zip->close();

        $result = $this->detector->detect($path);
        $this->assertEquals(FileType::DOCX, $result['file_type']);
    }

    public function test_detects_xlsx_by_internal_xl_structure(): void
    {
        $path = $this->tmpDir . '/sample.xlsx';
        $zip = new ZipArchive();
        $zip->open($path, ZipArchive::CREATE);
        $zip->addFromString('[Content_Types].xml', '<Types></Types>');
        $zip->addFromString('xl/workbook.xml', '<workbook></workbook>');
        $zip->close();

        $result = $this->detector->detect($path);
        $this->assertEquals(FileType::XLSX, $result['file_type']);
    }

    public function test_rejects_arbitrary_text_file(): void
    {
        $path = $this->tmpDir . '/plain.docx';
        file_put_contents($path, "Ini cuma file teks biasa.");

        $this->expectException(Exception::class);
        $this->detector->detect($path);
    }
}
