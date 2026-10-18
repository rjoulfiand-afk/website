<?php

namespace App\Services;

use App\Enums\DocumentGenre;
use App\Enums\JobStatus;
use App\Enums\LocationType;
use App\Enums\Severity;
use App\Models\AnalysisRun;
use App\Models\Document;
use App\Models\Finding;
use Exception;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Symfony\Component\Process\Process;

class DocumentAnalyzerService
{
    /**
     * Run Python analysis engine on a document.
     *
     * @param Document $document
     * @return AnalysisRun
     * @throws Exception
     */
    public function analyze(Document $document): AnalysisRun
    {
        $document->update(['status' => JobStatus::PROCESSING]);

        // Determine run number
        $lastRunNumber = $document->analysisRuns()->max('run_number') ?? 0;
        $runNumber = $lastRunNumber + 1;

        $run = AnalysisRun::create([
            'document_id' => $document->id,
            'run_number' => $runNumber,
            'status' => JobStatus::PROCESSING,
            'started_at' => now(),
        ]);

        try {
            $pythonPath = config('rapikan.python_path', base_path('python/.venv/Scripts/python.exe'));
            if (!file_exists($pythonPath)) {
                // Fallback to system python or python3
                $pythonPath = 'python';
            }

            $storageDir = storage_path('app/documents');
            $fullDocPath = $storageDir . DIRECTORY_SEPARATOR . $document->storage_path;

            if (!file_exists($fullDocPath)) {
                throw new Exception("Dokumen tidak ditemukan di penyimpanan: {$fullDocPath}");
            }

            // Output paths for IR and findings
            $irRelPath = "ir/{$document->id}_run{$runNumber}.json.gz";
            $irFullPath = $storageDir . DIRECTORY_SEPARATOR . $irRelPath;

            $findingsRelPath = "findings/{$document->id}_run{$runNumber}.json";
            $findingsFullPath = $storageDir . DIRECTORY_SEPARATOR . $findingsRelPath;

            // Build CLI command
            $cmd = [
                $pythonPath,
                '-m',
                'rapikan.main',
                'analyze',
                $document->storage_path,
                '--out-ir',
                $irFullPath,
                '--out-findings',
                $findingsFullPath,
            ];

            if ($document->campusProfile && $document->campusProfile->slug) {
                $cmd[] = '--profile';
                $cmd[] = $document->campusProfile->slug;
            }

            if ($document->genre && $document->genre !== DocumentGenre::AUTO) {
                $cmd[] = '--genre';
                $cmd[] = $document->genre->value;
            }

            $process = new Process($cmd, base_path('python'), [
                'PYTHONPATH' => base_path('python'),
                'RAPIKAN_BASE_DOCUMENTS_DIR' => $storageDir,
            ]);

            $process->setTimeout(180); // 3 minutes timeout
            $process->run();

            if (!$process->isSuccessful()) {
                $errorOutput = $process->getErrorOutput() ?: $process->getOutput();
                throw new Exception("Mesin analisis gagal: " . $errorOutput);
            }

            $stdout = $process->getOutput();
            $result = json_decode($stdout, true);

            if (!$result || !isset($result['status']) || $result['status'] !== 'success') {
                throw new Exception("Format keluaran analisis tidak valid: " . substr($stdout, 0, 500));
            }

            DB::beginTransaction();

            $findingsData = $result['findings'] ?? [];
            $errorCount = 0;
            $warningCount = 0;
            $infoCount = 0;

            foreach ($findingsData as $f) {
                $sev = $f['severity'] ?? 'info';
                if ($sev === 'error') $errorCount++;
                elseif ($sev === 'warning') $warningCount++;
                else $infoCount++;

                $loc = $f['location'] ?? [];
                $ev = $f['evidence'] ?? [];

                Finding::create([
                    'document_id' => $document->id,
                    'analysis_run_id' => $run->id,
                    'rule_id' => $f['rule_id'] ?? 'UNKNOWN',
                    'rule_name' => $f['rule_name'] ?? 'Pemeriksaan',
                    'severity' => Severity::tryFrom($sev) ?? Severity::INFO,
                    'location_type' => LocationType::tryFrom($loc['type'] ?? 'paragraph') ?? LocationType::PARAGRAPH,
                    'location_id' => $loc['id'] ?? 'unknown',
                    'location_label' => $loc['label'] ?? 'Lokasi tidak diketahui',
                    'page_estimate' => $loc['page_estimate'] ?? null,
                    'page_is_estimate' => $loc['page_is_estimate'] ?? true,
                    'section_index' => $loc['section_index'] ?? null,
                    'evidence_current' => $ev,
                    'evidence_expected' => null,
                    'suggestion_text' => $f['suggestion'] ?? 'Periksa bagian ini.',
                    'auto_fixable' => (bool) ($f['auto_fixable'] ?? false),
                    'confidence' => (float) ($f['confidence'] ?? 1.0),
                    'status' => 'open',
                    'guide_module_slug' => $f['guide_module_slug'] ?? null,
                    'llm_source' => false,
                ]);
            }

            $run->update([
                'status' => JobStatus::DONE,
                'completed_at' => now(),
                'findings_count' => count($findingsData),
                'error_count' => $errorCount,
                'warning_count' => $warningCount,
                'info_count' => $infoCount,
            ]);

            $genreData = $result['genre'] ?? [];
            $docUpdates = [
                'status' => JobStatus::DONE,
                'ir_path' => $irRelPath,
                'paragraphs_count' => $result['paragraphs_count'] ?? null,
                'tables_count' => $result['tables_count'] ?? null,
            ];

            if (!empty($genreData)) {
                $docUpdates['genre_detected'] = DocumentGenre::tryFrom($genreData['detected'] ?? '') ?? DocumentGenre::SKRIPSI;
                $docUpdates['genre_confidence'] = (float) ($genreData['confidence'] ?? 1.0);
                $docUpdates['genre_markers'] = $genreData['markers'] ?? [];
                if ($document->genre === DocumentGenre::AUTO || !$document->genre) {
                    $docUpdates['genre'] = DocumentGenre::tryFrom($genreData['applied'] ?? '') ?? DocumentGenre::SKRIPSI;
                }
            }

            $document->update($docUpdates);

            DB::commit();
            return $run;

        } catch (Exception $e) {
            DB::rollBack();
            Log::error("Analysis failed for document {$document->id}: " . $e->getMessage());

            $run->update([
                'status' => JobStatus::FAILED,
                'completed_at' => now(),
                'error_message' => $e->getMessage(),
            ]);

            $document->update([
                'status' => JobStatus::FAILED,
            ]);

            throw $e;
        }
    }
}
