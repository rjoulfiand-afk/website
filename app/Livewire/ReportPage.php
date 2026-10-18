<?php

namespace App\Livewire;

use App\Enums\JobStatus;
use App\Jobs\DispatchAnalysis;
use App\Models\AnalysisRun;
use App\Models\Document;
use App\Models\FixLog;
use App\Services\FixApplier;
use Livewire\Attributes\On;
use Livewire\Component;

class ReportPage extends Component
{
    public string $documentId;
    public ?string $currentRunId = null;

    public ?string $globalFixSuccess = null;
    public ?string $globalFixError = null;
    public ?string $latestFixLogId = null;

    public function mount(?string $id = null, ?string $documentId = null): void
    {
        $resolvedId = $id ?? $documentId ?? $this->documentId;
        $this->documentId = $resolvedId;
        $doc = Document::findOrFail($resolvedId);
        $latestRun = $doc->latestAnalysisRun;
        if ($latestRun) {
            $this->currentRunId = $latestRun->id;
        }

        $latestFix = FixLog::where('document_id', $this->documentId)->latest('applied_at')->first();
        if ($latestFix) {
            $this->latestFixLogId = $latestFix->id;
        }
    }

    public function reanalyze(): void
    {
        $doc = Document::findOrFail($this->documentId);
        $doc->update(['status' => JobStatus::QUEUED]);
        DispatchAnalysis::dispatch($doc);
        $this->dispatch('analysis-dispatched');
    }

    public function selectRun(string $runId): void
    {
        $this->currentRunId = $runId;
    }

    public function applyAllSafeFixes(FixApplier $fixApplier): void
    {
        $this->globalFixSuccess = null;
        $this->globalFixError = null;

        try {
            $doc = Document::findOrFail($this->documentId);
            // Apply only mechanical formatting fixes (Invariant 3: B002 excluded from batch)
            $fixLog = $fixApplier->applyFix($doc, null, false);

            $this->latestFixLogId = $fixLog->id;
            $appliedCount = $fixLog->change_summary['fixes_applied'] ?? 0;
            $this->globalFixSuccess = "Berhasil merapikan dokumen! Total {$appliedCount} perbaikan format aman diterapkan. File asli tetap utuh; salinan hasil perapian siap diunduh.";

            $this->dispatch('refresh-findings');

        } catch (\Throwable $e) {
            $this->globalFixError = "Gagal menjalankan perapian otomatis: " . $e->getMessage();
        }
    }

    #[On('fix-completed')]
    public function onFixCompleted(string $fixLogId): void
    {
        $this->latestFixLogId = $fixLogId;
        $this->dispatch('refresh-findings');
    }

    public function render()
    {
        $document = Document::with(['campusProfile', 'analysisRuns'])->findOrFail($this->documentId);
        $currentRun = $this->currentRunId
            ? AnalysisRun::find($this->currentRunId)
            : $document->latestAnalysisRun;

        // Invariant 3: B002 text-altering rules strictly excluded from batch count
        $autoFixableCount = $document->findings()
            ->where('auto_fixable', true)
            ->where('rule_id', '!=', 'B002')
            ->where('status', 'open')
            ->count();

        $rewriteProposalsCount = $document->findings()
            ->where('rule_id', 'B002')
            ->where('status', 'open')
            ->count();

        $fixedCount = $document->findings()
            ->where('status', 'fixed')
            ->count();

        $hasRevisionsOrComments = $document->findings()
            ->whereIn('rule_id', ['PRE_FLIGHT_REVISION', 'PRE_FLIGHT_COMMENT'])
            ->exists();
        $preflightWarningFinding = $document->findings()
            ->whereIn('rule_id', ['PRE_FLIGHT_REVISION', 'PRE_FLIGHT_COMMENT'])
            ->first();

        $latestFixLog = $this->latestFixLogId 
            ? FixLog::find($this->latestFixLogId) 
            : FixLog::where('document_id', $this->documentId)->latest('applied_at')->first();

        return view('livewire.report-page', [
            'document' => $document,
            'currentRun' => $currentRun,
            'autoFixableCount' => $autoFixableCount,
            'rewriteProposalsCount' => $rewriteProposalsCount,
            'fixedCount' => $fixedCount,
            'latestFixLog' => $latestFixLog,
            'hasRevisionsOrComments' => $hasRevisionsOrComments,
            'preflightWarningFinding' => $preflightWarningFinding,
        ])->layout('layouts.app', ['title' => 'Laporan Hasil Pemeriksaan - ' . $document->original_filename]);
    }
}
