<?php

namespace App\Jobs;

use App\Models\Document;
use App\Services\FixApplier;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;

class ApplyFix implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $timeout = 300;

    public function __construct(
        public Document $document,
        public ?array $findingIds = null
    ) {}

    public function handle(FixApplier $fixer): void
    {
        $fixer->applyFix($this->document, $this->findingIds);
    }
}
