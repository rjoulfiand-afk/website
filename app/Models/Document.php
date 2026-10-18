<?php

namespace App\Models;

use App\Enums\DocumentGenre;
use App\Enums\FileType;
use App\Enums\JobStatus;
use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\HasOne;

class Document extends Model
{
    use HasFactory, HasUuids;

    protected $fillable = [
        'user_id',
        'original_filename',
        'file_type',
        'detection_confidence',
        'storage_path',
        'file_hash',
        'file_size_bytes',
        'campus_profile_id',
        'genre',
        'genre_detected',
        'genre_confidence',
        'genre_markers',
        'status',
        'ir_path',
        'paragraphs_count',
        'tables_count',
        'text_hash',
        'llm_consent_given',
        'expires_at',
    ];

    protected $casts = [
        'file_type' => FileType::class,
        'genre' => DocumentGenre::class,
        'genre_detected' => DocumentGenre::class,
        'genre_confidence' => 'float',
        'genre_markers' => 'array',
        'status' => JobStatus::class,
        'detection_confidence' => 'float',
        'file_size_bytes' => 'integer',
        'paragraphs_count' => 'integer',
        'tables_count' => 'integer',
        'llm_consent_given' => 'boolean',
        'expires_at' => 'datetime',
    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function campusProfile(): BelongsTo
    {
        return $this->belongsTo(CampusProfile::class);
    }

    public function analysisRuns(): HasMany
    {
        return $this->hasMany(AnalysisRun::class)->orderBy('run_number', 'desc');
    }

    public function latestAnalysisRun(): HasOne
    {
        return $this->hasOne(AnalysisRun::class)->latestOfMany('run_number');
    }

    public function findings(): HasMany
    {
        return $this->hasMany(Finding::class);
    }

    public function fixLogs(): HasMany
    {
        return $this->hasMany(FixLog::class);
    }
}
