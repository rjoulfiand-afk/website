<?php

namespace App\Models;

use App\Enums\LocationType;
use App\Enums\Severity;
use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Finding extends Model
{
    use HasFactory, HasUuids;

    public $timestamps = false;

    protected $fillable = [
        'document_id',
        'analysis_run_id',
        'rule_id',
        'rule_name',
        'severity',
        'location_type',
        'location_id',
        'location_label',
        'page_estimate',
        'page_is_estimate',
        'section_index',
        'evidence_current',
        'evidence_expected',
        'suggestion_text',
        'auto_fixable',
        'confidence',
        'status',
        'guide_module_id',
        'guide_module_slug',
        'llm_source',
        'llm_paragraph_ref',
        'llm_quote',
        'created_at',
    ];

    protected $casts = [
        'severity' => Severity::class,
        'location_type' => LocationType::class,
        'page_estimate' => 'integer',
        'page_is_estimate' => 'boolean',
        'section_index' => 'integer',
        'evidence_current' => 'array',
        'evidence_expected' => 'array',
        'auto_fixable' => 'boolean',
        'confidence' => 'float',
        'llm_source' => 'boolean',
        'created_at' => 'datetime',
    ];

    public function document(): BelongsTo
    {
        return $this->belongsTo(Document::class);
    }

    public function analysisRun(): BelongsTo
    {
        return $this->belongsTo(AnalysisRun::class);
    }

    public function guideModule(): BelongsTo
    {
        return $this->belongsTo(GuideModule::class);
    }

    public function feedback(): HasMany
    {
        return $this->hasMany(FindingFeedback::class);
    }

    public function rewriteProposals(): HasMany
    {
        return $this->hasMany(RewriteProposal::class);
    }
}
