<?php

namespace App\Livewire;

use App\Models\Document;
use App\Models\Finding;
use App\Models\FindingFeedback;
use App\Models\GuideModule;
use App\Services\FixApplier;
use Livewire\Attributes\On;
use Livewire\Component;
use Livewire\WithPagination;

class FindingsList extends Component
{
    use WithPagination;

    public string $documentId;
    public ?string $selectedRunId = null;
    public string $severityFilter = 'all'; // all, error, warning, info
    public ?bool $autoFixableOnly = null;
    public string $search = '';

    public ?string $feedbackFindingId = null;
    public string $feedbackReason = '';
    public ?string $feedbackSuccessMessage = null;

    public ?GuideModule $activeGuideModule = null;
    public ?string $fixSuccessMessage = null;
    public ?string $fixErrorMessage = null;

    public function mount(string $documentId, ?string $runId = null): void
    {
        $this->documentId = $documentId;
        $this->selectedRunId = $runId;
    }

    public function setSeverity(string $severity): void
    {
        $this->severityFilter = $severity;
        $this->resetPage();
    }

    public function toggleAutoFixable(): void
    {
        $this->autoFixableOnly = $this->autoFixableOnly ? null : true;
        $this->resetPage();
    }

    public function openFeedbackModal(string $findingId): void
    {
        $this->feedbackFindingId = $findingId;
        $this->feedbackReason = '';
        $this->feedbackSuccessMessage = null;
    }

    public function submitFalsePositive(): void
    {
        if (!$this->feedbackFindingId) {
            return;
        }

        FindingFeedback::create([
            'finding_id' => $this->feedbackFindingId,
            'user_id' => auth()->id(),
            'is_false_positive' => true,
            'reason' => $this->feedbackReason ?: 'Ditandai salah oleh pengguna.',
        ]);

        // Update finding status
        Finding::where('id', $this->feedbackFindingId)->update([
            'status' => 'false_positive',
        ]);

        $this->feedbackSuccessMessage = 'Terima kasih, laporan ketidaktepatan temuan telah disimpan.';
        $this->feedbackFindingId = null;
    }

    public function openGuideModal(string $slug): void
    {
        $this->activeGuideModule = GuideModule::where('slug', $slug)->first();
    }

    public function closeGuideModal(): void
    {
        $this->activeGuideModule = null;
    }

    public function applySingleFix(string $findingId, FixApplier $fixApplier, bool $isApprovedRewrite = false): void
    {
        $this->fixSuccessMessage = null;
        $this->fixErrorMessage = null;

        try {
            $document = Document::findOrFail($this->documentId);
            $fixLog = $fixApplier->applyFix($document, [$findingId], $isApprovedRewrite);

            $msg = $isApprovedRewrite 
                ? "Usulan kata baku disetujui & diterapkan. Salinan berkas baru telah diperbarui."
                : "Perbaikan format berhasil diterapkan. Berkas baru tersimpan di salinan aman.";

            $this->fixSuccessMessage = $msg;
            $this->dispatch('fix-completed', fixLogId: $fixLog->id);

        } catch (\Throwable $e) {
            $this->fixErrorMessage = "Gagal menerapkan perbaikan (Rollback dilakukan): " . $e->getMessage();
        }
    }

    #[On('refresh-findings')]
    public function refreshList(): void
    {
        // triggers re-render
    }

    public function render()
    {
        $query = Finding::where('document_id', $this->documentId);

        if ($this->selectedRunId) {
            $query->where('analysis_run_id', $this->selectedRunId);
        }

        if ($this->severityFilter !== 'all') {
            $query->where('severity', $this->severityFilter);
        }

        if ($this->autoFixableOnly) {
            $query->where('auto_fixable', true);
        }

        if (trim($this->search)) {
            $s = '%' . trim($this->search) . '%';
            $query->where(function ($q) use ($s) {
                $q->where('rule_id', 'like', $s)
                  ->orWhere('rule_name', 'like', $s)
                  ->orWhere('location_label', 'like', $s)
                  ->orWhere('suggestion_text', 'like', $s);
            });
        }

        $findings = $query->orderByRaw("
            CASE severity 
                WHEN 'error' THEN 1 
                WHEN 'warning' THEN 2 
                WHEN 'info' THEN 3 
                ELSE 4 
            END
        ")->paginate(15);

        return view('livewire.findings-list', [
            'findings' => $findings,
        ]);
    }
}
