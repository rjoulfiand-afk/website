<?php

namespace App\Jobs;

use App\Models\Document;
use App\Services\DocumentAnalyzerService;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;

class DispatchAnalysis implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $timeout = 300; // 5 minutes max

    public function __construct(
        public Document $document
    ) {}

    public function handle(DocumentAnalyzerService $service): void
    {
        $service->analyze($this->document);
    }
}
