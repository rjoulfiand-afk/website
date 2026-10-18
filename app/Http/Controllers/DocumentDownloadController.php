<?php

namespace App\Http\Controllers;

use App\Models\Document;
use App\Models\FixLog;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\BinaryFileResponse;

class DocumentDownloadController extends Controller
{
    /**
     * Download the fixed document copy safely with IDOR protection & filename sanitization.
     */
    public function downloadFixed(Request $request, string $id, ?string $fixLogId = null): BinaryFileResponse
    {
        $document = Document::findOrFail($id);

        // Ownership check (IDOR guard)
        if ($document->user_id && auth()->check() && auth()->id() !== $document->user_id) {
            abort(403, 'Anda tidak memiliki hak akses untuk mengunduh berkas ini.');
        }

        // Scoped query: fixLog must strictly belong to this document
        if ($fixLogId) {
            $fixLog = FixLog::where('document_id', $document->id)->findOrFail($fixLogId);
        } else {
            $fixLog = FixLog::where('document_id', $document->id)->latest('applied_at')->firstOrFail();
        }

        $storageDir = storage_path('app/documents');
        $fullPath = $storageDir . DIRECTORY_SEPARATOR . $fixLog->fixed_storage_path;

        // Path Traversal Security check: Must strictly reside within storage/app/documents/fixed
        $realPath = realpath($fullPath);
        $expectedDir = realpath($storageDir . DIRECTORY_SEPARATOR . 'fixed');

        if (!$realPath || !$expectedDir || !str_starts_with($realPath, $expectedDir)) {
            abort(404, 'Berkas hasil perbaikan tidak ditemukan.');
        }

        // Filename Sanitization: Strip dangerous characters, control bytes, and traversal tokens
        $rawName = pathinfo($document->original_filename, PATHINFO_FILENAME);
        $sanitized = preg_replace('/[^\p{L}\p{N}_\-\.\s]/u', '', $rawName);
        $sanitized = trim(preg_replace('/\s+/', ' ', $sanitized));
        if (empty($sanitized)) {
            $sanitized = 'dokumen';
        }

        $ext = strtolower(pathinfo($document->original_filename, PATHINFO_EXTENSION)) ?: 'docx';
        if (!in_array($ext, ['docx', 'xlsx', 'pdf'])) {
            $ext = 'docx';
        }

        $downloadName = "[Rapikan] {$sanitized}.{$ext}";

        return response()->download($realPath, $downloadName, [
            'Content-Type' => 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        ]);
    }
}
