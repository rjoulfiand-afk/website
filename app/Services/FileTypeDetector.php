<?php

namespace App\Services;

use App\Enums\FileType;
use Exception;
use ZipArchive;

class FileTypeDetector
{
    /**
     * Detect file type from file content (magic bytes), not file extension.
     *
     * @param string $filePath Absolute path to the file on disk
     * @return array{file_type: FileType, confidence: float}
     * @throws Exception
     */
    public function detect(string $filePath): array
    {
        if (!file_exists($filePath)) {
            throw new Exception("File tidak ditemukan: {$filePath}");
        }

        $handle = fopen($filePath, 'rb');
        if (!$handle) {
            throw new Exception("Gagal membaca file untuk deteksi magic bytes.");
        }

        $header = fread($handle, 8);
        fclose($handle);

        // Check for PDF (%PDF)
        if (str_starts_with($header, "%PDF")) {
            return [
                'file_type' => FileType::PDF,
                'confidence' => 1.0,
            ];
        }

        // Check for Executable (MZ) - Dangerous!
        if (str_starts_with($header, "MZ")) {
            throw new Exception("Keamanan: File terdeteksi sebagai berkas executable (MZ), bukan dokumen valid.");
        }

        // Check for ZIP-based formats (PK\x03\x04)
        if (str_starts_with($header, "PK\x03\x04")) {
            return $this->detectZipType($filePath);
        }

        throw new Exception("Format berkas tidak didukung atau berkas rusak. Pastikan berkas berformat .docx, .xlsx, atau .pdf.");
    }

    /**
     * Differentiate DOCX vs XLSX from internal ZIP package structure.
     */
    protected function detectZipType(string $filePath): array
    {
        $zip = new ZipArchive();
        $res = $zip->open($filePath, ZipArchive::RDONLY);

        if ($res !== true) {
            throw new Exception("Berkas arsip dokumen tidak dapat dibuka atau rusak.");
        }

        $hasWord = false;
        $hasExcel = false;

        for ($i = 0; $i < $zip->numFiles; $i++) {
            $name = $zip->getNameIndex($i);
            if (str_starts_with($name, 'word/')) {
                $hasWord = true;
                break;
            }
            if (str_starts_with($name, 'xl/')) {
                $hasExcel = true;
                break;
            }
        }

        $zip->close();

        if ($hasWord) {
            return [
                'file_type' => FileType::DOCX,
                'confidence' => 0.99,
            ];
        }

        if ($hasExcel) {
            return [
                'file_type' => FileType::XLSX,
                'confidence' => 0.99,
            ];
        }

        throw new Exception("Berkas ZIP tidak memiliki struktur dokumen Word (word/) atau Excel (xl/) yang valid.");
    }
}
