<?php

namespace App\Services;

use App\Enums\JobStatus;
use App\Models\Document;
use App\Models\Finding;
use App\Models\FixLog;
use Exception;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;
use Symfony\Component\Process\Process;

class FixApplier
{
    public function __construct(
        protected DocumentAnalyzerService $analyzer
    ) {}

    /**
     * Apply automated safe repairs on a document without overwriting original.
     *
     * Non-negotiable Invariants:
     * 1. Original file is NEVER overwritten; a new file is created at fixed/{uuid}.docx.
     * 2. After fixing, re-analysis is run by orchestrator; if residual or new findings appear,
     *    automatic rollback is performed and no fixed file or log is saved.
     * 3. Text-altering rules (like B002) are excluded from batch 'Rapikan Semua Sekaligus'.
     *
     * @param Document $document
     * @param array<string>|null $findingIds Specific finding IDs to fix, or null for batch safe findings
     * @param bool $allowTextChanges
     * @return FixLog
     * @throws Exception
     */
    public function applyFix(Document $document, ?array $findingIds = null, bool $allowTextChanges = false): FixLog
    {
        $storageDir = storage_path('app/documents');
        $srcFullPath = $storageDir . DIRECTORY_SEPARATOR . $document->storage_path;

        if (!file_exists($srcFullPath)) {
            throw new Exception("Berkas asli tidak ditemukan: {$srcFullPath}");
        }

        // Query target findings
        $query = Finding::where('document_id', $document->id);

        if (!empty($findingIds)) {
            $query->whereIn('id', $findingIds);
        } else {
            // Batch mode: ONLY mechanical formatting fixes; strictly exclude B002/text-altering rules
            $query->where('auto_fixable', true)
                  ->where('rule_id', '!=', 'B002')
                  ->where('status', 'open');
        }

        $findings = $query->get();
        if ($findings->isEmpty()) {
            throw new Exception("Tidak ada temuan format yang dapat diperbaiki otomatis pada pilihan ini.");
        }

        // Generate target output path for fixed copy (Never overwrite original!)
        $fixedUuid = (string) Str::uuid();
        $ext = $document->file_type->value;
        $fixedRelPath = "fixed/{$fixedUuid}.{$ext}";
        $fixedFullPath = $storageDir . DIRECTORY_SEPARATOR . $fixedRelPath;

        // Ensure fixed directory exists
        if (!is_dir(dirname($fixedFullPath))) {
            mkdir(dirname($fixedFullPath), 0755, true);
        }

        // Prepare findings JSON for python fixer
        $findingsPayload = $findings->map(function ($f) {
            return [
                'rule_id' => $f->rule_id,
                'rule_name' => $f->rule_name,
                'severity' => $f->severity->value,
                'location' => [
                    'id' => $f->location_id,
                    'type' => $f->location_type->value,
                    'label' => $f->location_label,
                    'section_index' => $f->section_index,
                ],
                'evidence' => $f->evidence_current,
                'auto_fixable' => $f->auto_fixable,
                'changes_text' => ($f->rule_id === 'B002'),
                'suggestion' => $f->suggestion_text,
                'guide_module_slug' => $f->guide_module_slug,
            ];
        })->toArray();

        $tmpJson = tempnam(sys_get_temp_dir(), 'findings_');
        file_put_contents($tmpJson, json_encode($findingsPayload));

        // Call Python fixer CLI
        $pythonPath = config('rapikan.python_path', base_path('python/.venv/Scripts/python.exe'));
        if (!file_exists($pythonPath)) {
            $pythonPath = 'python';
        }

        $cmd = [
            $pythonPath,
            '-m',
            'rapikan.main',
            'fix',
            $document->storage_path,
            $fixedRelPath,
            '--findings-json',
            $tmpJson,
        ];

        if ($allowTextChanges || (!empty($findingIds) && count($findingIds) === 1)) {
            $cmd[] = '--allow-text-changes';
        }

        $process = new Process($cmd, base_path('python'), [
            'PYTHONPATH' => base_path('python'),
            'RAPIKAN_BASE_DOCUMENTS_DIR' => $storageDir,
        ]);

        $process->setTimeout(180);
        $process->run();

        if (file_exists($tmpJson)) {
            @unlink($tmpJson);
        }

        if (!$process->isSuccessful()) {
            if (file_exists($fixedFullPath)) {
                @unlink($fixedFullPath);
            }
            $err = $process->getErrorOutput() ?: $process->getOutput();
            throw new Exception("Gagal menjalankan perapian (Rollback otomatis dilakukan): " . $err);
        }

        $output = json_decode($process->getOutput(), true);
        if (!$output || !isset($output['status']) || $output['status'] !== 'success') {
            if (file_exists($fixedFullPath)) {
                @unlink($fixedFullPath);
            }
            throw new Exception("Keluaran perapian tidak valid atau rollback dipicu: " . substr($process->getOutput(), 0, 500));
        }

        $summary = $output['summary'] ?? [];

        // Invariant 4 check: reanalysis_clean MUST be True
        if (empty($summary['reanalysis_clean'])) {
            if (file_exists($fixedFullPath)) {
                @unlink($fixedFullPath);
            }
            throw new Exception("Violasi Invarian 4: Analisis ulang tidak bersih. Rollback dilakukan.");
        }

        DB::beginTransaction();
        try {
            // Update applied findings status
            $appliedRuleIds = $summary['applied_rule_ids'] ?? [];
            Finding::whereIn('id', $findings->pluck('id'))
                ->whereIn('rule_id', $appliedRuleIds)
                ->update(['status' => 'fixed']);

            // Create FixLog
            $fixLog = FixLog::create([
                'document_id' => $document->id,
                'finding_id' => $findings->first()->id,
                'fixed_storage_path' => $fixedRelPath,
                'change_summary' => $summary,
                'applied_at' => now(),
                'reanalysis_clean' => true,
            ]);

            DB::commit();
            return $fixLog;

        } catch (Exception $e) {
            DB::rollBack();
            if (file_exists($fixedFullPath)) {
                @unlink($fixedFullPath);
            }
            throw $e;
        }
    }
}
