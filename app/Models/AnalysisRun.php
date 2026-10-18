<?php

namespace App\Models;

use App\Enums\JobStatus;
use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class AnalysisRun extends Model
{
    use HasFactory, HasUuids;

    protected $fillable = [
        'document_id',
        'run_number',
        'status',
        'findings_count',
        'error_count',
        'warning_count',
        'info_count',
        'started_at',
        'completed_at',
        'error_message',
    ];

    protected $casts = [
        'status' => JobStatus::class,
        'run_number' => 'integer',
        'findings_count' => 'integer',
        'error_count' => 'integer',
        'warning_count' => 'integer',
        'info_count' => 'integer',
        'started_at' => 'datetime',
        'completed_at' => 'datetime',
    ];

    public function document(): BelongsTo
    {
        return $this->belongsTo(Document::class);
    }

    public function findings(): HasMany
    {
        return $this->hasMany(Finding::class);
    }
}
